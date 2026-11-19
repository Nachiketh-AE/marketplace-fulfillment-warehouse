-- Grain: one reschedule event (append-only).
select
    reschedule_event_id,
    booking_id,
    old_scheduled_start_at,
    new_scheduled_start_at,
    occurred_at,
    upper(actor_type) as actor_type,
    reason_code,
    idempotency_key,
    source_loaded_at
from {{ source('raw', 'raw_booking_reschedule_events') }}
