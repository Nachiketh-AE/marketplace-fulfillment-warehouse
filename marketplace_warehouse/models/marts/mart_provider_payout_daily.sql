-- Grain: payout date (NYC local, PAID only) x provider.
-- Payouts use the PAID date, never the booking completion date (TAD 9.6).
select
    (p.paid_at at time zone 'America/New_York')::date as payout_date,
    p.provider_id,
    sum(p.amount) as paid_payout_amount,
    count(*) as paid_payout_count
from {{ ref('fct_provider_payout') }} p
where p.payout_status = 'PAID'
group by 1, 2
