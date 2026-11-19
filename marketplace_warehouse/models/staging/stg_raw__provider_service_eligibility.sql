-- Grain: one provider x category x region eligibility interval.
select
    eligibility_id,
    provider_id,
    service_category_id,
    location_id,
    effective_from,
    effective_to,
    is_eligible,
    source_loaded_at
from {{ source('raw', 'raw_provider_service_eligibility') }}
where is_eligible
