-- Raw source tables, exactly per the TAD section 6 contracts.
-- Money is NUMERIC(12,2) — never floating point. Timestamps are timestamptz.

create table if not exists raw.raw_customers (
    customer_record_id uuid primary key,
    customer_id        uuid        not null,
    home_location_id   varchar(40),
    customer_segment   varchar(30),
    account_status     varchar(20) not null,
    created_at         timestamptz not null,
    effective_from     timestamptz not null,
    effective_to       timestamptz,
    is_current         boolean     not null,
    source_loaded_at   timestamptz not null,
    constraint uq_customer_version unique (customer_id, effective_from)
);

create table if not exists raw.raw_providers (
    provider_record_id uuid primary key,
    provider_id        uuid        not null,
    home_location_id   varchar(40),
    provider_status    varchar(20) not null,
    provider_tier      varchar(20),
    created_at         timestamptz not null,
    effective_from     timestamptz not null,
    effective_to       timestamptz,
    is_current         boolean     not null,
    source_loaded_at   timestamptz not null,
    constraint uq_provider_version unique (provider_id, effective_from)
);

create table if not exists raw.raw_service_categories (
    service_category_id   varchar(40) primary key,
    service_category_name varchar(100) not null,
    is_active             boolean      not null
);

create table if not exists raw.raw_locations (
    location_id       varchar(40) primary key,
    borough_name      varchar(60)  not null,
    neighborhood_name varchar(100) not null,
    is_active         boolean      not null
);

create table if not exists raw.raw_provider_service_eligibility (
    eligibility_id      uuid primary key,
    provider_id         uuid        not null references raw.raw_providers (provider_id),
    service_category_id varchar(40) not null references raw.raw_service_categories (service_category_id),
    location_id         varchar(40) not null references raw.raw_locations (location_id),
    effective_from      timestamptz not null,
    effective_to        timestamptz,
    is_eligible         boolean     not null,
    source_loaded_at    timestamptz not null,
    constraint uq_eligibility_version unique (provider_id, service_category_id, location_id, effective_from)
);

create table if not exists raw.raw_bookings (
    booking_id                 uuid primary key,
    customer_id                uuid        not null references raw.raw_customers (customer_id),
    provider_id                uuid        references raw.raw_providers (provider_id),
    service_category_id        varchar(40) not null references raw.raw_service_categories (service_category_id),
    service_location_id        varchar(40) not null references raw.raw_locations (location_id),
    created_at                 timestamptz not null,
    requested_start_at         timestamptz not null,
    requested_duration_minutes integer     not null check (requested_duration_minutes > 0),
    service_value_amount       numeric(12,2) not null check (service_value_amount >= 0),
    currency                   char(3)     not null default 'USD',
    is_test_booking            boolean     not null default false,
    source_loaded_at           timestamptz not null
);

create table if not exists raw.raw_booking_status_events (
    event_id         uuid primary key,
    booking_id       uuid        not null references raw.raw_bookings (booking_id),
    event_sequence   integer     not null,
    from_status      varchar(30),
    to_status        varchar(30) not null,
    occurred_at      timestamptz not null,
    actor_type       varchar(20) not null,
    actor_id         uuid,
    reason_code      varchar(50),
    idempotency_key  varchar(120) not null,
    source_loaded_at timestamptz not null,
    constraint uq_status_event_seq unique (booking_id, event_sequence),
    constraint uq_status_event_idem unique (idempotency_key),
    constraint ck_status_order check (to_status in
        ('CREATED','ACCEPTED','SCHEDULED','IN_PROGRESS','COMPLETED',
         'CANCELLED','REJECTED','EXPIRED','NO_SHOW'))
);

create table if not exists raw.raw_booking_reschedule_events (
    reschedule_event_id    uuid primary key,
    booking_id             uuid        not null references raw.raw_bookings (booking_id),
    old_scheduled_start_at timestamptz not null,
    new_scheduled_start_at timestamptz not null,
    occurred_at            timestamptz not null,
    actor_type             varchar(20) not null,
    reason_code            varchar(50),
    idempotency_key        varchar(120) not null,
    source_loaded_at       timestamptz not null,
    constraint uq_reschedule_idem unique (idempotency_key),
    constraint ck_reschedule_change check (new_scheduled_start_at <> old_scheduled_start_at)
);

