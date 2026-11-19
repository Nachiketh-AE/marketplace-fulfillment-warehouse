-- Grain: one provider profile version. SCD Type 2 (TAD 11.1, 11.2).
select
    row_number() over (
        order by provider_id, effective_from
    )::bigint as provider_sk,
    provider_id,
    home_location_id,
    provider_status,
    provider_tier,
    created_at,
    effective_from,
    effective_to,
    is_current
from {{ ref('stg_raw__providers') }}
