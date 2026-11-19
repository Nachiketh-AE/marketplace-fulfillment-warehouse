# Requirements Conflicts and Resolutions

A full read of PRD v1.0 and TAD v1.0 found **no direct business-rule conflicts**. The documents are aligned: the TAD implements the PRD's metric contracts, refund policy, transition map, and mart grains verbatim.

Minor interpretation points, documented for transparency:

| # | Observation | Resolution | Impact |
|---|---|---|---|
| 1 | PRD §10 lists FR-026 (incremental demo) as *Should* while the master build prompt requires the incremental demonstration. | Treated as required (stricter source wins). Implemented via ingestion-watermark loader + idempotency fixtures + `generator/incremental.py`. | None — strictly more complete. |
| 2 | PRD §9.1 gives target volumes as ranges ("60,000–100,000 combined payment events/attempts"); the TAD does not fix the exact split. | Generator emits one attempt per scheduled booking plus retries (deterministic proportions in `generator/config.py`); exact row counts reported in `docs/implementation_status.md`. | Split is a documented configuration choice, not a metric change. |
| 3 | PRD §8 (fulfillment rate) requires a "declared cohort maturity/reporting cutoff"; the exact window is an open default (PRD §18). | Set to 14 days in `generator/config.py::COHORT_MATURITY_WINDOW_DAYS` and surfaced as `is_cohort_mature` in `mart_booking_cohort_daily`. | Config value visible in code and this doc; no silent constant. |
| 4 | TAD §11.2 allows SCD2 dims with few/no profile changes ("schema and tests should still support the versioning contract" if none are generated). | Generator creates deterministic profile updates (~8% of customers, ~9% of providers) so SCD2 is exercised with real data. | Slightly richer dataset than the TAD minimum. |
| 5 | PRD §6.2 lists anomaly flags (FR-027) as *Could*; the master prompt's phase 5 mentions "anomaly flags". | Implemented as documented extension guidance (README §Future extensions) rather than production code, per "could" priority and scope discipline (master prompt §28). | Tracked in `docs/requirements_traceability.md` as documented-limitation. |
