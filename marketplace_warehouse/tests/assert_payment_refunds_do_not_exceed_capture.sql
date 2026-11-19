-- Cumulative refund/reversal can never exceed the booking's capture (TAD 9.3).
with totals as (
    select
        booking_id,
        sum(amount) filter (where event_type = 'CAPTURE') as captured,
        sum(amount) filter (where event_type in ('REFUND', 'REVERSAL')) as returned
    from {{ ref('stg_raw__payment_events') }}
    group by booking_id
)
select booking_id, captured, returned
from totals
where returned > captured
