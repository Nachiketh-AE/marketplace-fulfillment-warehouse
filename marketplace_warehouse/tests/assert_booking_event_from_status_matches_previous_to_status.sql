-- Chain continuity: from_status equals the previous event's to_status.
with ordered as (
    select
        event_id,
        booking_id,
        from_status,
        to_status,
        lag(to_status) over (partition by booking_id order by occurred_at, event_sequence, event_id)
            as previous_to_status
    from {{ ref('stg_raw__booking_status_events') }}
)
select event_id, booking_id, from_status, previous_to_status
from ordered
where from_status is distinct from previous_to_status
