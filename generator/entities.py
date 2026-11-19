"""Master entities: customers, providers, categories, locations, eligibility.

All identifiers are deterministic UUIDv5 values derived from the seed and
business natural keys (TAD 5.2).
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from generator.config import (
    BOROUGHS,
    CATEGORY_PROFILE,
    ELIGIBILITY_MAX_CATEGORIES,
    ELIGIBILITY_MAX_REGIONS,
    ELIGIBILITY_MIN_CATEGORIES,
    ELIGIBILITY_MIN_REGIONS,
    NEIGHBORHOODS,
    SERVICE_CATEGORIES,
    stable_uuid,
)


@dataclass
class GeneratedDataset:
    """In-memory container for every generated source record."""

    customers: list[dict] = field(default_factory=list)
    providers: list[dict] = field(default_factory=list)
    service_categories: list[dict] = field(default_factory=list)
    locations: list[dict] = field(default_factory=list)
    eligibility: list[dict] = field(default_factory=list)
    bookings: list[dict] = field(default_factory=list)
    status_events: list[dict] = field(default_factory=list)
    reschedule_events: list[dict] = field(default_factory=list)
    payment_attempts: list[dict] = field(default_factory=list)
    payment_events: list[dict] = field(default_factory=list)
    payouts: list[dict] = field(default_factory=list)
    availability_intervals: list[dict] = field(default_factory=list)
    fee_policy: list[dict] = field(default_factory=list)
    #: Invalid scenario rows deliberately generated for edge-case coverage;
    #: the loader must REJECT these (never silently load them).
    rejected_records: list[dict] = field(default_factory=list)


def generate_service_categories() -> list[dict]:
    return [
        {
            "service_category_id": category,
            "service_category_name": category.replace("_", " ").title(),
            "is_active": True,
        }
        for category in SERVICE_CATEGORIES
    ]


def generate_locations(neighborhoods_per_borough: int) -> list[dict]:
    locations: list[dict] = []
    for borough in BOROUGHS:
        for index, neighborhood in enumerate(NEIGHBORHOODS[borough][:neighborhoods_per_borough]):
            locations.append(
                {
                    "location_id": f"{borough.lower().replace(' ', '_')}_{index + 1:02d}",
                    "borough_name": borough,
                    "neighborhood_name": neighborhood,
                    "is_active": True,
                }
            )
    return locations


def generate_customers(scale_customers: int, locations: list[dict]) -> list[dict]:
    """Effective-dated customer profile versions (TAD 6.2).

    Most customers keep a single version; a deterministic ~8% receive one
    profile update to demonstrate SCD Type 2 behaviour.
    """
    rows: list[dict] = []
    loaded_at = datetime(2026, 11, 9, 12, 0, 0, tzinfo=timezone.utc)
    for number in range(scale_customers):
        customer_id = stable_uuid("customer", f"customer-{number}")
        created_at = datetime(2026, 8, 1, tzinfo=timezone.utc) + timedelta(
            days=number % 30, hours=number % 24
        )
        home_location = locations[number % len(locations)]
        segment = ["standard", "standard", "frequent", "new"][number % 4]
        versions = 2 if number % 13 == 0 else 1  # deterministic profile change
        for version in range(versions):
            effective_from = created_at + timedelta(days=60 * version)
            is_current = version == versions - 1
            effective_to = (
                created_at + timedelta(days=60 * version + 60) if not is_current else None
            )
            rows.append(
                {
                    "customer_record_id": stable_uuid(
                        "customer_record", f"customer-{number}-v{version}"
                    ),
                    "customer_id": customer_id,
                    "home_location_id": home_location["location_id"],
                    "customer_segment": "returning" if version else segment,
                    "account_status": "ACTIVE",
                    "created_at": created_at,
                    "effective_from": effective_from,
                    "effective_to": effective_to,
                    "is_current": is_current,
                    "source_loaded_at": loaded_at,
                }
            )
    return rows


def generate_providers(scale_providers: int, locations: list[dict]) -> list[dict]:
    rows: list[dict] = []
    loaded_at = datetime(2026, 11, 9, 12, 0, 0, tzinfo=timezone.utc)
    for number in range(scale_providers):
        provider_id = stable_uuid("provider", f"provider-{number}")
        created_at = datetime(2026, 7, 15, tzinfo=timezone.utc) + timedelta(
            days=number % 30, hours=number % 24
        )
        home_location = locations[number % len(locations)]
        tier = ["bronze", "silver", "gold"][number % 3]
        versions = 2 if number % 11 == 0 else 1
        for version in range(versions):
            effective_from = created_at + timedelta(days=60 * version)
            is_current = version == versions - 1
            effective_to = (
                created_at + timedelta(days=60 * version + 60) if not is_current else None
            )
            rows.append(
                {
                    "provider_record_id": stable_uuid(
                        "provider_record", f"provider-{number}-v{version}"
                    ),
                    "provider_id": provider_id,
                    "home_location_id": home_location["location_id"],
                    "provider_status": "ACTIVE",
                    "provider_tier": tier if version == 0 else "gold",
                    "created_at": created_at,
                    "effective_from": effective_from,
                    "effective_to": effective_to,
                    "is_current": is_current,
                    "source_loaded_at": loaded_at,
                }
            )
    return rows


def generate_eligibility(
    rng: random.Random,
    providers: list[dict],
    locations: list[dict],
) -> list[dict]:
    """Effective-dated provider eligibility (one row per provider/category/region)."""
    rows: list[dict] = []
    loaded_at = datetime(2026, 11, 9, 12, 0, 0, tzinfo=timezone.utc)
    seen: set[tuple] = set()
    for number, provider in enumerate(p["provider_id"] for p in providers if "provider_id" in p):
        provider_id = provider
        category_count = rng.randint(ELIGIBILITY_MIN_CATEGORIES, ELIGIBILITY_MAX_CATEGORIES)
        region_count = rng.randint(ELIGIBILITY_MIN_REGIONS, ELIGIBILITY_MAX_REGIONS)
        categories = rng.sample(SERVICE_CATEGORIES, category_count)
        regions = rng.sample([loc["location_id"] for loc in locations], region_count)
        for category in categories:
            for region in regions:
                key = (provider_id, category, region)
                if key in seen:
                    continue
                seen.add(key)
                effective_from = datetime(2026, 8, 1, tzinfo=timezone.utc)
                # A few deterministic eligibility end-dates to exercise
                # effective-dated logic.
                effective_to = (
                    datetime(2026, 10, 1, tzinfo=timezone.utc)
                    if number % 37 == 0
                    else None
                )
                rows.append(
                    {
                        "eligibility_id": stable_uuid(
                            "eligibility", f"{provider_id}|{category}|{region}"
                        ),
                        "provider_id": provider_id,
                        "service_category_id": category,
                        "location_id": region,
                        "effective_from": effective_from,
                        "effective_to": effective_to,
                        "is_eligible": True,
                        "source_loaded_at": loaded_at,
                    }
                )
    return rows


def generate_fee_policy() -> list[dict]:
    """One effective-dated fixed-fee policy row (TAD 6.14)."""
    return [
        {
            "fee_policy_id": stable_uuid("fee_policy", "baseline-15pct"),
            "fee_rate": 0.150000,
            "effective_from": datetime(2020, 1, 1, tzinfo=timezone.utc),
            "effective_to": None,
            "currency": "USD",
            "source_loaded_at": datetime(2026, 11, 9, 12, 0, 0, tzinfo=timezone.utc),
        }
    ]
