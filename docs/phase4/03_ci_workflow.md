# Phase 4 CI — GitHub Actions With Synthetic PostgreSQL

Workflow: `.github/workflows/quality-ci.yml`, triggered on pushes to
`main` and pull requests. Uses an ephemeral GitHub Actions service
`postgres:17-alpine`, Python 3.13, `dbt-core==1.12.6`,
`dbt-postgres==1.11.0` and `psycopg`.

## CI tasks

1. Checkout *only* tracked source code; no original Excel, `.env`,
   private PostgreSQL volume or employee-level datasets are stored in Git.
2. Run offline Phase 2, 3, 4 contract tests **plus all Phase 5 semantic
   model/PBIR tests** (46 tests for the six-page report at initial release).
3. Create exactly 12 tiny raw tables (22 fabricated records total)
   inside a database named `workforce_ci`.
4. Build 36 dbt models and run **80 generic/dbt custom tests** using the
   `dbt` executable installed on the GitHub-hosted runner's PATH.
   Three `full_baseline` tests are excluded because they assert historical
   counts only valid for the original private workbook.
5. Run the same 18 persisted Phase 4 quality gates.
6. Execute isolated corruption, duplicate-key, corrupt-file,
   schema-drift, stuck-run and restoration tests.
7. Generate dbt documentation and lineage artifacts with the same
   system-installed `dbt` command. The job uses read-only GitHub token
   permissions and a 20-minute timeout.

The fixture writer refuses to run unless **both**
`POSTGRES_DB=workforce_ci` and `HR_SYNTHETIC_DB=YES` are set.
The CI password is a disposable local service-container credential, not
the user's local/private PostgreSQL password.

## Local reproduction using an isolated database

For CI parity, use a **separate disposable PostgreSQL container** with a
different local port. Do not rename, truncate, or overwrite your real
`workforce_dw` database.

```powershell
Set-Location D:\Workforce_Management
docker run --name workforce-ci-synthetic-validation -d `
  -e POSTGRES_DB=workforce_ci -e POSTGRES_USER=hr_etl `
  -e POSTGRES_PASSWORD=synthetic_ci_only_password `
  -p 127.0.0.1:15433:5432 postgres:17-alpine
# Wait until docker exec workforce-ci-synthetic-validation
# pg_isready -U hr_etl -d workforce_ci returns ready.
$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_PORT = "15433"
$env:POSTGRES_DB = "workforce_ci"
$env:POSTGRES_USER = "hr_etl"
$env:POSTGRES_PASSWORD = "synthetic_ci_only_password"
$env:HR_SYNTHETIC_DB = "YES"
$env:HR_PHASE4_ISOLATED_TESTS = "YES"

python -m src.phase4.synthetic_fixture
.\.venv\Scripts\dbt.exe build --project-dir dbt_hr --profiles-dir dbt_hr --exclude tag:full_baseline
python -m src.phase4.pipeline --quality-only
python -m unittest discover -s tests -p test_phase4_recovery.py -v
python -m unittest discover -s tests -p 'test_phase5_*.py' -v
.\.venv\Scripts\dbt.exe docs generate --project-dir dbt_hr --profiles-dir dbt_hr

# Stop/remove ONLY the disposable synthetic container you created.
docker rm -f workforce-ci-synthetic-validation
@('POSTGRES_HOST','POSTGRES_PORT','POSTGRES_DB','POSTGRES_USER',
  'POSTGRES_PASSWORD','HR_SYNTHETIC_DB','HR_PHASE4_ISOLATED_TESTS') |
  ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }
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

### Hosted CI troubleshooting history (November 2026)

- Earlier Actions runs were blocked before job startup due to an account
  billing authorization issue. This is separate from data-pipeline logic.
- [Run 43141858026](https://github.com/thaquan/Workforce_Management/actions/runs/43141858026)
  started a runner on **2026-11-12** but failed at the **dbt build** step.
  The workflow had installed dbt into the runner's Python environment while
  invoking a helper that expected a project-local `.venv/bin/dbt`.
- The workflow now calls the installed `dbt` binary directly for build
  and docs, and adds offline Phase 5 checks. The corrected sequence passed
  a **local isolated synthetic trial** (116/116 dbt build steps, 6/6 recovery
  tests and 46/46 Phase 5 tests).
- Hosted results must be verified in the GitHub Actions tab after pushing;
  local checks alone do not prove the hosted workflow is green.
