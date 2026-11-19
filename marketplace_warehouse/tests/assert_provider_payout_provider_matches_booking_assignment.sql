-- A payout's provider must match the booking's assigned provider.
select
    p.payout_id,
    p.booking_id,
    p.provider_id as payout_provider,
    b.provider_id as booking_provider
from {{ ref('stg_raw__provider_payouts') }} p
inner join {{ ref('stg_raw__bookings') }} b using (booking_id)
where b.provider_id is not null
  and p.provider_id <> b.provider_id
