# Phase 7 - Dagster OSS orchestration

This extension provides an auditable Dagster asset graph using only invented synthetic HR data. It does not run the private-workbook pipeline.

## Graph

source_preflight -> raw_ingested -> dbt_marts_built -> quality_gates_checked -> report_ready

1. Source preflight: deterministic fixture SHA-256, 22 invented rows and latest historical period (2023-02).
2. Raw ingestion: compare normalized fixture with raw tables; skip an unchanged fixture, or seed the disposable synthetic DB after explicit approval.
3. dbt marts: run existing dbt models and non-baseline tests; output goes to ignored .phase7_runtime/dbt_target.
4. Quality gates: reuse Phase 4 quality-only audited execution and write the health report to ignored .phase7_runtime/phase7_health.md, not the tracked report.
5. Report-ready: emit a Dagster marker only when upstream steps and blocking quality gates succeed. This does NOT refresh Power BI.

The Dagster run ID and Phase 4 quality-only pipeline_run_id are separate audit IDs. REVIEW findings remain visible; FAIL blocks the marker.

## Offline setup (no database writes)

Run from the repository root in PowerShell:

~~~powershell
python -m venv .venv-phase7
.\.venv-phase7\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dbt.txt -r requirements-dagster.txt
.\.venv-phase7\Scripts\python.exe -m unittest discover -s tests -p "test_phase7_*.py" -v
.\.venv-phase7\Scripts\python.exe -m src.phase7.run
~~~

The final command defaults to dry_run and materializes five PLANNED assets without connecting to PostgreSQL. Local Dagster state is stored in ignored .phase7_runtime.

To inspect the UI, first run the dry-run, then:

~~~powershell
$env:DAGSTER_HOME = (Resolve-Path .phase7_runtime).Path
.\.venv-phase7\Scripts\dagster.exe dev -m src.phase7.definitions
~~~

Browse http://localhost:3000. The workforce_manual job is available. The Monday 07:00 Asia/Ho_Chi_Minh schedule is STOPPED by default. A schedule only works while the local Dagster daemon, machine and database are available.

## Disposable synthetic PostgreSQL example

Never use the existing Compose database or an existing PostgreSQL volume for this demonstration. Verify localhost port 5433 and the specified container name are free before running. The first/changed fixture load may truncate synthetic raw tables.

~~~powershell
# Only if 5433 is free:
docker run -d --rm --name hr-phase7-disposable --tmpfs /var/lib/postgresql/data -p 127.0.0.1:5433:5432 -e POSTGRES_DB=workforce_ci -e POSTGRES_USER=hr_etl -e POSTGRES_PASSWORD=phase7_disposable_only postgres:17-alpine

$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_PORT = "5433"
$env:POSTGRES_DB = "workforce_ci"
$env:POSTGRES_USER = "hr_etl"
$env:POSTGRES_PASSWORD = "phase7_disposable_only"
$env:HR_SYNTHETIC_DB = "YES"

.\.venv-phase7\Scripts\python.exe -m src.phase7.run --mode synthetic --allow-disposable-reset

# Repeat to demonstrate unchanged fixture SKIPPED_UNCHANGED behavior.
# Stop only this disposable container when finished.
docker stop hr-phase7-disposable
~~~

The CLI requires the explicit flag, the HR_SYNTHETIC_DB marker, a local endpoint and POSTGRES_DB=workforce_ci; it also queries the connected database name before any write. It refuses workforce_dw even with an allow flag. No private workbook is accessed.

## Reliability and known boundaries

- Transient connection failures request at most two retries; schema errors, dbt failure and blocking quality failures do not retry.
- Idempotent identical-fixture checks prevent duplicate raw business effects; exactly-once delivery is not claimed.
- Source latest period is historical, not the Dagster run timestamp.
- Run records and dbt artifacts are ignored by Git. The Phase 4 tracked health report is not modified.
- The authoritative private-workbook entrypoint remains: python -m src.phase4.pipeline.
- Power BI Service refresh remains independent of Dagster; no gateway/API refresh is configured.
- Offline tests and a throwaway synthetic PostgreSQL service run in GitHub CI.

## Verification

~~~powershell
.\.venv-phase7\Scripts\python.exe -m pip check
.\.venv-phase7\Scripts\python.exe -m unittest discover -s tests -p "test_phase7_*.py" -v
.\.venv-phase7\Scripts\python.exe -m src.phase7.run --mode dry_run
~~~
