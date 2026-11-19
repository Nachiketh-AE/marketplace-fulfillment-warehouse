-- Grain: one booking. Aggregates posted financial events to booking grain
-- BEFORE joining to bookings (prevents one-to-many fanout, TAD 14.3) and
-- applies the fee/refund policy.
with booking_totals as (
    select
        booking_id,
        sum(amount) filter (where event_type = 'CAPTURE')  as captured_amount,
        sum(amount) filter (where event_type in ('REFUND', 'REVERSAL'))
            as refunded_or_reversed_amount,
        min(occurred_at) filter (where event_type = 'CAPTURE') as first_capture_at
    from {{ ref('int_payment_events_signed') }}
    group by booking_id
),

attempt_totals as (
    select
        booking_id,
        sum(amount) filter (where attempt_status = 'SUCCEEDED') as successful_attempt_amount,
        sum(amount) filter (where attempt_status = 'FAILED')    as failed_attempt_amount,
        count(*) filter (where attempt_status = 'FAILED')       as failed_attempt_count
    from {{ ref('stg_raw__payment_attempts') }}
    group by booking_id
),

lifecycle as (
    select
        booking_id,
        final_status,
        completed_at,
        has_valid_lifecycle
    from {{ ref('int_booking_lifecycle') }}
),

bookings as (
    select
        b.booking_id,
        b.service_value_amount,
        b.currency,
        b.is_test_booking,
        l.final_status,
        l.completed_at,
        l.has_valid_lifecycle
    from {{ ref('stg_raw__bookings') }} b
    inner join lifecycle l using (booking_id)
),

-- fee policy effective at the booking's completion time (TAD 9.5)
fee as (
    select
        bk.booking_id,
        fp.fee_rate
    from bookings bk
    left join {{ ref('stg_raw__fee_policy') }} fp
        on fp.effective_from <= coalesce(bk.completed_at, bk.created_at)
       and (fp.effective_to is null or fp.effective_to > coalesce(bk.completed_at, bk.created_at))
),

enriched as (
    select
        bk.booking_id,
        bk.service_value_amount,
        bk.currency,
        bk.is_test_booking,
        bk.final_status,
        bk.completed_at,
        bk.has_valid_lifecycle,
        coalesce(bt.captured_amount, 0)              as captured_amount,
        coalesce(bt.refunded_or_reversed_amount, 0)  as refunded_or_reversed_amount,
        coalesce(at_.successful_attempt_amount, 0)   as successful_attempt_amount,
        coalesce(at_.failed_attempt_amount, 0)       as failed_attempt_amount,
        coalesce(at_.failed_attempt_count, 0)        as failed_attempt_count,
        f.fee_rate,
        bk.final_status = 'COMPLETED'
            and bk.has_valid_lifecycle
            and not bk.is_test_booking as is_financially_eligible_completed_booking
    from bookings bk
    left join booking_totals bt using (booking_id)
    left join attempt_totals at_ using (booking_id)
    left join fee f using (booking_id)
),

calculated as (
    select
        *,
        -- Eligible service-value refund/reversal: only amounts related to
        -- this completed booking's captured value count against completed
        -- GMV; capped so refunds can never exceed the capture (TAD 9.4).
        least(refunded_or_reversed_amount, captured_amount)
            as eligible_refund_amount,
        case when is_financially_eligible_completed_booking
            then least(refunded_or_reversed_amount, captured_amount)
            else 0 end as allocated_refund_amount
    from enriched
)

select
    booking_id,
    service_value_amount,
    currency,
    is_test_booking,
    final_status,
    completed_at,
    has_valid_lifecycle,
    is_financially_eligible_completed_booking,
    captured_amount,
    refunded_or_reversed_amount,
    eligible_refund_amount,
    allocated_refund_amount,
    successful_attempt_amount,
    failed_attempt_amount,
    failed_attempt_count,
    fee_rate,
    case when is_financially_eligible_completed_booking
        then service_value_amount else 0 end::numeric(12,2) as gross_completed_gmv,
    case when is_financially_eligible_completed_booking
        then service_value_amount - allocated_refund_amount
        else 0 end::numeric(12,2) as net_completed_gmv,
    -- Fee reversal uses the ORIGINAL effective rate even for later refunds.
    round(
        case when is_financially_eligible_completed_booking
            then allocated_refund_amount else 0 end * coalesce(fee_rate, 0)
    , 2)::numeric(12,2) as platform_fee_reversal,
    round(
        case when is_financially_eligible_completed_booking
            then service_value_amount * coalesce(fee_rate, 0) else 0 end
    , 2)::numeric(12,2) as gross_platform_fee
from calculated
