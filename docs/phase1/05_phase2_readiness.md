# Phase 1.5 — Decision Log and Phase 2 Handoff

## Architectural decision records
- ADR-001: PostgreSQL + Python + dbt Core for small dataset; no Spark/Kafka in base MVP.
- ADR-002: Three storage schemas `raw`, `staging`, `marts`, with controlled transformations.
- ADR-003: Month-end headcount/FTE is semi-additive: never sum across months.
- ADR-004: No fabricated employee-level monthly fact from aggregated snapshot.
- ADR-005: Historical employee attributes not reconstructible without change events; no SCD2 claims.
- ADR-006: Treat raw workbook as immutable; source duplication handled through checksum/load batch metadata.

## Open questions / decisions to verify
- Why 2024/2025 snapshot HC exceeds employee-event-derived HC by five?
- Is `BudgetedSalaryCost` annual salary run-rate or another unit/currency/time basis?
- Do summary recruitment measures represent month-end open stock or monthly flow?
- What is the exact interpretation of `ResponseRatePct` at survey-row grain?
- Should 2018–2022 hiring history be shown? If yes, extend DimDate before modeling.

## Phase 2 prioritized work
1. Configure PostgreSQL Docker Compose + schemas: `raw`, `staging`, `marts`, `audit`.
2. Create metadata tables: `audit.load_batches`, `audit.source_files`, `audit.quality_results`.
3. Python ingestion: validate headers, normalize dates, load all 12 raw tables transactionally.
4. Add source checksums and idempotent MERGE/replace policies per table.
5. Prove row reconciliation against `source_inventory.csv` and rerun without duplicate rows.
6. Separate errors from expected nulls; keep exceptions visible.

## Phase 2 exit criteria
- PostgreSQL loads all 12 tables and row counts equal Phase 1 baseline.
- No unexplained missing business keys; the audit logging captures failures.
- Pipeline reruns deterministically; source file remains untouched.
- A short README documents environment startup and ingestion commands.

## Updated handoff after evidence-based review

- **Headcount:** June 2025 +98 gap precisely equals 98 June exits in D002–D005, followed by July plan resets. Smaller mismatches remain in other months. In Phase 2, maintain separate snapshot and date-based populations and expose reconciliation flags; do not silently adjust source counts.
- **Date dimension:** A local, generated daily calendar now spans 2018-01-05 through 2025-12-31. Use this instead of the incomplete source calendar in curated marts.
- **Salary budget:** Currency for compensation is EUR; budget currency/annualization and scope are not explicit. Keep salary budget variance disabled pending business validation.
- **Transfers:** No historical transfer events are present. Remove internal mobility from Phase 2 acceptance criteria rather than creating invented transitions.
- **Public repo hygiene:** Raw Excel and derived employee-level data are ignored; column-level sample values are redacted from aggregate reports.
- **Acceptance gates:** `python src/phase1/run_phase1.py` succeeds with six tests; no personally identifiable row-level files are staged for Git.
