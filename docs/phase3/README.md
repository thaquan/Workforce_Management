# Phase 3 — dbt Analytics Warehouse

Phase 3 transforms the 12 raw HR tables ingested in Phase 2 into tested
star-schema dimensions, facts and business-facing marts in PostgreSQL.
No raw source values or employee-level data are added to Git.

## Deliverables

- **12** staging views, source declarations and 28 staging tests.
- **4** intermediate views for monthly aggregations and reconciliation.
- **5** conformed dimensions and **8** fact tables.
- **7** analytics marts for workforce, attrition, planning, recruitment,
  retention, reconciliation and salary run-rate.
- **83** dbt data tests, plus 11 standalone Python Phase 3 tests
  (six static, five live PostgreSQL).
- dbt Docs catalog/manifest (generated locally and ignored by Git).

See [Architecture and grain](01_architecture_and_grain.md),
[KPI contracts and limitations](02_kpi_semantics.md) and
[Local runbook](03_runbook.md).
The [Phase 3 acceptance report](../../reports/phase3/acceptance_report.md)
records verification evidence.

## What is not implemented

This is a local, batch-oriented **dbt analytics warehouse**. It does not
contain Power BI visuals, employee transfer history, validated budget-to-salary
variance, SCD Type 2 department histories, cloud scheduling or CDC.
These are either future phases or unsupported by the source.
