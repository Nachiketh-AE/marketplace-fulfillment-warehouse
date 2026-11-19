# Product Requirements Document (PRD)

## Marketplace Supply & Fulfillment Warehouse

**Suggested repository:** `marketplace-fulfillment-warehouse`  
**Document type:** Product Requirements Document  
**Status:** Baseline approved for MVP implementation  
**Version:** 1.0  
**Date:** 10 November 2026  
**Primary audience:** Analytics Engineering recruiters, Analytics Engineers, data leaders, and the project implementer  
**Portfolio assessment supplied in the concept brief:** 88.75 / 100; high complexity; indicative effort 4–6 weeks; reference alignment: Taskrabbit, Linear, Plaid, Temporal (subjective portfolio positioning, not an external evaluation)

---

## 1. Executive summary

Marketplace Supply & Fulfillment Warehouse is a portfolio-grade Analytics Engineering project for a fictional, Taskrabbit-like home-services marketplace operating in New York City. The marketplace connects customers who request services with independent providers who perform them.

The project demonstrates how an Analytics Engineer turns operational booking, payment, refund, payout, and provider-availability records into reliable, tested, explainable business metrics and operational dashboards.

The central design principle is that **booking lifecycle, payment lifecycle, and provider capacity are separate business processes**. They must be modeled separately and connected through explicit keys, timestamps, and calculation rules. A booking being completed does not prove that its payment succeeded or its provider was paid. Similarly, an available provider-hour is not the same thing as a completed booking-hour.

The deliverable is not a production marketplace application. It is a reproducible analytical warehouse with synthetic data, PostgreSQL, dbt Core, SQL, Python, GitHub Actions, and Metabase. The MVP is intentionally limited to the smallest polished system that can be demonstrated in a public GitHub repository and defended in an Analytics Engineer interview.

## 2. Product vision and positioning

### 2.1 Vision

Provide marketplace operations and finance stakeholders with a consistent view of:

- What customers request and what gets completed.
- Where bookings fail, cancel, expire, or result in a no-show.
- How gross service value becomes refunds, platform fee revenue, provider earnings, and provider payouts.
- Where eligible provider capacity is insufficient relative to recorded booking demand.
- How these outcomes vary by borough, neighborhood, service category, and time window.

### 2.2 Portfolio positioning

The project is designed to demonstrate entry-level Analytics Engineering capability for US-based roles and remote international roles, with an emphasis on marketplace, fintech, SaaS, and e-commerce analytics teams.

The reference-company alignment is illustrative, not a claim of affiliation or access to proprietary systems:

- **Taskrabbit-like marketplace analytics:** GMV, completed tasks, take rate, fulfillment, provider supply, and operational performance.
- **Plaid-like financial-data discipline:** financial event history, payment/refund treatment, reconciliation, and clear money-flow semantics.
- **Linear-like workflow analytics:** event history, lifecycle transitions, stage outcomes, and elapsed-time analysis.
- **Temporal-like workflow discipline:** deterministic state transitions, event ordering, retries, idempotency, and reproducible processing.

The project should also be understandable and relevant to analytics teams outside home services because the underlying patterns are reusable.

## 3. Goals and success criteria

### 3.1 Primary goals

1. Build a reproducible synthetic home-services marketplace dataset.
2. Preserve booking status history as immutable transition events.
3. Keep payment attempts and posted payment/refund/reversal events separate from booking status history.
4. Model provider availability as actual time intervals, independently from realized bookings.
5. Build dimensional facts and dimensions with explicit, documented grains.
6. Publish governed business metrics with precise numerators, denominators, eligibility rules, and refund treatment.
7. Validate key business logic with dbt tests and hand-calculated fixtures.
8. Present operations and marketplace-economics dashboards in Metabase.
9. Automate essential build and test checks using GitHub Actions.
10. Make the repository understandable, reproducible, and defensible in a recruiter discussion.

### 3.2 Success definition

The project succeeds when it achieves all three outcomes:

- **Recruiter-ready MVP:** a clean public repository that can be set up and run from documented instructions.
- **Strong Analytics Engineering portfolio:** credible SQL, dimensional modeling, dbt, tests, financial reconciliation, incremental processing, and business metrics.
- **Interview showcase:** the project owner can explain the grain, joins, event history, metric contracts, data-quality checks, trade-offs, and limitations without relying on the coding agent.

### 3.3 Measurable acceptance outcomes

