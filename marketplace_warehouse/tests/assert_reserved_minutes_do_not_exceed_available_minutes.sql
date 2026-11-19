-- Reserved minutes per availability interval can never exceed its open
-- minutes (TAD 10.6 / 17.3 #21).
select
    r.availability_id,
    sum(r.reserved_minutes) as reserved_minutes,
    a.interval_minutes
from {{ ref('int_reserved_booking_minutes') }} r
inner join {{ ref('fct_provider_availability') }} a using (availability_id)
group by r.availability_id, a.interval_minutes
having sum(r.reserved_minutes) > a.interval_minutes + 0.001
