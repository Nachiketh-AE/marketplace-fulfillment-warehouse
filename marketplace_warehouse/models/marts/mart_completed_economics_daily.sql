-- Grain: completion date (NYC local) x borough x neighborhood x category.
select
    e.completed_date,
    e.borough_name,
    e.neighborhood_name,
    e.service_category_name,
    count(*) as completed_bookings,
    sum(e.gross_completed_gmv) as gross_completed_gmv,
    sum(e.net_completed_gmv) as net_completed_gmv,
    sum(e.net_platform_fee_revenue) as net_platform_fee_revenue,
    sum(e.provider_earnings) as provider_earnings
from {{ ref('mart_marketplace_economics_booking') }} e
where e.is_financially_eligible_completed_booking
group by 1, 2, 3, 4