- A fresh setup can initialize PostgreSQL, generate synthetic data, run dbt, execute tests, and open Metabase using documented steps.
- Every fact and dimension has a declared grain and key strategy.
- Every headline metric has a metric definition and a tested calculation path.
- Booking history is not overwritten when a booking changes state.
- Duplicate event reprocessing does not create duplicate analytical events or double-count financial amounts.
- Payment/refund and provider-payout amounts reconcile to deterministic fixtures.
- Availability intervals cannot create overlapping capacity for the same provider.
- The dashboards answer the required operational and economic questions.
- CI runs the core dbt validation workflow on repository changes.

## 4. Users and stakeholder needs

This is an analytical warehouse, not a customer-facing booking application. Its personas represent the consumers of the warehouse outputs.

| Persona | Questions / needs | Primary output |
|---|---|---|
| Marketplace operations manager | Which areas or categories have low fulfillment? Where is provider capacity tight? Which lifecycle stages fail? | Operations dashboard |
| Marketplace finance analyst | What is completed GMV? How much was refunded? What fee revenue was earned? How much was paid to providers? | Marketplace economics dashboard |
| Marketplace leadership | Is the marketplace completing demand efficiently and generating sustainable platform revenue? | KPI summary across both dashboards |
| Analytics Engineer / data team | Are grains, joins, transformations, metric rules, and tests trustworthy? | dbt project, documentation, SQL, CI |
| Recruiter / interviewer | Can the candidate explain an end-to-end analytical system and defend modeling decisions? | README, architecture, diagrams, dashboard, walkthrough |

## 5. Business context and domain definition

### 5.1 Fictional marketplace

The synthetic marketplace provides home services in New York City. It uses five boroughs and synthetic neighborhoods within those boroughs. The selected service categories are:

1. Furniture assembly
2. Home cleaning
3. Plumbing
4. Electrical repairs
5. Painting
6. Moving assistance

Customers create service bookings. A provider may accept a booking if the provider is eligible for the requested service category and service location. A booking has one provider at most. A provider can serve multiple categories and locations, subject to the generated eligibility relationships.

### 5.2 Geography

- Primary geography: New York City.
- Geographic hierarchy: borough → neighborhood/service region.
- Reporting grain: neighborhood or borough, with service category and time-window filters.
- Location values are synthetic labels based on the NYC context; generated activity is not a representation of actual local marketplace demand or provider supply.
- No geospatial extension is required for the MVP. Relational location keys are sufficient.

### 5.3 Currency and time

- Currency: USD.
- Persist event timestamps as timezone-aware timestamps in UTC (`timestamptz` in PostgreSQL).
- Present business reporting in `America/New_York` local time.
- Store both event timestamps and the relevant requested/scheduled service timestamps. They answer different questions.

## 6. Scope

### 6.1 MVP — required

The MVP must include:

- Synthetic customers and providers.
- Service categories, NYC boroughs, and neighborhoods.
- Provider-to-service and provider-to-region eligibility.
- Bookings with requested service duration, amount, requested service time, and location.
- Booking status-transition events, including creation, acceptance, scheduling, start, completion, cancellation, rejection, expiration, and no-show outcomes.
- Rescheduling events that preserve the booking ID and record old and new scheduled times.
- Payment attempts with success/failure and retries.
- Posted customer payment, refund, and reversal events.
- Platform fee calculation and provider-earnings calculation under documented rules.
- Provider payout records, separate from provider earnings.
- Provider availability intervals using actual start/end timestamps.
- PostgreSQL source/raw tables.
- dbt staging, intermediate, dimension, fact, and mart models.
- Core tests and financial/lifecycle reconciliation fixtures.
- Gross and net completed-service GMV, completed bookings, cancellation rate, fulfillment rate, and take rate.
- Modeled supply-versus-demand analysis using requested hours and eligible capacity hours.
- Metabase operations and marketplace-economics dashboards.
- GitHub Actions CI for core validation.
- README, diagrams, metric dictionary, setup instructions, dashboard evidence, and recruiter walkthrough notes.

### 6.2 Strong-portfolio additions — included after the core MVP works

- Incremental dbt processing or a clearly documented incremental-load simulation.
- Additional provider utilization and completion-time analysis.
- Expanded reconciliation and adversarial data-quality tests.
- Basic anomaly flags for sudden changes in cancellation, fulfillment, refund, or capacity metrics.
- A documented hypothetical supply intervention and a discussion of why observational data alone does not establish causal impact.

