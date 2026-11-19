-- Grain: one booking. Derives the current scheduled start by applying
-- reschedule events in order; the old time must equal the previously
-- current scheduled start (TAD 8.4).
with events as (
    select
        reschedule_event_id,
        booking_id,
        old_scheduled_start_at,
        new_scheduled_start_at,
        occurred_at,
        lag(new_scheduled_start_at) over (
            partition by booking_id order by occurred_at, reschedule_event_id
        ) as expected_old_time,
        row_number() over (
            partition by booking_id order by occurred_at, reschedule_event_id
        ) as reschedule_position
    from {{ ref('stg_raw__booking_reschedule_events') }}
),

latest as (
    select distinct on (booking_id)
        booking_id, new_scheduled_start_at
    from events
    order by booking_id, occurred_at desc, reschedule_event_id desc
)

select
    b.booking_id,
    coalesce(l.new_scheduled_start_at, b.requested_start_at) as current_scheduled_start_at,
    coalesce(l.new_scheduled_start_at, b.requested_start_at)
        <> b.requested_start_at as was_rescheduled,
    coalesce(r.reschedule_count, 0) as reschedule_count
from {{ ref('stg_raw__bookings') }} b
left join latest l using (booking_id)
left join (
    select booking_id, count(*) as reschedule_count
    from events
    group by booking_id
) r using (booking_id)
