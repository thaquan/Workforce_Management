# Phase 5 — Live DAX Acceptance (Power BI Desktop)

## Verification environment

- Power BI Desktop, local `WorkforceIntelligence` model (Import mode)
- Local Microsoft Power BI Authoring MCP Server v1.0.1
- PostgreSQL `workforce_dw` (read-only SQL comparisons)
- Validation performed after successful user-initiated refresh on 2026-11-11

## DAX execution

All **51/51 DAX measures** executed successfully in six MCP `EVALUATE ROW`
batches (10+10+10+10+10+1), with no DAX evaluation errors. This is an
expression-level smoke test, **not** proof that every filter context is correct.

## SQL-to-DAX acceptance checks

| Scenario | Live DAX | SQL baseline | Outcome |
|---|---:|---:|---|
| Dec 2025 Ending Headcount | 999 | 999 | PASS |
| Dec 2025 Planned Headcount | 1,079 | 1,079 | PASS |
| Dec 2025 Headcount Gap | -80 | -80 | PASS |
| Dec 2025 Ending FTE | 968.6 | 968.6 | PASS |
| Jan 2023 Ending HC | 622 | 622 | PASS |
| Jan 2023 Monthly Attrition | BLANK | No prior snapshot | PASS |
| Dec 2025 Weighted Avg Tenure (months) | 40.648248 | 40.648248 | PASS |
| Nov 2025 HC (as prior month) | 986 | 986 | PASS |
| 2025 Period Attrition | 14.7258085% | 14.7258085% | PASS |
| Dec 2025 Rolling 12M Attrition | 14.7258085% | 14.7258085% | PASS |
| Jan 2024 Rolling 12M Attrition | 4.4015855% | 4.4015855% | PASS |
| Overall Weighted Days to Fill | 50.011236 | 50.011236 | PASS |
| Jun 2025 Reconciliation Difference | +98 | +98 | PASS |
| Review Months | 33 | 33 | PASS |
| Retention endpoint population | 1,200 | 1,200 | PASS |
| Exited Employees | 206 | 206 | PASS |
| Latest Pipeline Status | SUCCEEDED | SUCCEEDED at last ingestion | PASS |
| Latest Quality FAIL | 0 | 0 | PASS |
| Dec 2025, Department D001 HC | 346 | 346 | PASS |
| Dec 2025, Department D001 Plan | 350 | 350 | PASS |

## Filter-context tests

- Full-year 2025 selection: Ending HC remains **999**, not a sum of 12 snapshots.
- January 2023: Monthly and period attrition and rolling 12-month attrition
  return **BLANK** where the required denominator/window is unavailable.
- Location L001 selected: workforce HC still filters (389), but
  Planned HC, Monthly Attrition and company-wide reconciliation return BLANK,
  since they cannot truthfully be attributed to location.
- Department D001 selected: HC (346) and plan (350) are available, while
  company-wide reconciliation remains BLANK.
- December 2025 attrition quality status is **Provisional - source mismatch**.

## Caveats

Headcount source discrepancies (33/36 months) remain uncorrected REVIEW
items; the result is provisional, not an assertion that source workforce
counts are accurate. The retention model is an endpoint cohort rather than
a historic snapshot panel. Salary-budget variance and internal mobility
remain excluded due to unverified source semantics.

No raw employee records or database credentials are included in this report.

## Next acceptance gates

Model save/reopen/refresh, Power BI report visual bindings and rendered
screenshot review must pass before a completed dashboard is claimed.
