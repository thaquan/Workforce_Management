# Phase 2 — Ingestion Reconciliation

- Batch ID: 32
- Status: **SUCCEEDED**
- Source checksum SHA-256: `d40a85095faabb4c18517a51c977747c57d7f248d952039ec442923ca5042626`
- Expected row count: **29,728**

| Raw table | Source rows |
|---|---:|
| raw.dim_employee | 1,200 |
| raw.fact_monthly_snapshot | 6,826 |
| raw.fact_employee_events | 1,406 |
| raw.fact_compensation | 2,914 |
| raw.fact_performance | 2,741 |
| raw.fact_engagement | 10,200 |
| raw.fact_absence | 2,755 |
| raw.fact_recruitment | 288 |
| raw.workforce_targets | 288 |
| raw.dim_department | 8 |
| raw.dim_location | 6 |
| raw.dim_date | 1,096 |

Source workbook remains unchanged. All counts are aggregate-only.
Data quality exceptions from Phase 1 remain documented and are not silently corrected.
