-- Grain: one provider availability/block interval.
select
    availability_id,
    provider_id,
    service_category_id,
    location_id,
    start_at,
    end_at,
    upper(availability_status) as availability_status,
    source_loaded_at
from {{ source('raw', 'raw_provider_availability_intervals') }}
