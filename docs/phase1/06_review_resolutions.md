# Phase 1.6 — Review, Fixes, and Source Exceptions

Reviewed against the original 12-sheet workbook. **No source values have been modified.**
Use `python src/phase1/phase1_profiler.py` and `python src/phase1/review_fixes.py` to reproduce the evidence.

## 1. Headcount reconciliation — explained, not overwritten

- Out of 36 months (January 2023–December 2025), **33 have a non-zero difference** between aggregate month-end snapshot HC and HC calculated from employee hire/termination dates.
- June 2025: snapshot HC **1,021** vs employee-as-of HC **923** (difference **+98**). Exactly **98 termination events** are dated in June 2025.
- Four affected departments: **D002: 42, D003: 25, D004: 19, D005: 12**. Each June departmental HC difference equals the count of June departures.
- These exact departments switch to **Post-restructuring reset** in the targets beginning July 2025. July's remaining snapshot HC difference is **+1**.
- December 2025: snapshot **999** vs employee-as-of **994** (difference **+5**).
- The June pattern is consistent with a snapshot timing/processing mismatch around restructuring, **not proof of the source system's intended cutoff**. Other monthly residuals remain unexplained.

**Reporting policy:** Workforce / planning reports use source `FactMonthlySnapshot` with reconciliation warnings. Employment-event analysis uses `FactEmployeeEvents` and date-based headcount as a separate, clearly labeled reference. Do not silently merge or overwrite the two populations. Rates with incompatible numerators/denominators must be labeled provisional until validated.

Artifacts: `reports/phase1/monthly_reconciliation.csv`, `reports/phase1/restructuring_evidence.csv`.

## 2. Calendar coverage — fixed in derived data

- Source `DimDate` covers 2023–2025; earliest event is **2018-01-05**.
- Generated **2,918** daily calendar rows from **2018-01-05** to **2025-12-31** in `data/processed/dim_date_extended.csv`.
- ISO weekday convention used: Monday = 1, Sunday = 7 (matching source).
- This generated calendar is for Phase 2/3 transformation, not a replacement for the raw Excel tab.

## 3. Salary budget units — safely blocked

- Compensation version rows explicitly identify **EUR** and `AnnualSalary`.
- `BudgetedSalaryCost` is numerically annual-scale (about 65k per planned employee on average), but its **currency, time period, employer cost components, and coverage are not documented** by source metadata.
- Do **not** report salary-budget variance as a validated KPI or divide by 12 without confirmation.
- Keep salary vs budget comparison in a future gated/experimental analysis only after documenting aligned units, staff population, effective dates, and plan scenario.

## 4. Transfers — unsupported by source

- Event types are only **Hire (1,200)** and **Termination (206)**.
- No transfer events or effective-dated department assignment table exist. Historical transfers **cannot** be recovered from current employee department.
- Disable transfer rate / internal mobility measures and do not manufacture SCD Type 2 employee history.

## 5. GitHub publication safeguards

- Raw Excel and derived employee-level data remain ignored by Git via `.gitignore`.
- `column_profile.csv` sample values are redacted by the profiler; aggregate descriptive statistics and source schema may be published.
- Audit reports contain aggregated workforce counts, not employee-level salary or employee identifiers.
- Validate license/redistribution rights before posting any additional data or unmasked report screenshots.

## Status summary

| Finding | Resolution | Phase 2 requirement |
|---|---|---|
| HC discrepancies | EXPLAINED_NOT_OVERWRITTEN | retain monthly flags; reconcile with data owner |
| Missing calendar coverage | DERIVED_CALENDAR_CREATED | adopt derived calendar |
| Salary budget semantics | BLOCKED_UNVERIFIED | confirm business definition before KPI release |
| No transfer history | UNSUPPORTED_BY_SOURCE | omit internal mobility KPIs |

A finding marked explained or blocked is **not** a claim that the upstream source data was repaired.
