-- Fee reversal must equal the allocated refund x the ORIGINAL effective
-- rate, rounded to cents (TAD 9.5 / 17.3 #13).
select
    booking_id,
    allocated_refund_amount,
    fee_rate,
    platform_fee_reversal,
    round(allocated_refund_amount * coalesce(fee_rate, 0), 2) as expected_reversal
from {{ ref('int_booking_financials') }}
where is_financially_eligible_completed_booking
  and platform_fee_reversal
      <> round(allocated_refund_amount * coalesce(fee_rate, 0), 2)
