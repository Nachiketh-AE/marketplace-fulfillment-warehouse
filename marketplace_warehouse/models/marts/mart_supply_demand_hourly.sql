-- Grain: one hour bucket (UTC start; NYC service_date) x borough x
-- neighborhood x category. Modeled supply-demand indicator only — NOT
-- confirmed unmet demand (TAD 10.5).
with demand as (
    select
        d.hour_bucket_start_at,
        dl.borough_name,
        dl.neighborhood_name,
        ds.service_category_name,
        count(distinct d.booking_id) as booking_count,
        sum(d.overlap_minutes) / 60.0 as requested_demand_hours
    from {{ ref('int_requested_demand_hourly') }} d
    inner join {{ ref('dim_location') }} dl on dl.location_id = d.service_location_id
    inner join {{ ref('dim_service') }} ds on ds.service_category_id = d.service_category_id
    group by 1, 2, 3, 4
),

capacity as (
    select
        c.hour_bucket_start_at,
        dl.borough_name,
        dl.neighborhood_name,
        ds.service_category_name,
        sum(c.overlap_minutes) / 60.0 as eligible_available_capacity_hours
    from {{ ref('int_eligible_capacity_hourly') }} c
    inner join {{ ref('dim_location') }} dl on dl.location_id = c.location_id
    inner join {{ ref('dim_service') }} ds on ds.service_category_id = c.service_category_id
    group by 1, 2, 3, 4
),

reserved as (
    select
        r.hour_bucket_start_at,
        dl.borough_name,
        dl.neighborhood_name,
        ds.service_category_name,
        sum(r.reserved_minutes) / 60.0 as reserved_booking_hours
    from {{ ref('int_reserved_booking_minutes') }} r
    inner join {{ ref('dim_location') }} dl on dl.location_id = r.location_id
    inner join {{ ref('dim_service') }} ds on ds.service_category_id = r.service_category_id
    group by 1, 2, 3, 4
),

grain as (
    select
        coalesce(d.hour_bucket_start_at, c.hour_bucket_start_at, r.hour_bucket_start_at)
            as hour_bucket_start_at,
        coalesce(d.borough_name, c.borough_name, r.borough_name) as borough_name,
        coalesce(d.neighborhood_name, c.neighborhood_name, r.neighborhood_name)
            as neighborhood_name,
        coalesce(d.service_category_name, c.service_category_name, r.service_category_name)
            as service_category_name,
        coalesce(d.booking_count, 0) as booking_count,
        coalesce(d.requested_demand_hours, 0) as requested_demand_hours,
        coalesce(c.eligible_available_capacity_hours, 0) as eligible_available_capacity_hours,
        coalesce(r.reserved_booking_hours, 0) as reserved_booking_hours
    from demand d
    full outer join capacity c using
        (hour_bucket_start_at, borough_name, neighborhood_name, service_category_name)
    full outer join reserved r using
        (hour_bucket_start_at, borough_name, neighborhood_name, service_category_name)
)

select
    hour_bucket_start_at,
    (hour_bucket_start_at at time zone 'America/New_York')::date as service_date,
    borough_name,
    neighborhood_name,
    service_category_name,
    booking_count,
    round(requested_demand_hours, 4) as requested_demand_hours,
    round(eligible_available_capacity_hours, 4) as eligible_available_capacity_hours,
    round(reserved_booking_hours, 4) as reserved_booking_hours,
    round(requested_demand_hours - eligible_available_capacity_hours, 4)
        as modeled_gap_hours,
    case
        when eligible_available_capacity_hours > 0 then
            round(reserved_booking_hours / eligible_available_capacity_hours * 100, 4)
        else null
    end as reserved_utilization_rate
from grain
