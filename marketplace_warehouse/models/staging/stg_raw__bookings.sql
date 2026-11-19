-- Grain: one booking.
select
    booking_id,
    customer_id,
    provider_id,
    service_category_id,
    service_location_id,
    created_at,
    requested_start_at,
    requested_duration_minutes,
    service_value_amount,
    currency,
    is_test_booking,
    source_loaded_at
from {{ source('raw', 'raw_bookings') }}
