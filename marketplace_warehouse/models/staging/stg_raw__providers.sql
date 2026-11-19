-- Grain: one provider profile version (raw row).
select
    provider_record_id,
    provider_id,
    home_location_id,
    upper(provider_status)   as provider_status,
    lower(provider_tier)     as provider_tier,
    created_at,
    effective_from,
    effective_to,
    is_current,
    source_loaded_at
from {{ source('raw', 'raw_providers') }}
