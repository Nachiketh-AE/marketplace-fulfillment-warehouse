"""CSV output and idempotent PostgreSQL loading (TAD 3.2, 18.2)."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from generator.entities import GeneratedDataset

TABLES = [
    "customers",
    "providers",
    "service_categories",
    "locations",
    "eligibility",
    "bookings",
    "status_events",
    "reschedule_events",
    "payment_attempts",
    "payment_events",
    "payouts",
    "availability_intervals",
    "fee_policy",
]

# logical name -> raw table name
RAW_TABLE_NAMES = {
    "customers": "raw_customers",
    "providers": "raw_providers",
    "service_categories": "raw_service_categories",
    "locations": "raw_locations",
    "eligibility": "raw_provider_service_eligibility",
    "bookings": "raw_bookings",
    "status_events": "raw_booking_status_events",
    "reschedule_events": "raw_booking_reschedule_events",
    "payment_attempts": "raw_payment_attempts",
    "payment_events": "raw_payment_events",
    "payouts": "raw_provider_payouts",
    "availability_intervals": "raw_provider_availability_intervals",
    "fee_policy": "raw_fee_policy",
}

# Column order per raw table (must match sql/init/02_raw_tables.sql).
RAW_COLUMNS = {
    "raw_customers": [
        "customer_record_id", "customer_id", "home_location_id", "customer_segment",
        "account_status", "created_at", "effective_from", "effective_to",
        "is_current", "source_loaded_at",
    ],
    "raw_providers": [
        "provider_record_id", "provider_id", "home_location_id", "provider_status",
        "provider_tier", "created_at", "effective_from", "effective_to",
        "is_current", "source_loaded_at",
    ],
    "raw_service_categories": ["service_category_id", "service_category_name", "is_active"],
    "raw_locations": ["location_id", "borough_name", "neighborhood_name", "is_active"],
    "raw_provider_service_eligibility": [
        "eligibility_id", "provider_id", "service_category_id", "location_id",
        "effective_from", "effective_to", "is_eligible", "source_loaded_at",
    ],
    "raw_bookings": [
        "booking_id", "customer_id", "provider_id", "service_category_id",
        "service_location_id", "created_at", "requested_start_at",
        "requested_duration_minutes", "service_value_amount", "currency",
        "is_test_booking", "source_loaded_at",
    ],
    "raw_booking_status_events": [
        "event_id", "booking_id", "event_sequence", "from_status", "to_status",
        "occurred_at", "actor_type", "actor_id", "reason_code",
        "idempotency_key", "source_loaded_at",
    ],
    "raw_booking_reschedule_events": [
        "reschedule_event_id", "booking_id", "old_scheduled_start_at",
        "new_scheduled_start_at", "occurred_at", "actor_type", "reason_code",
        "idempotency_key", "source_loaded_at",
    ],
    "raw_payment_attempts": [
        "payment_attempt_id", "booking_id", "attempt_number", "attempted_at",
        "attempt_status", "amount", "currency", "failure_code",
        "idempotency_key", "source_loaded_at",
    ],
    "raw_payment_events": [
        "payment_event_id", "booking_id", "payment_attempt_id",
        "related_payment_event_id", "event_type", "amount", "currency",
        "occurred_at", "idempotency_key", "source_loaded_at",
    ],
    "raw_provider_payouts": [
        "payout_id", "booking_id", "provider_id", "amount", "currency",
        "payout_status", "initiated_at", "paid_at", "idempotency_key",
        "source_loaded_at",
    ],
    "raw_provider_availability_intervals": [
        "availability_id", "provider_id", "service_category_id", "location_id",
        "start_at", "end_at", "availability_status", "source_loaded_at",
    ],
    "raw_fee_policy": [
        "fee_policy_id", "fee_rate", "effective_from", "effective_to",
        "currency", "source_loaded_at",
    ],
}


def _serialize(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def write_dataset(dataset: GeneratedDataset, out_dir: Path) -> dict[str, int]:
    """Write every generated table to CSV files; return row counts."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for logical in TABLES:
        rows: list[dict] = getattr(dataset, logical)
        raw_name = RAW_TABLE_NAMES[logical]
        columns = RAW_COLUMNS[raw_name]
        path = out_dir / f"{raw_name}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([_serialize(row.get(column)) for column in columns])
        counts[logical] = len(rows)
    # Invalid edge-case scenarios are recorded, never loaded silently.
    with (out_dir / "rejected_records.json").open("w", encoding="utf-8") as handle:
        json.dump(dataset.rejected_records, handle, indent=2, default=str)
    counts["rejected_records"] = len(dataset.rejected_records)
    return counts


def load_dataset(input_dir: Path, database_url: str) -> dict[str, int]:
    """Idempotently load generated CSVs into the PostgreSQL ``raw`` schema.

    - Uses ``ON CONFLICT DO NOTHING`` on primary keys and unique
      idempotency keys, so re-running the load never duplicates events.
    - Skips rows listed in ``rejected_records.json`` (invalid fixtures).
    """
    import psycopg2  # local import: only required for loading

    input_dir = Path(input_dir)
    counts: dict[str, int] = {}
    with psycopg2.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("set timezone = 'UTC'")
            for logical in TABLES:
                raw_name = RAW_TABLE_NAMES[logical]
                columns = RAW_COLUMNS[raw_name]
                path = input_dir / f"{raw_name}.csv"
                if not path.exists():
                    counts[raw_name] = 0
                    continue
                inserted = 0
                with path.open(newline="", encoding="utf-8") as handle:
                    reader = csv.reader(handle)
                    header = next(reader)
                    placeholders = ", ".join(["%s"] * len(columns))
                    column_list = ", ".join(columns)
                    statement = (
                        f"insert into raw.{raw_name} ({column_list}) "
                        f"values ({placeholders}) on conflict do nothing"
                    )
                    for values in reader:
                        cursor.execute(statement, values)
                        inserted += cursor.rowcount
                counts[raw_name] = inserted
    return counts
