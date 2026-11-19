-- Assigned providers must be eligible for the booking's category/region
-- effective at acceptance time (TAD 7.3 / 17.3 #8).
with accepted as (
    select booking_id, min(occurred_at) as accepted_at
    from {{ ref('stg_raw__booking_status_events') }}
    where to_status = 'ACCEPTED'
    group by booking_id
)
select
    b.booking_id,
    b.provider_id,
    b.service_category_id,
    b.service_location_id,
    a.accepted_at
from {{ ref('stg_raw__bookings') }} b
inner join accepted a using (booking_id)
left join {{ ref('stg_raw__provider_service_eligibility') }} e
    on e.provider_id = b.provider_id
   and e.service_category_id = b.service_category_id
   and e.location_id = b.service_location_id
   and e.is_eligible
   and e.effective_from <= a.accepted_at
   and (e.effective_to is null or e.effective_to > a.accepted_at)
where b.provider_id is not null
  and e.eligibility_id is null
