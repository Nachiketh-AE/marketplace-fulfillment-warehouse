-- Cancellation actor and reason mix.
select
    cancellation_actor_type,
    coalesce(terminal_reason_code, 'UNSPECIFIED') as reason_code,
    count(*) as bookings
from marts.mart_booking_lifecycle
where is_eligible_booking and final_status = 'CANCELLED'
group by 1, 2
order by bookings desc
