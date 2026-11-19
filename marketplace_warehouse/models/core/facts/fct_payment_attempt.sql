-- Grain: one payment attempt. Failed attempts never become captured value.
select
    a.payment_attempt_id,
    a.booking_id,
    a.attempt_number,
    a.attempted_at,
    dd.date_key as attempt_date_key,
    a.attempt_status,
    a.amount,
    a.currency,
    a.failure_code,
    a.idempotency_key,
    a.source_loaded_at
from {{ ref('stg_raw__payment_attempts') }} a
inner join {{ ref('dim_date') }} dd
    on dd.full_date = (a.attempted_at at time zone 'America/New_York')::date
