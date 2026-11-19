# Architecture Notes

This directory holds implementation-level architecture notes. Visual diagrams
(Mermaid, rendered by GitHub) live in the [README](../../README.md) and in
`docs/diagrams/`.

## Schema boundaries (TAD 3.4)

| Schema | Writer | Reader | Contents |
|---|---|---|---|
| `raw` | `warehouse_loader` (Python) | dbt | Source-shaped synthetic tables, append-only events |
| `staging` | dbt (`warehouse_transformer`) | dbt | One view per raw table; standardized |
| `intermediate` | dbt | dbt | Lifecycle reconstruction, financial allocation, interval math |
| `core` | dbt | dbt | Dimensions (SCD2), facts, eligibility bridge |
| `marts` | dbt | `metabase_reader` | Business-facing analytics |

## Least-privilege roles (TAD 19.2)

- `warehouse_admin` — bootstrap/DDL (local development).
- `warehouse_loader` — INSERT/SELECT on `raw` only; cannot touch dbt objects.
- `warehouse_transformer` — reads `raw`; creates/replaces `staging`–`marts`.
- `metabase_reader` — SELECT on `marts` only.

This demonstrates local role separation; it is not a multi-tenant security
architecture, and row-level security is intentionally out of scope (single
fictional marketplace).

## Incremental processing design (TAD 18)

1. Raw event tables are append-only; unique constraints on `idempotency_key`
   make re-ingestion a no-op (`ON CONFLICT DO NOTHING`).
2. `source_loaded_at` is the ingestion watermark: a late event (old
   `occurred_at`, new `source_loaded_at`) is discovered through its ingestion
   time, and its booking is recomputed from full event history.
3. `fct_booking` rebuilds per run from complete history (batch-first);
   `dbt build` is idempotent for the same source snapshot — verified by
   re-loading the same batch and re-running the fixture reconciliation test.
4. Backfill = `dbt build --full-refresh` after re-loading the affected batch.
