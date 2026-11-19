-- Every capacity row traces to an OPEN interval with effective eligibility
-- at interval start (TAD 10.4 / 17.3 #20).
select
    c.availability_id,
    c.hour_bucket_start_at
from {{ ref('int_eligible_capacity_hourly') }} c
left join {{ ref('stg_raw__provider_availability_intervals') }} a
    on a.availability_id = c.availability_id
   and a.availability_status = 'OPEN'
left join {{ ref('bridge_provider_eligibility') }} e
    on e.provider_id = c.provider_id
   and e.service_category_id = c.service_category_id
   and e.location_id = c.location_id
   and e.is_eligible
   and e.effective_from <= a.start_at
   and (e.effective_to is null or e.effective_to > a.start_at)
where a.availability_id is null or e.eligibility_id is null
