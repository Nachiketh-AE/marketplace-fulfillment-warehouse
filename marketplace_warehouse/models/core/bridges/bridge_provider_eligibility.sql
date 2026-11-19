-- Grain: one provider x category x region eligibility interval (TAD 12.7).
select
    e.eligibility_id,
    dp.provider_sk,
    ds.service_sk,
    dl.location_sk,
    e.provider_id,
    e.service_category_id,
    e.location_id,
    e.effective_from,
    e.effective_to,
    e.is_eligible
from {{ ref('stg_raw__provider_service_eligibility') }} e
inner join {{ ref('dim_provider') }} dp
    on dp.provider_id = e.provider_id
   and dp.effective_from <= e.effective_from
   and (dp.effective_to is null or dp.effective_to > e.effective_from)
inner join {{ ref('dim_service') }} ds on ds.service_category_id = e.service_category_id
inner join {{ ref('dim_location') }} dl on dl.location_id = e.location_id
