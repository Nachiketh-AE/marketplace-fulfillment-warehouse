-- Grain: one booking status transition (append-only).
select
    event_id,
    booking_id,
    event_sequence,
    upper(from_status)   as from_status,
    upper(to_status)     as to_status,
    occurred_at,
    upper(actor_type)    as actor_type,
    actor_id,
    reason_code,
    idempotency_key,
    source_loaded_at
from {{ source('raw', 'raw_booking_status_events') }}
