"""Incremental processing and idempotency demonstration (TAD 18).

Batch-first: the full batch pipeline is the primary path. This module
documents and demonstrates the incremental behaviour:

1. Append-only raw events with unique idempotency keys.
2. ``source_loaded_at`` as the ingestion watermark (late events discovered
   by ingestion time, not occurrence time).
3. Affected booking IDs recomputed from full event history.
4. Reprocessing the same batch never changes business totals.

Run the demonstration end-to-end with the dbt workflow:

    # batch
    python -m generator.cli generate --seed 42 --scale fixtures --out-dir data/fixtures
    python -m generator.cli load --input-dir data/fixtures
    dbt build --project-dir marketplace_warehouse \\
        --vars "$(python -m generator.incremental fixture_vars)"

    # re-load the SAME batch and rebuild: totals must not change
    python -m generator.cli load --input-dir data/fixtures
    dbt build ...  # assert_completed_gmv_reconciles_to_fixture still passes
"""

from __future__ import annotations

import argparse
import json

from generator.fixtures import fixture_expected_totals


def fixture_vars() -> str:
    """CLI helper: emit dbt --vars JSON for fixture reconciliation."""
    return json.dumps({"fixture_expected_totals": fixture_expected_totals()})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generator.incremental", description=__doc__)
    parser.add_argument("mode", choices=["fixture_vars"], help="emit dbt vars JSON")
    args = parser.parse_args(argv)
    if args.mode == "fixture_vars":
        print(fixture_vars())
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
