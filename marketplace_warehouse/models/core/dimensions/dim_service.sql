-- Grain: one service category (Type 1 for the MVP catalog).
select
    row_number() over (order by service_category_id)::bigint as service_sk,
    service_category_id,
    service_category_name,
    is_active
from {{ ref('stg_raw__service_categories') }}
