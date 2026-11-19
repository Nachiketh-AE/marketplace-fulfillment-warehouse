# Data Dictionary — Analytical Models

Column-level definitions for core and mart models. Raw source contracts are defined
in the TAD §6 (kept verbatim in `docs/TAD.md`); staging models preserve those
columns with light standardization (status casing, name normalization).

## core dimensions

### dim_customer — one customer profile version (SCD2)
| Column | Type | Meaning |
|---|---|---|
| customer_sk | bigint | Surrogate PK |
| customer_id | uuid | Stable business ID |
| home_location_id | varchar(40) | Synthetic home neighborhood |
| customer_segment | varchar(30) | Synthetic segment |
| account_status | varchar(20) | ACTIVE / INACTIVE |
| created_at / effective_from / effective_to / is_current | timestamptz / bool | SCD2 versioning (from inclusive, to exclusive) |

### dim_provider — one provider profile version (SCD2)
Same pattern as dim_customer plus `provider_tier` (synthetic bronze/silver/gold).

### dim_service — one service category (Type 1)
service_sk, service_category_id, service_category_name, is_active.

### dim_location — one neighborhood/service region (Type 1)
location_sk, location_id, borough_name, neighborhood_name, is_active.
Boroughs: Manhattan, Brooklyn, Queens, Bronx, Staten Island (synthetic neighborhoods).

### dim_date — one calendar date
date_key (YYYYMMDD int), full_date, year/quarter/month numbers, month_name,
week_number (ISO), day_of_month, day_of_week_number (ISO 1=Mon), day_name, is_weekend.
Role-playing joins: created / requested-service / completed / event / payout dates.

## core facts and bridge

### fct_booking — one row per booking
Keys: booking_id (PK), customer_sk, provider_sk (nullable), service_sk, location_sk,
created_date_key, requested_service_date_key, completed_date_key (nullable).
Lifecycle: created_at, accepted_at, scheduled_at, in_progress_at, completed_at,
terminal_at (nullable each per stage), requested_start_at, current_scheduled_start_at.
Measures: requested_duration_minutes (int), service_value_amount numeric(12,2), currency.
Flags: final_status, is_eligible_booking (valid chain AND not test), is_test_booking,
source_loaded_at, final_actor_type, terminal_reason_code.

### fct_booking_status_event — one status transition
event_id (PK), booking_id, event_sequence, from_status (null for creation), to_status,
occurred_at, event_date_key, actor_type (CUSTOMER/PROVIDER/SYSTEM), actor_id,
reason_code, idempotency_key, source_loaded_at, is_valid_transition.

### fct_booking_reschedule_event — one reschedule
reschedule_event_id (PK), booking_id, old_scheduled_start_at, new_scheduled_start_at,
occurred_at, event_date_key, actor_type, reason_code, idempotency_key, source_loaded_at.

### fct_payment_attempt — one payment attempt
payment_attempt_id (PK), booking_id, attempt_number, attempted_at, attempt_date_key,
attempt_status (SUCCEEDED/FAILED), amount, currency, failure_code, idempotency_key,
source_loaded_at. Attempted amounts are NOT collected money.

### fct_payment — one posted financial event
payment_event_id (PK), booking_id, payment_attempt_id, related_payment_event_id,
event_type (CAPTURE/REFUND/REVERSAL), amount (positive magnitude), signed_amount
(capture +, refund/reversal −), currency, occurred_at, event_date_key, idempotency_key,
source_loaded_at.

### fct_provider_payout — one payout transaction
payout_id (PK), booking_id, provider_sk, provider_id, amount, currency,
payout_status (PENDING/PAID/FAILED/REVERSED), initiated_at, paid_at (paid only),
paid_date_key, initiated_date_key, idempotency_key, source_loaded_at.

### fct_provider_availability — one availability interval
availability_id (PK), provider_sk, service_sk, location_sk, provider_id,
service_category_id, location_id, start_at (inclusive), end_at (exclusive),
availability_status (OPEN/BLOCKED), interval_minutes, source_loaded_at.

### bridge_provider_eligibility — one eligibility interval
eligibility_id (PK), provider_sk, service_sk, location_sk, provider_id,
service_category_id, location_id, effective_from, effective_to, is_eligible.

## marts

### mart_booking_lifecycle — one row per booking
booking_id; created_date / service_date (NYC local); borough_name, neighborhood_name,
service_category_name; final_status; is_eligible_booking; requested_duration_minutes;
service_value_amount; created_to_accepted_minutes, accepted_to_scheduled_minutes,
in_progress_to_completed_minutes, created_to_completed_minutes (numeric minutes);
cancellation_actor_type; terminal_reason_code.

### mart_marketplace_economics_booking — one row per booking
booking_id, completed_date, service_category_name, borough_name, final_status,
is_financially_eligible_completed_booking, gross_completed_gmv, eligible_refund_amount,
net_completed_gmv, fee_rate, gross_platform_fee, platform_fee_reversal,
net_platform_fee_revenue, provider_earnings, captured_amount,
refunded_or_reversed_amount, paid_provider_payout_amount.

### mart_supply_demand_hourly — one hour bucket x borough x neighborhood x category
hour_bucket_start_at (UTC), service_date (NYC local), borough_name, neighborhood_name,
service_category_name, booking_count, requested_demand_hours,
eligible_available_capacity_hours, reserved_booking_hours, modeled_gap_hours,
reserved_utilization_rate (null when capacity = 0).

### mart_booking_cohort_daily — one booking-created date x borough x neighborhood x category
booking_created_date, borough_name, neighborhood_name, service_category_name,
eligible_created_bookings, completed_bookings, cancelled_bookings, rejected_bookings,
expired_bookings, no_show_bookings, is_cohort_mature.

### mart_completed_economics_daily — one completion date x borough x neighborhood x category
completed_date, borough_name, neighborhood_name, service_category_name,
completed_bookings, gross_completed_gmv, net_completed_gmv,
net_platform_fee_revenue, provider_earnings.

### mart_provider_payout_daily — one payout date (PAID only) x provider
payout_date, provider_id, paid_payout_amount, paid_payout_count.
