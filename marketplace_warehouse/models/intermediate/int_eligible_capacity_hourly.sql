-- Grain: one hour bucket x provider x category x region. Eligible OPEN
-- availability minutes intersecting each hourly bucket (TAD 10.4).
with availability as (
    select
        availability_id,
        provider_id,
        service_category_id,
        location_id,
        start_at,
        end_at
    from {{ ref('stg_raw__provider_availability_intervals') }}
    where availability_status = 'OPEN'
),

-- Effective eligibility as of the interval start (TAD 10.4).
qualified as (
    select
        a.availability_id,
        a.provider_id,
        a.service_category_id,
        a.location_id,
        a.start_at,
        a.end_at
    from availability a
    inner join {{ ref('bridge_provider_eligibility') }} e
        on e.provider_id = a.provider_id
       and e.service_category_id = a.service_category_id
       and e.location_id = a.location_id
       and e.is_eligible
       and e.effective_from <= a.start_at
       and (e.effective_to is null or e.effective_to > a.start_at)
),

expanded as (
    select
        q.availability_id,
        q.provider_id,
        q.service_category_id,
        q.location_id,
        hour_bucket.hour_start as hour_bucket_start_at,
        greatest(q.start_at, hour_bucket.hour_start) as overlap_start,
        least(q.end_at, hour_bucket.hour_start + interval '1 hour') as overlap_end
    from qualified q
    cross join lateral (
        select generate_series(
            date_trunc('hour', q.start_at),
            date_trunc('hour', q.end_at - interval '1 microsecond'),
            interval '1 hour'
        ) as hour_start
    ) hour_bucket
)

select
    availability_id,
    provider_id,
    service_category_id,
    location_id,
    hour_bucket_start_at,
    overlap_start,
    overlap_end,
    round(
        (extract(epoch from (overlap_end - overlap_start)) / 60.0)::numeric, 6
    ) as overlap_minutes
from expanded
where overlap_end > overlap_start
