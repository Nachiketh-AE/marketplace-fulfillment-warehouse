-- One provider cannot be reserved for two overlapping service windows.
with reservations as (
    select
        b.booking_id,
        b.provider_id,
        r.current_scheduled_start_at as window_start,
        r.current_scheduled_start_at
            + (b.requested_duration_minutes || ' minutes')::interval as window_end
    from {{ ref('stg_raw__bookings') }} b
    inner join {{ ref('int_booking_reschedule_reconstructed') }} r using (booking_id)
    inner join {{ ref('int_booking_lifecycle') }} l using (booking_id)
    where b.provider_id is not null
      and l.final_status in ('ACCEPTED','SCHEDULED','IN_PROGRESS','COMPLETED')
)
select
    a.provider_id,
    a.booking_id as booking_a,
    b.booking_id as booking_b
from reservations a
inner join reservations b
    on a.provider_id = b.provider_id
   and a.booking_id < b.booking_id
   and a.window_start < b.window_end
   and b.window_start < a.window_end
