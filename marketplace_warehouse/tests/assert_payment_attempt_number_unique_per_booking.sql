select booking_id, attempt_number, count(*) as attempt_rows
from {{ ref('stg_raw__payment_attempts') }}
group by booking_id, attempt_number
having count(*) > 1
