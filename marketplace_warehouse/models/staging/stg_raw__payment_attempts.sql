-- Grain: one payment attempt.
select
    payment_attempt_id,
    booking_id,
    attempt_number,
    attempted_at,
    upper(attempt_status) as attempt_status,
    amount,
    currency,
    failure_code,
    idempotency_key,
    source_loaded_at
from {{ source('raw', 'raw_payment_attempts') }}
