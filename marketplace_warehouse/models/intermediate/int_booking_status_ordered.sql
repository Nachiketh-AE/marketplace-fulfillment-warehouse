-- Grain: one booking status event, deterministically ordered per booking.
-- Ordering: occurred_at, then event_sequence, then event_id (TAD 8.3).
with ranked as (
    select
        event_id,
        booking_id,
        event_sequence,
        from_status,
        to_status,
        occurred_at,
        actor_type,
        actor_id,
        reason_code,
        idempotency_key,
        source_loaded_at,
        lag(to_status) over (
            partition by booking_id
            order by occurred_at, event_sequence, event_id
        ) as prior_reconstructed_status,
        row_number() over (
            partition by booking_id
            order by occurred_at, event_sequence, event_id
        ) as history_position
    from {{ ref('stg_raw__booking_status_events') }}
)
select
    *,
    case
        when history_position = 1 and from_status is null and to_status = 'CREATED' then true
        when from_status = prior_reconstructed_status
             and from_status is not null
             and prior_reconstructed_status not in
                 ('COMPLETED', 'CANCELLED', 'REJECTED', 'EXPIRED', 'NO_SHOW')
            then true
        else false
    end as is_valid_transition
from ranked
