-- Grain: one provider availability/block interval (TAD 12.6).
select
    a.availability_id,
    dp.provider_sk,
    ds.service_sk,
    dl.location_sk,
    a.provider_id,
    a.service_category_id,
    a.location_id,
    a.start_at,
    a.end_at,
    a.availability_status,
    round((extract(epoch from (a.end_at - a.start_at)) / 60.0)::numeric, 6)
        as interval_minutes,
    a.source_loaded_at
from {{ ref('stg_raw__provider_availability_intervals') }} a
inner join {{ ref('dim_provider') }} dp
    on dp.provider_id = a.provider_id
   and dp.effective_from <= a.start_at
   and (dp.effective_to is null or dp.effective_to > a.start_at)
inner join {{ ref('dim_service') }} ds on ds.service_category_id = a.service_category_id
inner join {{ ref('dim_location') }} dl on dl.location_id = a.location_id
