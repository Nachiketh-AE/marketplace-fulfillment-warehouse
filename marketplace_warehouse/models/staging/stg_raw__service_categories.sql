-- Grain: one service category.
select
    service_category_id,
    service_category_name,
    is_active
from {{ source('raw', 'raw_service_categories') }}
