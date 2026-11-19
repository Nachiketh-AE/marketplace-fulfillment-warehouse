-- Grain: one customer profile version (raw row). Light standardization only.
select
    customer_record_id,
    customer_id,
    home_location_id,
    initcap(lower(customer_segment))  as customer_segment,
    upper(account_status)             as account_status,
    created_at,
    effective_from,
    effective_to,
    is_current,
    source_loaded_at
from {{ source('raw', 'raw_customers') }}
