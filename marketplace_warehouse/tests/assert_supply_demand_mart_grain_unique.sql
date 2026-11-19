-- One row per hour x borough x neighborhood x category (TAD 17.3 #22).
select
    hour_bucket_start_at, borough_name, neighborhood_name, service_category_name,
    count(*) as grain_rows
from {{ ref('mart_supply_demand_hourly') }}
group by 1, 2, 3, 4
having count(*) > 1
