-- Grain: one booking x availability-interval intersection x hour bucket. Reserved minutes
-- come from valid accepted/scheduled/in-progress/completed bookings with an
-- assigned provider; the window is intersected with the provider's OPEN
-- intervals so reserved time can never exceed available time (TAD 10.6).
with bookings as (
    select
        b.booking_id,
        b.provider_id,
        b.service_category_id,
        b.service_location_id,
        r.current_scheduled_start_at as service_start_at,
        r.current_scheduled_start_at
            + (b.requested_duration_minutes || ' minutes')::interval as service_end_at
    from {{ ref('stg_raw__bookings') }} b
    inner join {{ ref('int_booking_reschedule_reconstructed') }} r using (booking_id)
    inner join {{ ref('int_booking_lifecycle') }} l using (booking_id)
    where b.provider_id is not null
      and l.final_status in ('ACCEPTED', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED')
      and l.has_valid_lifecycle
      and not b.is_test_booking
),

intersections as (
    select
        b.booking_id,
        b.provider_id,
        a.availability_id,
        a.service_category_id,
        a.location_id,
        greatest(b.service_start_at, a.start_at) as overlap_start,
        least(b.service_end_at, a.end_at) as overlap_end
    from bookings b
    inner join {{ ref('stg_raw__provider_availability_intervals') }} a
        on a.provider_id = b.provider_id
       and a.availability_status = 'OPEN'
       and b.service_start_at < a.end_at
       and a.start_at < b.service_end_at
),

-- Split each intersection into hourly buckets for the hourly supply-demand mart.
hourly as (
    select
        i.booking_id,
        i.provider_id,
        i.availability_id,
        i.service_category_id,
        i.location_id,
        hour_bucket.hour_start as hour_bucket_start_at,
        greatest(i.overlap_start, hour_bucket.hour_start) as overlap_start,
        least(i.overlap_end, hour_bucket.hour_start + interval '1 hour') as overlap_end
    from intersections i
    cross join lateral (
        select generate_series(
            date_trunc('hour', i.overlap_start),
            date_trunc('hour', i.overlap_end - interval '1 microsecond'),
            interval '1 hour'
        ) as hour_start
    ) hour_bucket
    where i.overlap_end > i.overlap_start
)

select
    booking_id,
    provider_id,
    availability_id,
    service_category_id,
    location_id,
    hour_bucket_start_at,
    overlap_start,
    overlap_end,
    round(
        (extract(epoch from (overlap_end - overlap_start)) / 60.0)::numeric, 6
    ) as reserved_minutes
from hourly
where overlap_end > overlap_start
