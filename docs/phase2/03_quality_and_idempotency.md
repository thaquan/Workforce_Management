# Phase 2 / Session 3 — Quality and reliability contract

## Blocking tests

- Exact worksheet set and ordered columns.
- Non-null and unique business keys for each of the 12 tables.
- Employee, department and location key references to their dimensions.
- Hire/Termination events consistent with employee employment dates/status.
- Nonnegative headcount and FTE within headcount bounds.
- Nonnegative recruitment counts and valid numeric/date types.
- Database row count for each raw table equals its normalized source row count.

Any block failure aborts loading and adds an audited FAILED batch. If the input was pre-validated, the database `COPY`/replacement is still protected by a single transaction.

## Non-blocking known source anomalies

- Historical HC reconciliation: compute the number of mismatched months dynamically and retain REVIEW status rather than adjusting any source values.
- Incomplete source DimDate: keep the derived 2018–2025 calendar separate.
- Salary-budget semantics: leave the variance KPI disabled until currency, period and population are confirmed.
- Internal transfers: no transfer events; disable mobility KPI.

## How to verify end-to-end

```powershell
Set-Location D:\Workforce_Management
python -m unittest discover -s tests -p "test_*.py" -v
$env:HR_INTEGRATION_TESTS = "1"
python -m unittest discover -s tests -p "test_phase2_integration.py" -v
Remove-Item Env:HR_INTEGRATION_TESTS
python -m src.phase2.ingest --force
```

The integration suite tests all 12 table counts, repeated-load SKIPPED behavior, mid-COPY rollback, corrupt workbook audit, duplicate business keys, missing foreign keys, corrected-source replacement, same-row-count database tampering, report failure after commit, and source checksum changes during read.

## Limits

- This is **full-snapshot batch ingestion**, not incremental CDC or streaming.
- Identical-source skip verifies both row counts and all raw column values; it repairs manual data mutations that preserve counts. This is intentional for the ~30k-row dataset, but may become expensive for much larger datasets.
- Database audit and filesystem reporting are intentionally separate: a local report error is surfaced as a warning, not as a failed database load.
- SQL raw schemas retain the source grain. dbt staging/marts, dimensional history and Power BI belong in Phase 3+.
- Source license and any external publication of HR details still require confirmation.
