-- ACTUAL paid provider payouts by payout date (PAID only).
-- Payout dates are a different event basis than completion dates.
select
    payout_date,
    sum(paid_payout_amount) as paid_payout_amount,
    sum(paid_payout_count)  as paid_payout_count
from marts.mart_provider_payout_daily
group by 1
order by 1
