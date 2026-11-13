# Phase 9 - Validation and Benchmark Evidence

Date: **2026-11-13**, Vietnam (UTC+07). All generated rows are fictional deterministic integer values with no PII. Local CPU/OS information and source data are not published.

## Validation

| Validation | Result |
|---|---|
| Git branch before Phase 9 | main, clean at 8874ab9 |
| Python runtime | 3.13.15 |
| DuckDB | 1.5.6 |
| psutil | 7.2.2 |
| PostgreSQL | 17.11 (temporary memory-backed test container) |
| Database access default | Safe plan mode; no connection |
| DuckDB 100K, 500K, 1M | Completed locally (3 timed samples each) |
| PostgreSQL 1K full rebuild vs selective UPSERT | Completed locally (2 timed samples), exact row/column parity |
| PG before/after index EXPLAIN | Seq Scan before, Index Scan after on the 1K smoke test |
| Full PostgreSQL 100K/500K/1M | **NOT VERIFIED**; local large-run invocation was blocked |
| Phase 9 offline unit tests | 14/14 PASS |
| Entire repository offline tests | 120 collected; 91 PASS, 29 gated/integration SKIP |
| Python dependency consistency | pip check: no broken requirements |
| CI-safe DuckDB 10K smoke | PASS, 2 samples, no PostgreSQL connection |
| PostgreSQL 2K manual integration | Not executed; remains gated and skipped |
| Parquet files | Deleted after each run, no actual HR data |
| Hosted GitHub CI | Check the repository Quality Gates workflow run for the pushed commit |

## Measured local aggregates

See benchmark_results.csv and benchmark_dashboard.html for self-contained, PII-free evidence.

| Base N | Final N | Changed N | Parquet bytes | Query median ms |
|---:|---:|---:|---:|---:|
| 1,000 | 1,010 | 60 | 5,925 | 5.953 |
| 100,000 | 101,000 | 6,000 | 329,588 | 6.703 |
| 500,000 | 505,000 | 30,000 | 1,480,218 | 13.262 |
| 1,000,000 | 1,010,000 | 60,000 | 2,916,059 | 21.101 |

The PostgreSQL 1K smoke median was 8.793 ms for TEMP full rebuild and 6.407 ms for TEMP selective UPSERT. Two samples cannot establish a robust speedup; a ratio of 1.372 is **not a portfolio-wide performance claim**. No PostgreSQL scale beyond 1K was validated in this session.

At N=1K, before/after composite-index query medians were 1.931/2.056 ms. The index is **not demonstrated to help** on this tiny dataset. The binary Parquet source compresses unusually well because it contains repetitive integer formulas.

All percentiles are descriptive sample interpolations (N=2 or 3), not SLOs. The report does not measure real file-to-PostgreSQL ingestion, cloud/network throughput, PostgreSQL process memory/CPU, or live Power BI performance.

## Safety

- No real workbooks, Power BI files, raw/marts/audit schemas or valued PostgreSQL volumes accessed.
- PostgreSQL used TEMP tables on a disposable database; no permanent benchmark schema exists.
- CI should use offline-only tests and lightweight DuckDB smoke; its service is reserved for existing synthetic project checks.
- Realistic HR data, names, salaries and identifying attributes are excluded.
