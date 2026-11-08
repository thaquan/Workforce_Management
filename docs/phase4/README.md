# Phase 4 — Data Quality, Monitoring & Operational Validation

**Purpose:** Validate and monitor the local PostgreSQL + dbt HR warehouse
before Power BI consumes it. The source workbook and raw employee records
remain private and are never committed.

## Delivered

1. [Quality contract](01_quality_contract.md): 18 executable quality gates,
   a documented BLOCK vs REVIEW policy, and raw-to-marts reconciliation.
2. [Monitoring and recovery](02_monitoring_recovery.md): PostgreSQL audit
   tables, persisted run outcomes, duration/freshness metrics, and alerts
   discoverable through CLI queries.
3. [CI with synthetic data](03_ci_workflow.md): GitHub Actions workflow using
   an isolated PostgreSQL service with only invented HR sample records.
4. [Execution runbook](04_runbook.md): commands, failure behavior, validation
   strategy, and safe operational boundaries.
5. [Acceptance evidence](../../reports/phase4/acceptance_report.md):
   full real-data E2E and local synthetic CI results.

## End-to-end commands

```powershell
Set-Location D:\Workforce_Management
docker compose up -d postgres
python -m src.phase4.pipeline
python -m src.phase4.health
```

The full pipeline runs the existing **Python ingestion → dbt build (36 models,
83 data tests) → 18 quality gates**. It records results in PostgreSQL
`audit.pipeline_runs`, `audit.data_quality_results` and
`audit.pipeline_metrics`.

No cloud monitoring subscription or paid service is required. GitHub Actions
executes tests on an invented dataset; it does not connect to the local HR
database or download the source Excel.