### 6.3 Explicitly out of scope

- Production customer/provider applications, authentication, messaging, or booking APIs.
- Real customer or provider PII.
- Real payment processor integrations or real money movement.
- Multiple providers assigned to one booking.
- Search impressions or anonymous customer demand that never creates a booking.
- Kafka or streaming infrastructure.
- Airflow, Dagster, or another orchestrator in the initial implementation.
- Mandatory DuckDB or geospatial extensions.
- Production-grade multi-region deployment, high availability, disaster recovery, or enterprise access management.
- Causal claims about the effect of operational interventions.
- Public NYC taxi trip data as a proxy for home-services marketplace behavior. If explored later, NYC Taxi and Limousine Commission trip records may be used only to practise timestamp/location-scale processing; they are not a home-services marketplace dataset and must be labeled as unrelated proxy data.

## 7. Core business process requirements

### 7.1 Booking lifecycle

A booking is a customer service request. Its lifecycle is represented by a series of append-only status-transition events. The current/final status is derived from valid events; the event history is never overwritten.

Primary statuses:

- `CREATED`
- `ACCEPTED`
- `SCHEDULED`
- `IN_PROGRESS`
- `COMPLETED`
- `CANCELLED`
- `REJECTED`
- `EXPIRED`
- `NO_SHOW`

Conceptual happy path:

`CREATED → ACCEPTED → SCHEDULED → IN_PROGRESS → COMPLETED`

Alternative terminal outcomes can occur at permitted stages. The allowed transition map and transition guards are specified in the TAD.

Requirements:

- Every booking has one stable `booking_id`.
- Every status transition has a unique event identifier, event timestamp, prior state (nullable for creation), next state, actor type, and reason where applicable.
- A booking may have zero or one provider at any point; it must have one provider to enter `ACCEPTED` under the chosen one-provider model.
- A booking cannot reach `COMPLETED` without a valid preceding state path through `IN_PROGRESS`.
- Terminal outcomes cannot be silently overwritten. If a business correction is necessary, record a correction/reversal event or regenerate the synthetic fixture; do not edit history invisibly.
- A cancellation records who initiated it and a reason code.
- A rejection records provider rejection as the outcome and does not count as a cancellation.
- Expiration represents a request that did not receive acceptance before its expiry rule; the exact synthetic timeout is configurable.
- No-show is recorded as a terminal outcome after the scheduled service time when the parties fail to complete the service, with responsible party/reason captured where generated.

### 7.2 Rescheduling

- Rescheduling retains the original `booking_id`.
- Each reschedule is an event with the previous scheduled start, new scheduled start, event time, actor, and optional reason.
- The current scheduled time is derived from the latest valid reschedule event.
- Rescheduling does not create an additional booking or add a second unit of demand.
- A genuinely new service request creates a new booking ID.

### 7.3 Provider allocation

- One provider maximum per booking.
- Provider assignment must satisfy service-category and service-area eligibility effective at the relevant time.
- A booking without an accepted provider can still exist and contributes to booking-based recorded demand.
- Provider eligibility is represented separately from availability. Eligibility means the provider is qualified/allowed to serve a category and region; availability means the provider declared capacity during a specific time interval.

### 7.4 Payment lifecycle

Payment events are not booking status events. A payment can fail while a booking continues, and a completed booking can require financial reconciliation.

The system must represent:

- One or more payment attempts per booking.
- Failed and successful attempts, including retries.
- Posted customer payment capture events.
- Full or partial customer refunds.
- Payment reversals.
- Platform fee revenue calculations and proportional fee reversals under refunds.
- Provider earnings calculations.
- Actual provider payout records and payout status.

Requirements:

- A payment attempt has a stable attempt ID and an attempt number scoped to a booking/payment intent.
- A failed attempt is not treated as captured money.
- A posted capture is a financial event, not merely a successful status label.
- For the synthetic MVP, a booking may reach `COMPLETED` only when a successful capture for the service value exists; exhausted payment attempts prevent completion in generated scenarios. This is a simplifying project rule, not a universal payment-processing rule.
- Refunds and reversals reference the original capture or related financial event where possible.
- A refund cannot exceed the remaining refundable captured amount for the booking.
- Reprocessing the same financial event must not duplicate its amount.
- Provider earnings and provider payouts are different measures. Earnings are what the provider is owed under the fee policy; payout is cash disbursed/recorded as paid.
- Payouts are not included in platform fee revenue or GMV.

