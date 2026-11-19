-- Grain: one booking. Principal source for outcome, lifecycle durations,
-- and operational analysis (TAD 13.3). Dates are NYC local reporting dates.
select
    f.booking_id,
    (f.created_at at time zone 'America/New_York')::date  as created_date,
    (f.requested_start_at at time zone 'America/New_York')::date as service_date,
    dl.borough_name,
    dl.neighborhood_name,
    ds.service_category_name,
    f.final_status,
    f.is_eligible_booking,
    f.requested_duration_minutes,
    f.service_value_amount,
    round((extract(epoch from (f.accepted_at - f.created_at)) / 60.0)::numeric, 2)
        as created_to_accepted_minutes,
    round((extract(epoch from (f.scheduled_at - f.accepted_at)) / 60.0)::numeric, 2)
        as accepted_to_scheduled_minutes,
    round((extract(epoch from (f.completed_at - f.in_progress_at)) / 60.0)::numeric, 2)
        as in_progress_to_completed_minutes,
    round((extract(epoch from (f.completed_at - f.created_at)) / 60.0)::numeric, 2)
        as created_to_completed_minutes,
    case when f.final_status = 'CANCELLED' then f.final_actor_type end
        as cancellation_actor_type,
    case when f.final_status in ('CANCELLED','REJECTED','EXPIRED','NO_SHOW')
        then f.terminal_reason_code end as terminal_reason_code
from {{ ref('fct_booking') }} f
inner join {{ ref('dim_location') }} dl on dl.location_sk = f.location_sk
inner join {{ ref('dim_service') }} ds on ds.service_sk = f.service_sk
