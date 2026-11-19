"""Payment attempts, posted financial events, earnings, and payouts (TAD 9, 16)."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from generator.config import (
    FAILED_FIRST_ATTEMPT_PROPORTION,
    FAILURE_CODES,
    FEE_RATE,
    FULL_REFUND_PROPORTION,
    PARTIAL_REFUND_PROPORTION,
    PAYMENT_RETRY_LIMIT,
    PAYMENT_RETRY_SPACING_MINUTES,
    PAYOUT_DELAY_MAX_DAYS,
    PAYOUT_DELAY_MIN_DAYS,
    PAYOUT_PAID_PROPORTION,
    PAYOUT_PENDING_PROPORTION,
    REVERSAL_PROPORTION,
    STATUS_COMPLETED,
    stable_uuid,
)
from generator.entities import GeneratedDataset

LOADED_AT = datetime(2026, 11, 9, 12, 0, 0, tzinfo=timezone.utc)


def _round_cents(amount: float) -> float:
    return round(amount + 1e-9, 2)


def generate_payments(
    rng: random.Random,
    dataset: GeneratedDataset,
    payment_events_by_booking: dict[uuid.UUID, list[dict]],
) -> None:
    """Create attempts, captures, refunds, reversals, and payouts.

    ``payment_events_by_booking`` receives the posted events grouped by
    booking so lifecycle fixtures can inspect them.
    """
    # Index status history once: O(events) instead of O(bookings x events).
    completed_ids: set = set()
    scheduled_ids: set = set()
    exhausted_ids: set = set()
    for e in dataset.status_events:
        if e["to_status"] == STATUS_COMPLETED:
            completed_ids.add(e["booking_id"])
        elif e["to_status"] == "SCHEDULED":
            scheduled_ids.add(e["booking_id"])
        elif e.get("reason_code") == "PAYMENT_EXHAUSTED":
            exhausted_ids.add(e["booking_id"])

    bookings_by_id = {b["booking_id"]: b for b in dataset.bookings}
    completed = {bid: bookings_by_id[bid] for bid in completed_ids if bid in bookings_by_id}
    scheduled = {
        bid: bookings_by_id[bid]
        for bid in scheduled_ids - completed_ids
        if bid in bookings_by_id
    }

    for booking in dataset.bookings:
        booking_id = booking["booking_id"]
        value = float(booking["service_value_amount"])
        is_completed = booking_id in completed
        is_scheduled = booking_id in scheduled
        if not (is_completed or is_scheduled):
            continue  # bookings never scheduled generate no payment activity

        exhausted = booking_id in exhausted_ids

        attempts: list[dict] = []
        first_attempt_time = booking["requested_start_at"] - timedelta(hours=1)
        failed_first = rng.random() < FAILED_FIRST_ATTEMPT_PROPORTION

        if exhausted:
            attempt_count = PAYMENT_RETRY_LIMIT
        elif failed_first:
            attempt_count = 2
        else:
            attempt_count = 1

        succeeded = False
        for attempt_number in range(1, attempt_count + 1):
            attempt_success = exhausted is False and (
                attempt_number == attempt_count  # last allowed attempt succeeds
            )
            if exhausted:
                attempt_success = False
            attempted_at = first_attempt_time + timedelta(
                minutes=PAYMENT_RETRY_SPACING_MINUTES * (attempt_number - 1)
            )
            attempts.append(
                {
                    "payment_attempt_id": stable_uuid(
                        "payment_attempt", f"{booking_id}|{attempt_number}"
                    ),
                    "booking_id": booking_id,
                    "attempt_number": attempt_number,
                    "attempted_at": attempted_at,
                    "attempt_status": "SUCCEEDED" if attempt_success else "FAILED",
                    "amount": value,
                    "currency": "USD",
                    "failure_code": None if attempt_success else rng.choice(FAILURE_CODES),
                    "idempotency_key": f"attempt:{booking_id}:{attempt_number}",
                    "source_loaded_at": LOADED_AT,
                }
            )
            if attempt_success:
                succeeded = True
        dataset.payment_attempts.extend(attempts)

        events: list[dict] = []
        if succeeded:
            successful_attempt = attempts[-1]
            capture_id = stable_uuid("payment_event", f"{booking_id}|capture")
            events.append(
                {
                    "payment_event_id": capture_id,
                    "booking_id": booking_id,
                    "payment_attempt_id": successful_attempt["payment_attempt_id"],
                    "related_payment_event_id": None,
                    "event_type": "CAPTURE",
                    "amount": value,
                    "currency": "USD",
                    "occurred_at": successful_attempt["attempted_at"],
                    "idempotency_key": f"capture:{booking_id}:1",
                    "source_loaded_at": LOADED_AT,
                }
            )
            if is_completed:
                draw = rng.random()
                if draw < FULL_REFUND_PROPORTION:
                    refund_amount = value
                elif draw < FULL_REFUND_PROPORTION + PARTIAL_REFUND_PROPORTION:
                    refund_amount = _round_cents(value * rng.uniform(0.10, 0.40))
                else:
                    refund_amount = 0.0
                if refund_amount > 0:
                    events.append(
                        {
                            "payment_event_id": stable_uuid(
                                "payment_event", f"{booking_id}|refund"
                            ),
                            "booking_id": booking_id,
                            "payment_attempt_id": None,
                            "related_payment_event_id": capture_id,
                            "event_type": "REFUND",
                            "amount": refund_amount,
                            "currency": "USD",
                            "occurred_at": booking["requested_start_at"]
                            + timedelta(minutes=int(booking["requested_duration_minutes"]),
                                        hours=rng.randrange(2, 72)),
                            "idempotency_key": f"refund:{booking_id}:1",
                            "source_loaded_at": LOADED_AT,
                        }
                    )
                elif rng.random() < REVERSAL_PROPORTION:
                    # Capture reversal instead of a refund (TAD 9.3).
                    events.append(
                        {
                            "payment_event_id": stable_uuid(
                                "payment_event", f"{booking_id}|reversal"
                            ),
                            "booking_id": booking_id,
                            "payment_attempt_id": None,
                            "related_payment_event_id": capture_id,
                            "event_type": "REVERSAL",
                            "amount": value,
                            "currency": "USD",
                            "occurred_at": booking["requested_start_at"]
                            + timedelta(hours=rng.randrange(24, 96)),
                            "idempotency_key": f"reversal:{booking_id}:1",
                            "source_loaded_at": LOADED_AT,
                        }
                    )
        dataset.payment_events.extend(events)
        payment_events_by_booking[booking_id] = events

    _generate_payouts(rng, dataset, completed)


def _generate_payouts(rng: random.Random, dataset: GeneratedDataset, completed: dict) -> None:
    """Provider payout transactions, separate from provider earnings."""
    completed_bookings = completed
    for booking_id, booking in completed_bookings.items():
        provider_id = booking.get("provider_id")
        if provider_id is None:
            continue
        draw = rng.random()
        if draw < PAYOUT_PAID_PROPORTION:
            status, paid_at = "PAID", None
        elif draw < PAYOUT_PAID_PROPORTION + PAYOUT_PENDING_PROPORTION:
            status, paid_at = "PENDING", None
        else:
            status, paid_at = rng.choice(["FAILED", "REVERSED"]), None
        initiated_at = booking["requested_start_at"] + timedelta(
            days=rng.randrange(PAYOUT_DELAY_MIN_DAYS, PAYOUT_DELAY_MAX_DAYS + 1)
        )
        dataset.payouts.append(
            {
                "payout_id": stable_uuid("payout", f"{booking_id}|1"),
                "booking_id": booking_id,
                "provider_id": provider_id,
                "amount": booking["service_value_amount"],
                "currency": "USD",
                "payout_status": status,
                "initiated_at": initiated_at,
                "paid_at": initiated_at + timedelta(days=1) if status == "PAID" else paid_at,
                "idempotency_key": f"payout:{booking_id}:1",
                "source_loaded_at": LOADED_AT,
            }
        )


def fee_reversal_amount(refund_amount: float, fee_rate: float = FEE_RATE) -> float:
    """Deterministic proportional fee reversal used by fixtures and tests."""
    return _round_cents(refund_amount * fee_rate)
