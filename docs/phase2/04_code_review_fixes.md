# Phase 2 Code Review — 2026-11-07

Review scope: Python ingestion, PostgreSQL table contract, audit status, source-integrity checks, regression coverage and Git privacy.

## Findings and resolutions

| Severity | Finding | Fix | Evidence |
|---|---|---|---|
| High | Same-checksum/same-row-count data mutations could be skipped | Compare all source values with all corresponding raw-table values before SKIPPED | Integration test 08; same-count tamper detected and repaired |
| High | Post-commit report write failure could mark a committed load FAILED | Separate database transaction error handling from optional report file I/O; return `report_warning` | Integration test 09; batch remains SUCCEEDED |
| Medium | File could change after its first SHA-256 was calculated | Recalculate source SHA-256 after workbook parsing; abort if changed | Integration test 10; FAILED batch, raw data retained |
| Medium | `CREATE TABLE IF NOT EXISTS` did not validate pre-existing table structure | Verify column names, data types, precision, nullability and primary keys against contract | Forced load with schema checks passes for all 12 tables |
| Medium | Earlier docs described idempotency as count-only | Update Phase 2 runbooks, limitations and regression test references | Documentation and release checklist updated |

## Final observed evidence

- PostgreSQL 17 Docker container: healthy.
- 12 raw tables containing 29,728 source rows.
- Batch 32: SUCCEEDED, 29,728 expected / 29,728 loaded.
- Batch 33: SKIPPED after exact content comparison.
- Latest successful batch quality: 19 PASS, 4 REVIEW.
- Python offline suite: 23 PASS (10 opt-in integration tests skipped).
- PostgreSQL integration suite: 10 PASS.
- Excel SHA-256 unchanged: `d40a85095faabb4c18517a51c977747c57d7f248d952039ec442923ca5042626`.
- Raw HR workbook, `.env` and generated row-level outputs excluded from Git.

## Remaining source limitations (not pipeline bugs)

- Snapshot-versus-employee headcount mismatches persist in 33 historical months. Do not modify source counts.
- Salary budget currency, annualization and coverage are unconfirmed. Salary variance KPI must stay blocked.
- No Transfer event history exists; do not infer historical internal mobility.
- Exact-content skip is an O(rows) database comparison suitable for this small historical dataset. For production-scale volumes, use partition-level fingerprints or change-data capture.

## Reproduce

```powershell
Set-Location D:\Workforce_Management
python -m unittest discover -s tests -p "test_*.py" -v
$env:HR_INTEGRATION_TESTS = "1"
python -m unittest discover -s tests -p "test_phase2_integration.py" -v
Remove-Item Env:HR_INTEGRATION_TESTS
python -m src.phase2.ingest --force
python -m src.phase2.ingest
```

These tests interact with local PostgreSQL; integration tests intentionally change and restore sample database values, not the Excel source. Run them in a disposable/local development database, never against production.