### 7.5 Financial policy

The primary financial model uses a configurable fixed platform fee percentage.

Baseline policy:

- GMV is service value only; exclude taxes and tips.
- Gross completed-service GMV is the service value of bookings that reach `COMPLETED`, before refunds.
- Net completed-service GMV is gross completed-service GMV less customer refunds/reversals allocated to the service value of completed bookings.
- Platform fee is a fixed percentage of eligible completed-service value.
- Refunds proportionally reverse the platform fee associated with the refunded service value.
- Primary take rate uses net platform fee revenue divided by net completed-service GMV for the same scope and reporting period.
- The fee policy effective at booking completion applies to that booking; proportional fee reversals use that same original rate even if the refund occurs later.
- Cancellation fees are excluded from the MVP and from primary platform revenue/take rate.
- The fee percentage is stored as configuration/seed data and is not scattered as a hard-coded constant across models.

Illustration: a completed service of $100 with a $20 service-value refund has $100 gross completed GMV and $80 net completed GMV. At a hypothetical 15% fee rate, gross platform fee is $15 and the proportional fee reversal is $3, leaving $12 net platform fee revenue. The 15% rate is an implementation seed default only; it is not a claim about any real marketplace.

### 7.6 Provider availability and capacity

- Availability is modeled as real start/end intervals, not daily aggregate hours.
- An availability interval is associated with one provider, one service category, and one service region.
- A provider may be eligible for multiple categories and service regions, but the synthetic MVP must not create overlapping availability intervals for the same provider. This prevents the same provider-minute from being counted multiple times.
- Availability records distinguish open/available time from blocked/unavailable time where useful; only valid open intervals contribute capacity.
- Provider eligibility and provider availability are separate.
- Booked service time is not the same as available capacity.
- Capacity calculations must avoid double-counting overlapping intervals or counting time outside the reporting window.

### 7.7 Demand and supply-demand gap

MVP demand is **booking-based demand**. Search activity and customers who never create a booking are not captured.

- Requested demand hours are the sum of requested service duration for eligible bookings in the defined region, category, and service-time window.
- Eligible supply capacity hours are the available provider interval minutes in the same region, category, and time window, after applying provider eligibility and overlap rules.
- Modeled gap = requested demand hours − eligible available capacity hours.
- A positive gap indicates recorded requested service hours exceed modeled available capacity hours.
- A positive gap does not prove that the same number of hours of customer demand went unfulfilled. No unmatched search/request data exists in the MVP.
- Dashboards must display the metric label and limitation clearly. Do not label the result as observed lost demand or confirmed unmet demand.
- Show booking counts separately from requested service hours so users cannot confuse volume and duration.

## 8. Metric requirements and metric contracts

All metrics must have a metric dictionary entry containing: business name, business purpose, grain, numerator, denominator (if applicable), filters/exclusions, timestamp basis, refund treatment, dimensional slice rules, and caveats.

| Metric | Required definition | Guardrail |
|---|---|---|
| Gross completed-service GMV | Sum of service value for bookings whose valid lifecycle reaches `COMPLETED`, before service-value refunds | Exclude taxes, tips, cancelled, rejected, expired, and no-show bookings |
| Net completed-service GMV | Gross completed-service GMV less eligible customer refunds and payment reversals allocated to completed service value | Refunds cannot be subtracted more than once or beyond captured/refundable value |
| Completed bookings / completed tasks | Count of distinct eligible bookings whose final valid lifecycle outcome is `COMPLETED` | Count booking IDs, not status events |
| Cancellation rate | Eligible created bookings ending in `CANCELLED` ÷ eligible created bookings in the same creation cohort | Denominator excludes test/invalid/duplicate records; rejection/expiry/no-show remain distinct outcomes |
| Fulfillment rate | Eligible created bookings ending in `COMPLETED` ÷ eligible created bookings in the same creation cohort | Use a declared cohort maturity/reporting cutoff; do not compare immature cohorts as final |
| Take rate | Net platform fee revenue ÷ net completed-service GMV × 100 | Same scope, period, currency, eligibility rules, and refund treatment in numerator/denominator |
| Platform fee revenue | Fee earned on eligible completed service value less proportional fee reversals for refunds | Does not include provider payout or cancellation fees |
| Provider earnings | Eligible completed service value less platform fee, adjusted for service-value refunds under the same allocation policy | Amount owed is not the same as amount paid |
| Provider payouts | Sum of payout transactions marked paid in the reporting period | Do not equate payout date with booking completion date |
| Provider utilization | Reserved/booked service minutes in the provider's eligible availability window ÷ open available provider minutes in the same scope | Avoid overlapping capacity; clearly label whether numerator is scheduled/reserved or completed/realized |
| Median completion time | Median elapsed time from `IN_PROGRESS` event to `COMPLETED` event for completed bookings | Do not substitute booking creation time unless explicitly reporting request-to-completion |
| Request-to-completion time | Median elapsed time from booking creation to completion | Optional companion metric; distinct from service execution duration |
| Requested demand hours | Sum of requested duration for eligible booking requests in the service-time window | Booking-based demand only; not all latent demand |
| Eligible provider capacity hours | Sum of eligible open availability minutes intersecting the same region/category/time window, after overlap protections | Availability is modeled, not actual attendance or guaranteed labor |
| Modeled supply-demand gap | Requested demand hours − eligible provider capacity hours | Modelled indicator, not proof of unfulfilled demand |

