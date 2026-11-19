-- Provider earnings (amount OWED) by completion date. Not payouts.
select
    completed_date,
    sum(provider_earnings) as provider_earnings
from marts.mart_marketplace_economics_booking
where is_financially_eligible_completed_booking
group by 1
order by 1
