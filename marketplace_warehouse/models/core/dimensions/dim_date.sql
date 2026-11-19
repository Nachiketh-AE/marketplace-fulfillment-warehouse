-- Grain: one calendar date. Bounds derive from the data itself with margin,
-- so the dimension always covers every role-playing date key.
{% macro nyc_date_key(column) -%}
(((extract(year from {{ column }} at time zone 'America/New_York') * 10000)
+ (extract(month from {{ column }} at time zone 'America/New_York') * 100)
+ (extract(day from {{ column }} at time zone 'America/New_York')))::integer)
{%- endmacro %}

with timestamps as (
    select created_at as ts from {{ ref('stg_raw__bookings') }}
    union all select occurred_at from {{ ref('stg_raw__booking_status_events') }}
    union all select occurred_at from {{ ref('stg_raw__booking_reschedule_events') }}
    union all select attempted_at from {{ ref('stg_raw__payment_attempts') }}
    union all select occurred_at from {{ ref('stg_raw__payment_events') }}
    union all select initiated_at from {{ ref('stg_raw__provider_payouts') }}
    union all select paid_at from {{ ref('stg_raw__provider_payouts') }}
    union all select start_at from {{ ref('stg_raw__provider_availability_intervals') }}
    union all select end_at from {{ ref('stg_raw__provider_availability_intervals') }}
),

bounds as (
    select
        date_trunc('day', min(ts)) - interval '30 days'  as min_day,
        date_trunc('day', max(ts)) + interval '30 days'  as max_day
    from timestamps
),

days as (
    select (generate_series(min_day, max_day, interval '1 day'))::date as full_date
    from bounds
)

select
    (extract(year from full_date) * 10000
     + extract(month from full_date) * 100
     + extract(day from full_date))::integer as date_key,
    full_date,
    extract(year from full_date)::smallint          as year_number,
    extract(quarter from full_date)::smallint       as quarter_number,
    extract(month from full_date)::smallint         as month_number,
    to_char(full_date, 'Month')                     as month_name,
    extract(week from full_date)::smallint          as week_number,
    extract(day from full_date)::smallint           as day_of_month,
    extract(isodow from full_date)::smallint        as day_of_week_number,
    to_char(full_date, 'FMDay')                     as day_name,
    extract(isodow from full_date) in (6, 7)        as is_weekend
from days
