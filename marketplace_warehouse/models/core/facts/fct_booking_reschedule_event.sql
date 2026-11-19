-- Grain: one reschedule event (TAD 12.ftr: reschedule history).
select
    r.reschedule_event_id,
    r.booking_id,
    r.old_scheduled_start_at,
    r.new_scheduled_start_at,
    r.occurred_at,
    dd.date_key as event_date_key,
    r.actor_type,
    r.reason_code,
    r.idempotency_key,
    r.source_loaded_at
from {{ ref('stg_raw__booking_reschedule_events') }} r
inner join {{ ref('dim_date') }} dd
    on dd.full_date = (r.occurred_at at time zone 'America/New_York')::date
