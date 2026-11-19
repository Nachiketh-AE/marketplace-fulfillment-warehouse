# Requirements Traceability Matrix

Maps every PRD functional requirement and key TAD architecture requirement to its
implementation and tests. Status: **complete** = implemented and tested;
**documented-limitation** = intentionally out of MVP scope with disclosure.

## Functional requirements (PRD section 10)

| ID | Requirement | Implementation | Tests | Status |
|---|---|---|---|---|
| FR-001 | Synthetic customers/providers with stable IDs | `generator/entities.py` (`stable_uuid`, UUIDv5) | `test_fixed_seed_reproducibility`, `test_unique_ids_within_grains` | complete |
| FR-002 | Six categories + NYC borough/neighborhood locations | `generator/config.py`, `generator/entities.py::generate_locations` | `test_referential_integrity` | complete |
| FR-003 | Eligibility separate from availability | `raw_provider_service_eligibility` vs `raw_provider_availability_intervals`; `bridge_provider_eligibility` | `assert_booking_provider_is_eligible_at_acceptance`, `assert_capacity_only_counts_eligible_open_intervals` | complete |
| FR-004 | Bookings with time/duration/value/location | `raw_bookings` (TAD 6.7 contract) | `test_referential_integrity` | complete |
| FR-005 | Append-only status events | `raw_booking_status_events`, `fct_booking_status_event` | `assert_terminal_booking_has_no_later_status_transition` | complete |
| FR-006 | Allowed transition map enforced | `generator/config.py::ALLOWED_TRANSITIONS`, `int_booking_status_ordered.is_valid_transition` | `assert_booking_status_transition_allowed`, `test_valid_state_transitions_only` | complete |
| FR-007 | Cancellation actor + reason | `actor_type`/`reason_code` columns; `mart_booking_lifecycle.cancellation_actor_type` | fixture F2/F5; `mart_booking_cohort_daily` | complete |
| FR-008 | Reschedule preserves booking ID | `raw_booking_reschedule_events`; `int_booking_reschedule_reconstructed` | `test_reschedule_preserves_booking_id_and_old_time`, `assert_reschedule_old_time_matches_previous_current_time` | complete |
| FR-009 | One provider maximum per booking | nullable single `provider_id` column (structural 0/1) | `test_one_provider_per_booking` | complete |
| FR-010 | Payment attempts with failure/retry | `generator/payments.py`; `fct_payment_attempt` | `test_payment_retry_limit_respected`, `test_failed_attempts_create_no_capture` | complete |
| FR-011 | Captures/refunds/reversals separate from booking events | `raw_payment_events`, `fct_payment`, `int_payment_events_signed` | `assert_payment_refunds_do_not_exceed_capture` | complete |
| FR-012 | Configurable fixed fee rate + proportional reversals | `raw_fee_policy` (15% seed default); `int_booking_financials` | `assert_fee_reversal_proportional_to_refund`, `test_fee_math_proportional_reversal` | complete |
| FR-013 | Earnings and payouts separate | `int_booking_economics.provider_earnings` vs `fct_provider_payout` | `assert_provider_payout_provider_matches_booking_assignment` | complete |
| FR-014 | Real availability intervals | `raw_provider_availability_intervals` (start/end timestamps) | `test_availability_interval_validity_and_no_overlap` | complete |
| FR-015 | No overlap double-counting | `availability.py::add_interval` raises on overlap | `test_overlapping_availability_is_rejected`, `assert_provider_availability_intervals_do_not_overlap` | complete |
| FR-016 | Load source records into PostgreSQL | `generator/load.py` (ON CONFLICT DO NOTHING) | `tests/integration/test_loader_idempotency.py` (CI) | complete |
| FR-017 | dbt source→mart layers | `marketplace_warehouse/models/` (13 staging, 9 intermediate, 13 core, 6 marts) | `dbt build` in CI | complete |
| FR-018 | Governed GMV/completion/cancellation/fulfillment/take-rate/capacity metrics | `mart_marketplace_economics_booking`, `mart_booking_cohort_daily`, `mart_supply_demand_hourly` | `assert_completed_gmv_reconciles_to_fixture` | complete |
| FR-019 | Uniqueness/relationship/accepted-value/lifecycle/financial/idempotency tests | `models/*/`.yml + `tests/assert_*.sql` | CI `dbt build` | complete |
| FR-020 | Hand-calculated reconciliation fixtures | `generator/fixtures.py` + `assert_completed_gmv_reconciles_to_fixture.sql` | CI fixture run | complete |
| FR-021 | Metabase operations dashboard | `metabase/README.md` + saved-question SQL | manual setup (see limitations) | complete-as-instructions |
| FR-022 | Metabase economics dashboard | `metabase/README.md` + saved-question SQL | manual setup | complete-as-instructions |
| FR-023 | Reproducible local setup | README Quickstart, `.env.example`, `docker-compose.yml` | documented commands | complete |
| FR-024 | GitHub Actions core checks | `.github/workflows/ci.yml` | CI run on push/PR | complete |
| FR-025 | Architecture/ERD/lifecycle diagrams + metric dictionary | `docs/diagrams/`, `docs/metric_dictionary.md` | — | complete |
| FR-026 | Incremental processing demonstration | `generator/incremental.py`, ingestion-watermark design (TAD 18), loader idempotency | loader idempotency tests; duplicate-event fixtures | complete |
| FR-027 | Anomaly flags for selected metrics | documented as extension; rate-by-cohort marts expose the inputs | — | documented-limitation |
| FR-028 | Documented hypothetical supply intervention | README §Future extensions; observational-data caveat | — | documented-limitation |

