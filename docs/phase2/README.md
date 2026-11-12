# Phase 2 — PostgreSQL ingestion

**Status:** Implemented and tested locally. Raw Excel remains immutable and excluded from Git.

## Delivered

1. [Environment setup](01_environment_setup.md): PostgreSQL 17, Docker Compose, four schemas, audit tables.
2. [Python ingestion](02_ingestion.md): explicit 12-sheet schema contract, typed COPY, SHA-256, atomic full load, run logs.
3. [Quality and idempotency](03_quality_and_idempotency.md): blocking rules, source REVIEW issues, repeat-run/rollback tests.
4. [Verification checklist](../../reports/phase2/verification_checklist.md): observed pass/fail evidence and known limitations.
5. [Code review and fixes](04_code_review_fixes.md): release risks, remediation and regression evidence.

## Quick start

```powershell
Set-Location D:\Workforce_Management
python -m pip install -r requirements.txt
docker compose up -d postgres
python -m src.phase2.ingest
```

The CLI returns `SUCCEEDED` on first/forced load or `SKIPPED` when an identical source has already been loaded and all raw row contents match. A post-commit report problem returns `SUCCEEDED` with `report_warning`.

## Raw source-to-warehouse contract for Phase 3

- Each of the 12 source sheets maps to one `raw.<snake_case_sheet_name>` table.
- Source column names are converted to snake_case, including `EmployeeID -> employee_id`, `FTE -> fte`, `Date -> date`.
- Source data types map to PostgreSQL `DATE`, `INTEGER`, `NUMERIC(20,6)` or `TEXT`.
- Raw tables retain original business grain; especially `fact_monthly_snapshot` has no employee key.
- dbt staging should reference raw tables via `sources.yml`, build conformed dimensions/marts without joining facts at mismatched grain.
- dbt dimension for reporting dates must use the derived extended calendar (2018–2025), not claim source `raw.dim_date` covers early hires.
- Retain monthly headcount-reconciliation flags; no silent adjustments to snapshot headcount.
- Salary budget variance and internal mobility KPI stay disabled until external business evidence exists.

## Project boundaries

This phase is a repeatable full-snapshot batch pipeline. It does not implement CDC, Kafka, Spark, streaming, dbt transformations or Power BI. Those are intentionally separate milestones.
