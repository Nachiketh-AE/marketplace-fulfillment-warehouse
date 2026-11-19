<div align="center">

<img src="docs/assets/banner.svg" alt="Marketplace Supply & Fulfillment Warehouse" width="100%"/>

**A recruiter-grade Analytics Engineering warehouse for a fictional Taskrabbit-style NYC home-services marketplace.**
Booking lifecycle, payment lifecycle, and provider capacity — modeled as separate business processes, connected by explicit keys, tested end-to-end, and reconciled to hand-calculated fixtures.

`Python` · `PostgreSQL` · `dbt Core` · `Metabase` · `GitHub Actions` · `Docker Compose`

[Quickstart](#-quickstart) · [Architecture](#-system-architecture) · [Metrics](#-metrics-and-business-logic) · [Insights](#-insights-from-synthetic-data) · [Docs](#-documentation-navigation)

</div>

---

## 📊 Project Overview

| | |
|---|---|
| **The fictional marketplace** | Customers request home services (furniture assembly, cleaning, plumbing, electrical, painting, moving) across five NYC boroughs; independent providers accept and perform them. |
| **The problem this warehouse solves** | Operational events (bookings, status changes, payment attempts, captures, refunds, reversals, payouts, availability intervals) are siloed and easy to conflate. This project turns them into reliable, tested, explainable business metrics. |
| **Why separate modeling matters** | A completed booking ≠ a successful payment ≠ a paid provider. An available provider-hour ≠ a completed booking-hour. Conflating them inflates GMV, hides refund drag, and double-counts capacity. |
| **What it demonstrates** | Dimensional modeling with declared grains, append-only event history with state reconstruction, SCD Type 2 dimensions, effective-dated eligibility, interval-based capacity math, governed metric contracts, hand-calculated financial reconciliation, idempotent ingestion, incremental processing, CI, and BI dashboards. |

## ❓ Business Questions

1. Where does recorded demand exceed available provider capacity? *(modeled indicator)*
2. Which booking lifecycle stages lose the most bookings?
3. How do refunds and reversals change platform revenue?
4. Which boroughs and service categories have poor fulfillment?
5. How efficiently is declared provider availability actually reserved?
6. How much do providers earn versus how much has actually been paid out?

## 🏗 System Architecture

```mermaid
flowchart LR
    G["🐍 Python generator<br/>(seeded, configurable scale)"] --> C["CSV source files<br/>data/fixtures · data/generated"]
    C --> R["PostgreSQL · raw schema<br/>13 source tables, append-only"]
    R --> S["dbt staging<br/>13 standardized views"]
    S --> I["dbt intermediate<br/>lifecycle · financials · intervals"]
    I --> K["dbt core<br/>5 dims · 7 facts · 1 bridge"]
    K --> M["dbt marts<br/>6 business marts"]
    M --> B["📈 Metabase<br/>Operations + Economics"]
    T["Git / GitHub"] --> A["⚙️ GitHub Actions CI"]
    A --> P["pytest (17 tests)"]
    A --> D["PostgreSQL service"]
    A --> W["dbt build + tests<br/>fixture reconciliation"]
```

**Testing boundary:** CI validates the *deterministic fixture dataset* — Python unit tests, idempotent double-load, full `dbt build`, and the financial reconciliation test — on every push/PR. The medium demo dataset and Metabase are never required in CI.

## 🔄 Booking Lifecycle

```mermaid
stateDiagram-v2
    [*] --> CREATED: customer request
    CREATED --> ACCEPTED: provider accepts (eligible + assigned)
    CREATED --> REJECTED: provider declines
    CREATED --> EXPIRED: acceptance window (240 min) elapses
    CREATED --> CANCELLED: customer/system cancels
    ACCEPTED --> SCHEDULED: slot confirmed
    ACCEPTED --> CANCELLED: customer/provider cancels
    SCHEDULED --> IN_PROGRESS: work begins
    SCHEDULED --> CANCELLED: permitted cancellation
    SCHEDULED --> NO_SHOW: service not fulfilled
    IN_PROGRESS --> COMPLETED: service completed
    IN_PROGRESS --> CANCELLED: exceptional only
    COMPLETED --> [*]
    CANCELLED --> [*]
    REJECTED --> [*]
    EXPIRED --> [*]
    NO_SHOW --> [*]
```

**Why append-only?** Status events are business history. `fct_booking` stores the *reconstructed* final state (ordered by `occurred_at, event_sequence, event_id`); the events themselves are never overwritten or deleted. Corrections happen as new explicit events or a regenerated dataset — never silent edits. Rescheduling preserves the `booking_id` and records old → new scheduled times; the current scheduled time is derived from the latest valid reschedule.

## 💳 Payment & Financial Flow

```mermaid
flowchart LR
    PA["Payment attempt<br/>(may fail, retried ≤3x)"] -->|success| CA["Posted CAPTURE<br/>(collected money)"]
    CA --> RF["REFUND<br/>(full / partial)"]
    CA --> RV["REVERSAL<br/>(posted reversal)"]
    CO["Booking COMPLETED"] -.->|service value| GMV["Gross → Net GMV"]
    CA --> GMV
    RF --> GMV
    RV --> GMV
    GMV --> FEE["Platform fee<br/>(fee policy at completion)"]
    FEE --> FEEREV["Proportional fee reversal<br/>(refund × original rate)"]
    FEE --> PE["Provider earnings<br/>(owed)"]
    PE --> PO["Provider payout<br/>(PAID cash, own date basis)"]
```

Four concepts that are easy to conflate — kept strictly separate here:

| Concept | Source | Key rule |
|---|---|---|
| Payment attempt | `fct_payment_attempt` | A failed attempt is **not** captured money |
| Capture / refund / reversal | `fct_payment` | Posted financial events with signed effects |
| Provider earnings | derived | Amount **owed** under the fee/refund policy |
| Provider payout | `fct_provider_payout` | Cash **disbursed**, reported by payout date, never booked into GMV |

## 🗄 Data Model & ERD

```mermaid
erDiagram
    RAW_CUSTOMERS ||--o{ RAW_BOOKINGS : creates
    RAW_PROVIDERS ||--o{ RAW_BOOKINGS : assigned_to
    RAW_SERVICE_CATEGORIES ||--o{ RAW_BOOKINGS : requested_service
    RAW_LOCATIONS ||--o{ RAW_BOOKINGS : service_region
    RAW_BOOKINGS ||--o{ RAW_BOOKING_STATUS_EVENTS : status_history
    RAW_BOOKINGS ||--o{ RAW_BOOKING_RESCHEDULE_EVENTS : reschedule_history
    RAW_BOOKINGS ||--o{ RAW_PAYMENT_ATTEMPTS : attempts
    RAW_BOOKINGS ||--o{ RAW_PAYMENT_EVENTS : posted_events
    RAW_BOOKINGS ||--o{ RAW_PROVIDER_PAYOUTS : payouts
    RAW_PROVIDERS ||--o{ RAW_PROVIDER_SERVICE_ELIGIBILITY : eligible_for
    RAW_PROVIDERS ||--o{ RAW_PROVIDER_AVAILABILITY_INTERVALS : available_during
    RAW_FEE_POLICY {
        numeric fee_rate "0.150000 (15%, synthetic default)"
    }

    DIM_CUSTOMER ||--o{ FCT_BOOKING : "customer (SCD2 as-of creation)"
    DIM_PROVIDER ||--o{ FCT_BOOKING : "provider (SCD2 as-of acceptance)"
    DIM_SERVICE ||--o{ FCT_BOOKING : service
    DIM_LOCATION ||--o{ FCT_BOOKING : region
    DIM_DATE ||--o{ FCT_BOOKING : "created / service / completed roles"
    FCT_BOOKING ||--o{ FCT_PAYMENT : financial_events
    FCT_BOOKING ||--o{ FCT_PROVIDER_PAYOUT : payouts
    DIM_PROVIDER ||--o{ FCT_PROVIDER_AVAILABILITY : capacity
    BRIDGE_PROVIDER_ELIGIBILITY ||--o{ FCT_PROVIDER_AVAILABILITY : qualifies
```

| Model | Grain | Purpose |
|---|---|---|
| `fct_booking` | one booking | Final reconstructed lifecycle + service value + eligibility flags |
| `fct_booking_status_event` | one transition | Append-only event history, validity flag |
| `fct_booking_reschedule_event` | one reschedule | Old/new scheduled times, booking ID preserved |
| `fct_payment_attempt` | one attempt | Success/failure/retry; never counted as cash |
| `fct_payment` | one posted event | Capture/refund/reversal with signed amount |
| `fct_provider_payout` | one payout | Disbursement record + status + paid date |
| `fct_provider_availability` | one interval | OPEN/BLOCKED time, [start, end), per provider×category×region |
| `bridge_provider_eligibility` | one eligibility interval | Effective-dated permission to serve |
| `mart_booking_lifecycle` | one booking | Outcome mix, stage durations, actor/reason |
| `mart_marketplace_economics_booking` | one booking | GMV gross/net, fees, reversals, earnings, paid payouts |
| `mart_supply_demand_hourly` | hour × borough × neighborhood × category | Demand, capacity, modeled gap, reserved utilization |
| `mart_booking_cohort_daily` | created-date × region × category | Outcome counts + cohort maturity |
| `mart_completed_economics_daily` | completion-date × region × category | Daily economics |
| `mart_provider_payout_daily` | payout-date × provider | Actual paid cash |

## 🧱 dbt Model Architecture

| Layer | Models | Materialization |
|---|---|---|
| Sources | 13 raw tables declared in `sources.yml` | — |
| Staging | `stg_raw__*` (13) — naming/casting/standardization only | view |
| Intermediate | `int_booking_status_ordered`, `int_booking_lifecycle`, `int_booking_reschedule_reconstructed`, `int_payment_events_signed`, `int_booking_financials`, `int_booking_economics`, `int_requested_demand_hourly`, `int_eligible_capacity_hourly`, `int_reserved_booking_minutes` | table |
| Core | `dim_customer` (SCD2), `dim_provider` (SCD2), `dim_service`, `dim_location`, `dim_date` (role-playing), 7 facts, `bridge_provider_eligibility` | table |
| Marts | 6 business marts (above) | table |

Fanout protection: every one-to-many child fact (payments, payouts, events) is aggregated to booking grain **before** any join to bookings — enforced by SQL conventions (TAD 14.3) and reconciliation tests.

## 📐 Metrics and Business Logic

| Metric | Formula | Time basis |
|---|---|---|
| Gross completed GMV | Σ service value of valid `COMPLETED` bookings | completion date |
| Net completed GMV | Gross GMV − eligible refunds/reversals (capped at capture) | completion date |
| Completed bookings | count distinct booking IDs, final status `COMPLETED` | creation cohort |
| Cancellation rate | cancelled ÷ eligible created (same cohort, mature only) | creation date |
| Fulfillment rate | completed ÷ eligible created (same cohort, mature only) | creation date |
| Platform fee revenue | gross fee − proportional fee reversal | completion date |
| Take rate | net fee revenue ÷ net completed GMV × 100 | completion date |
| Provider earnings | net GMV − net fee revenue (owed) | completion period |
| Provider payouts | Σ `PAID` payouts | **payout date** |
| Provider utilization | reserved minutes ÷ open minutes × 100 | service time |
| Median completion time | median(`completed_at − in_progress_at`) | status events |
| Request-to-completion | median(`completed_at − created_at`) | creation → completion |
| Requested demand hours | Σ requested duration split by exact interval intersection | requested service time |
| Eligible capacity hours | Σ OPEN interval minutes ∩ bucket, eligibility applied | availability time |
| Modeled supply-demand gap | demand hours − capacity hours (**modeled, not observed unmet demand**) | service time |

**Worked financial example** — $100 completed service, 15% fee, $20 refund:

| Measure | Value |
|---|---:|
| Gross completed GMV | $100.00 |
| Net completed GMV | $80.00 |
| Gross platform fee (15%) | $15.00 |
| Fee reversal (15% × $20, **original rate**) | $3.00 |
| Net platform fee revenue | $12.00 |
| Provider earnings ($80 − $12) | $68.00 |

This exact case is generated as fixture F10 and proven by `assert_completed_gmv_reconciles_to_fixture` against hand-calculated constants — the expected values never reuse the production SQL.

## 📈 Dashboard Previews

Two Metabase dashboards (Operations, Marketplace Economics) are wired to the `marts` schema via a read-only `metabase_reader` role, with one saved question per card in [`metabase/queries/`](metabase/queries/) and a full setup guide in [`metabase/README.md`](metabase/README.md).

> **Honest disclosure:** this build environment had no Docker/Metabase, so no browser screenshots were captured — none are fabricated here. To generate them: `docker compose up -d` → open `localhost:3000` → follow `metabase/README.md` → save PNGs to `docs/assets/dashboard_*.png`.

## 🔍 Insights from Synthetic Data

From the **deterministic fixture dataset** (seed 42, scale `fixtures`, 12 bookings covering all 15 edge cases) — actual outputs of the generated data, independently aggregated from the raw CSVs:

| Observation | Value (synthetic) |
|---|---:|
| Bookings / status events / payment events | 12 / 48 / 3 |
| Outcome mix | 7 completed · 2 cancelled · 1 rejected · 1 expired · 1 no-show |
| Gross completed GMV | $810.00 |
| Eligible refunds/reversals | $160.00 |
| Net completed GMV | $650.00 |
| Gross platform fee (15%) | $121.50 |
| Fee reversals | $24.00 |
| Net platform fee revenue | $97.50 |
| Provider earnings | $552.50 |
| Paid payouts (3 of 5 transactions) | $263.50 (2 PENDING) |
| Refunded share of gross GMV | 19.75% |
| Take rate | 15.0% (by construction — flat fee policy) |

What this synthetic data demonstrates (mechanics, not market behavior): refunds/reversals cut gross GMV by ~20% and fee revenue proportionally at the original 15% rate; provider payouts lag and trail provider earnings (owed $552.50 vs $263.50 disbursed — the earnings/payout gap the warehouse is designed to expose); both fixtures in the rejected-records file (duplicate payment event, overlapping availability) were correctly refused.

> ⚠️ All figures above come from synthetic data with a documented seed. They do not represent real NYC home-services marketplace economics.

For the full demo: `python -m generator.cli generate --seed 42 --scale medium` produces the PRD target volumes (≈5,000 customers, 500 providers, 50,000 bookings) and `python -m generator.insights` re-runs these aggregations over the loaded medium marts.

## 🛡 Data Quality & Testing

| Layer | What it protects | Count |
|---|---|---|
| Python unit tests | Reproducibility, unique IDs, referential integrity, legal transitions, refund caps, retry limits, interval overlap rejection, fixture scenarios | 17 |
| dbt generic tests | unique / not_null / relationships / accepted_values / composite grain | ~60 |
| dbt singular tests | All 22 named tests from TAD 17.3 — lifecycle legality, chain continuity, eligibility-at-acceptance, refund overage, fee-reversal proportionality, fixture reconciliation, payout-provider match, interval overlap, reservation ≤ availability, mart grain | 22 |
| Idempotency | DB unique constraints on `idempotency_key`; `ON CONFLICT DO NOTHING` loader; CI loads the fixture batch **twice** and asserts nothing changes | — |

```bash
pytest tests/unit -q                                  # 17 passed
dbt build --vars "$(python -m generator.incremental fixture_vars)"
```

The reconciliation test compares mart output to **hand-calculated** constants (`generator/fixtures.py`), not to a re-computation of the production SQL.

## 🧰 Technology Stack

| Technology | Responsibility | Why chosen |
|---|---|---|
| Python | Seeded synthetic data, loader, tests | Full control of edge-case fixtures and determinism |
| PostgreSQL | Raw persistence + warehouse | Constraints, `timestamptz`, `numeric(12,2)` money |
| dbt Core | Transformations, tests, docs | Dependency graph, executable metric contracts |
| SQL | All business logic | Transparent, reviewable, interview-defensible |
| Metabase | Dashboards | Reads governed marts only via read-only role |
| Docker Compose | Postgres + Metabase locally | One-command reproducible services |
| GitHub Actions | CI | Small-fixture build + test on every change |

## 🚀 Quickstart

**Windows PowerShell** (macOS/Linux: replace `$env:VAR` with `export VAR=...`):

```powershell
git clone https://github.com/Nachiketh-AE/marketplace-fulfillment-warehouse
cd marketplace-fulfillment-warehouse

# 1. Services (PostgreSQL :5432 + Metabase :3000)
Copy-Item .env.example .env
docker compose up -d

# 2. Python environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Generate synthetic data
python -m generator.cli generate --seed 42 --scale fixtures --out-dir data/fixtures
python -m generator.cli generate --seed 42 --scale small    # data/generated/small
python -m generator.cli generate --seed 42 --scale medium   # PRD target volumes

# 4. Load into PostgreSQL (idempotent — safe to re-run)
$env:DATABASE_URL = "postgresql://warehouse_admin:warehouse_admin@localhost:5432/warehouse"
python -m generator.cli load --input-dir data/fixtures --database-url $env:DATABASE_URL

# 5. dbt
pip install "dbt-core>=1.8,<2" "dbt-postgres>=1.8,<2"
cd marketplace_warehouse
Copy-Item profiles.yml.example profiles.yml   # adjust credentials if needed
dbt deps
dbt build --vars "$(python -m generator.incremental fixture_vars)"

# 6. Metabase
# open http://localhost:3000 → follow metabase/README.md
```

Rebuild from scratch: `docker compose down -v` → repeat steps 1–5.

## 📁 Repository Structure

```
marketplace-fulfillment-warehouse/
├── README.md                        ← you are here
├── docs/
│   ├── PRD.md · TAD.md              ← authoritative specs (verbatim)
│   ├── requirements_traceability.md ← every FR mapped to code + test
│   ├── requirements_conflicts.md    ← PRD/TAD divergence log (none material)
│   ├── metric_dictionary.md         ← 15 governed metric contracts
│   ├── data_dictionary.md           ← column-level model docs
│   ├── implementation_status.md     ← phase-by-phase, honest limits
│   ├── recruiter_walkthrough.md     ← 5–8 min guided tour
│   ├── architecture/ · diagrams/ · assets/banner.svg
├── generator/                       ← config · entities · lifecycle · payments
│                                      availability · fixtures · load · cli
│                                      incremental · insights
├── data/fixtures/                   ← committed deterministic fixture CSVs
├── data/generated/                  ← regenerable datasets (gitignored)
├── sql/init/                        ← schemas, roles, raw tables + constraints
├── marketplace_warehouse/           ← dbt project (13 stg / 9 int / 13 core / 6 marts)
│                                      + 22 singular tests + test YAML
├── tests/unit · tests/integration   ← pytest
├── metabase/                        ← dashboard guide + saved-question SQL
├── .github/workflows/ci.yml
├── docker-compose.yml · .env.example · requirements.txt
```

## ⚠️ Limitations & Assumptions

- **All data is synthetic.** No Taskrabbit/Plaid/Linear/Temporal or other real company data; NYC borough labels are synthetic context, not real marketplace coverage.
- **Demand is booking-based.** Searches that never became bookings are invisible; the supply-demand gap is a modeled indicator, never confirmed unmet demand.
- **Availability is modeled**, not attendance or guaranteed labor; utilization is reserved-time based and labeled as such.
- **No real payment processor.** Captures/refunds/reversals are synthetic financial events; "completion requires capture" is a project rule, not universal payment logic.
- **No causal claims.** Observational synthetic data cannot prove intervention effects.
- **Cohort rates need maturity.** Rates are only quoted for mature cohorts (14-day window + all-terminal rule).

## 🏛 Engineering Decisions (ADRs)

| Decision | Rationale |
|---|---|
| Append-only event history; state derived | Preserves lifecycle evidence; enables stage analytics (ADR-002) |
| Attempts ≠ posted events; earnings ≠ payouts | Prevents counting failed attempts as cash, owed as paid (ADR-003/004) |
| One provider per booking; reschedule keeps booking ID | Bounded allocation logic; reschedule is an event, not a new request (ADR-005/006) |
| Interval-based availability, no provider overlap | Prevents double-counted provider minutes (ADR-007/008) |
| Effective-dated fee policy in `raw_fee_policy` | Take rate reproducible; rate never a scattered constant (ADR-010) |
| Batch-first, then incremental with ingestion watermark | Correctness before complexity; late events handled by `source_loaded_at` (ADR-011) |
| SCD2 dims + role-playing dates | Historical profiles; no ambiguous single date join (ADR-013) |
| Local least-privilege roles | Demonstrates loader/transformer/reader separation, honestly scoped (ADR-014) |

## 🔭 Future Extensions

Compatible with the PRD/TAD but beyond current MVP: anomaly flags on cohort metrics (FR-027); documented hypothetical supply intervention with causal-inference caveats (FR-028); incremental dbt materializations for event-level facts keyed on `source_loaded_at` watermark; dbt snapshots as an alternative to source SCD2; dbt docs site publication.

## 🎯 Recruiter Walkthrough

A 5–8 minute guided tour — what each artifact demonstrates and the questions it arms you to answer — lives in [`docs/recruiter_walkthrough.md`](docs/recruiter_walkthrough.md).

## 📚 Documentation Navigation

| Document | Purpose |
|---|---|
| [PRD](docs/PRD.md) | Business requirements, metric contracts, acceptance checklist |
| [TAD](docs/TAD.md) | Source contracts, ERD, grains, financial rules, build order, ADRs |
| [Traceability matrix](docs/requirements_traceability.md) | Every requirement → implementation → test → status |
| [Metric dictionary](docs/metric_dictionary.md) | Governed definitions (numerator, denominator, time basis, caveats) |
| [Data dictionary](docs/data_dictionary.md) | Column-level model documentation |
| [Conflicts log](docs/requirements_conflicts.md) | PRD/TAD divergences and resolutions |
| [Implementation status](docs/implementation_status.md) | What ran, what passed, honest environment limits |
| [Recruiter walkthrough](docs/recruiter_walkthrough.md) | Interview-ready tour |
| [Metabase guide](metabase/README.md) | Dashboard setup + saved questions |

---

<div align="center">
<sub>All data in this repository is synthetic and for portfolio demonstration only. No real marketplace, provider, or customer data is used or implied.</sub>
</div>
