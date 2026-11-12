# Phase 7 - Local Validation (Synthetic-Only)

Verified: 2026-11-12 (Asia/Ho_Chi_Minh). This report contains only aggregate counts and invented fixture evidence.

| Check | Observed result |
|---|---|
| Python / Dagster | Python 3.13.15 / Dagster 1.13.29 |
| Package integrity | pip check: no broken requirements |
| Dagster asset definitions | Five assets, one manual job, weekly schedule STOPPED |
| Offline smoke run | PASS, all five assets materialized as PLANNED without PostgreSQL |
| Phase 7 offline tests | 10/10 PASS, including transient retry and blocking quality |
| Full unittest collection | 83 tests: 62 passed / 21 skipped (integration guard flags off) |
| Isolated recovery suite | 6/6 PASS; generated health report redirected to ignored runtime path |
| Synthetic PostgreSQL | Fresh PostgreSQL 17-alpine, localhost-only port, temporary memory-backed data |
| Synthetic source | 22 invented rows; latest fixture period 2023-02 |
| Synthetic dbt | 116 successful model/test nodes |
| Synthetic Phase 4 quality gates | 15 PASS, 3 REVIEW, 0 FAIL |
| Synthetic end-to-end run | Dagster run e348716e-15fd-49b5-8371-46ab8f5f0dfa: SUCCESS |
| Idempotent repeat | raw_status=SKIPPED_UNCHANGED; raw employee and monthly mart counts remained 2 and 2 |
| Phase 4 audit | pipeline_run_id incremented from 1 to 2 on the repeated run |
| Real workforce_dw, real workbook, PBIR | Not accessed or modified during Dagster integration |
| Hosted GitHub CI | Pending push and workflow result at time of this local report |

Important limitations:
- The original private-workbook pipeline remains independent.
- A REVIEW result is explicitly not a claim that all historical HR reconciliation issues are resolved.
- No scheduled source refresh or Power BI Service refresh was enabled.
- The temporary synthetic container must not be confused with the user's existing Compose service.