### 8.1 Denominator and cohort policy

- Cancellation and fulfillment rates use bookings grouped by booking creation cohort unless a dashboard explicitly names another cohort basis.
- A booking is eligible if it is a valid, non-test booking with a unique accepted source identity and a valid creation event.
- Cohorts should be considered mature only after the configured observation window has elapsed or all bookings in the cohort have reached a terminal outcome. The dashboard must disclose the maturity rule.
- Rejected, expired, cancelled, and no-show outcomes are not completed. They should be available as separate outcome categories.
- Metric numerator and denominator filters must be aligned. A metric may not silently mix booking-created dates with service dates.

### 8.2 Time basis

- Booking cohort metrics: `created_at` / creation date.
- Service operations and capacity: requested/current scheduled service start time.
- Financial activity and payouts: financial event or payout transaction timestamp.
- Completion duration: status-event timestamps.
- Dashboard filters must make the time basis understandable.

## 9. Data generation requirements

The dataset is synthetic and reproducible.

### 9.1 Starting target volumes

| Dataset | Target volume |
|---|---:|
| Customers | 5,000 |
| Providers | 500 |
| Bookings | 50,000 |
| Booking status events | 150,000–250,000 |
| Payment events / attempts | 60,000–100,000 combined starting range; exact split determined by generator scenarios |
| Provider availability intervals | 50,000+ |

These are target volumes, not a requirement that the first development run generates all rows. Use small fixtures during development and the target dataset for final validation/demo.

### 9.2 Generator requirements

- Use Python.
- Use a fixed random seed by default so the dataset is reproducible.
- Support configurable scale and seed.
- Generate referentially valid IDs and timestamps.
- Generate coherent event ordering and only allowed state transitions.
- Generate realistic variation in booking outcomes, provider assignment, time-to-acceptance, service duration, cancellations, failures, refunds, and payouts.
- Generate explicit edge-case fixtures: completed booking, cancelled booking, rescheduled booking, payment retry after failure, partial refund, full refund, reversal, duplicate event, late-arriving event, provider ineligible for service/region, and overlapping availability attempt.
- The generator must not produce real personal data. Names, IDs, and values are fictional.
- The generator must expose scenario proportions as configuration rather than hiding all assumptions in code.

### 9.3 Data provenance and limitation disclosure

- All marketplace/customer/provider/booking/payment/availability data is synthetic.
- No actual Taskrabbit, Plaid, Linear, Temporal, or other company data is used.
- NYC taxi data is not a home-services marketplace dataset and is not part of the core MVP.
- Synthetic patterns demonstrate engineering mechanics, not statistically valid predictions of a real marketplace.

