-- Terminal outcomes are final: no event may depart from a terminal state.
select event_id, booking_id, from_status, to_status
from {{ ref('stg_raw__booking_status_events') }}
where from_status in ('COMPLETED', 'CANCELLED', 'REJECTED', 'EXPIRED', 'NO_SHOW')
