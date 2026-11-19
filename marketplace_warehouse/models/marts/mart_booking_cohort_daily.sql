-- Grain: booking-created date (NYC) x borough x neighborhood x category.
-- Source for cancellation and fulfillment rates with cohort maturity.
{% set maturity_days = 14 %}
select
    l.created_date as booking_created_date,
    l.borough_name,
    l.neighborhood_name,
    l.service_category_name,
    count(*) filter (where l.is_eligible_booking) as eligible_created_bookings,
    count(*) filter (where l.is_eligible_booking and l.final_status = 'COMPLETED') as completed_bookings,
    count(*) filter (where l.is_eligible_booking and l.final_status = 'CANCELLED') as cancelled_bookings,
    count(*) filter (where l.is_eligible_booking and l.final_status = 'REJECTED') as rejected_bookings,
    count(*) filter (where l.is_eligible_booking and l.final_status = 'EXPIRED') as expired_bookings,
    count(*) filter (where l.is_eligible_booking and l.final_status = 'NO_SHOW') as no_show_bookings,
    -- mature: every eligible cohort booking terminal, or the cohort window
    -- (PRD 8.1 / config COHORT_MATURITY_WINDOW_DAYS) has elapsed
    bool_and(case when l.is_eligible_booking
        then l.final_status in ('COMPLETED','CANCELLED','REJECTED','EXPIRED','NO_SHOW')
        else true end)
        and (l.created_date <= current_date - interval '{{ maturity_days }} days')
        as is_cohort_mature
from {{ ref('mart_booking_lifecycle') }} l
group by 1, 2, 3, 4
