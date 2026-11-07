# Phase 3 Acceptance Report — 2026-11-07

## Verified technical results

| Gate | Actual result | Status |
|---|---|---|
| PostgreSQL | Docker PostgreSQL 17 healthy; `raw`, `staging`, `marts`, `audit` present | PASS |
| dbt toolchain | dbt Core 1.12.6 / dbt-postgres 1.11.0, Python 3.13.15 | PASS |
| dbt debug/parse | PostgreSQL connection and parsing successful | PASS |
| Staging | 12 source views and 4 intermediate views | PASS |
| Analytical tables | 5 dimensions + 8 facts + 7 business marts | PASS |
| dbt build | 36 models + 83 tests = **119 successes**, zero errors/warnings | PASS |
| dbt documentation | `manifest.json` and `catalog.json` generated locally | PASS |
| Phase 3 Python tests | 6 static + 5 live PostgreSQL integration tests | PASS |
| Privacy | Source workbook and secrets not included in source definitions | PASS |

## Read-only reconciliation results

| Table | Rows |
|---|---:|
| `marts.mart_workforce_monthly` | 6,826 |
| `marts.mart_attrition_monthly` | 288 |
| `marts.mart_workforce_plan_vs_actual` | 288 |
| `marts.mart_recruitment_monthly` | 288 |
| `marts.mart_retention_analysis` | 1,200 |
| `marts.mart_workforce_reconciliation` | 36 |
| `marts.mart_salary_run_rate_monthly` | 36 |

- **33/36** months have a headcount reconciliation status of `REVIEW`.
- June 2025: snapshot HC 1,021 vs employee-as-of 923; difference **+98**.
- December 2025: snapshot HC 999 vs employee-as-of 994; difference **+5**.
- January 2023 planning: actual 622, planned 989; gap **−367**.
- December 2025 planning: actual 999, planned 1,079; gap **−80**.
- Attrition quality: eight January-2023 department-month rows
  `NO_PRIOR_SNAPSHOT`; 280 are `PROVISIONAL_SOURCE_MISMATCH`.
- The date dimension includes **2,918** days, beginning 2018-01-05.

## Exit criteria and known limitations

All technical acceptance gates above passed for the current workbook and
local PostgreSQL database. **Business validation remains open** for historic
snapshot cutoffs, salary-budget units/population and internal transfers.
No amount, rate or historical department movement was fabricated to
mask those constraints.

This is a batch dbt warehouse ready for Power BI semantic-model development,
not yet a published Power BI report or a production scheduler.
