# Phase 9 - Synthetic Performance Benchmark and Query Optimization

Phase 9 adds a **reproducible performance experiment**, not a production benchmark or a claim about the real employee workbook. It compares two PostgreSQL **in-database DML** strategies, and measures DuckDB analytical SQL over compressed Parquet created from identical deterministic fictional rows.

## What is being measured?

- Six numeric synthetic columns: fictional employee number, department, location, month, integer salary cents, integer FTE thousandths.
- 40 departments, 10 locations and 36 month buckets.
- A baseline size N, updated employees every 20th record (5%), and N/100 inserted records (1%).
- Final identical records contain N + N/100 rows. At N=1M, the change set is only 60K rows.
- **Full rebuild**: PostgreSQL TEMP table TRUNCATE + INSERT SELECT of all final records (measured together, including transaction).
- **Incremental**: start from the same baseline, then INSERT ... ON CONFLICT UPDATE for just 5% updates + 1% inserts (measured together, including transaction).
- **Correctness**: compare every PostgreSQL row and column via FULL OUTER JOIN. The SQL aggregation must also agree across PostgreSQL and DuckDB.
- **Query optimization**: a selective department/month count and two SUMs, measured before/after a composite PostgreSQL index; EXPLAIN operations captured. A new index is not presumed to be faster.
- **Parquet analytics**: DuckDB generates final-state ZSTD Parquet and reads it directly using the same query semantics. The Parquet generation time is reported separately from its filtered query.
- **Instrumentation**: 1 warm-up query, 2-10 measured samples, median and descriptive interpolated p95, index build milliseconds, TEMP relation bytes and Parquet bytes. Python client CPU/RSS are labelled as **client-only**, not PostgreSQL server CPU or memory.

The PostgreSQL test is a **controlled SQL DML workload**, not actual external file ingestion, batch ETL, streaming CDC, or a full-stack database-to-Power BI refresh. Full vs incremental ratios are not comparable to the whole previous HR ETL pipeline.

## Safety contract

The CLI defaults to **plan** and cannot connect to PostgreSQL in that mode. DuckDB-only mode writes temporary generated Parquet under ignored .phase9_runtime and requires no database.

PostgreSQL compare mode requires **all**:

- Explicit CLI --allow-disposable-db flag (sets HR_PHASE9_ALLOW_WRITE=YES)
- HR_PHASE9_DISPOSABLE_ACK=YES
- HR_SYNTHETIC_DB=YES
- POSTGRES_HOST=localhost or 127.0.0.1, POSTGRES_PORT=5433, POSTGRES_DB=workforce_ci
- Actual PostgreSQL SELECT current_database() result must equal workforce_ci

The compare runner creates **session-scoped TEMP tables only**. No permanent schemas, actual raw/marts/audit tables, real workbook or Power BI report are read or modified. Temporary tables vanish on connection close. Do not use a valued database despite the guard; the script is intended for a fresh, disposable local PostgreSQL container.

**Do not commit** .env, PostgreSQL passwords, synthetic source files, generated .parquet exports or connection logs.

## Prerequisites

Windows PowerShell from D:\Workforce_Management or a Linux shell with equivalent environment values. Python 3.13 and the Phase 7 local environment already contain PostgreSQL and PyArrow dependencies:

    .\.venv-phase7\Scripts\python.exe -m pip install -r requirements-phase9.txt

### Step 1: Safe offline plan and tests

    .\.venv-phase7\Scripts\python.exe -m src.phase9.run --mode plan --rows 100000 500000 1000000 --repeats 3
    .\.venv-phase7\Scripts\python.exe -m unittest discover -s tests -p "test_phase9_*.py" -v

The PostgreSQL integration suite skips unless explicitly authorized.

### Step 2: DuckDB/Parquet comparison scales (no PostgreSQL required)

    .\.venv-phase7\Scripts\python.exe -m src.phase9.run --mode duckdb --rows 100000 500000 1000000 --repeats 3

The CLI writes aggregate timings to a JSON file under .phase9_runtime; generated source Parquet is removed automatically. Runtime JSON files are ignored by Git.

### Step 3: Optional isolated PostgreSQL comparison

