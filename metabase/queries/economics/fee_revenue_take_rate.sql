-- Net platform fee revenue and take rate on the aligned net scope.
select
    completed_date,
    sum(net_platform_fee_revenue) as net_platform_fee_revenue,
    sum(net_completed_gmv) as net_completed_gmv,
    round(100.0 * sum(net_platform_fee_revenue) / nullif(sum(net_completed_gmv), 0), 2)
        as take_rate_pct
from marts.mart_marketplace_economics_booking
where is_financially_eligible_completed_booking
group by 1
order by 1
