"""Queries the medium synthetic dataset for README insights (master prompt §11).

Every number printed here comes from the actual generated/loaded dataset and
is labeled as a synthetic-data observation. Run after loading the medium
dataset and running dbt build:

    DATABASE_URL=... python -m generator.insights --scale medium
"""

from __future__ import annotations

import argparse
import os


QUERIES = {
    "outcome_mix": """
        select final_status, count(*) as bookings
        from marts.mart_booking_lifecycle
        where is_eligible_booking
        group by 1 order by 2 desc
    """,
    "cancellation_by_category": """
        select service_category_name,
               round(100.0 * count(*) filter (where final_status = 'CANCELLED')
                     / nullif(count(*), 0), 2) as cancellation_rate_pct,
               count(*) as bookings
        from marts.mart_booking_lifecycle
        where is_eligible_booking
        group by 1 order by cancellation_rate_pct desc
    """,
    "fulfillment_by_borough": """
        select borough_name,
               round(100.0 * count(*) filter (where final_status = 'COMPLETED')
                     / nullif(count(*), 0), 2) as fulfillment_rate_pct,
               count(*) as bookings
        from marts.mart_booking_lifecycle
        where is_eligible_booking
        group by 1 order by fulfillment_rate_pct desc
    """,
    "economics_totals": """
        select sum(gross_completed_gmv) as gross_completed_gmv,
               sum(eligible_refund_amount) as eligible_refund_amount,
               sum(net_completed_gmv) as net_completed_gmv,
               sum(gross_platform_fee) as gross_platform_fee,
               sum(platform_fee_reversal) as platform_fee_reversal,
               sum(net_platform_fee_revenue) as net_platform_fee_revenue,
               sum(provider_earnings) as provider_earnings,
               round(100.0 * sum(net_platform_fee_revenue)
                     / nullif(sum(net_completed_gmv), 0), 2) as take_rate_pct
        from marts.mart_marketplace_economics_booking
        where is_financially_eligible_completed_booking
    """,
    "payout_status": """
        select payout_status, count(*) as payouts, sum(amount) as amount
        from core.fct_provider_payout
        group by 1 order by 2 desc
    """,
    "gap_by_borough": """
        select borough_name,
               round(sum(requested_demand_hours), 1) as requested_demand_hours,
               round(sum(eligible_available_capacity_hours), 1) as eligible_capacity_hours,
               round(sum(modeled_gap_hours), 1) as modeled_gap_hours
        from marts.mart_supply_demand_hourly
        group by 1 order by modeled_gap_hours desc
    """,
    "utilization_by_borough": """
        select borough_name,
               round(sum(reserved_booking_hours)
                     / nullif(sum(eligible_available_capacity_hours), 0) * 100, 2)
               as reserved_utilization_pct
        from marts.mart_supply_demand_hourly
        group by 1 order by reserved_utilization_pct desc nulls last
    """,
    "median_completion": """
        select percentile_cont(0.5) within group (order by in_progress_to_completed_minutes)
                   as median_completion_minutes
        from marts.mart_booking_lifecycle
        where is_eligible_booking and final_status = 'COMPLETED'
    """,
    "refund_rate": """
        select round(100.0 * sum(eligible_refund_amount)
                     / nullif(sum(gross_completed_gmv), 0), 2) as refunded_value_share_pct
        from marts.mart_marketplace_economics_booking
        where is_financially_eligible_completed_booking
    """,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generator.insights", description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args(argv)
    if not args.database_url:
        parser.error("--database-url or DATABASE_URL required")

    import psycopg2

    print("# Observations from SYNTHETIC data (not real marketplace economics)\n")
    with psycopg2.connect(args.database_url) as connection:
        with connection.cursor() as cursor:
            for name, query in QUERIES.items():
                cursor.execute(query)
                columns = [d.name for d in cursor.description]
                print(f"## {name}\n")
                print("| " + " | ".join(columns) + " |")
                print("|" + "---|" * len(columns))
                for row in cursor.fetchall():
                    print("| " + " | ".join(str(v) for v in row) + " |")
                print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
