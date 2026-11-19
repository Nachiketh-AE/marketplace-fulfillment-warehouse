-- Take-rate inputs must share scope: net fee revenue derives from the SAME
-- net GMV it is divided by (TAD 9.6 / 17.3 #15).
select
    booking_id,
    net_completed_gmv,
    net_platform_fee_revenue,
    provider_earnings,
    gross_completed_gmv,
    allocated_refund_amount
from {{ ref('int_booking_financials') }} f
where is_financially_eligible_completed_booking
  and (
    f.net_completed_gmv <> f.gross_completed_gmv - f.allocated_refund_amount
    or f.gross_platform_fee - f.platform_fee_reversal
       <> round(f.service_value_amount * coalesce(f.fee_rate, 0), 2)
          - round(f.allocated_refund_amount * coalesce(f.fee_rate, 0), 2)
  )
