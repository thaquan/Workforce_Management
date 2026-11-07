# Phase 2 — Local acceptance checklist

Latest complete local smoke run: **batch 20, SUCCEEDED, 29,728 / 29,728 rows**. Offline suite: **22 passed, 7 integration tests intentionally skipped**. Live integration suite: **7 passed**; tested independently in Session 3. Audit quality results on final success: **19 PASS, 4 REVIEW**. The source workbook's SHA-256 matches the original file outside the repository.

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
