# Phase 8 - Local Synthetic Acceptance Evidence

**Date:** 2026-11-13 (Asia/Ho_Chi_Minh). The values below are invented data and aggregate-only evidence, not employee facts.

| Check | Observed result |
|---|---|
| Working tree before Phase 8 | Clean, HEAD fe90fd0 |
| Python / Dagster / Parquet | Python 3.13.15, Dagster 1.13.29, PyArrow 23.0.1 |
| Dependencies | pip check: No broken requirements |
| Four-asset Dagster dry-run | PASS, status PLANNED, zero PostgreSQL connections |
| Offline Phase 8 contract & Dagster tests | 15 PASS |
| Phase 8 PostgreSQL integration | 7 PASS, disposable PostgreSQL 17-alpine tmpfs |
| All repository offline tests | 105 collected: 77 PASS, 28 isolated/integration SKIP |
| Source batches | 3 immutable synthetic Parquet batches |
| Event ledger | 8 fictional events |
| Watermark | 0 -> 3 -> 6 -> 8 |
| Final employee state | 3 active, 1 logical deleted, 2.55 active FTE |
| Late event | 1 audited; newest employee state preserved |
| Idempotent replay | 3/3 SKIPPED_UNCHANGED; watermark and event counts unchanged |
| Transaction recovery | Injected failure rolled back event, state, audit, watermark |
| Audit integrity | Batch counts and derived latest event state reconcile |
| Schema drift | Detected and test-only alteration rolled back |
| Dagster success | cffb35ba-9da3-4802-9d58-8cb361ea0a88 |
| Parquet benchmark | 10,000 invented events, 77,260 bytes (ZSTD) |
| Parquet write/read sample | 0.4571 s / 0.8249 s; single-machine snapshot, not stable benchmark |
| Hosted GitHub Actions | Pending final push and hosted run |

The benchmark is a single local Parquet I/O example with no full-load comparison. Do not infer production speed improvements from it.

## Safety and scope

- No real HR workbook, proprietary records, historical warehouse schemas, production data, Power BI reports or service refresh were modified.
- PostgreSQL integration used a temporary in-memory database named workforce_ci, with isolated write guards and an independent incremental_demo schema. No existing named Docker volumes were mounted.
- The existing Phase 2 full-reload ingestion and the Phase 7 synthetic orchestration remain unchanged.
- The historical 33/36-month REVIEW headcount reconciliation remains provisional, as documented in earlier phases.
- Hosted CI needs an actual completed/success run before Phase 8 is considered delivered to GitHub.
