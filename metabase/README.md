# Metabase Dashboards

Two dashboards, both reading **only** the `marts` schema through the
`metabase_reader` role (TAD 20). Business logic lives in dbt — Metabase
displays governed outputs; it never recalculates metrics.

## One-time setup

1. Start services: `docker compose up -d` (PostgreSQL on :5432, Metabase on :3000).
2. Open http://localhost:3000, create the admin account.
3. **Add database**: PostgreSQL → host `postgres` (or `host.docker.internal`
   if Metabase runs outside the compose network), port 5432, database
   `warehouse`, user `metabase_reader`, password `metabase_reader`.
4. Verify only `marts` (plus core if explicitly granted) are visible.

## Dashboard 1 — Marketplace Operations

Primary source: `mart_booking_lifecycle`, `mart_booking_cohort_daily`,
`mart_supply_demand_hourly`. Saved questions in `queries/operations/`:

| Card | Question file | Notes |
|---|---|---|
| Eligible created bookings by cohort date | `operations/eligible_created_by_cohort.sql` | cohort (created) date basis |
| Outcome distribution | `operations/outcome_distribution.sql` | COMPLETED/CANCELLED/REJECTED/EXPIRED/NO_SHOW |
| Fulfillment & cancellation rates (mature cohorts) | `operations/fulfillment_cancellation_rates.sql` | withheld for immature cohorts |
| Cancellations by actor & reason | `operations/cancellations_by_actor_reason.sql` | |
| Median completion time | `operations/median_completion_time.sql` | IN_PROGRESS → COMPLETED basis |
| Demand vs capacity vs gap | `operations/demand_capacity_gap.sql` | labeled *modeled* gap |

## Dashboard 2 — Marketplace Economics

Primary source: `mart_marketplace_economics_booking`,
`mart_completed_economics_daily`, `mart_provider_payout_daily`.
Saved questions in `queries/economics/`.

| Card | Question file | Notes |
|---|---|---|
| Gross & net completed GMV | `economics/gmv_gross_net.sql` | completion-date basis |
| Captures / refunds / reversals | `economics/financial_activity.sql` | financial-event-date basis |
| Net platform fee revenue & take rate | `economics/fee_revenue_take_rate.sql` | aligned net scope |
| Provider earnings | `economics/provider_earnings.sql` | owed ≠ paid |
| Paid provider payouts | `economics/provider_payouts.sql` | **payout-date basis — separate axis from GMV** |

## Conventions every dashboard must keep

- Currency USD; times in America/New_York.
- Cohort (created) dates, service dates, completion dates, and payout dates
  are labeled and never mixed on one axis.
- `is_cohort_mature = false` cohorts show rates as unavailable, not zero.
- Every dashboard shows: **synthetic data** caveat and **modeled
  supply-demand gap ≠ confirmed unmet demand** caveat.
- Filters (borough/neighborhood/category/date) never silently change a
  metric's denominator or time basis.

## Screenshots

Screenshots are captured from your own running instance (none are fabricated
or committed). After setup: arrange cards per the tables above, then save
PNGs into `docs/assets/dashboard_*.png` — the README will render them from
that path.
