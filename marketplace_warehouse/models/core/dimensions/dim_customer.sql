-- Grain: one customer profile version. SCD Type 2 (TAD 11.1, 11.2).
select
    row_number() over (
        order by customer_id, effective_from
    )::bigint as customer_sk,
    customer_id,
    home_location_id,
    customer_segment,
    account_status,
    created_at,
    effective_from,
    effective_to,
    is_current
from {{ ref('stg_raw__customers') }}
