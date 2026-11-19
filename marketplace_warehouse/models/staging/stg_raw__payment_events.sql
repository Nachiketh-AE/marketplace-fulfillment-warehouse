-- Grain: one posted capture/refund/reversal event.
select
    payment_event_id,
    booking_id,
    payment_attempt_id,
    related_payment_event_id,
    upper(event_type) as event_type,
    amount,
    currency,
    occurred_at,
    idempotency_key,
    source_loaded_at
from {{ source('raw', 'raw_payment_events') }}
