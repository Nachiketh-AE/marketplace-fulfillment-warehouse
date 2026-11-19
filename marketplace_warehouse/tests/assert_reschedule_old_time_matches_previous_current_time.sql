-- Each reschedule's old time equals the previously current scheduled start
-- (first reschedule: the originally requested start) (TAD 8.4).
with events as (
    select
        r.*,
        lag(new_scheduled_start_at) over (
            partition by booking_id order by occurred_at, reschedule_event_id
        ) as expected_old_time
    from {{ ref('stg_raw__booking_reschedule_events') }} r
),
first_events as (
    select * from events where expected_old_time is null
)
select
    e.reschedule_event_id,
    e.booking_id,
    e.old_scheduled_start_at,
    e.expected_old_time
from events e
left join {{ ref('stg_raw__bookings') }} b using (booking_id)
where
    (e.expected_old_time is not null and e.old_scheduled_start_at <> e.expected_old_time)
    or (
        e.expected_old_time is null
        and e.old_scheduled_start_at <> b.requested_start_at
    )
