# Recruiter Walkthrough (5–8 minutes)

A guided tour of what this project demonstrates and where to look.

## 1. The business problem (1 min)

A Taskrabbit-like home-services marketplace produces booking events, payment
events, and provider-availability records. They are **three separate business
processes**: a completed booking does not prove money moved, and a paid
booking does not prove the provider was paid. The warehouse models them
separately and connects them with explicit keys, timestamps, and documented
metric contracts. → Show README §Architecture and §Booking lifecycle.

## 2. Grains first (1–2 min)

- `fct_booking` — one row per booking (current/final state; history preserved)
- `fct_booking_status_event` — one row per transition (append-only)
- `fct_payment` — one posted capture/refund/reversal
- `fct_provider_payout` — one cash-disbursement record
- `fct_provider_availability` — one time interval
→ `docs/data_dictionary.md`, `marketplace_warehouse/models/core/`.

Key habit: child facts are aggregated to booking grain **before** joining to
bookings — no fanout. See `int_booking_financials` and the TAD §14.3 rules.

## 3. Trace one booking (1 min)

Pick any `booking_id` in `mart_booking_lifecycle`: its history lives in
`fct_booking_status_event`, its final status is *reconstructed* from valid
events (`int_booking_status_ordered` → `int_booking_lifecycle`), and
rescheduling preserved the booking ID
(`int_booking_reschedule_reconstructed`).

## 4. Trace one dollar (1–2 min)

The canonical fixture: $100 completed service, 15% fee, $20 refund →
$100 gross GMV, $80 net GMV, $15 gross fee, **$3 fee reversal** (15% of the
refund at the original rate), $12 net fee revenue, $68 provider earnings.
The dbt test `assert_completed_gmv_reconciles_to_fixture` compares mart output
to these hand-calculated constants — the expected values never reuse the
production SQL. → `generator/fixtures.py`, `marketplace_warehouse/tests/`.

## 5. Supply and demand, honestly (1 min)

`mart_supply_demand_hourly` splits requested service intervals and OPEN
availability intervals across hourly buckets with exact intersection math,
per region/category. The gap is a **modeled indicator** — booking-based
demand only; it must never be called confirmed unmet demand. → README §Metrics.

## 6. Tests protect the metrics (1 min)

- 17 Python unit tests: reproducibility, transition validity, refund caps,
  interval overlap rejection, fixture scenarios.
- ~60 dbt generic tests + 22 singular tests: lifecycle legality, idempotency,
  financial reconciliation, grain uniqueness, capacity sanity.
- CI builds the fixture dataset against a PostgreSQL service on every push.
→ `.github/workflows/ci.yml`, `docs/requirements_traceability.md`.

## 7. Trade-offs (1 min)

Batch-first before incremental; ingestion watermark for late events; local
least-privilege roles (not a security product); synthetic data only — no
claims about real marketplace economics. → README §Limitations, TAD ADRs.

## Common interview questions this project arms you for

- Why append-only events instead of a status column?
- How do you prevent double-counting when joining 1-to-many facts?
- How do refunds flow into GMV and take rate without double subtraction?
- Why is eligibility not availability?
- What breaks first if this moved from dbt-postgres to a warehouse?
