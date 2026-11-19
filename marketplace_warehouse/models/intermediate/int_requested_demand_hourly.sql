-- Grain: one hour bucket x booking. Splits each booking's requested service
-- interval across hourly buckets using exact interval intersection — a
-- 90-minute request starting 10:30 contributes 0.5h to 10:00 and 0.5h to
-- 11:00 (TAD 10.3). Uses the ORIGINAL requested service slot basis.
with bookings as (
    select
        b.booking_id,
        b.service_category_id,
        b.service_location_id,
        r.current_scheduled_start_at as service_start_at,
        r.current_scheduled_start_at
            + (b.requested_duration_minutes || ' minutes')::interval as service_end_at
    from {{ ref('stg_raw__bookings') }} b
    inner join {{ ref('int_booking_reschedule_reconstructed') }} r using (booking_id)
    where not b.is_test_booking
),

expanded as (
    select
        b.booking_id,
        b.service_category_id,
        b.service_location_id,
        hour_bucket.hour_start as hour_bucket_start_at,
        greatest(b.service_start_at, hour_bucket.hour_start) as overlap_start,
        least(b.service_end_at, hour_bucket.hour_start + interval '1 hour') as overlap_end
    from bookings b
    cross join lateral (
        select generate_series(
            date_trunc('hour', b.service_start_at),
            date_trunc('hour', b.service_end_at - interval '1 microsecond'),
            interval '1 hour'
        ) as hour_start
    ) hour_bucket
)

select
    booking_id,
    service_category_id,
    service_location_id,
    hour_bucket_start_at,
    overlap_start,
    overlap_end,
    round(
        (extract(epoch from (overlap_end - overlap_start)) / 60.0)::numeric, 6
    ) as overlap_minutes
from expanded
where overlap_end > overlap_start
