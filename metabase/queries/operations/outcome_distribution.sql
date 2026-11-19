-- Final booking outcome distribution (distinct bookings, all time).
select
    final_status,
    count(*) as bookings
from marts.mart_booking_lifecycle
where is_eligible_booking
group by 1
order by bookings desc
