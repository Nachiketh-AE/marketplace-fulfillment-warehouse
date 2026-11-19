-- Fulfillment and cancellation rates by creation cohort.
-- Rates shown ONLY for mature cohorts (14-day window + all terminal).
select
    booking_created_date,
    round(100.0 * sum(completed_bookings) / nullif(sum(eligible_created_bookings), 0), 2)
        as fulfillment_rate_pct,
    round(100.0 * sum(cancelled_bookings) / nullif(sum(eligible_created_bookings), 0), 2)
        as cancellation_rate_pct
from marts.mart_booking_cohort_daily
where is_cohort_mature
group by 1
order by 1
