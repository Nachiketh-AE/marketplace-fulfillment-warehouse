-- Every event follows the allowed transition contract (TAD 8.2 / 17.3 #2).
select event_id, booking_id, from_status, to_status
from {{ ref('int_booking_status_ordered') }}
where not is_valid_transition
