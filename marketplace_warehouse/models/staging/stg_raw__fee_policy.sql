-- Grain: one effective-dated fee policy version.
select
    fee_policy_id,
    fee_rate,
    effective_from,
    effective_to,
    currency,
    source_loaded_at
from {{ source('raw', 'raw_fee_policy') }}