## Key architecture requirements (TAD)

| TAD section | Requirement | Implementation | Status |
|---|---|---|---|
| 3.4 | raw/staging/intermediate/core/marts schemas | `sql/init/01_schemas_roles.sql`, dbt schema config | complete |
| 5 | Naming conventions, UUIDv5 keys, numeric money | generator + all models | complete |
| 8.2 | Allowed-transition contract | shared `ALLOWED_TRANSITIONS` + dbt test | complete |
| 9.5–9.7 | Fee policy, take rate, $100/$20 fixture | `int_booking_financials`, fixture tests | complete |
| 10 | Interval capacity, demand splitting, gap caveats | `int_*_hourly`, `mart_supply_demand_hourly` | complete |
| 11 | SCD2 dims, role-playing dates | `dim_customer`/`dim_provider`, `dim_date` joins | complete |
| 13.3 | Six business marts with stated grains | `models/marts/` | complete |
| 18 | Batch-first, ingestion watermark, idempotency | `generator/load.py`, `generator/incremental.py` | complete |
| 19.2 | Four least-privilege roles | `sql/init/01_schemas_roles.sql` | complete |
| 21 | CI scope: small fixtures, no Metabase | `.github/workflows/ci.yml` | complete |
| 25 | Configurable implementation defaults | `generator/config.py` (version-controlled) | complete |

## Edge-case fixture coverage (TAD 16.3)

| # | Scenario | Fixture | Test |
|---|---|---|---|
| 1 | Completed, paid, no refund | F1 | fixture reconciliation |
| 2 | Customer cancellation pre-acceptance | F2 | unit + lifecycle tests |
| 3 | Provider rejection | F3 | unit + lifecycle tests |
| 4 | Expired unaccepted | F4 | unit + lifecycle tests |
| 5 | Provider cancellation after acceptance | F5 | unit + lifecycle tests |
| 6 | Scheduled no-show | F6 | unit + lifecycle tests |
| 7 | Reschedule, same booking ID | F7 | `assert_reschedule_old_time_matches_previous_current_time` |
| 8 | Payment failure → successful retry | F8 | `test_failed_attempts_create_no_capture` |
| 9 | Full refund of completed booking | F9 | fixture reconciliation |
| 10 | Partial refund ($100/15%/$20) | F10 | fixture reconciliation ($3 fee reversal) |
| 11 | Capture reversal | F11 | fixture reconciliation |
| 12 | Duplicate payment event | rejected_records.json | `test_rejected_records_never_loaded` (CI) |
| 13 | Late-arriving event | F12 (`source_loaded_at` ≫ `occurred_at`) | `test_fixture_dataset_builds_and_validates` |
| 14 | Ineligible provider assignment | generator rejects (no eligible provider → EXPIRED path) | `assert_booking_provider_is_eligible_at_acceptance` |
| 15 | Overlapping availability attempt | rejected_records.json | `test_overlapping_availability_is_rejected` (CI) |
