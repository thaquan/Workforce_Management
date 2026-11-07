# Phase 3 Runbook — Windows, PostgreSQL and dbt Core

## Prerequisites

- Git checkout of this project with Phase 2 completed.
- Docker Desktop (Linux engine) running PostgreSQL 17.
- Local ignored `.env` with `POSTGRES_PASSWORD` and optional host, port,
  user and database overrides.
- The source Excel stored locally at
  `data/raw/HR_Workforce_Planning_Attrition_Dataset.xlsx`
  (not included in Git).
- Python 3.13 was used in the verified run; Python 3.10+ with compatible
  dbt packages may also work but is not explicitly tested here.

## Reproduce

```powershell
Set-Location D:\Workforce_Management

# Prepare your ignored .env and original Excel before first use.
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dbt.txt

docker compose up -d postgres
python -m src.phase2.ingest

python -m src.phase3.generate_staging
python -m src.phase3.dbt_runner debug
python -m src.phase3.dbt_runner parse
python -m src.phase3.dbt_runner build
python -m src.phase3.dbt_runner docs generate
```

The local runner `src/phase3/dbt_runner.py` reads PostgreSQL environment
variables from `.env` but does not print the password. The dbt profile
references `env_var('POSTGRES_PASSWORD')`; no credentials belong in YAML
or Git.

To view dbt Docs and the model lineage locally:

```powershell
python -m src.phase3.dbt_runner docs serve --port 8080
```

Browse `http://localhost:8080`. The generated `dbt_hr/target/`
manifest and catalog are deliberately ignored by Git.

## Automated verification

```powershell
# All non-database Python tests (Phase 1, 2 and 3).
python -m unittest discover -s tests -p "test_*.py" -v

# Phase 3 integration tests; read-only queries against a built warehouse.
$env:HR_PHASE3_INTEGRATION_TESTS="1"
python -m unittest discover -s tests -p "test_phase3_modeling.py" -v
Remove-Item Env:HR_PHASE3_INTEGRATION_TESTS
```

The Phase 2 integration suite is separate and performs **database mutations
with restoration**; do not run it against production data. Phase 3 integration
tests are read-only. dbt's own tests run as part of `dbt build`.

## Troubleshooting

| Symptom | Resolution |
|---|---|
| `POSTGRES_PASSWORD` missing | Configure ignored `.env`, do not commit it |
| `dbt.exe` not found | Install `requirements-dbt.txt` into `.venv` |
| `dbt debug` connection failure | Check `docker compose ps` and local port 5433 |
| Raw relation missing | Run Phase 2 ingestion with local workbook |
| dbt test failure on headcount | Review upstream source reconciliation; no auto-fix |
| Salary budget KPI absent | Intentionally blocked until source units are validated |
| `dbt docs` not available on GitHub | Generated target directory intentionally excluded |

## Release hygiene

Before publishing: `git status --short`, `git diff --check`,
`git check-ignore -v .env data/raw/HR_Workforce_Planning_Attrition_Dataset.xlsx
dbt_hr/target/manifest.json`, and `git ls-files` checks for private inputs.

Do not upload the workbook, raw database volumes, `.env`, the employee-level
contents of dimensions/facts or public screenshots containing employee rows.
