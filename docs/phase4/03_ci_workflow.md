# Phase 4 CI — GitHub Actions With Synthetic PostgreSQL

Workflow: `.github/workflows/quality-ci.yml`, triggered on pushes to
`main` and pull requests. Uses an ephemeral GitHub Actions service
`postgres:17-alpine`, Python 3.13, `dbt-core==1.12.6`,
`dbt-postgres==1.11.0` and `psycopg`.

## CI tasks

1. Checkout *only* tracked source code; no original Excel, `.env`,
   private PostgreSQL volume or employee-level datasets are stored in Git.
2. Run offline Phase 2, 3 and 4 contract tests.
3. Create exactly 12 tiny raw tables (22 fabricated records total)
   inside a database named `workforce_ci`.
4. Build 36 dbt models and run **80 generic/dbt custom tests**.
   Three `full_baseline` tests are excluded because they assert historical
   counts only valid for the original private workbook.
5. Run the same 18 persisted Phase 4 quality gates.
6. Execute isolated corruption, duplicate-key, corrupt-file,
   schema-drift, stuck-run and restoration tests.
7. Generate local dbt documentation and lineage artifacts.

The fixture writer refuses to run unless **both**
`POSTGRES_DB=workforce_ci` and `HR_SYNTHETIC_DB=YES` are set.
The CI password is a disposable local service-container credential, not
the user's local/private PostgreSQL password.

## Local reproduction using an isolated database

For CI parity, create a **separate disposable database** named
`workforce_ci` on the PostgreSQL container; do not rename or overwrite
`workforce_dw` or its raw data.

```powershell
Set-Location D:\Workforce_Management
$env:POSTGRES_DB = "workforce_ci"
$env:HR_SYNTHETIC_DB = "YES"
$env:HR_PHASE4_ISOLATED_TESTS = "YES"

python -m src.phase4.synthetic_fixture
python -m src.phase3.dbt_runner build --exclude tag:full_baseline
python -m src.phase4.pipeline --quality-only
python -m unittest discover -s tests -p test_phase4_recovery.py -v

Remove-Item Env:POSTGRES_DB
Remove-Item Env:HR_SYNTHETIC_DB
Remove-Item Env:HR_PHASE4_ISOLATED_TESTS
```

CI guards are intentionally strict. The real workbook is unavailable
to GitHub Actions, so this workflow verifies SQL/pipeline **logic** and
fault handling, not whether the private workbook's historical metrics
are accurate. Those baseline assertions run separately in the local
real-data pipeline.

## Operational limits

Hosted GitHub Actions' result should be checked in the repository's
**Actions** tab after each push. Local synthetic CI rehearsal proves the
workflow's commands are runnable but does not, on its own, prove a hosted
GitHub runner completed successfully.
