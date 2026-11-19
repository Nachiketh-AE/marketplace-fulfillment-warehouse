"""Command-line interface.

Examples (PowerShell):

    python -m generator.cli generate --seed 42 --scale small
    python -m generator.cli generate --seed 42 --scale fixtures --out-dir data/fixtures
    python -m generator.cli load --input-dir data/generated/small --database-url $env:DATABASE_URL

``--scale fixtures`` builds the deterministic edge-case dataset used by the
dbt reconciliation tests; ``small``/``medium`` build the randomized-by-seed
datasets described in the PRD.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from generator import availability as availability_module
from generator import booking_lifecycle as lifecycle
from generator import payments as payments_module
from generator.config import (
    DATA_END,
    DATA_START,
    DEFAULT_SCENARIO_PROPORTIONS,
    SCALES,
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
from generator.fixtures import build_fixture_dataset
from generator.load import write_dataset

DEFAULT_OUT_DIRS = {
    "fixtures": Path("data/fixtures"),
    "small": Path("data/generated/small"),
    "medium": Path("data/generated/medium"),
}


def build_dataset(seed: int, scale: str):
    """Build a dataset at the requested scale (fixtures ignores the seed)."""
    if scale == "fixtures":
        return build_fixture_dataset()
    config = SCALES[scale]
    rng = random.Random(seed)
    dataset = GeneratedDataset()
    dataset.service_categories = generate_service_categories()
    dataset.locations = generate_locations(config.neighborhoods_per_borough)
    dataset.customers = generate_customers(config.customers, dataset.locations)
    dataset.providers = generate_providers(config.providers, dataset.locations)
    dataset.eligibility = generate_eligibility(rng, dataset.providers, dataset.locations)
    dataset.fee_policy = generate_fee_policy()
    lifecycle.generate_bookings(
        rng, dataset, config.bookings, DATA_START, DATA_END,
        DEFAULT_SCENARIO_PROPORTIONS,
    )
    payments_module.generate_payments(rng, dataset, payment_events_by_booking={})
    availability_module.generate_availability(
        rng, dataset, DATA_START, DATA_END, config.availability_intervals_per_provider
    )
    return dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generator.cli", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate synthetic source data")
    generate.add_argument("--seed", type=int, default=42)
    generate.add_argument("--scale", choices=[*SCALES, "fixtures"], default="small")
    generate.add_argument("--out-dir", type=Path, default=None)

    load = subparsers.add_parser("load", help="Load generated CSVs into PostgreSQL")
    load.add_argument("--input-dir", type=Path, default=None)
    load.add_argument(
        "--database-url",
        default=None,
        help="postgres://... (defaults to env DATABASE_URL)",
    )

    args = parser.parse_args(argv)

    if args.command == "generate":
        out_dir = args.out_dir or DEFAULT_OUT_DIRS[args.scale]
        dataset = build_dataset(args.seed, args.scale)
        counts = write_dataset(dataset, out_dir)
        print(f"Scale {args.scale!r} written to {out_dir}")
        for name, count in counts.items():
            print(f"  {name}: {count}")
        return 0

    if args.command == "load":
        import os

        input_dir = args.input_dir or Path("data/fixtures")
        database_url = args.database_url or os.environ.get("DATABASE_URL")
        if not database_url:
            print("error: --database-url or DATABASE_URL is required", file=sys.stderr)
            return 2
        from generator.load import load_dataset

        counts = load_dataset(input_dir, database_url)
        print("Rows inserted (idempotent; re-runs insert nothing new):")
        for name, count in sorted(counts.items()):
            print(f"  {name}: {count}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
