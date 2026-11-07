# Phase 2 — Local acceptance checklist

Phase 2 code review verified **2026-11-07**: latest successful load **batch 32**, 29,728/29,728 rows, followed by matching-source **batch 33 SKIPPED**. Offline suite: **23 passed, 10 integration tests skipped by default**. Live PostgreSQL integration suite: **10/10 passed**. Latest successful batch: **19 PASS / 4 REVIEW** quality checks. The local source Excel SHA-256 matched the original Excel outside the project directory.

| Acceptance gate | Observed result | Status |
|---|---|---|
| Docker Compose config | `docker compose config -q` exits 0 | PASS |
| PostgreSQL health | `hr-workforce-postgres` healthy | PASS |
| Warehouse schemas | raw, staging, marts, audit | PASS |
| Audit metadata tables | source_files, load_batches, quality_results | PASS |
| Number of raw tables | 12 | PASS |
| Total source rows loaded | 29,728 | PASS |
| Source checksum | SHA-256 recorded in audit | PASS |
| Repeating identical file | SKIPPED, unchanged row counts | PASS |
| Database tampering with same row count | Full raw content comparison detects change and reloads | PASS |
| Schema contract drift | PostgreSQL metadata checked against defined columns/types/PK | PASS |
| Report I/O failure after commit | Audit remains SUCCEEDED; CLI emits report_warning | PASS |
| Source mutation during parsing | Second SHA-256 detects mismatch; batch FAILED | PASS |
| Mid-load failure | Transaction rollback, previous tables retained | PASS |
| Corrupt workbook | FAILED batch and quality_result, no raw mutation | PASS |
| Invalid business key / foreign key | Rejected by source contract | PASS |
| Changed source | Full transactional replacement, baseline restored | PASS |
| Local security exclusions | .env, original Excel and processed rows ignored | PASS |
| Phase 1 source caveats | Headcount, calendar, budget and transfers still documented | REVIEW |
| dbt staging and Power BI | Out of scope until Phase 3+ | NOT STARTED |

## Regression commands

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
$env:HR_INTEGRATION_TESTS="1"
python -m unittest discover -s tests -p "test_phase2_integration.py" -v
Remove-Item Env:HR_INTEGRATION_TESTS
python -m src.phase2.ingest --force
```

The first command runs offline tests and explicitly skips integration tests unless the flag is set. The second command exercises a live PostgreSQL instance and restores original data after its corrected-input test. Do not publish the local source workbook or row-level HR data.

## Outstanding business questions

1. Thirty-three source months have a headcount mismatch against employee-date-as-of counts. Preserve both representations until the data owner confirms business cutoffs.
2. Budget period, currency and salary coverage are not stated in the source metadata; salary variance remains blocked.
3. Internal transfers are not available in source events; do not claim mobility analytics.
4. This test run used an existing PostgreSQL volume. Fresh-volume initialization is documented, but not destructively retested.
