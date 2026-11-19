-- Every booking has exactly one creation event (TAD 17.3 #1).
select booking_id
from {{ ref('stg_raw__booking_status_events') }}
where to_status = 'CREATED'
group by booking_id
having count(*) <> 1
