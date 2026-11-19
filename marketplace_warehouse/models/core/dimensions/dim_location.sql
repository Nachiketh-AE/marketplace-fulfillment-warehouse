-- Grain: one neighborhood/service region (Type 1; borough attribute).
select
    row_number() over (order by location_id)::bigint as location_sk,
    location_id,
    borough_name,
    neighborhood_name,
    is_active
from {{ ref('stg_raw__locations') }}
