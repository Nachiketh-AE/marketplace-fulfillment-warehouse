-- COMPLETED requires a preceding IN_PROGRESS state (TAD 12.2 lifecycle check).
select
    l.booking_id,
    l.final_status,
    l.in_progress_at,
    l.completed_at
from {{ ref('int_booking_lifecycle') }} l
where l.final_status = 'COMPLETED'
  and (l.in_progress_at is null or l.completed_at <= l.in_progress_at)
