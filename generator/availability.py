"""Provider availability interval generation (TAD 10.2, ADR-008).

Each interval belongs to one provider, one category, one region. Intervals
for the same provider may never overlap — the generator raises on violations
so invalid data cannot silently enter the business dataset.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from generator.config import stable_uuid
from generator.entities import GeneratedDataset

LOADED_AT = datetime(2026, 11, 9, 12, 0, 0, tzinfo=timezone.utc)


class OverlappingAvailabilityError(ValueError):
    """Raised when a provider's availability intervals would overlap."""


def add_interval(
    dataset: GeneratedDataset,
    provider_id,
    service_category_id: str,
    location_id: str,
    start_at: datetime,
    end_at: datetime,
    availability_status: str = "OPEN",
    validate: bool = True,
) -> dict:
    if end_at <= start_at:
        raise ValueError(f"Availability end must be after start ({start_at} >= {end_at})")
    if availability_status not in {"OPEN", "BLOCKED"}:
        raise ValueError(f"Invalid availability status {availability_status!r}")
    if validate:
        for row in dataset.availability_intervals:
            if row["provider_id"] != provider_id:
                continue
            # [start, end) convention: touching endpoints do not overlap.
            if start_at < row["end_at"] and row["start_at"] < end_at:
                raise OverlappingAvailabilityError(
                    f"Provider {provider_id} availability overlap: "
                    f"[{row['start_at']}, {row['end_at']}) vs [{start_at}, {end_at})"
                )
    interval = {
        "availability_id": stable_uuid(
            "availability", f"{provider_id}|{service_category_id}|{location_id}|{start_at.isoformat()}"
        ),
        "provider_id": provider_id,
        "service_category_id": service_category_id,
        "location_id": location_id,
        "start_at": start_at,
        "end_at": end_at,
        "availability_status": availability_status,
        "source_loaded_at": LOADED_AT,
    }
    dataset.availability_intervals.append(interval)
    return interval


def generate_availability(
    rng: random.Random,
    dataset: GeneratedDataset,
    data_start: datetime,
    data_end: datetime,
    intervals_per_provider: int,
) -> None:
    """Sequential, non-overlapping availability blocks per provider.

    A deterministic ~7% of intervals are BLOCKED; blocked time never
    contributes capacity.
    """
    eligibility_by_provider: dict = {}
    for row in dataset.eligibility:
        eligibility_by_provider.setdefault(row["provider_id"], []).append(row)

    for provider_rows in eligibility_by_provider.values():
        cursor = data_start
        made = 0
        guard = 0
        while made < intervals_per_provider and cursor < data_end and guard < intervals_per_provider * 3:
            guard += 1
            # Skip 0-2 days between availability blocks.
            cursor += timedelta(days=rng.randrange(0, 3), hours=rng.randrange(0, 10))
            duration_minutes = rng.choice([120, 180, 240, 300, 480])
            end_at = min(cursor + timedelta(minutes=duration_minutes), data_end)
            if end_at <= cursor:
                break
            choice = rng.choice(provider_rows)
            status = "BLOCKED" if rng.random() < 0.07 else "OPEN"
            add_interval(
                dataset,
                choice["provider_id"],
                choice["service_category_id"],
                choice["location_id"],
                cursor,
                end_at,
                status,
                validate=True,
            )
            made += 1
            cursor = end_at
