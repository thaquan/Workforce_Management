# Phase 4 — Latest Pipeline Health

- Pipeline run: **3**
- Mode: **FULL**
- Status: **SUCCEEDED**
- Quality checks: 14 PASS, 4 REVIEW, 0 FAIL
- Verified at (UTC): 2026-11-08T16:04:01+00:00

Historic workforce exceptions are REVIEW; no employee-level rows are included.
Freshness measures use ingestion audit timestamps, not the last historical event date.

| Quality gate | Status | Affected count | Explanation |
|---|---|---:|---|
| raw_table_count | PASS | 0 | Exactly twelve source tables must be present. |
| staging_view_count | PASS | 0 | All twelve staging and four intermediate views must exist. |
| marts_table_count | PASS | 0 | Five dimensions, eight facts and seven business marts. |
| snapshot_to_mart_rows | PASS | 0 | Source monthly snapshot rows must survive without fanout or loss. |
| employee_to_retention_rows | PASS | 0 | Exactly one retention feature row per source employee. |
| recruitment_to_mart_rows | PASS | 0 | Aggregated recruitment should not duplicate by joins. |
| targets_to_plan_rows | PASS | 0 | Planning mart must remain Month x Department. |
| snapshot_grain | PASS | 0 | The workforce mart has one row per monthly source grain. |
| department_month_grain | PASS | 0 | Attrition mart must not fan out. |
| negative_hc_fte | PASS | 0 | Headcount/FTE value bounds. |
| attrition_logic | PASS | 0 | Terminations and monthly rate denominator agree. |
| retention_post_exit_leakage | PASS | 0 | Retained feature values must precede termination strictly. |
| salary_budget_disabled | PASS | 0 | Unverified budget units must never enable variance KPI. |
| date_coverage | PASS | 0 | Historical events must map into extended date dimension. |
| headcount_reference_mismatch | REVIEW | 33 | Source snapshot and employee-as-of counts disagree; never auto-correct. |
| source_calendar_shortfall | REVIEW | 1 | Source calendar starts after earliest hire; derived dim_date is extended. |
| salary_budget_semantics | REVIEW | 1 | Currency, period, and coverage of salary budget are unverified. |
| no_transfer_events | REVIEW | 1 | Internal transfers cannot be inferred without transfer history. |