create table if not exists raw.raw_payment_attempts (
    payment_attempt_id uuid primary key,
    booking_id         uuid        not null references raw.raw_bookings (booking_id),
    attempt_number     integer     not null,
    attempted_at       timestamptz not null,
    attempt_status     varchar(20) not null check (attempt_status in ('SUCCEEDED','FAILED')),
    amount             numeric(12,2) not null check (amount >= 0),
    currency           char(3)     not null default 'USD',
    failure_code       varchar(50),
    idempotency_key    varchar(120) not null,
    source_loaded_at   timestamptz not null,
    constraint uq_attempt_number unique (booking_id, attempt_number),
    constraint uq_attempt_idem unique (idempotency_key)
);

create table if not exists raw.raw_payment_events (
    payment_event_id        uuid primary key,
    booking_id              uuid        not null references raw.raw_bookings (booking_id),
    payment_attempt_id      uuid references raw.raw_payment_attempts (payment_attempt_id),
    related_payment_event_id uuid references raw.raw_payment_events (payment_event_id),
    event_type              varchar(20) not null check (event_type in ('CAPTURE','REFUND','REVERSAL')),
    amount                  numeric(12,2) not null check (amount >= 0),
    currency                char(3)     not null default 'USD',
    occurred_at             timestamptz not null,
    idempotency_key         varchar(120) not null,
    source_loaded_at        timestamptz not null,
    constraint uq_payment_event_idem unique (idempotency_key)
);

create table if not exists raw.raw_provider_payouts (
    payout_id        uuid primary key,
    booking_id       uuid        not null references raw.raw_bookings (booking_id),
    provider_id      uuid        not null references raw.raw_providers (provider_id),
    amount           numeric(12,2) not null check (amount >= 0),
    currency         char(3)     not null default 'USD',
    payout_status    varchar(20) not null check (payout_status in ('PENDING','PAID','FAILED','REVERSED')),
    initiated_at     timestamptz not null,
    paid_at          timestamptz,
    idempotency_key  varchar(120) not null,
    source_loaded_at timestamptz not null,
    constraint uq_payout_idem unique (idempotency_key)
);

create table if not exists raw.raw_provider_availability_intervals (
    availability_id     uuid primary key,
    provider_id         uuid        not null references raw.raw_providers (provider_id),
    service_category_id varchar(40) not null references raw.raw_service_categories (service_category_id),
    location_id         varchar(40) not null references raw.raw_locations (location_id),
    start_at            timestamptz not null,
    end_at              timestamptz not null,
    availability_status varchar(20) not null check (availability_status in ('OPEN','BLOCKED')),
    source_loaded_at    timestamptz not null,
    constraint ck_interval_positive check (end_at > start_at)
);

create table if not exists raw.raw_fee_policy (
    fee_policy_id    uuid primary key,
    fee_rate         numeric(7,6) not null check (fee_rate >= 0 and fee_rate < 1),
    effective_from   timestamptz not null,
    effective_to     timestamptz,
    currency         char(3)     not null default 'USD',
    source_loaded_at timestamptz not null,
    constraint uq_fee_policy_effective unique (effective_from)
);

create index if not exists ix_status_events_booking on raw.raw_booking_status_events (booking_id, occurred_at, event_sequence);
create index if not exists ix_payment_events_booking on raw.raw_payment_events (booking_id);
create index if not exists ix_attempts_booking on raw.raw_payment_attempts (booking_id);
create index if not exists ix_payouts_booking on raw.raw_provider_payouts (booking_id);
create index if not exists ix_availability_provider on raw.raw_provider_availability_intervals (provider_id, start_at);
create index if not exists ix_bookings_customer on raw.raw_bookings (customer_id);
