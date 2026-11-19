-- Grain: one provider payout transaction. Provider version resolved at
-- PAID time for paid payouts, otherwise at initiation (TAD 12.5).
select
    p.payout_id,
    p.booking_id,
    dp.provider_sk,
    p.provider_id,
    p.amount,
    p.currency,
    p.payout_status,
    p.initiated_at,
    p.paid_at,
    dd_paid.date_key as paid_date_key,
    dd_init.date_key as initiated_date_key,
    p.idempotency_key,
    p.source_loaded_at
from {{ ref('stg_raw__provider_payouts') }} p
left join {{ ref('dim_provider') }} dp
    on dp.provider_id = p.provider_id
   and dp.effective_from <= coalesce(p.paid_at, p.initiated_at)
   and (dp.effective_to is null or dp.effective_to > coalesce(p.paid_at, p.initiated_at))
left join {{ ref('dim_date') }} dd_paid
    on dd_paid.full_date = (p.paid_at at time zone 'America/New_York')::date
inner join {{ ref('dim_date') }} dd_init
    on dd_init.full_date = (p.initiated_at at time zone 'America/New_York')::date