## 10. Functional requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Generate synthetic customers and providers with stable IDs | Must |
| FR-002 | Generate six service categories and NYC borough/neighborhood locations | Must |
| FR-003 | Represent provider category and region eligibility separately from availability | Must |
| FR-004 | Generate bookings with requested service time, duration, service value, customer, category, and location | Must |
| FR-005 | Generate append-only booking status-transition events | Must |
| FR-006 | Enforce the allowed booking transition map | Must |
| FR-007 | Record cancellation actor and reason | Must |
| FR-008 | Record rescheduling events without changing booking ID | Must |
| FR-009 | Support one provider maximum per booking | Must |
| FR-010 | Generate payment attempts with failures, success, and retry sequence | Must |
| FR-011 | Generate posted captures, refunds, and reversals separately from booking events | Must |
| FR-012 | Calculate platform fees and fee reversals using a configurable fixed fee rate | Must |
| FR-013 | Generate provider earnings and payout records separately | Must |
| FR-014 | Generate actual provider availability intervals | Must |
| FR-015 | Prevent provider availability overlap from double-counting capacity | Must |
| FR-016 | Load source records into PostgreSQL | Must |
| FR-017 | Build dbt source, staging, intermediate, dimension, fact, and mart layers | Must |
| FR-018 | Build governed GMV, completion, cancellation, fulfillment, take-rate, and capacity metrics | Must |
| FR-019 | Add uniqueness, relationship, accepted-value, lifecycle, financial, and idempotency tests | Must |
| FR-020 | Provide hand-calculated reconciliation fixtures | Must |
| FR-021 | Provide Metabase operations dashboard | Must |
| FR-022 | Provide Metabase marketplace-economics dashboard | Must |
| FR-023 | Provide reproducible local setup instructions | Must |
| FR-024 | Run core checks through GitHub Actions | Must |
| FR-025 | Provide architecture/ERD/lifecycle diagrams and metric dictionary | Must |
| FR-026 | Add incremental processing demonstration | Should |
| FR-027 | Add anomaly flags for selected metrics | Could |
| FR-028 | Add a documented hypothetical supply intervention | Could |

## 11. Dashboard requirements

### 11.1 Operations dashboard

Primary audience: marketplace operations manager.

Required views:

- Eligible bookings, completed bookings, and outcome mix.
- Fulfillment rate and cancellation rate by booking creation cohort.
- Cancellation, rejection, expiration, and no-show counts by reason/actor where available.
- Stage counts and elapsed time between lifecycle stages.
- Median completion time.
- Requested demand hours versus eligible provider capacity hours by borough, neighborhood, service category, and service-time window.
- Modeled supply-demand gap with explicit caveat.
- Provider utilization, with the numerator definition shown.

Operational questions answered:

1. Which regions need additional provider capacity relative to recorded requests?
2. Which service categories have low fulfillment?
3. Which lifecycle stages experience the most failures?
4. Are customer/provider cancellations changing over time?
5. Are available provider hours being utilized effectively?

### 11.2 Marketplace economics dashboard

Primary audience: finance analyst and marketplace leadership.

Required views:

- Gross completed-service GMV.
- Net completed-service GMV.
- Customer capture, refund, and reversal totals.
- Platform fee revenue, gross fee, and fee reversals where available.
- Take rate.
- Provider earnings.
- Provider payouts, separated by payout status/date.
- Average service value per completed booking (optional but useful).
- Refund rate or refunded-value share, with an explicit denominator.

Economic questions answered:

1. How much completed service value is generated?
2. How do refunds change net completed-service GMV?
3. How much platform fee revenue is earned after fee reversals?
4. What is the take rate on the same net GMV scope?
5. How much do providers earn versus how much has actually been paid out?

### 11.3 Dashboard conventions

- Every KPI must link to a documented metric definition.
- Show currency as USD and time in the documented business timezone.
- Filters must not silently change denominator or time-basis semantics.
- Clearly label cohort-date metrics versus service-date and financial-event-date metrics.
- Show missing/insufficient data as unavailable rather than silently displaying zero.
- Show a visible caveat for synthetic data and the modeled supply-demand gap.

## 12. Data quality and validation requirements

### 12.1 Structural checks

- Primary business IDs are unique at their declared grains.
- Required IDs and event timestamps are non-null.
- Foreign keys resolve to their parent records.
- Amounts and durations have valid signs/ranges.
- Availability end time is after start time.
- Provider eligibility exists for assigned service/category/region at the relevant time.

### 12.2 Lifecycle checks

- Every booking has exactly one creation event.
- Event ordering is deterministic using event timestamp plus a stable tie-breaker.
- Each transition follows the allowed state map.
- `COMPLETED` requires a preceding `IN_PROGRESS` state.
- Terminal outcomes cannot be followed by ordinary transitions.
- Reschedule events preserve booking identity and contain old/new scheduled timestamps.

### 12.3 Financial checks

- Payment attempts are distinct from posted capture events.
- Refund totals do not exceed the eligible captured amount.
- Reversals reference a prior related event and do not reverse more than its remaining amount.
- Fee reversals are proportional to eligible service-value refunds under the configured fee policy.
- Gross and net GMV reconcile to the fixture calculations.
- Provider earnings reconcile to net eligible service value less platform fees under the declared policy.
- Provider payout totals are not substituted for provider earnings.

