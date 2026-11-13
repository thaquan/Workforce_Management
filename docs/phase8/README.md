# Phase 8 - Synthetic Incremental Ingestion & Parquet

Phase 8 adds an auditable, **synthetic-only** incremental source to HR Workforce Intelligence. It is NOT a production CDC connector, an incremental retrofit of the real workbook, or a Power BI refresh.

## Architecture

    Invented three-batch change stream
                 |
          Immutable Parquet
                 |
      Dagster synthetic_changes_prepared
                 |
       incremental_batches_ingested
       (transactional PostgreSQL)
                 |
       incremental_quality_checked
                 |
       incremental_report_ready
        (no Power BI refresh)

The PostgreSQL schema is **incremental_demo**, and the target database MUST be a disposable local **workforce_ci**. Nothing touches the real raw/staging/marts/audit schemas or Power BI.

## Event and safety contract

Each batch has a fictional ID, a fixed stream name, and ordered events. Each event supplies a fictional event ID, source_offset, employee ID, source_version, UTC event_time, operation and synthetic department/FTE/status. Unexpected fields and non-fictional identifiers are rejected.

- **Watermark:** source_offset is an integer event arrival position, NOT business event time. Fresh offsets must begin at the previous watermark plus one, without gaps.
- **Idempotency:** batch_id plus canonical SHA-256 is immutable. Replaying identical contents returns SKIPPED_UNCHANGED; reusing the ID with different contents fails.
- **Late arrivals:** a higher source offset carrying an older business version is recorded in the event ledger but cannot overwrite newer employee state.
- **Deletes:** logical tombstones, never physical employee deletions.
- **Atomic recovery:** events, employee state, audit and watermark commit together in one PostgreSQL transaction; injected failures roll all back.
- **Privacy:** invented TEST_ IDs and Synthetic departments only. Phase 8 never opens a private HR workbook.
- **Write permission:** requires HR_PHASE8_ALLOW_WRITE=YES, HR_SYNTHETIC_DB=YES, local port 5433, POSTGRES_DB=workforce_ci, and a live connected database name check.

Three fixed batches include eight fictional events, with an update, logical delete, late business event and new employee. The source event timestamp is different from the Dagster run timestamp.

## Safe setup (PowerShell)

From the project root with the existing Phase 7 environment:

    .\.venv-phase7\Scripts\python.exe -m pip install -r requirements-phase8.txt
    .\.venv-phase7\Scripts\python.exe -m unittest discover -s tests -p "test_phase8_incremental.py" -v
    .\.venv-phase7\Scripts\python.exe -m src.phase8.run
    .\.venv-phase7\Scripts\python.exe -m src.phase8.benchmark --rows 10000

The CLI defaults to dry_run and materializes four PLANNED Dagster assets without PostgreSQL writes or Parquet source file writes. All runtime data is under ignored .phase8_runtime. The benchmark tests Parquet read/write only; it is not a database speed comparison.

To inspect the Dagster UI:

    $env:DAGSTER_HOME = (Resolve-Path .phase8_runtime).Path
    .\.venv-phase7\Scripts\dagster.exe dev -m src.phase8.definitions

Visit http://localhost:3000. The incremental_manual job is available; its Monday 08:00 Asia/Ho_Chi_Minh schedule is STOPPED by default. Local scheduling requires a running machine and Dagster daemon. The UI does not authorize writes to workforce_dw.

## Isolated synthetic PostgreSQL demo

WARNING: Never use the existing Compose service, its data volume, or workforce_dw. Confirm localhost port 5433 and the test container name are unused.

    docker run -d --rm --name hr-phase8-disposable --tmpfs /var/lib/postgresql/data -p 127.0.0.1:5433:5432 -e POSTGRES_DB=workforce_ci -e POSTGRES_USER=hr_etl -e POSTGRES_PASSWORD=phase8_disposable_only postgres:17-alpine

    $env:POSTGRES_HOST = "127.0.0.1"
    $env:POSTGRES_PORT = "5433"
    $env:POSTGRES_DB = "workforce_ci"
    $env:POSTGRES_USER = "hr_etl"
    $env:POSTGRES_PASSWORD = "phase8_disposable_only"
    $env:HR_SYNTHETIC_DB = "YES"

    .\.venv-phase7\Scripts\python.exe -m src.phase8.run --mode synthetic --allow-synthetic-write

Repeating the same command must mark all three batches SKIPPED_UNCHANGED while retaining watermark 8. Stop ONLY this disposable test container when finished:

    docker stop hr-phase8-disposable

For integration tests on a fresh disposable workforce_ci database, set HR_PHASE8_ALLOW_WRITE=YES and HR_PHASE8_INTEGRATION_TESTS=YES, then run:

    .\.venv-phase7\Scripts\python.exe -m unittest discover -s tests -p "test_phase8_postgres.py" -v

These tests intentionally inject transaction failures and schema drift, then verify rollback. They must not run on valued databases.

## Acceptance

| Capability | Evidence |
|---|---|
| Dagster | 4 assets; disabled schedule; dry-run does not call PostgreSQL |
| Parquet | Round-trip SHA-256 and immutable batch files |
| Watermark | 0 to 3 to 6 to 8, no gaps or offset reuse |
| Batch replay | SKIPPED_UNCHANGED; no duplicate state or events |
| Recovery | Failure mid-batch leaves ledger, state, audit and watermark unchanged |
| Late event | One old version logged without reverting newer employee state |
| Delete | One logical tombstone |
| Quality | 8 events, 3 batches, 3 active, 1 deleted, 1 late, active FTE 2.55 |
| Isolation | No writes to workforce_dw, raw, marts or PBIR |
| CI | Offline tests and isolated synthetic PostgreSQL integration |

## Limits

The real workbook still uses the Phase 2 full-load pipeline. No real CDC, source-update contract, Power BI Service gateway, inferred transfers or predictive claims were introduced. The historic 33/36 headcount reconciliation REVIEW findings remain unchanged. Large comparative PostgreSQL/Parquet/DuckDB full-reload benchmarks remain future work.
