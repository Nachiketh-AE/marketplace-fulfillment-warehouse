-- Every successful attempt is linked to a posted capture event; failed
-- attempts never create one (TAD 9.2 / 17.3 #10).
select
    a.payment_attempt_id,
    a.booking_id,
    a.attempt_number
from {{ ref('stg_raw__payment_attempts') }} a
left join {{ ref('stg_raw__payment_events') }} pe
    on pe.payment_attempt_id = a.payment_attempt_id
   and pe.event_type = 'CAPTURE'
where a.attempt_status = 'SUCCEEDED'
  and pe.payment_event_id is null
