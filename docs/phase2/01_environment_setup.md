# Phase 2 / Session 1 — PostgreSQL Foundation

## Scope
Local PostgreSQL 17 in Docker Compose, four schemas (`raw`, `staging`, `marts`, `audit`), and three audit metadata tables. No HR row data is ingested in session 1.

## Prerequisites
- Docker Desktop with **Linux containers** running.
- Python 3.10+ and Git.
- The working directory is `D:\Workforce_Management` on Windows.

## Secure local setup
```powershell
Set-Location D:\Workforce_Management
Copy-Item .env.example .env
# Replace the placeholder password inside .env with a strong random value.
docker compose config -q
docker compose up -d postgres
docker compose ps
```
The PostgreSQL port defaults to `127.0.0.1:5433`. All credentials stay in the locally ignored `.env` file. Do **not** commit `.env`, raw Excel files or employee-level generated datasets.

## Database smoke checks
```powershell
docker compose exec -T postgres pg_isready -U hr_etl -d workforce_dw
docker compose exec -T postgres psql -U hr_etl -d workforce_dw -v ON_ERROR_STOP=1 -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('raw','staging','marts','audit') ORDER BY schema_name;"
docker compose exec -T postgres psql -U hr_etl -d workforce_dw -v ON_ERROR_STOP=1 -c "SELECT table_name FROM information_schema.tables WHERE table_schema='audit' ORDER BY table_name;"
```
Expected: `pg_isready` succeeds, four schemas, three audit tables.

## Idempotent bootstrap
The script `sql/00_bootstrap.sql` runs automatically **only when Docker initializes a fresh, empty PostgreSQL volume**. For an existing volume, re-run it manually:
```powershell
Get-Content -Raw sql/00_bootstrap.sql | docker compose exec -T postgres psql -U hr_etl -d workforce_dw -v ON_ERROR_STOP=1
```
Do not delete or recreate persistent volumes to force reinitialization.

## Local test commands
```powershell
python -m unittest discover -s tests -p test_phase2_foundation.py -v
python -m unittest discover -s tests -p test_phase1_review.py -v
docker compose config -q
```

## Privacy and scope guardrails
- No employee-level data in session 1, and no spreadsheet copied into Git.
- `FactMonthlySnapshot` is aggregated and is not an employee-grain table.
- Continue using Phase 1 review flags. Do not silently alter 33 mismatched months.
- Salary-budget units and transfers remain unsupported until business validation.
- Use the extended derived date calendar in future curated layers; raw source stays immutable.
