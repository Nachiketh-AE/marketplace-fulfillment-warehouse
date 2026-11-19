select idempotency_key
from {{ ref('stg_raw__payment_events') }}
group by idempotency_key
having count(*) > 1
