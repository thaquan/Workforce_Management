# Phase 4 Runbook — End-to-End Quality and Monitoring

## Prerequisites

- Phase 1–3 checked out and verified; local `.env` with PostgreSQL
  credential, untouched HR Excel under `data/raw/`, and Docker Desktop.
- `python -m pip install -r requirements.txt -r requirements-dbt.txt`
  and a project-local `.venv` for dbt. No paid cloud tools required.
- PostgreSQL 17 accessible on the local-only port configured in
  `compose.yaml` (typically `127.0.0.1:5433`).

## Full pipeline

```powershell
Set-Location D:\Workforce_Management
docker compose up -d postgres
python -m src.phase4.pipeline
python -m src.phase4.health
```

The command uses an audited Python ingestion run, executes the normal
`dbt build` (including all 83 tests on the real workbook), runs 18
post-build quality checks, records metrics and writes the aggregate-only
Markdown health report.

For a read-only data validation without rerunning ingestion/dbt:

```powershell
python -m src.phase4.pipeline --quality-only
```

In the verified historical source, PASS=14, REVIEW=4, FAIL=0 is expected.
Exit code is **0** for SUCCEEDED (including non-blocking REVIEW) and **2**
when a blocking quality failure occurs. PostgreSQL connectivity failures
can also prevent audit insertion and must be handled as failed executions.

## Tests

```powershell
# Safe offline unit suite. Live integration suites are disabled unless
# their dedicated environment flags are set.
python -m unittest discover -s tests -p "test_*.py" -v

# Phase 4 quality contract, no live database mutation.
python -m unittest discover -s tests -p "test_phase4_quality.py" -v
```

The synthetic failure tests must be run only in
`workforce_ci` as described in
[CI and isolated testing](03_ci_workflow.md).

## Observability and recovery decisions

- Unexpected `FAILED`: inspect run stage, the failed gate IDs and
  `dbt_hr/logs/` locally. Do not copy rows with employee details into
  public issue reports.
- Long-running `RUNNING` over two hours: the monitor reports it, but
  manual intervention is required; check whether the process is alive.
- Report file I/O failure: pipeline audit remains authoritative.
- Source freshness: use timestamps from `audit.load_batches` and
  `audit.pipeline_runs`; a historical 2025 event is not inherently stale.
- dbt mid-build failure: rerun the build after fixing the issue, because
  the entire warehouse isn't a single atomic transaction.
- After a successful recovery, rerun quality checks, verify
  `audit.pipeline_runs.status='SUCCEEDED'`, and only then refresh BI.

## Not included in Phase 4

No always-on scheduler, automatic email notification, new cloud monitoring
account, or live Power BI dashboard is configured. Production-scale data
observability and orchestration are future enhancements.

## Security before Git push

```powershell
git check-ignore -v .env data/raw/HR_Workforce_Planning_Attrition_Dataset.xlsx
git check-ignore -v dbt_hr/target/manifest.json
git ls-files -- .env data/raw/HR_Workforce_Planning_Attrition_Dataset.xlsx
git diff --check
```

No private workbook bytes, live HR records, environment passwords or dbt
compiled artifacts should be present in the committed file list.
