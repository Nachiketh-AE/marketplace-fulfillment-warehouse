-- Grain: one provider payout transaction.
select
    payout_id,
    booking_id,
    provider_id,
    amount,
    currency,
    upper(payout_status) as payout_status,
    initiated_at,
    paid_at,
    idempotency_key,
    source_loaded_at
from {{ source('raw', 'raw_provider_payouts') }}
