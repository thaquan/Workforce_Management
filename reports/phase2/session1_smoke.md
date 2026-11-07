# Phase 2 / Session 1 — Local smoke evidence

Environment: Windows PowerShell, Docker Desktop Linux engine, `postgres:17-alpine`.
Project: `D:\Workforce_Management`. No HR data was loaded by session 1.

| Command | Exit code | Observed evidence |
|---|---:|---|
| `python -m compileall -q src\phase1 tests` | 0 | Python sources compile |
| `python -m unittest discover -s tests -p test_phase2_foundation.py -v` | 0 | 6/6 foundation tests OK |
| `python -m unittest discover -s tests -p test_phase1_review.py -v` | 0 | 6/6 Phase 1 regression tests OK |
| `docker compose config -q` | 0 | Compose configuration valid |
| `docker compose up -d postgres` | 0 | Container created and started |
| `docker compose exec -T postgres pg_isready -U hr_etl -d workforce_dw` | 0 | Accepting connections |
| `psql ... information_schema.schemata` | 0 | raw, staging, marts, audit |
| `psql ... information_schema.tables` | 0 | load_batches, quality_results, source_files |
| Re-run `sql/00_bootstrap.sql` two times through `psql -v ON_ERROR_STOP=1` | 0, 0 | All CREATE IF NOT EXISTS statements skipped existing objects |
| `psql ... COUNT(*)` on three audit tables | 0 | All three counts 0 (expected before ingestion) |
| `git check-ignore -v .env data/raw/...xlsx data/processed/...csv` | 0 | Local secrets and HR row data ignored |
| `git diff --check` | 0 | No whitespace errors |

**Verification boundary:** This evidence is from AGENT EXECUTION, not Agent Verification. Independent verification must run its own checks and create `done_verified_1.json`. No Phase 2 ingestion data was loaded, and no Git push was attempted.
