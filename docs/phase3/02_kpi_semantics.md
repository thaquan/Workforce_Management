# Phase 3 KPI Contracts, Assumptions and Limitations

## Ending workforce (stock)

- `headcount` and `fte` use `FactMonthlySnapshot`; they are
  **semi-additive** across time. For a year or a selected range,
  use the last selected month, **not** the sum of monthly headcounts.
- Sum within one month over Department, Location and Level.
- Do not manufacture individual historical assignments from current
  `DimEmployee.department_id`.

## Attrition (flow divided by average stock)

- `terminations` are counted from recorded employee termination events
  by event month and recorded event department.
- `average_headcount = (previous_month_end_HC + current_month_end_HC)/2`
  at Month × Department.
- `attrition_rate_pct = 100 * terminations / average_headcount`;
  voluntary/involuntary rates use their respective event counts.
- January 2023 has no December 2022 snapshot: the rate is **NULL**
  and quality flag is `NO_PRIOR_SNAPSHOT`.
- For the current workbook, **280/288** department-month rates are labeled
  `PROVISIONAL_SOURCE_MISMATCH`; no attrition rate should be represented
  as fully verified while source reconciliation is unresolved.

## Planning and recruitment

- Plan vs actual: join `Month × Department` targets only to an
  aggregated snapshot of the same grain. Validated January 2023 gap is
  **622 − 989 = −367**, and December 2025 is **999 − 1,079 = −80**.
- FTE gap is `actual_fte - budgeted_fte`; these share a comparable
  FTE unit, unlike salary budget.
- `open_requisitions` is a month-end stock, not additive across time.
  `filled_requisitions` is a monthly flow. Weighted mean days-to-fill
  across departments is `SUM(weighted_days_to_fill_numerator) /
  NULLIF(SUM(filled_requisitions),0)`.
- `PlanningScenario` distinguishes baseline from
  `Post-restructuring reset` starting July 2025 in four departments.

## Retention and compensation

- Retention mart is **one employee-level observation at termination
  (for exited employees) or the last available reporting date (for active)**.
  It is not a longitudinal employee-month panel or a causal attrition model.
- Last engagement/performance and 365-day absence features must precede
  termination strictly, preventing post-exit look-ahead.
- For salary, use the **latest eligible compensation version** at each month
  end; do not add historical salary versions. Results are an annual salary
  run-rate in EUR for the employee-date-as-of population, not necessarily
  the source snapshot population.
- `BudgetedSalaryCost` has undocumented period, currency and staff coverage.
  Consequently the salary-versus-budget KPI is **disabled**.

## Upstream source discrepancies

For **33/36** months, snapshot headcount differs from headcount calculated
using employee hire and termination dates. June 2025: **1,021 vs 923**
(difference +98) coincides with 98 recorded exits; December 2025:
**999 vs 994** (+5). These facts are retained as REVIEW, not silently
corrected. A source business owner must confirm snapshot cutoffs to
reclassify the rates.

The source has no Transfer event history and no effective-dated historical
department mapping. Internal mobility metrics and historical SCD Type 2
department views cannot be recovered reliably.
