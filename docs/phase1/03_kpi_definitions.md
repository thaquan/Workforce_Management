# Phase 1.3 — KPI Definitions & Calculation Contract

**Time rule:** Treat `Month` as month-start key; `FactMonthlySnapshot` stores month-end workforce status. Show the latest selected month by default. Do not sum month-end HC/FTE over multiple months.

| KPI | Calculation | Required grain | Note |
|---|---|---|---|
| Ending headcount | SUM(Snapshot.Headcount) at selected Month | Month + selected Department/Location/Level | Semi-additive across time |
| Ending FTE | SUM(Snapshot.FTE) at selected Month | Same as above | Sum within month only |
| Headcount change | Ending HC - Previous Month Ending HC | Month | A 2-month difference, not number of hires |
| Net hires / exits | #Hire events - #Termination events in period | EventDate period | May not reconcile exactly with HC due to data corrections and transfers |
| Average HC | (Beginning HC + Ending HC)/2 | Period | For monthly attrition; agree policy for longer periods |
| Attrition % | Termination events / Average HC × 100 | Month or period | Rate denominator must match context/grain |
| Voluntary attrition % | Voluntary terminations / Average HC × 100 | Month | Never divide by active-employee count only |
| Involuntary attrition % | Involuntary terminations / Average HC × 100 | Month | Compare with voluntary separately |
| Planned HC gap | Actual HC - Planned HC | Month × Department | Negative = below plan |
| Planned HC attainment % | Actual HC / Planned HC × 100 | Month × Department | Guard against zero targets |
| FTE gap | Actual FTE - Budgeted FTE | Month × Department | Match period scope |
| Mean engagement | AVG(EngagementScore) among responses | Survey month/cohort | Avoid causal language |
| Average performance | AVG(PerformanceRating) among rated employees | Review period/cohort | Reviews are not monthly observations |
| Absence days | SUM(DaysAbsent) | Absence date/cohort | Not an absence **rate** without eligible working days |
| Avg days to fill | SUM(AvgDaysToFill × FilledRequisitions) / SUM(FilledRequisitions) | Month × Department | Exclude zero-fill rows from denominator; assess business definition |
| Open requisitions | SUM(OpenRequisitions) at selected month | Month × Department | Not time-additive stock if measured as month-end open |
| Salary run-rate | SUM(latest eligible AnnualSalary as of reference date) | Employee as-of month | Not the sum of all salary history versions |
| Salary variance | Comparable actual salary run-rate - budgeted salary cost | Month × Department | **Blocked** until budget units/coverage validated |

## Important DAX/SQL guardrails
- Calculate per-month HC with a single selected period or last-visible-period measure; a year slicer needs a deliberate December/last month rule.
- To compute attrition by department, employee events carry historical DepartmentID; do not categorize termination events using DimEmployee current department by default.
- Correlation of poor engagement and attrition ≠ causation; survey dates must precede exit date.
- For recruitment, `FilledRequisitions` are counts inside aggregates; `ReqID` is a summary-row identifier, not an actual job-opening ID.
- Salary budgets appear annual-scale in sample data; treat that as hypothesis until validated.

## KPI validation examples
- January 2023: HC actual=622 vs target=989; gap=-367.
- December 2025: HC actual=999 vs target=1,079; gap=-80.
- December 2025: FTE actual=968.6 vs budgeted=1,053.8; gap=-85.2.
- DimEmployee: 994 active and 206 terminated records; 206/1200 is **not** a time-bounded attrition rate.
