-- Gross and net completed-service GMV by completion date (NYC local).
select
    completed_date,
    sum(gross_completed_gmv) as gross_completed_gmv,
    sum(net_completed_gmv)   as net_completed_gmv
from marts.mart_marketplace_economics_booking
where is_financially_eligible_completed_booking
group by 1
order by 1