### 12.4 Capacity checks

- Availability interval duration is positive.
- No overlapping open intervals exist for the same provider in the MVP generator/modeling scope.
- Availability is counted only for eligible providers and within the selected region/category/time window.
- Intervals are clipped to reporting windows before aggregation.
- A booked minute is not added to available capacity a second time.

### 12.5 Idempotency checks

- Source event identifiers and idempotency keys are retained.
- Re-running ingestion does not create duplicate raw business events.
- Re-running dbt produces the same business totals for the same source snapshot.
- Incremental models use a reliable unique key and handle late-arriving events according to the TAD policy.

## 13. Non-functional requirements

| Area | Requirement |
|---|---|
| Reproducibility | Fixed-seed generator and documented setup |
| Maintainability | Small, readable modules and dbt models with clear names |
| Explainability | Every business metric and important rule is documented |
| Reliability | Tests fail on key integrity, lifecycle, financial, or capacity violations |
| Performance | The target synthetic dataset should run locally without distributed compute |
| Portability | Windows-friendly instructions; Docker Compose recommended for PostgreSQL/Metabase services |
| Security/privacy | Synthetic identities only; no credentials committed; local secrets in environment variables |
| Version control | Git-tracked code/config/docs; generated large artifacts handled deliberately |
| CI | Automated dependency/build/test checks on pull requests and pushes to the primary branch |
| Usability | A recruiter can follow the README to understand and run the core project |

## 14. Technical constraints and implementation approach

- Core stack: Python, PostgreSQL, SQL, dbt Core, Git/GitHub, GitHub Actions, and Metabase.
- Docker Compose is recommended for reproducible PostgreSQL and Metabase services.
- Python and dbt may run in a local virtual environment to keep the initial setup simple.
- Start with batch generation/loading/building; add incremental processing after batch correctness is demonstrated.
- Do not add Kafka, Airflow, Dagster, DuckDB, or geospatial extensions unless a concrete project requirement justifies them.
- The architecture and data model must remain understandable to an entry-level candidate.

## 15. MVP release plan and definition of done

### Phase 0 — Project foundation

Deliverables:
- Repository structure.
- PRD and TAD.
- Python environment and dependency lock/requirements.
- PostgreSQL schema and connection configuration.
- README skeleton and configuration template.

Definition of done:
- Project initializes locally using documented commands.
- No secrets are committed.

### Phase 1 — Synthetic source data and booking lifecycle

Deliverables:
- Customers, providers, categories, locations, eligibility, bookings, availability, and booking status events.
- Deterministic generator and edge-case fixtures.
- Raw PostgreSQL tables.

Definition of done:
- Referential integrity holds.
- Event sequences are valid and reproducible.
- Rescheduling preserves booking ID.

### Phase 2 — dbt core model and operational metrics

Deliverables:
- Source declarations, staging, intermediate, dimensions, and facts.
- Booking lifecycle mart.
- Completed, cancellation, fulfillment, and completion-time metrics.
- Core dbt tests.

Definition of done:
- Final status is derived from history.
- Counts reconcile to hand-calculated fixtures.

### Phase 3 — Payments, refunds, fees, and payouts

Deliverables:
- Payment attempts and posted financial events.
- GMV, net GMV, platform fee, take rate, provider earnings, and payout models.
- Financial reconciliation tests.

Definition of done:
- Full/partial refunds and reversals reconcile.
- Provider earnings and actual payouts remain distinct.

### Phase 4 — Capacity and supply-demand analysis

Deliverables:
- Provider availability interval fact.
- Capacity aggregation by service region/category/time window.
- Utilization and modeled supply-demand gap.

Definition of done:
- No overlapping availability double-counting.
- All capacity and demand calculations use aligned region/category/time windows.
- Caveats are visible in documentation and dashboard.

### Phase 5 — Dashboards, CI, and incremental processing

Deliverables:
- Operations and marketplace economics dashboards.
- GitHub Actions checks.
- Incremental processing demonstration.
- Final README and dashboard screenshots.

Definition of done:
- A fresh clone can reproduce the demo.
- CI catches selected failures.
- Dashboard figures reconcile to dbt marts.

### Phase 6 — Recruiter polish

Deliverables:
- Architecture, ERD, state diagrams, metric dictionary, model documentation.
- Demo script and interview questions/answers.
- Known limitations and design trade-offs.