Use only a **new disposable PostgreSQL 17 container** with memory-backed data and a free 5433 port. Verify that you are not replacing an existing Docker container or touching any named persistent volume.

    docker run -d --rm --name hr-phase9-disposable --tmpfs /var/lib/postgresql/data -p 127.0.0.1:5433:5432 -e POSTGRES_DB=workforce_ci -e POSTGRES_USER=hr_etl -e POSTGRES_PASSWORD=phase9_disposable_only postgres:17-alpine

    $env:POSTGRES_HOST = "127.0.0.1"
    $env:POSTGRES_PORT = "5433"
    $env:POSTGRES_DB = "workforce_ci"
    $env:POSTGRES_USER = "hr_etl"
    $env:POSTGRES_PASSWORD = "phase9_disposable_only"
    $env:HR_SYNTHETIC_DB = "YES"
    $env:HR_PHASE9_DISPOSABLE_ACK = "YES"

    .\.venv-phase7\Scripts\python.exe -m src.phase9.run --mode compare --allow-disposable-db --rows 100000 500000 1000000 --repeats 3

Run lower scales first if RAM/CPU is limited. 1M is an **opt-in local workload**, not a CI default. For the isolated 2K-row integration check:

    $env:HR_PHASE9_ALLOW_WRITE = "YES"
    $env:HR_PHASE9_INTEGRATION_TESTS = "YES"
    .\.venv-phase7\Scripts\python.exe -m unittest discover -s tests -p "test_phase9_postgres.py" -v

Stop only this named disposable container when finished:

    docker stop hr-phase9-disposable

The runtime includes PostgreSQL server and Python process effects, but client-only psutil RSS/CPU **does not capture PostgreSQL server CPU/memory**.

### Step 4: Build the local results dashboard

    $files = Get-ChildItem .phase9_runtime -Filter 'benchmark_*.json' | Sort-Object Name | ForEach-Object FullName
    .\.venv-phase7\Scripts\python.exe -m src.phase9.report --inputs $files --overwrite

This generates aggregate-only CSV and a self-contained offline HTML dashboard under reports/phase9. It explicitly says when PostgreSQL was **not measured** at a scale. Do not substitute sample numbers for actual local PostgreSQL observations.

## Evidence captured 2026-11-13

| Baseline | Final rows | ZSTD Parquet | DuckDB filtered query median | PostgreSQL full / incremental |
|---:|---:|---:|---:|---|
| 1,000 | 1,010 | 5,925 B | 5.953 ms | 8.793 / 6.407 ms (2 reps, smoke only) |
| 100,000 | 101,000 | 329,588 B | 6.703 ms | Not measured locally |
| 500,000 | 505,000 | 1,480,218 B | 13.262 ms | Not measured locally |
| 1,000,000 | 1,010,000 | 2,916,059 B | 21.101 ms | Not measured locally |

The 1,000-row PostgreSQL comparison passed all-column/all-row parity and DuckDB query parity. PostgreSQL EXPLAIN used a Seq Scan without the composite index and an Index Scan afterward; the median at this small scale was 1.931 ms without the index and 2.056 ms with it. **Do not conclude the index improves this workload at small scale.**

The compressed Parquet sizes are artificially small because the source values are simple, repeated arithmetic formulas, unlike real-world HR text and dates. Measurements are single-machine, warm-ish query samples and small N, not robust p95/SLO or cross-machine normalized rankings. No speedup is claimed for 100K/500K/1M PostgreSQL because those tests have not completed.

For the aggregate dashboard, open reports/phase9/benchmark_dashboard.html locally. Source: reports/phase9/benchmark_results.csv.

## Acceptance criteria

- No real data, private workbook or project warehouse access.
- Plan and DuckDB modes never connect to PostgreSQL.
- PostgreSQL requires explicit disposable flags and verifies connected database.
- Full rebuild and selective UPSERT begin from equal baselines; temp tables only.
- PostgreSQL final state checked across **all rows and columns**.
- DuckDB/Parquet query aggregate equals PostgreSQL for each compare mode scale.
- Different scales do not overwrite source files; generated Parquet removed after runs.
- Timing repetitions and descriptive statistics published with full workload caveats.
- CI installs dependencies, runs offline correctness and DuckDB smoke; never runs a 1M database benchmark.

## Next extension

A separately approved, comparable **file-to-PostgreSQL ingestion benchmark** would need real COPY / streaming pipelines, disk and process memory/CPU instrumentation, change rates, cold/warm cache control, a predeclared SQL workload and more repetitions. Real production CDC or historical HR update behavior cannot be inferred from the synthetic results.
