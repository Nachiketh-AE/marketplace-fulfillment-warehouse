-- Grain: one neighborhood/service region.
select
    location_id,
    borough_name,
    neighborhood_name,
    is_active
from {{ source('raw', 'raw_locations') }}
