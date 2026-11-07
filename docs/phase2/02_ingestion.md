# Phase 2 / Session 2 — Excel to PostgreSQL raw ingestion

## Prerequisites

1. Docker Desktop running Linux containers.
2. Local private `.env` configured (never committed).
3. Source workbook under `data/raw/HR_Workforce_Planning_Attrition_Dataset.xlsx`.
4. Python 3.10+ and `python -m pip install -r requirements.txt`.

## Run

```powershell
Set-Location D:\Workforce_Management
docker compose up -d postgres
python -m src.phase2.ingest
```

Force an atomic reload of the same checksum, if needed:

```powershell
python -m src.phase2.ingest --force
```

## Source contract

- **12 worksheets**, exact headers in `src/phase2/schema_contract.py`.
- Column names in PostgreSQL are snake_case; tables are in `raw`, one per worksheet.
- Source date serials are converted to PostgreSQL `DATE`; numbers to `INTEGER` or `NUMERIC(20,6)`.
- Empty source cells become SQL `NULL`; required business keys cannot be null.
- No invented employee-level monthly snapshot: `raw.fact_monthly_snapshot` remains aggregated at Month × Department × Location × Level.
- Business keys are declared as table primary keys; invalid keys/duplicates fail before loading.
- The exact SQL name/type mapping is in `docs/phase2/source_to_raw_mapping.csv`. Regenerate with `python -m src.phase2.schema_contract`. This supersedes Phase 1's preliminary table names.

## Audit and atomicity

- `audit.source_files` stores SHA-256, filename and byte size.
- `audit.load_batches` stores RUNNING / SUCCEEDED / FAILED / SKIPPED, expected and loaded counts.
- `audit.quality_results` records each source rule, including REVIEW flags for known limitations.
- All 12 raw tables are loaded via `COPY` inside **one PostgreSQL transaction**. A failure rolls back all 12 tables.
- Repeated identical checksums yield SKIPPED **only when all 12 raw tables match the source both by row count and by every column value**; `--force` reprocesses.
- Existing raw table columns, types, nullability and primary keys are checked before replacing rows; schema drift blocks the load.
- The source SHA-256 is recalculated after reading the workbook. If the file changed during the read, ingestion is rejected and audited.
- A corrected workbook with a different checksum triggers full atomic replacement (not row-append).
- Failed loads remain in audit, while previous valid raw data remains accessible.
- The report file is written **after** the database transaction. Report I/O failure returns `report_warning` in the CLI result but cannot rewrite an already committed SUCCEEDED batch as FAILED.

## Privacy

The workbook, generated row-level extracts and `.env` are excluded from Git. The public reconciliation report uses aggregate table counts only. Error messages do not include individual employee values.
