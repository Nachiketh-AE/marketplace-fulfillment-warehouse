-- Grain: one posted payment event. Derives the signed balance effect:
-- capture positive, refund/reversal negative (TAD 9.3, 12.4).
select
    payment_event_id,
    booking_id,
    payment_attempt_id,
    related_payment_event_id,
    event_type,
    amount,
    case event_type
        when 'CAPTURE' then amount
        when 'REFUND'  then -amount
        when 'REVERSAL' then -amount
    end as signed_amount,
    currency,
    occurred_at,
    idempotency_key,
    source_loaded_at
from {{ ref('stg_raw__payment_events') }}
