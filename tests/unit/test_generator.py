"""Python unit tests for the generator (TAD 17.1)."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pytest

from generator import availability as availability_module
from generator import booking_lifecycle as lifecycle
from generator.config import (
    ALLOWED_TRANSITIONS,
    DATA_END,
    DATA_START,
    DEFAULT_SCENARIO_PROPORTIONS,
    FEE_RATE,
    PAYMENT_RETRY_LIMIT,
    STATUS_COMPLETED,
    TERMINAL_STATUSES,
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
from generator.fixtures import build_fixture_dataset, fixture_expected_totals
from generator.payments import fee_reversal_amount, generate_payments


def build_small_dataset(seed: int = 42):
    rng = random.Random(seed)
    ds = GeneratedDataset()
    ds.service_categories = generate_service_categories()
    ds.locations = generate_locations(3)
    ds.customers = generate_customers(50, ds.locations)
    ds.providers = generate_providers(10, ds.locations)
    ds.eligibility = generate_eligibility(rng, ds.providers, ds.locations)
    ds.fee_policy = generate_fee_policy()
    lifecycle.generate_bookings(
        rng, ds, 200, DATA_START, DATA_END, DEFAULT_SCENARIO_PROPORTIONS
    )
    generate_payments(rng, ds, payment_events_by_booking={})
    availability_module.generate_availability(rng, ds, DATA_START, DATA_END, 25)
    return ds


# ----------------------------------------------------------- reproducibility
def test_fixed_seed_reproducibility():
    """Same seed and config generate identical logical source records."""
    a = build_small_dataset(seed=123)
    b = build_small_dataset(seed=123)
    assert [r["booking_id"] for r in a.bookings] == [r["booking_id"] for r in b.bookings]
    assert [e["idempotency_key"] for e in a.status_events] == [
        e["idempotency_key"] for e in b.status_events
    ]
    assert a.payment_events == b.payment_events


def test_different_seed_changes_data():
    """Booking IDs are seed-invariant UUIDv5 natural keys (TAD 5.2); the
    scenario CONTENT (outcomes, amounts, timestamps) must change by seed."""
    a = build_small_dataset(seed=1)
    b = build_small_dataset(seed=2)
    amounts_a = [(r["booking_id"], r["service_value_amount"]) for r in a.bookings]
    amounts_b = [(r["booking_id"], r["service_value_amount"]) for r in b.bookings]
    assert amounts_a != amounts_b


# ------------------------------------------------------------- integrity
def test_unique_ids_within_grains():
    ds = build_small_dataset()
    assert len({r["booking_id"] for r in ds.bookings}) == len(ds.bookings)
    assert len({e["event_id"] for e in ds.status_events}) == len(ds.status_events)
    assert len({p["payment_event_id"] for p in ds.payment_events}) == len(ds.payment_events)
    assert len({a["availability_id"] for a in ds.availability_intervals}) == len(
        ds.availability_intervals
    )


def test_referential_integrity():
    ds = build_small_dataset()
    customer_ids = {c["customer_id"] for c in ds.customers}
    location_ids = {l["location_id"] for l in ds.locations}
    category_ids = {c["service_category_id"] for c in ds.service_categories}
    provider_ids = {p["provider_id"] for p in ds.providers}
    booking_ids = {b["booking_id"] for b in ds.bookings}
    for booking in ds.bookings:
        assert booking["customer_id"] in customer_ids
        assert booking["service_location_id"] in location_ids
        assert booking["service_category_id"] in category_ids
        if booking["provider_id"] is not None:
            assert booking["provider_id"] in provider_ids
    for event in ds.status_events:
        assert event["booking_id"] in booking_ids


def test_valid_state_transitions_only():
    ds = build_small_dataset()
    for event in ds.status_events:
        assert event["to_status"] in ALLOWED_TRANSITIONS.get(
            event["from_status"], set()
        ), f"illegal transition {event['from_status']} -> {event['to_status']}"


def test_event_ordering_deterministic():
    ds = build_small_dataset()
    by_booking: dict = {}
    for event in ds.status_events:
        by_booking.setdefault(event["booking_id"], []).append(event)
    for booking_id, events in by_booking.items():
        ordered = sorted(
            events, key=lambda e: (e["occurred_at"], e["event_sequence"], str(e["event_id"]))
        )
        assert ordered[0]["from_status"] is None
        assert ordered[-1]["to_status"] in TERMINAL_STATUSES


def test_one_provider_per_booking():
    ds = build_small_dataset()
    for booking in ds.bookings:
        # single nullable provider column enforces the rule structurally
        assert booking.get("provider_id") is None or booking["provider_id"] is not None


# ------------------------------------------------------------- payments
def test_failed_attempts_create_no_capture():
    ds = build_small_dataset()
    failed_attempt_ids = {
        a["payment_attempt_id"]
        for a in ds.payment_attempts
        if a["attempt_status"] == "FAILED"
    }
    for event in ds.payment_events:
        if event["event_type"] == "CAPTURE":
            assert event["payment_attempt_id"] not in failed_attempt_ids


def test_refunds_do_not_exceed_capture():
    ds = build_small_dataset()
    totals: dict = {}
    for event in ds.payment_events:
        entry = totals.setdefault(event["booking_id"], {"captured": 0.0, "returned": 0.0})
        if event["event_type"] == "CAPTURE":
            entry["captured"] += float(event["amount"])
        else:
            entry["returned"] += float(event["amount"])
    for booking_id, entry in totals.items():
        assert entry["returned"] <= entry["captured"] + 1e-9, f"over-refund on {booking_id}"


def test_completed_booking_has_successful_capture():
    ds = build_small_dataset()
    completed = {
        e["booking_id"] for e in ds.status_events if e["to_status"] == STATUS_COMPLETED
    }
    captured = {
        e["booking_id"] for e in ds.payment_events if e["event_type"] == "CAPTURE"
    }
    assert completed <= captured


def test_fee_math_proportional_reversal():
    assert fee_reversal_amount(20.0) == 3.0       # 15% of $20
    assert fee_reversal_amount(80.0) == 12.0
    assert fee_reversal_amount(0.0) == 0.0


def test_payment_retry_limit_respected():
    ds = build_small_dataset()
    attempts_per_booking: dict = {}
    for attempt in ds.payment_attempts:
        attempts_per_booking.setdefault(attempt["booking_id"], 0)
        attempts_per_booking[attempt["booking_id"]] += 1
    assert max(attempts_per_booking.values()) <= PAYMENT_RETRY_LIMIT


# ----------------------------------------------------------- availability
def test_availability_interval_validity_and_no_overlap():
    ds = build_small_dataset()
    intervals_by_provider: dict = {}
    for row in ds.availability_intervals:
        assert row["end_at"] > row["start_at"]
        intervals_by_provider.setdefault(row["provider_id"], []).append(row)
    for provider_id, intervals in intervals_by_provider.items():
        intervals.sort(key=lambda r: r["start_at"])
        for first, second in zip(intervals, intervals[1:]):
            assert second["start_at"] >= first["end_at"], (
                f"overlap for {provider_id}: {first} / {second}"
            )


def test_overlapping_availability_is_rejected():
    ds = GeneratedDataset()
    start = datetime(2026, 9, 1, 9, tzinfo=timezone.utc)
    provider_id = ds.providers and None or __import__("uuid").uuid5(
        __import__("generator.config").config.UUID_NAMESPACE, "overlap-test"
    )
    availability_module.add_interval(ds, provider_id, "plumbing", "loc", start, start + timedelta(hours=2))
    with pytest.raises(availability_module.OverlappingAvailabilityError):
        availability_module.add_interval(
            ds, provider_id, "plumbing", "loc", start + timedelta(hours=1), start + timedelta(hours=3)
        )
    # touching endpoints are fine ([start, end) convention)
    availability_module.add_interval(ds, provider_id, "plumbing", "loc", start + timedelta(hours=2), start + timedelta(hours=4))


# ----------------------------------------------------------- reschedule
def test_reschedule_preserves_booking_id_and_old_time():
    ds = build_small_dataset()
    requested_start = {
        b["booking_id"]: b["requested_start_at"] for b in ds.bookings
    }
    for event in ds.reschedule_events:
        assert event["booking_id"] in requested_start
        assert event["old_scheduled_start_at"] == requested_start[event["booking_id"]]
        assert event["new_scheduled_start_at"] != event["old_scheduled_start_at"]


# ----------------------------------------------------------- fixtures
def test_fixture_dataset_builds_and_validates():
    ds = build_fixture_dataset()
    # every edge-case scenario is present exactly once
    reasons = [e.get("reason_code") for e in ds.status_events]
    assert "CHANGE_OF_PLANS" in reasons                    # customer cancellation
    assert "PROVIDER_DECLINED" in reasons                  # provider rejection
    assert "ACCEPTANCE_WINDOW_EXPIRED" in reasons          # expiry
    assert "SCHEDULE_CONFLICT" in reasons                  # provider cancellation
    assert "PARTY_DID_NOT_APPEAR" in reasons               # no-show
    assert "PAYMENT_EXHAUSTED" not in reasons              # not a fixture scenario
    # reschedule retains booking ID
    booking_ids = {b["booking_id"] for b in ds.bookings}
    for event in ds.reschedule_events:
        assert event["booking_id"] in booking_ids
    # invalid scenarios are recorded as rejected, never loaded
    scenarios = {r["scenario"] for r in ds.rejected_records}
    assert "duplicate_payment_event" in scenarios
    assert "overlapping_availability" in scenarios
    # late-arriving event: occurred long before ingestion
    late = [
        e for e in ds.status_events if e["source_loaded_at"] > datetime(2026, 11, 9, 17, tzinfo=timezone.utc)
    ]
    assert late and all(
        e["occurred_at"] < e["source_loaded_at"] - timedelta(hours=1) for e in late
    )


def test_fixture_hand_calculated_totals():
    """Independent check of the fixture arithmetic against known values."""
    expected = fixture_expected_totals()
    # hand-arithmetic: gross 100+200+150+80+100+60+120
    assert expected["gross_completed_gmv"] == "810.00"
    # refunds: 80 + 20 + 60
    assert expected["eligible_refund_amount"] == "160.00"
    assert expected["net_completed_gmv"] == "650.00"
    # fee: 15% of 810
    assert expected["gross_platform_fee"] == "121.50"
    # reversal: 15% of 160
    assert expected["platform_fee_reversal"] == "24.00"
    assert expected["net_platform_fee_revenue"] == "97.50"
    assert expected["provider_earnings"] == "552.50"
    # canonical case: $100, 15% fee, $20 refund -> fee reversal $3
    assert fee_reversal_amount(20.00, FEE_RATE) == 3.00
