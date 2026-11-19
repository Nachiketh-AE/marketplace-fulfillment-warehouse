-- Hand-calculated fixture reconciliation (TAD 9.7 / 17.4).
-- Runs ONLY when fixture reconciliation totals are supplied, because the
-- expected values are defined outside the production SQL:
--   dbt build --vars '{fixture_expected_totals: {...}}'
-- CI supplies them for the deterministic fixtures dataset.
{%- set expected = var('fixture_expected_totals', none) %}
{%- if expected %}
with actual as (
    select
        sum(gross_completed_gmv) as gross_completed_gmv,
        sum(eligible_refund_amount) as eligible_refund_amount,
        sum(net_completed_gmv) as net_completed_gmv,
        sum(gross_platform_fee) as gross_platform_fee,
        sum(platform_fee_reversal) as platform_fee_reversal,
        sum(net_platform_fee_revenue) as net_platform_fee_revenue,
        sum(provider_earnings) as provider_earnings,
        count(*) filter (where final_status = 'COMPLETED'
            and is_financially_eligible_completed_booking) as completed_bookings
    from {{ ref('mart_marketplace_economics_booking') }}
)
select 'gross_completed_gmv' as measure, gross_completed_gmv::text as actual_value, '{{ expected.gross_completed_gmv }}' as expected_value
from actual where gross_completed_gmv::text <> '{{ expected.gross_completed_gmv }}'
union all
select 'eligible_refund_amount', eligible_refund_amount::text, '{{ expected.eligible_refund_amount }}'
from actual where eligible_refund_amount::text <> '{{ expected.eligible_refund_amount }}'
union all
select 'net_completed_gmv', net_completed_gmv::text, '{{ expected.net_completed_gmv }}'
from actual where net_completed_gmv::text <> '{{ expected.net_completed_gmv }}'
union all
select 'gross_platform_fee', gross_platform_fee::text, '{{ expected.gross_platform_fee }}'
from actual where gross_platform_fee::text <> '{{ expected.gross_platform_fee }}'
union all
select 'platform_fee_reversal', platform_fee_reversal::text, '{{ expected.platform_fee_reversal }}'
from actual where platform_fee_reversal::text <> '{{ expected.platform_fee_reversal }}'
union all
select 'net_platform_fee_revenue', net_platform_fee_revenue::text, '{{ expected.net_platform_fee_revenue }}'
from actual where net_platform_fee_revenue::text <> '{{ expected.net_platform_fee_revenue }}'
union all
select 'provider_earnings', provider_earnings::text, '{{ expected.provider_earnings }}'
from actual where provider_earnings::text <> '{{ expected.provider_earnings }}'
union all
select 'completed_bookings', completed_bookings::text, '{{ expected.completed_bookings }}'
from actual where completed_bookings::text <> '{{ expected.completed_bookings }}'
{%- else %}
-- fixture_expected_totals var not supplied: nothing to check.
select null::text as measure, null::text as actual_value, null::text as expected_value
where false
{%- endif %}
