-- Grain: one booking. Reconstructs the full lifecycle from the append-only
-- event history. Events are never overwritten; state is derived (TAD 8.3).
with ordered as (
    select * from {{ ref('int_booking_status_ordered') }}
),

validity as (
    select
        booking_id,
        bool_and(is_valid_transition) as has_valid_chain,
        count(*) = count(distinct event_sequence) as has_unique_sequences
    from ordered
    group by booking_id
),

lifecycle as (
    select
        booking_id,
        bool_and(is_valid_transition) as all_transitions_valid,
        count(*) filter (where to_status = 'CREATED') as created_event_count,
        min(occurred_at) filter (where to_status = 'CREATED')     as created_at,
        min(occurred_at) filter (where to_status = 'ACCEPTED')    as accepted_at,
        min(occurred_at) filter (where to_status = 'SCHEDULED')   as scheduled_at,
        min(occurred_at) filter (where to_status = 'IN_PROGRESS') as in_progress_at,
        min(occurred_at) filter (where to_status = 'COMPLETED')   as completed_at
    from ordered
    group by booking_id
),

final_state as (
    select distinct on (booking_id)
        booking_id,
        to_status   as final_status,
        occurred_at as final_event_at,
        actor_type  as final_actor_type,
        reason_code as terminal_reason_code
    from ordered
    order by booking_id, occurred_at desc, event_sequence desc, event_id desc
)

select
    b.booking_id,
    l.created_at,
    l.accepted_at,
    l.scheduled_at,
    l.in_progress_at,
    l.completed_at,
    f.final_event_at as terminal_at,
    f.final_status,
    f.final_actor_type,
    f.terminal_reason_code,
    l.created_event_count = 1
        and v.has_valid_chain
        and v.has_unique_sequences as has_valid_lifecycle,
    l.all_transitions_valid
from (select distinct booking_id from ordered) b
left join lifecycle l using (booking_id)
left join final_state f using (booking_id)
left join validity v using (booking_id)
