"""Booking lifecycle generation (TAD sections 8 and 16).

Emits only transitions allowed by ``ALLOWED_TRANSITIONS`` with strictly
monotonic event timestamps, and keeps booking IDs stable across reschedules.
Fixture/edge-case bookings live in ``fixtures.py``.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from generator.config import (
    ACCEPTANCE_WINDOW_MINUTES,
    ACTOR_CUSTOMER,
    ACTOR_PROVIDER,
    ACTOR_SYSTEM,
    ALLOWED_TRANSITIONS,
    CANCELLATION_REASONS_CUSTOMER,
    CANCELLATION_REASONS_PROVIDER,
    CATEGORY_PROFILE,
    PAYMENT_RETRY_LIMIT,
    RESCHEDULE_PROPORTION,
    RESCHEDULE_REASONS,
    STATUS_ACCEPTED,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_CREATED,
    STATUS_EXPIRED,
    STATUS_IN_PROGRESS,
    STATUS_NO_SHOW,
    STATUS_REJECTED,
    STATUS_SCHEDULED,
    TERMINAL_STATUSES,
    stable_uuid,
)
from generator.entities import GeneratedDataset

LOADED_AT = datetime(2026, 11, 9, 12, 0, 0, tzinfo=timezone.utc)


def add_status_event(
    dataset: GeneratedDataset,
    booking_id: uuid.UUID,
    event_sequence: int,
    from_status: str | None,
    to_status: str,
    occurred_at: datetime,
    actor_type: str,
    actor_id: uuid.UUID | None,
    reason_code: str | None,
) -> dict:
    """Append one validated status event."""
    if to_status not in ALLOWED_TRANSITIONS.get(from_status, set()):
        raise ValueError(
            f"Invalid transition {from_status!r} -> {to_status!r} "
            f"for booking {booking_id}"
        )
    event = {
        "event_id": stable_uuid("status_event", f"{booking_id}|{event_sequence}"),
        "booking_id": booking_id,
        "event_sequence": event_sequence,
        "from_status": from_status,
        "to_status": to_status,
        "occurred_at": occurred_at,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "reason_code": reason_code,
        "idempotency_key": f"status:{booking_id}:{event_sequence}",
        "source_loaded_at": LOADED_AT,
    }
    dataset.status_events.append(event)
    return event


def _pick_outcome(rng: random.Random, proportions: dict[str, float]) -> str:
    draw = rng.random()
    cumulative = 0.0
    for outcome, weight in proportions.items():
        cumulative += weight
        if draw < cumulative:
            return outcome
    return "completed"


def eligibility_index(dataset: GeneratedDataset) -> dict:
    """Index eligibility rows by (category, location) for fast lookup."""
    index: dict = {}
    for row in dataset.eligibility:
        if row["is_eligible"]:
            index.setdefault(
                (row["service_category_id"], row["location_id"]), []
            ).append(row)
    return index


def _eligible_provider(
    dataset: GeneratedDataset,
    rng: random.Random,
    category: str,
    location_id: str,
    as_of: datetime,
    index: dict | None = None,
) -> uuid.UUID | None:
    """Pick a provider eligible for category+region effective at ``as_of``."""
    if index is None:
        index = eligibility_index(dataset)
    rows = index.get((category, location_id), [])
    candidates = [
        row["provider_id"]
        for row in rows
        if row["effective_from"] <= as_of
        and (row["effective_to"] is None or row["effective_to"] > as_of)
    ]
    return rng.choice(candidates) if candidates else None


def generate_bookings(
    rng: random.Random,
    dataset: GeneratedDataset,
    scale_bookings: int,
    data_start: datetime,
    data_end: datetime,
    proportions: dict[str, float],
) -> None:
    """Generate bookings, status events, and reschedule events."""
    span_minutes = int((data_end - data_start).total_seconds() // 60)
    customer_ids = [row["customer_id"] for row in dataset.customers]
    locations = dataset.locations
    categories = [c["service_category_id"] for c in dataset.service_categories]
    customer_created = {
        row["customer_id"]: row["created_at"] for row in dataset.customers
    }
    elig_index = eligibility_index(dataset)

    for number in range(scale_bookings):
        booking_id = stable_uuid("booking", f"booking-{number}")
        category = categories[number % len(categories)]
        location = locations[number % len(locations)]
        profile = CATEGORY_PROFILE[category]
        created_at = data_start + timedelta(minutes=rng.randrange(span_minutes))
        customer_id = rng.choice(customer_ids)
        guard = 0
        while customer_created[customer_id] > created_at and guard < 10:
            customer_id = rng.choice(customer_ids)
            guard += 1

        duration = rng.randrange(*profile["duration"])
        value = round(rng.uniform(*profile["value"]), 2)
        requested_start_at = created_at + timedelta(hours=rng.randrange(24, 240))

        outcome = _pick_outcome(rng, proportions)
        provider_id = _eligible_provider(
            dataset, rng, category, location["location_id"], created_at, elig_index
        )

        seq = 0
        state: list[str | None] = [None]
        last_time: list[datetime] = [created_at - timedelta(microseconds=1)]

        def emit(
            to_status: str,
            occurred_at: datetime,
            actor_type: str,
            actor_id: uuid.UUID | None,
            reason: str | None = None,
        ) -> datetime:
            """Emit an event, enforcing strictly increasing event times."""
            nonlocal seq
            seq += 1
            effective_time = max(occurred_at, last_time[0] + timedelta(minutes=1))
            add_status_event(
                dataset, booking_id, seq, state[0], to_status,
                effective_time, actor_type, actor_id, reason,
            )
            state[0] = to_status
            last_time[0] = effective_time
            return effective_time

        emit(STATUS_CREATED, created_at, ACTOR_CUSTOMER, customer_id)

        needs_provider = outcome in {
            "completed", "customer_cancelled", "provider_cancelled",
            "no_show", "payment_exhausted",
        }

        if outcome == "rejected" or (needs_provider and provider_id is None):
            if outcome in {
                "customer_cancelled", "provider_cancelled", "no_show", "payment_exhausted",
            }:
                emit(STATUS_EXPIRED,
                     created_at + timedelta(minutes=ACCEPTANCE_WINDOW_MINUTES),
                     ACTOR_SYSTEM, None, "NO_PROVIDER_ELIGIBLE")
            else:
                emit(STATUS_REJECTED,
                     created_at + timedelta(minutes=rng.randrange(15, ACCEPTANCE_WINDOW_MINUTES)),
                     ACTOR_PROVIDER, provider_id, "PROVIDER_DECLINED")
            dataset.bookings.append(_booking_row(
                booking_id, customer_id, None, category,
                location["location_id"], created_at,
                requested_start_at, duration, value,
            ))
            continue

        accepted_time = emit(
            STATUS_ACCEPTED,
            created_at + timedelta(minutes=rng.randrange(10, 180)),
            ACTOR_PROVIDER, provider_id,
        )
        scheduled_event_time = min(
            max(
                accepted_time + timedelta(minutes=1),
                requested_start_at - timedelta(hours=rng.randrange(12, 48)),
            ),
            requested_start_at - timedelta(minutes=1),
        )

        if outcome == "customer_cancelled":
            if rng.random() < 0.5:
                # Cancel before scheduling.
                emit(STATUS_CANCELLED,
                     accepted_time + timedelta(hours=rng.randrange(1, 12)),
                     ACTOR_CUSTOMER, customer_id,
                     rng.choice(CANCELLATION_REASONS_CUSTOMER))
            else:
                emit(STATUS_SCHEDULED, scheduled_event_time, ACTOR_SYSTEM, provider_id)
                emit(STATUS_CANCELLED,
                     min(
                         max(scheduled_event_time + timedelta(minutes=1),
                             requested_start_at - timedelta(hours=rng.randrange(1, 12))),
                         requested_start_at - timedelta(minutes=1),
                     ),
                     ACTOR_CUSTOMER, customer_id,
                     rng.choice(CANCELLATION_REASONS_CUSTOMER))
            dataset.bookings.append(_booking_row(
                booking_id, customer_id, provider_id, category,
                location["location_id"], created_at,
                requested_start_at, duration, value,
            ))
            continue

        if outcome == "provider_cancelled":
            emit(STATUS_SCHEDULED, scheduled_event_time, ACTOR_SYSTEM, provider_id)
            emit(STATUS_CANCELLED,
                 min(
                     max(scheduled_event_time + timedelta(minutes=1),
                         requested_start_at - timedelta(hours=rng.randrange(1, 12))),
                     requested_start_at - timedelta(minutes=1),
                 ),
                 ACTOR_PROVIDER, provider_id,
                 rng.choice(CANCELLATION_REASONS_PROVIDER))
            dataset.bookings.append(_booking_row(
                booking_id, customer_id, provider_id, category,
                location["location_id"], created_at,
                requested_start_at, duration, value,
            ))
            continue

        if outcome == "no_show":
            emit(STATUS_SCHEDULED, scheduled_event_time, ACTOR_SYSTEM, provider_id)
            emit(STATUS_NO_SHOW,
                 requested_start_at + timedelta(minutes=duration),
                 ACTOR_SYSTEM, provider_id, "PARTY_DID_NOT_APPEAR")
            dataset.bookings.append(_booking_row(
                booking_id, customer_id, provider_id, category,
                location["location_id"], created_at,
                requested_start_at, duration, value,
            ))
            continue

        if outcome == "payment_exhausted":
            # Scheduled but every payment attempt fails: the booking may not
            # reach COMPLETED (TAD 9.2) and ends cancelled by the system.
            emit(STATUS_SCHEDULED, scheduled_event_time, ACTOR_SYSTEM, provider_id)
            emit(STATUS_CANCELLED,
                 requested_start_at + timedelta(minutes=duration),
                 ACTOR_SYSTEM, None, "PAYMENT_EXHAUSTED")
            dataset.bookings.append(_booking_row(
                booking_id, customer_id, provider_id, category,
                location["location_id"], created_at,
                requested_start_at, duration, value,
            ))
            continue

        # Completed path.
        emit(STATUS_SCHEDULED, scheduled_event_time, ACTOR_SYSTEM, provider_id)
        emit(STATUS_IN_PROGRESS, requested_start_at, ACTOR_PROVIDER, provider_id)
        emit(STATUS_COMPLETED,
             requested_start_at + timedelta(minutes=duration),
             ACTOR_PROVIDER, provider_id)
        dataset.bookings.append(_booking_row(
            booking_id, customer_id, provider_id, category,
            location["location_id"], created_at,
            requested_start_at, duration, value,
        ))

        _maybe_reschedule(
            rng, dataset, booking_id, customer_id, provider_id,
            requested_start_at, duration,
        )

    _validate_history(dataset)


def _maybe_reschedule(
    rng: random.Random,
    dataset: GeneratedDataset,
    booking_id: uuid.UUID,
    customer_id: uuid.UUID,
    provider_id: uuid.UUID | None,
    requested_start_at: datetime,
    duration: int,
) -> None:
    """Attach a deterministic reschedule before the service happens."""
    if rng.random() >= RESCHEDULE_PROPORTION:
        return
    actor = rng.choice([ACTOR_CUSTOMER, ACTOR_PROVIDER])
    new_start = requested_start_at + timedelta(days=rng.randrange(1, 5),
                                               hours=rng.randrange(1, 12))
    dataset.reschedule_events.append(
        {
            "reschedule_event_id": stable_uuid("reschedule", f"{booking_id}|1"),
            "booking_id": booking_id,
            "old_scheduled_start_at": requested_start_at,
            "new_scheduled_start_at": new_start,
            "occurred_at": requested_start_at - timedelta(hours=rng.randrange(12, 48)),
            "actor_type": actor,
            "reason_code": rng.choice(RESCHEDULE_REASONS),
            "idempotency_key": f"reschedule:{booking_id}:1",
            "source_loaded_at": LOADED_AT,
        }
    )


def _booking_row(
    booking_id: uuid.UUID,
    customer_id: uuid.UUID,
    provider_id: uuid.UUID | None,
    category: str,
    location_id: str,
    created_at: datetime,
    requested_start_at: datetime,
    duration: int,
    value: float,
) -> dict:
    return {
        "booking_id": booking_id,
        "customer_id": customer_id,
        "provider_id": provider_id,
        "service_category_id": category,
        "service_location_id": location_id,
        "created_at": created_at,
        "requested_start_at": requested_start_at,
        "requested_duration_minutes": duration,
        "service_value_amount": value,
        "currency": "USD",
        "is_test_booking": False,
        "source_loaded_at": LOADED_AT,
    }


def _validate_history(dataset: GeneratedDataset) -> None:
    """Replay each booking's events through the transition contract."""
    by_booking: dict[uuid.UUID, list[dict]] = {}
    for event in dataset.status_events:
        by_booking.setdefault(event["booking_id"], []).append(event)
    for booking_id, events in by_booking.items():
        events.sort(key=lambda e: (e["occurred_at"], e["event_sequence"], str(e["event_id"])))
        state: str | None = None
        for event in events:
            if event["from_status"] != state:
                raise ValueError(
                    f"Event chain mismatch for booking {booking_id}: "
                    f"expected from_status={state!r}, got {event['from_status']!r}"
                )
            if state in TERMINAL_STATUSES:
                raise ValueError(f"Terminal state {state!r} followed by another event")
            state = event["to_status"]
