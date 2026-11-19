-- Grain: one booking. Adds the derived net platform fee revenue and
-- provider earnings on top of int_booking_financials (TAD 9.5, 9.6).
select
    booking_id,
    final_status,
    is_financially_eligible_completed_booking,
    gross_completed_gmv,
    allocated_refund_amount as eligible_refund_amount,
    net_completed_gmv,
    fee_rate,
    gross_platform_fee,
    platform_fee_reversal,
    (gross_platform_fee - platform_fee_reversal)::numeric(12,2)
        as net_platform_fee_revenue,
    (net_completed_gmv - (gross_platform_fee - platform_fee_reversal))::numeric(12,2)
        as provider_earnings,
    captured_amount,
    refunded_or_reversed_amount
from {{ ref('int_booking_financials') }}
