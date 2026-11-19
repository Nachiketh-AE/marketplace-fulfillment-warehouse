-- Requested demand hours vs eligible capacity hours and the MODELED gap.
-- Modeled indicator only: NOT confirmed unmet customer demand.
select
    service_date,
    borough_name,
    service_category_name,
    sum(requested_demand_hours) as requested_demand_hours,
    sum(eligible_available_capacity_hours) as eligible_capacity_hours,
    sum(modeled_gap_hours) as modeled_gap_hours
from marts.mart_supply_demand_hourly
group by 1, 2, 3
order by modeled_gap_hours desc
