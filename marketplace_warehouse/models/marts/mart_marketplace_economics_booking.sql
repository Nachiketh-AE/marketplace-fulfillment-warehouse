-- Grain: one booking. Booking-level marketplace economics (TAD 13.3).
-- Financial event amounts are aggregated to booking grain upstream
-- (int_booking_financials) so no fanout can inflate values here.
select
    e.booking_id,
    (f.completed_at at time zone 'America/New_York')::date as completed_date,
    ds.service_category_name,
    dl.borough_name,
    dl.neighborhood_name,
    e.final_status,
    e.is_financially_eligible_completed_booking,
    e.gross_completed_gmv,
    e.eligible_refund_amount,
    e.net_completed_gmv,
    e.fee_rate,
    e.gross_platform_fee,
    e.platform_fee_reversal,
    (e.gross_platform_fee - e.platform_fee_reversal) as net_platform_fee_revenue,
    (e.net_completed_gmv - (e.gross_platform_fee - e.platform_fee_reversal))
        as provider_earnings,
    e.captured_amount,
    e.refunded_or_reversed_amount,
    coalesce(paid.paid_amount, 0) as paid_provider_payout_amount
from {{ ref('int_booking_economics') }} e
inner join {{ ref('fct_booking') }} f using (booking_id)
inner join {{ ref('dim_service') }} ds on ds.service_sk = f.service_sk
inner join {{ ref('dim_location') }} dl on dl.location_sk = f.location_sk
left join (
    -- payout aggregated separately: its grain/date basis differs from GMV
    select booking_id, sum(amount) as paid_amount
    from {{ ref('fct_provider_payout') }}
    where payout_status = 'PAID'
    group by booking_id
) paid using (booking_id)
