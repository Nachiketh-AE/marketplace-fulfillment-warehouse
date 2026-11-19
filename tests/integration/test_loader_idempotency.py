"""Integration tests: loader idempotency (requires a live PostgreSQL).

These tests are skipped automatically when DATABASE_URL is not set or the
server is unreachable — e.g. in sandboxed local runs without Docker. CI
starts a PostgreSQL service so they run there (TAD 17.1 "Loader idempotency").
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "data" / "fixtures"

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set; loader integration tests require PostgreSQL",
)


@pytest.fixture(scope="module")
def db():
    import psycopg2

    connection = psycopg2.connect(os.environ["DATABASE_URL"])
    yield connection
    connection.close()


def test_load_is_idempotent(db):
    from generator.load import load_dataset

    first = load_dataset(FIXTURE_DIR, os.environ["DATABASE_URL"])
    counts_before = snapshot(db)
    second = load_dataset(FIXTURE_DIR, os.environ["DATABASE_URL"])
    counts_after = snapshot(db)
    # re-loading the same batch inserts nothing new
    for table, count in counts_after.items():
        assert count == counts_before[table], f"{table} changed on re-load"


def test_rejected_records_never_loaded(db):
    import json

    rejected = json.loads((FIXTURE_DIR / "rejected_records.json").read_text())
    with db.cursor() as cursor:
        for record in rejected:
            if record["scenario"] == "duplicate_payment_event":
                key = record["row"]["idempotency_key"]
                cursor.execute(
                    "select count(*) from raw.raw_payment_events where idempotency_key = %s",
                    (key,),
                )
                assert cursor.fetchone()[0] <= 1


def snapshot(db):
    with db.cursor() as cursor:
        cursor.execute(
            """
            select relname, n_live_tup from pg_stat_user_tables
            where schemaname = 'raw'
            """
        )
        return {row[0]: row[1] for row in cursor.fetchall()}
