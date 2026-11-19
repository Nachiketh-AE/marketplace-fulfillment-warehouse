select availability_id, start_at, end_at
from {{ ref('stg_raw__provider_availability_intervals') }}
where end_at <= start_at