Definition of done:
- A reviewer can understand the system without reading every source file.
- Project owner can explain grains, metric definitions, joins, data-quality decisions, and synthetic-data limitations.

## 16. Repository deliverables

Expected public repository contents:

- `README.md` — business context, architecture summary, setup, commands, example findings, limitations.
- `docs/PRD.md` — this document.
- `docs/TAD.md` — technical architecture document.
- `docs/diagrams/` — architecture, ERD, booking lifecycle, and financial lifecycle diagrams.
- `docs/metric_dictionary.md` — metric contracts.
- `docs/data_dictionary.md` — table/column definitions.
- `generator/` — synthetic data generation modules and scenario configuration.
- `data/fixtures/` — small deterministic test fixtures; avoid committing unnecessarily large generated datasets.
- `sql/` or PostgreSQL initialization scripts — source schema and seed loading where appropriate.
- `dbt_project/` — dbt project, sources, models, tests, seeds, macros, and documentation.
- `metabase/` or `docs/dashboard/` — dashboard setup/export instructions and screenshots, depending on Metabase export approach.
- `.github/workflows/` — GitHub Actions CI workflow.
- `docker-compose.yml` — local PostgreSQL and Metabase services.
- `.env.example` — configuration names without secrets.

Exact directory names may be adjusted during implementation, but the deliverables must remain discoverable.

## 17. Risks, assumptions, and limitations

| Risk / limitation | Mitigation / disclosure |
|---|---|
| Synthetic behavior may look realistic but is not observed marketplace behavior | Label all data synthetic and avoid empirical claims |
| Booking-based demand excludes searches that never become bookings | Label supply-demand result as a modeled indicator; add unmatched-request events only as a later extension |
| Provider availability does not guarantee actual attendance | Distinguish scheduled/reserved utilization from realized service time |
| Refunds can make GMV and take rate inconsistent if policies differ | Use one documented refund allocation rule and reconciliation tests |
| Payment capture, platform fee, provider earnings, and payout may be conflated | Model separately and document money-flow semantics |
| Cohort metrics can be biased by immature bookings | Apply maturity/cutoff rules and make cohort time basis visible |
| Availability can be double-counted across categories/regions | One category/region per interval and no overlapping provider intervals in MVP |
| NYC context can be mistaken for real NYC marketplace coverage | State that locations are synthetic labels and not representative data |
| Scope creep can reduce project completion quality | Preserve explicit MVP and defer optional infrastructure |

## 18. Open implementation defaults (not additional product commitments)

The following values are intentionally configurable and must be finalized in code/configuration before generating the final dataset. They are implementation defaults, not facts about a real marketplace:

- Initial platform fee rate: use a clearly labeled synthetic default such as 15%, configurable in seed/config data.
- Booking expiry window: configurable synthetic duration.
- Synthetic outcome proportions: configurable probabilities.
- Synthetic date range and data-generation seed: configurable.
- Cohort maturity window: set and document before dashboard publication.
- Refund allocation order and rounding: use cents precision and a documented deterministic allocation rule.
- Payment retry limit: configurable synthetic rule.
- Provider payout timing: configurable delay after eligible completion/financial settlement.

If a value materially affects a metric, the value and its effective dates must be visible in configuration or documentation—not buried as an unexplained constant.

## 19. Final product acceptance checklist

- [ ] Business context, goals, scope, and limitations documented.
- [ ] Booking lifecycle and allowed transitions implemented.
- [ ] Rescheduling retains booking ID and preserves event history.
- [ ] One-provider-per-booking rule enforced.
- [ ] Payment attempts separate from financial events.
- [ ] Captures, full/partial refunds, and reversals supported.
- [ ] Platform fee and proportional fee reversal policy implemented.
- [ ] Provider earnings separate from provider payouts.
- [ ] Actual provider availability intervals modeled.
- [ ] Eligibility and availability modeled separately.
- [ ] Booking-based demand and modeled supply-demand caveat documented.
- [ ] Facts/dimensions and metric contracts implemented.
- [ ] Structural, lifecycle, financial, capacity, and idempotency tests pass.
- [ ] Operations and economics dashboards reconcile to marts.
- [ ] GitHub Actions CI runs core checks.
- [ ] README and setup instructions validated from a fresh clone.
- [ ] Architecture, ERD, data dictionary, metric dictionary, and recruiter walkthrough available.
