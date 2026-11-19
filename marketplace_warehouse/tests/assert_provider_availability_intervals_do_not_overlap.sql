-- No overlapping intervals per provider across any category/region (ADR-008).
select
    a.provider_id,
    a.availability_id as interval_a,
    b.availability_id as interval_b,
    a.start_at, a.end_at, b.start_at, b.end_at
from {{ ref('stg_raw__provider_availability_intervals') }} a
inner join {{ ref('stg_raw__provider_availability_intervals') }} b
    on a.provider_id = b.provider_id
   and a.availability_id < b.availability_id
   and a.start_at < b.end_at
   and b.start_at < a.end_at
