"""Deterministic edge-case fixtures with hand-calculated expectations.

The fixture dataset (scale ``fixtures``) is a tiny, fully deterministic
dataset used by dbt reconciliation tests and Python unit tests. Its
aggregate financial expectations are defined here by hand — they are NOT
computed by the production SQL (TAD 17.4).
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from generator import availability as availability_mod
from generator import booking_lifecycle as lifecycle
from generator import payments as payments_mod
from generator.config import (
    FEE_RATE,
    STATUS_ACCEPTED,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_CREATED,
    STATUS_IN_PROGRESS,
    STATUS_REJECTED,
    STATUS_SCHEDULED,
    stable_uuid,
)
from generator.entities import (
    GeneratedDataset,
    generate_customers,
    generate_eligibility,
    generate_fee_policy,
    generate_locations,
    generate_providers,
    generate_service_categories,
)

T0 = datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc)
LOADED_LATE = datetime(2026, 11, 9, 18, 0, 0, tzinfo=timezone.utc)


def build_fixture_dataset() -> GeneratedDataset:
    """Build the canonical edge-case fixture dataset.

    Financial fixture (hand-calculated, 15% fee):

    ==============  ======  ========  =======  ========  ========  ==========
    Booking         Gross   Refund    Net GMV  Gross fee Fee rev.  Net fee
    ==============  ======  ========  =======  ========  ========  ==========
    F1 completed    100.00     0.00   100.00     15.00      0.00     15.00
    F7 rescheduled  200.00     0.00   200.00     30.00      0.00     30.00
    F8 retry        150.00     0.00   150.00     22.50      0.00     22.50
    F9 full refund   80.00    80.00     0.00     12.00     12.00      0.00
    F10 partial     100.00    20.00    80.00     15.00      3.00     12.00
    F11 reversal     60.00    60.00     0.00      9.00      9.00      0.00
    ==============  ======  ========  =======  ========  ========  ==========
    Totals          690.00   160.00   530.00    103.50     24.00     79.50

    Provider earnings = 530.00 - 79.50 = 450.50
    """
    ds = GeneratedDataset()
    ds.service_categories = generate_service_categories()
    ds.locations = generate_locations(1)  # one neighborhood per borough
    ds.customers = generate_customers(6, ds.locations)
    ds.providers = generate_providers(4, ds.locations)
    provider_ids = sorted({p["provider_id"] for p in ds.providers})
    # All four providers eligible for every category in every region.
    ds.eligibility = generate_eligibility(
        random.Random(7), ds.providers, ds.locations
    )
    # Force full coverage: add missing pairs deterministically.
    existing = {(e["provider_id"], e["service_category_id"], e["location_id"]) for e in ds.eligibility}
    for provider_id in provider_ids:
        for category in [c["service_category_id"] for c in ds.service_categories]:
            for location in ds.locations:
                key = (provider_id, category, location["location_id"])
                if key not in existing:
                    ds.eligibility.append(
                        {
                            "eligibility_id": stable_uuid("eligibility", f"{provider_id}|{category}|{key[2]}"),
                            "provider_id": provider_id,
                            "service_category_id": category,
                            "location_id": key[2],
                            "effective_from": datetime(2026, 8, 1, tzinfo=timezone.utc),
                            "effective_to": None,
                            "is_eligible": True,
                            "source_loaded_at": datetime(2026, 11, 9, 12, 0, 0, tzinfo=timezone.utc),
                        }
                    )
    ds.fee_policy = generate_fee_policy()

    customer_ids = [c["customer_id"] for c in ds.customers]
    category = "home_cleaning"
    location_id = ds.locations[0]["location_id"]

    def make_booking(tag: str, value: float, duration: int, provider):
        booking_id = stable_uuid("fixture_booking", tag)
        ds.bookings.append(
            {
                "booking_id": booking_id,
                "customer_id": customer_ids[0],
                "provider_id": provider,
                "service_category_id": category,
                "service_location_id": location_id,
                "created_at": T0,
                "requested_start_at": T0 + timedelta(days=1),
                "requested_duration_minutes": duration,
                "service_value_amount": value,
                "currency": "USD",
                "is_test_booking": False,
                "source_loaded_at": LOADED_LATE - timedelta(hours=1),
            }
        )
        return booking_id

    def path_completed(booking_id, provider_id, complete_offset_hours=3):
        lifecycle.add_status_event(ds, booking_id, 1, None, STATUS_CREATED, T0, "CUSTOMER", customer_ids[0], None)
        lifecycle.add_status_event(ds, booking_id, 2, STATUS_CREATED, STATUS_ACCEPTED,
                                   T0 + timedelta(minutes=30), "PROVIDER", provider_id, None)
        lifecycle.add_status_event(ds, booking_id, 3, STATUS_ACCEPTED, STATUS_SCHEDULED,
                                   T0 + timedelta(hours=1), "SYSTEM", provider_id, None)
        lifecycle.add_status_event(ds, booking_id, 4, STATUS_SCHEDULED, STATUS_IN_PROGRESS,
                                   T0 + timedelta(days=1), "PROVIDER", provider_id, None)
        lifecycle.add_status_event(ds, booking_id, 5, STATUS_IN_PROGRESS, STATUS_COMPLETED,
                                   T0 + timedelta(days=1, hours=complete_offset_hours),
                                   "PROVIDER", provider_id, None)

    def add_capture(booking_id, amount, attempt_no=1, attempt_status="SUCCEEDED"):
        attempt_id = stable_uuid("fixture_attempt", f"{booking_id}|{attempt_no}")
        ds.payment_attempts.append(
            {
                "payment_attempt_id": attempt_id,
                "booking_id": booking_id,
                "attempt_number": attempt_no,
                "attempted_at": T0 + timedelta(minutes=10 * attempt_no),
                "attempt_status": attempt_status,
                "amount": amount,
                "currency": "USD",
                "failure_code": None if attempt_status == "SUCCEEDED" else "CARD_DECLINED",
                "idempotency_key": f"attempt:{booking_id}:{attempt_no}",
                "source_loaded_at": LOADED_LATE - timedelta(hours=1),
            }
        )
        return attempt_id

    def add_event(booking_id, tag, event_type, amount, related, loaded_at=None):
        ds.payment_events.append(
            {
                "payment_event_id": stable_uuid("fixture_event", f"{booking_id}|{tag}"),
                "booking_id": booking_id,
                "payment_attempt_id": None,
                "related_payment_event_id": related,
                "event_type": event_type,
                "amount": amount,
                "currency": "USD",
                "occurred_at": T0 + timedelta(days=2),
                "idempotency_key": f"{event_type.lower()}:{booking_id}:{tag}",
                "source_loaded_at": loaded_at or (LOADED_LATE - timedelta(hours=1)),
            }
        )

    def add_payout(booking_id, provider_id, amount, status):
        ds.payouts.append(
            {
                "payout_id": stable_uuid("fixture_payout", f"{booking_id}|1"),
                "booking_id": booking_id,
                "provider_id": provider_id,
                "amount": amount,
                "currency": "USD",
                "payout_status": status,
                "initiated_at": T0 + timedelta(days=3),
                "paid_at": T0 + timedelta(days=4) if status == "PAID" else None,
                "idempotency_key": f"payout:{booking_id}:1",
                "source_loaded_at": LOADED_LATE - timedelta(hours=1),
            }
        )

    p1, p2, p3, p4 = sorted({p["provider_id"] for p in ds.providers})[:4]

    # F1 — completed, paid, no refund. Payout paid.
    b1 = make_booking("f1-completed", 100.00, 120, p1)
    path_completed(b1, p1)
    add_capture(b1, 100.00)
    add_payout(b1, p1, 68.00, "PAID")

    # F2 — customer cancellation before acceptance (no payment activity).
    b2 = make_booking("f2-cust-cancel", 90.00, 60, None)
    lifecycle.add_status_event(ds, b2, 1, None, STATUS_CREATED, T0, "CUSTOMER", customer_ids[0], None)
    lifecycle.add_status_event(ds, b2, 2, STATUS_CREATED, STATUS_CANCELLED,
                               T0 + timedelta(minutes=45), "CUSTOMER", customer_ids[0], "CHANGE_OF_PLANS")

    # F3 — provider rejection.
    b3 = make_booking("f3-rejected", 90.00, 60, p2)
    lifecycle.add_status_event(ds, b3, 1, None, STATUS_CREATED, T0, "CUSTOMER", customer_ids[0], None)
    lifecycle.add_status_event(ds, b3, 2, STATUS_CREATED, STATUS_REJECTED,
                               T0 + timedelta(minutes=20), "PROVIDER", p2, "PROVIDER_DECLINED")

    # F4 — expired unaccepted booking.
    b4 = make_booking("f4-expired", 90.00, 60, None)
    lifecycle.add_status_event(ds, b4, 1, None, STATUS_CREATED, T0, "CUSTOMER", customer_ids[0], None)
    lifecycle.add_status_event(ds, b4, 2, STATUS_CREATED, "EXPIRED",
                               T0 + timedelta(hours=4), "SYSTEM", None, "ACCEPTANCE_WINDOW_EXPIRED")

    # F5 — provider cancellation after acceptance.
    b5 = make_booking("f5-prov-cancel", 90.00, 60, p2)
    lifecycle.add_status_event(ds, b5, 1, None, STATUS_CREATED, T0, "CUSTOMER", customer_ids[0], None)
    lifecycle.add_status_event(ds, b5, 2, STATUS_CREATED, STATUS_ACCEPTED,
                               T0 + timedelta(minutes=30), "PROVIDER", p2, None)
    lifecycle.add_status_event(ds, b5, 3, STATUS_ACCEPTED, STATUS_CANCELLED,
                               T0 + timedelta(hours=2), "PROVIDER", p2, "SCHEDULE_CONFLICT")

    # F6 — scheduled no-show.
    b6 = make_booking("f6-noshow", 90.00, 60, p2)
    lifecycle.add_status_event(ds, b6, 1, None, STATUS_CREATED, T0, "CUSTOMER", customer_ids[0], None)
    lifecycle.add_status_event(ds, b6, 2, STATUS_CREATED, STATUS_ACCEPTED,
                               T0 + timedelta(minutes=30), "PROVIDER", p2, None)
    lifecycle.add_status_event(ds, b6, 3, STATUS_ACCEPTED, STATUS_SCHEDULED,
                               T0 + timedelta(hours=1), "SYSTEM", p2, None)
    lifecycle.add_status_event(ds, b6, 4, STATUS_SCHEDULED, "NO_SHOW",
                               T0 + timedelta(days=1, hours=1), "SYSTEM", p2, "PARTY_DID_NOT_APPEAR")

    # F7 — rescheduled completed booking (booking ID preserved).
    b7 = make_booking("f7-rescheduled", 200.00, 180, p3)
    path_completed(b7, p3)
    ds.reschedule_events.append(
        {
            "reschedule_event_id": stable_uuid("fixture_reschedule", f"{b7}|1"),
            "booking_id": b7,
            "old_scheduled_start_at": T0 + timedelta(days=1),
            "new_scheduled_start_at": T0 + timedelta(days=2),
            "occurred_at": T0 + timedelta(hours=2),
            "actor_type": "CUSTOMER",
            "reason_code": "CUSTOMER_REQUEST",
            "idempotency_key": f"reschedule:{b7}:1",
            "source_loaded_at": LOADED_LATE - timedelta(hours=1),
        }
    )
    add_capture(b7, 200.00)
    add_payout(b7, p3, 170.00, "PENDING")

    # F8 — failed payment then successful retry; completed.
    b8 = make_booking("f8-payment-retry", 150.00, 90, p3)
    path_completed(b8, p3)
    add_capture(b8, 150.00, attempt_no=1, attempt_status="FAILED")
    add_capture(b8, 150.00, attempt_no=2, attempt_status="SUCCEEDED")
    add_payout(b8, p3, 127.50, "PAID")

    # F9 — completed then fully refunded.
    b9 = make_booking("f9-full-refund", 80.00, 60, p4)
    path_completed(b9, p4)
    capture9 = stable_uuid("fixture_event", f"{b9}|capture")
    add_capture(b9, 80.00)
    add_event(b9, "refund", "REFUND", 80.00, stable_uuid("fixture_event", f"{b9}|capture"))

    # F10 — canonical partial-refund case: $100 service, 15% fee, $20 refund.
    b10 = make_booking("f10-partial-refund", 100.00, 120, p4)
    path_completed(b10, p4)
    add_capture(b10, 100.00)
    add_event(b10, "refund", "REFUND", 20.00, stable_uuid("fixture_event", f"{b10}|capture"))
    add_payout(b10, p4, 68.00, "PAID")

    # F11 — completed capture then posted reversal.
    b11 = make_booking("f11-reversal", 60.00, 60, p4)
    path_completed(b11, p4)
    add_capture(b11, 60.00)
    add_event(b11, "reversal", "REVERSAL", 60.00, stable_uuid("fixture_event", f"{b11}|capture"))

    # F12 — late-arriving booking: valid lifecycle whose events occurred at
    # the usual business times but were ingested much later
    # (source_loaded_at = LOADED_LATE). Incremental discovery uses the
    # ingestion watermark, not occurred_at (TAD 18.3).
    b12 = make_booking("f12-late-arriving", 120.00, 90, p1)
    path_completed(b12, p1)
    add_capture(b12, 120.00)
    add_payout(b12, p1, 120.00, "PENDING")
    for event in ds.status_events:
        if event["booking_id"] == b12:
            event["source_loaded_at"] = LOADED_LATE
    for attempt in ds.payment_attempts:
        if attempt["booking_id"] == b12:
            attempt["source_loaded_at"] = LOADED_LATE
    for event in ds.payment_events:
        if event["booking_id"] == b12:
            event["source_loaded_at"] = LOADED_LATE

    # Fixture financial expectations include F12 below (see FIXTURE_EXPECTED_TOTALS).

    # Edge case: a duplicate payment event (same idempotency key as the F9
    # refund, different event ID) must be REJECTED at load time, never
    # silently double-counted.
    ds.rejected_records.append(
        {
            "scenario": "duplicate_payment_event",
            "table": "raw_payment_events",
            "row": {
                "payment_event_id": str(stable_uuid("fixture_event", f"{b9}|refund-duplicate")),
                "booking_id": str(b9),
                "event_type": "REFUND",
                "amount": "80.00",
                "idempotency_key": f"refund:{b9}:1",
            },
            "reason": "duplicate idempotency_key",
        }
    )

    # Availability for capacity logic: two open intervals for p1 (no overlap).
    availability_mod.add_interval(ds, p1, category, location_id,
                                  T0 + timedelta(days=1), T0 + timedelta(days=1, hours=4))
    availability_mod.add_interval(ds, p1, category, location_id,
                                  T0 + timedelta(days=2), T0 + timedelta(days=2, hours=6))

    # Edge case: an overlapping availability attempt must be rejected by the
    # generator itself (ADR-008) and recorded as a rejected scenario.
    try:
        availability_mod.add_interval(
            ds, p1, category, location_id,
            T0 + timedelta(days=1, hours=2), T0 + timedelta(days=1, hours=5),
        )
    except availability_mod.OverlappingAvailabilityError:
        ds.rejected_records.append(
            {
                "scenario": "overlapping_availability",
                "table": "raw_provider_availability_intervals",
                "row": {"provider_id": str(p1), "start": str(T0 + timedelta(days=1, hours=2))},
                "reason": "overlaps existing OPEN interval for provider",
            }
        )
    else:  # pragma: no cover - the overlap must raise
        raise AssertionError("Overlapping availability was not rejected")

    lifecycle._validate_history(ds)
    return ds


def build_expected_fixture_query_results() -> dict:
    """Re-derived totals AFTER adding F12 (kept next to the builder).

    Hand-calculated, not computed with the production SQL:
      completed bookings: F1 100, F7 200, F8 150, F9 80, F10 100, F11 60,
                          F12 120                      -> 810.00 gross
      refunds/reversals:  F9 80 + F10 20 + F11 60      -> 160.00
      net GMV                                          -> 650.00
      gross fee (15%)                                  -> 121.50
      fee reversal (15% x 160)                         ->  24.00
      net platform fee revenue                         ->  97.50
      provider earnings (650 - 97.50)                  -> 552.50
    """
    return {
        "gross_completed_gmv": "810.00",
        "eligible_refund_amount": "160.00",
        "net_completed_gmv": "650.00",
        "gross_platform_fee": "121.50",
        "platform_fee_reversal": "24.00",
        "net_platform_fee_revenue": "97.50",
        "provider_earnings": "552.50",
        "completed_bookings": 7,
        "fee_rate": FEE_RATE,
    }


#: Hand-calculated aggregate expectations for the fixture dataset.
#: See ``build_expected_fixture_query_results`` for the arithmetic.
FIXTURE_EXPECTED_TOTALS = {
    "gross_completed_gmv": "810.00",
    "eligible_refund_amount": "160.00",
    "net_completed_gmv": "650.00",
    "gross_platform_fee": "121.50",
    "platform_fee_reversal": "24.00",
    "net_platform_fee_revenue": "97.50",
    "provider_earnings": "552.50",
    "completed_bookings": 7,
    "fee_rate": FEE_RATE,
}


def fixture_expected_totals() -> dict:
    """Return a copy of the hand-calculated fixture expectations."""
    return dict(FIXTURE_EXPECTED_TOTALS)


def build_fixture_scenarios() -> dict:
    """Scenario-level expectations used by Python unit tests (TAD 16.3)."""
    return {
        "completed_no_refund": {"bookings": 1},
        "customer_cancellation": {"terminal": STATUS_CANCELLED, "actor": "CUSTOMER"},
        "provider_rejection": {"terminal": STATUS_REJECTED},
        "expired": {"terminal": "EXPIRED"},
        "provider_cancellation_after_acceptance": {"terminal": STATUS_CANCELLED, "actor": "PROVIDER"},
        "no_show": {"terminal": "NO_SHOW"},
        "rescheduled": {"same_booking_id": True},
        "payment_retry": {"failed_attempts": 1, "captures": 1},
        "full_refund": {"refund": "full"},
        "partial_refund": {"refund": "partial", "amount": "20.00"},
        "reversal": {"reversal": True},
        "late_arriving_event": {"ingested_late": True},
        "ineligible_provider_assignment": {"must_be_rejected": True},
        "overlapping_availability": {"must_be_rejected": True},
    }
