-- Grain: one posted capture/refund/reversal event, with signed effect.
select
    p.payment_event_id,
    p.booking_id,
    p.payment_attempt_id,
    p.related_payment_event_id,
    p.event_type,
    p.amount,
    p.signed_amount,
    p.currency,
    p.occurred_at,
    dd.date_key as event_date_key,
    p.idempotency_key,
    p.source_loaded_at
from {{ ref('int_payment_events_signed') }} p
inner join {{ ref('dim_date') }} dd
    on dd.full_date = (p.occurred_at at time zone 'America/New_York')::date
