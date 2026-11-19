-- Grain: one booking. Current/final lifecycle state; event history lives in
-- fct_booking_status_event (TAD 12.1).
with lifecycle as (
    select * from {{ ref('int_booking_lifecycle') }}
),

reschedule as (
    select * from {{ ref('int_booking_reschedule_reconstructed') }}
),

eligible as (
    select
        b.booking_id,
        b.customer_id,
        b.service_category_id,
        b.service_location_id,
        b.provider_id,
        b.created_at,
        b.requested_start_at,
        b.requested_duration_minutes,
        b.service_value_amount,
        b.currency,
        b.is_test_booking,
        b.source_loaded_at
    from {{ ref('stg_raw__bookings') }} b
)

select
    b.booking_id,
    dc.customer_sk,
    dp.provider_sk,
    ds.service_sk,
    dl.location_sk,
    dd_created.date_key as created_date_key,
    dd_requested.date_key as requested_service_date_key,
    dd_completed.date_key as completed_date_key,
    b.created_at,
    l.accepted_at,
    l.scheduled_at,
    l.in_progress_at,
    l.completed_at,
    l.terminal_at,
    b.requested_start_at,
    r.current_scheduled_start_at,
    b.requested_duration_minutes,
    b.service_value_amount,
    b.currency,
    l.final_status,
    l.has_valid_lifecycle and not b.is_test_booking as is_eligible_booking,
    b.is_test_booking,
    greatest(b.source_loaded_at, max_se.max_loaded_at) as source_loaded_at,
    l.final_actor_type,
    l.terminal_reason_code
from eligible b
inner join lifecycle l using (booking_id)
inner join reschedule r using (booking_id)
left join {{ ref('dim_customer') }} dc
    on dc.customer_id = b.customer_id
   and dc.effective_from <= b.created_at
   and (dc.effective_to is null or dc.effective_to > b.created_at)
left join {{ ref('dim_provider') }} dp
    on dp.provider_id = b.provider_id
   and dp.effective_from <= coalesce(l.accepted_at, b.created_at)
   and (dp.effective_to is null or dp.effective_to > coalesce(l.accepted_at, b.created_at))
inner join {{ ref('dim_service') }} ds on ds.service_category_id = b.service_category_id
inner join {{ ref('dim_location') }} dl on dl.location_id = b.service_location_id
left join {{ ref('dim_date') }} dd_created
    on dd_created.full_date = (b.created_at at time zone 'America/New_York')::date
left join {{ ref('dim_date') }} dd_requested on dd_requested.full_date = (b.requested_start_at at time zone 'America/New_York')::date
left join {{ ref('dim_date') }} dd_completed on dd_completed.full_date = (l.completed_at at time zone 'America/New_York')::date
inner join (
    select booking_id, max(source_loaded_at) as max_loaded_at
    from {{ ref('stg_raw__booking_status_events') }}
    group by booking_id
) max_se using (booking_id)
