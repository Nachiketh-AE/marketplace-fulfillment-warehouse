select idempotency_key
from {{ ref('stg_raw__booking_reschedule_events') }}
group by idempotency_key
having count(*) > 1
