# Implementation Status

Updated: 2026-11-10 (seed 42, fixture + small + medium datasets).

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| 0 — Foundation | Repo structure, env config, SQL bootstrap, docs | Complete | `sql/init/`, `.env.example`, `docker-compose.yml`, `docs/` |
| 1 — Generator + lifecycle | Entities, bookings, events, reschedules, loader, unit tests | Complete | `generator/`, `tests/unit` — 17/17 pytest pass |
| 2 — dbt booking warehouse | Staging, intermediate, dimensions, booking facts, lifecycle mart | Complete | `marketplace_warehouse/models/` |
| 3 — Financial architecture | Payment facts, fee policy, economics mart, reconciliation tests | Complete | `int_booking_financials`, fixture tests |
| 4 — Capacity | Availability fact, demand/capacity/reserved intermediates, hourly mart | Complete | `int_*_hourly`, `mart_supply_demand_hourly` |
| 5 — Incremental + idempotency | Ingestion watermark, idempotent loader, duplicate/late fixtures | Complete | `generator/load.py`, `generator/incremental.py`, CI |
| 6 — Dashboards + CI | Saved-question SQL, Metabase setup guide, GitHub Actions | Complete (dashboard rendering is a manual Metabase step — see limitations) | `metabase/`, `.github/workflows/ci.yml` |
| 7 — Recruiter polish | README, diagrams, walkthrough, traceability, real insights | Complete | `README.md`, `docs/` |

## Verified in this environment

- `python -m pytest tests/unit -q` → **17 passed** (reproducibility, integrity, transitions, refund caps, fee math, interval overlap, fixture scenarios).
- Generator determinism: two runs with seed 42 produce byte-identical CSVs.
- Fixture dataset: 12 bookings covering all 15 TAD-16.3 edge cases; 2 invalid scenarios recorded in `rejected_records.json` and never loaded.
- Medium dataset (seed 42): generated to `data/generated/medium` (PRD volumes; see README insights for actual row counts and metrics).

## Environment limitations (honest disclosure)

- The build environment used here had **no Docker daemon and no Metabase**, so Metabase dashboards were **not clicked through in a browser**. The dashboard layer ships as: reproducible container setup (`docker-compose.yml`), a step-by-step connection guide (`metabase/README.md`), and saved-question SQL per card (`metabase/queries/*.sql`). No fabricated screenshots are included.
- `tests/integration/test_loader_idempotency.py` runs in CI (PostgreSQL service) and locally whenever `DATABASE_URL` is set; it is skipped — with a clear skip reason — when no database is reachable.
- GitHub Actions workflow is defined and exercised by structure, but no remote repository was pushed (no authorization to publish).
