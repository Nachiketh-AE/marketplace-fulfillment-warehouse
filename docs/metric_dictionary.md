# Metric Dictionary

Governed metric contracts (PRD §8, TAD §14.2). Every KPI on a dashboard must
trace to an entry here and to a dbt model. Time basis and refund treatment are
part of each contract — they may not be changed by a dashboard filter.

---

## Gross completed-service GMV

| Aspect | Contract |
|---|---|
| Business definition | Service value of bookings whose valid lifecycle reaches `COMPLETED`, before refunds |
| Business purpose | Size the marketplace's completed-service activity |
| Formula | `SUM(service_value_amount)` over financially eligible completed bookings |
| Numerator / denominator | n/a (additive measure) |
| Grain | Booking → daily/period aggregates via `mart_completed_economics_daily` |
| Required joins | `fct_booking` → `int_booking_economics` (aggregated to booking grain upstream) |
| dbt model | `mart_marketplace_economics_booking.gross_completed_gmv` |
| Timestamp basis | Completion date (NYC local) for daily reporting |
| Filters / exclusions | Excludes taxes, tips, cancelled/rejected/expired/no-show bookings, test bookings, invalid lifecycles |
| Refund treatment | None — gross measure |
| Dimensional slicing | Borough, neighborhood, service category, completion date |
| Caveats | A completed booking always has a successful capture in this dataset (project rule, TAD 9.2) |
| Example | `select sum(gross_completed_gmv) from marts.mart_marketplace_economics_booking where is_financially_eligible_completed_booking` |

## Net completed-service GMV

Gross completed GMV **less** eligible customer refunds/reversals allocated to
completed service value, capped at captured value. Refunds for non-completed
bookings never reduce it (they were never in the numerator). Same scope,
grain, filters, and completion-date basis as gross GMV.
Model: `mart_marketplace_economics_booking.net_completed_gmv`.

## Completed bookings

Count of **distinct** `booking_id` with valid lifecycle and final status
`COMPLETED`. Counts bookings, never status events. Cohort basis: booking
creation date. Model: `mart_booking_cohort_daily.completed_bookings` /
`mart_booking_lifecycle`.

## Cancellation rate

| Aspect | Contract |
|---|---|
| Definition | Eligible created bookings ending `CANCELLED` ÷ eligible created bookings, same creation cohort |
| Purpose | Track customer/provider-driven demand loss |
| Formula | `cancelled_bookings / nullif(eligible_created_bookings, 0)` |
| Grain | Booking-created date × borough × neighborhood × category |
| dbt model | `mart_booking_cohort_daily` |
| Timestamp basis | `created_date` (NYC local) — numerator and denominator share it |
| Exclusions | Test/invalid records; rejection/expiry/no-show are separate outcomes, not cancellations |
| Caveats | Only quote rates for `is_cohort_mature` cohorts (14-day window + all-terminal rule) |

## Fulfillment rate

Eligible created bookings ending `COMPLETED` ÷ eligible created bookings in
the same creation cohort, using the same maturity rule as cancellation rate.
Model: `mart_booking_cohort_daily` (`completed_bookings / eligible_created_bookings`,
mature cohorts only).

## Platform fee revenue (net)

Gross platform fee (completed service value × fee rate effective at completion)
minus proportional fee reversal (allocated refund × the **same original rate**).
Rounded to cents at calculation boundary. Model:
`mart_marketplace_economics_booking.net_platform_fee_revenue`. Excludes payout
amounts and cancellation fees (none generated in MVP).

## Take rate

Net platform fee revenue ÷ net completed-service GMV × 100, same scope/period/
eligibility/refund treatment on both sides. `nullif(denominator, 0)` — never a
misleading zero. Model: ratio over `mart_marketplace_economics_booking`
(see README §Metrics for SQL pattern).

## Provider earnings

Net completed GMV − net platform fee revenue, per booking under the baseline
policy. This is the amount **owed** to providers. Model:
`mart_marketplace_economics_booking.provider_earnings`.

## Provider payouts

Sum of payout transactions with `payout_status='PAID'`, attributed to the
**payout date** (`paid_at`), never the booking completion date. PENDING /
FAILED / REVERSED payouts are reported separately and excluded from paid
totals. Model: `mart_provider_payout_daily`, `fct_provider_payout`.

## Provider utilization (reserved)

| Aspect | Contract |
|---|---|
| Definition | Reserved booking minutes intersecting OPEN availability ÷ open available minutes × 100 |
| Purpose | How effectively declared availability is booked |
| Formula | `reserved_booking_hours / eligible_available_capacity_hours × 100` (null when capacity = 0) |
| Grain | Hour × borough × neighborhood × category |
| dbt model | `mart_supply_demand_hourly.reserved_utilization_rate` |
| Timestamp basis | Requested/current scheduled service time |
| Exclusions | Cancelled bookings excluded from reserved time; BLOCKED intervals excluded from capacity |
| Caveats | Reserved (scheduled) utilization, NOT realized labor; availability is modeled |

## Median completion time

Median (`percentile_cont(0.5)`) of `completed_at − in_progress_at` for
completed bookings — service execution duration. Request-to-completion
(`completed_at − created_at`) is the separate companion metric
(`mart_booking_lifecycle.created_to_completed_minutes`). Never mix the two.

## Requested demand hours

Sum of requested service duration for eligible non-test bookings allocated to
hourly buckets by **exact interval intersection** (a 90-minute request at
10:30 adds 0.5h to 10:00 and 0.5h to 11:00). Booking-based demand only —
searches that never became bookings are invisible. Model:
`mart_supply_demand_hourly.requested_demand_hours` via
`int_requested_demand_hourly`.

## Eligible provider capacity hours

OPEN availability minutes (for effectively eligible providers, [start, end)
convention) intersecting the same hour × category × region bucket, clipped to
the bucket. No double counting: provider intervals never overlap (ADR-008).
Model: `mart_supply_demand_hourly.eligible_available_capacity_hours`.

## Modeled supply-demand gap

Requested demand hours − eligible available capacity hours. **A modeled
indicator only**: it is not observed or confirmed unmet customer demand —
no search/no-match events exist in the MVP. Dashboards must use the label
"modeled supply-demand gap" and display the caveat. Model:
`mart_supply_demand_hourly.modeled_gap_hours`.
