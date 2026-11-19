-- Grain: one booking status transition (append-only event history, TAD 12.2).
select
    o.event_id,
    o.booking_id,
    o.event_sequence,
    o.from_status,
    o.to_status,
    o.occurred_at,
    dd.date_key as event_date_key,
    o.actor_type,
    o.actor_id,
    o.reason_code,
    o.idempotency_key,
    o.source_loaded_at,
    o.is_valid_transition
from {{ ref('int_booking_status_ordered') }} o
inner join {{ ref('dim_date') }} dd
    on dd.full_date = (o.occurred_at at time zone 'America/New_York')::date
