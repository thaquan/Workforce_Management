# Phase 4 — Verified Local Acceptance

Verified on Windows with Docker Desktop / PostgreSQL 17,
Python 3.13.15 and dbt Core 1.12.6.

## Real private workbook: end-to-end batch

| Gate | Observed evidence | Result |
|---|---|---|
| PostgreSQL | `hr-workforce-postgres` healthy, main `workforce_dw` untouched by fault injections | PASS |
| Full pipeline | Audit pipeline run **#3**, status SUCCEEDED | PASS |
| dbt models/tests | **36 successful models + 83 passing tests = 119** | PASS |
| Phase 4 gates | **14 PASS, 4 REVIEW, 0 FAIL** | PASS |
| Business source caveats | Reconciliation, source calendar, budget units and transfers remain REVIEW | REVIEW |
| Monitoring | Pipeline runs, per-gate status, runtime, ingested rows and freshness age in PostgreSQL audit | PASS |

Latest full run: **39.87 seconds** elapsed, including **35.68 seconds**
for the dbt build. The latest successful snapshot model has **6,826 rows**.
Python offline discovery: **60 tests, 39 PASS, 21 intentionally skipped**
(those require explicit live/isolated integration flags).

The source workbook is still private. This repository publishes only model
definitions and aggregate evidence, never employee-level rows.

## Isolated synthetic CI rehearsal

| Test | Observed evidence | Result |
|---|---|---|
| Environment | Separate PostgreSQL database `workforce_ci`, never `workforce_dw` | PASS |
| Fixtures | 12 synthetic raw tables, 22 invented records; validated against Phase 2 schema | PASS |
| dbt | **36 models + 80 tests passed**; three private-workbook baseline tests deliberately excluded | PASS |
| Synthetic Phase 4 gates | **15 PASS, 3 REVIEW, 0 FAIL** | PASS |
| Fault/recovery suite | **6 tests passed**: baseline, bad FTE, duplicate PK, corrupt file, schema drift, stuck run | PASS |
| Corrupted mart | Run audited FAILED; after restoring test values, following run audited SUCCEEDED | PASS |

## Interpretation

Technical Phase 4 gates are passing locally, including failure/recovery
behavior in an isolated database. **Hosted GitHub Actions execution is not
asserted here** until confirmed separately in the Actions UI/API.

Open business questions remain unchanged: 33 historical headcount
discrepancies, salary-budget units, and missing transfer history.
These are upstream evidence gaps, not pipeline defects. No fake SCD2 or
unvalidated salary variance KPI has been introduced.
