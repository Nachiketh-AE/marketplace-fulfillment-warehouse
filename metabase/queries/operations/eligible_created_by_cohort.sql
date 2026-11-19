-- Eligible created bookings by booking-creation cohort date (NYC local).
select
    booking_created_date,
    sum(eligible_created_bookings) as eligible_created_bookings
from marts.mart_booking_cohort_daily
group by 1
order by 1
