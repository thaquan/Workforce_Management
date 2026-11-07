# Phase 1.2 — Source Grain, Relationships and Warehouse Blueprint

## Source grain and natural/business keys
| Source | Grain | Logical key / warning |
|---|---|---|
| DimEmployee | Employee current/end state | EmployeeID unique; department/location are not full historical SCD |
| FactMonthlySnapshot | Month × Department × Location × Level | Month, DepartmentID, LocationID, Level unique; no EmployeeID |
| FactEmployeeEvents | One employee event | EmployeeID, EventDate, EventType; only Hire/Termination exist |
| FactCompensation | Employee salary version | EmployeeID, EffectiveDate; three distinct effective dates |
| FactPerformance | Employee annual review | EmployeeID, ReviewDate |
| FactEngagement | Employee survey | EmployeeID, SurveyDate |
| FactAbsence | Employee absence record | EmployeeID, AbsenceDate, AbsenceType |
| FactRecruitment | Month × Department aggregates | Month, DepartmentID unique; ReqID labels one summary row, not individual candidate/requisition history |
| WorkforceTargets | Month × Department plan | Month, DepartmentID unique; scenario label switches in part of 2025 |
| DimDepartment | One department | DepartmentID unique |
| DimLocation | One work location | LocationID unique |
| DimDate | One calendar day (2023-2025) | Date unique; must extend to earliest HireDate for all event history |

## Recommended logical warehouse tables (not yet implemented)
- `dim_date` — full calendar from earliest source date through reporting end, both date_key and month_key.
- `dim_department`, `dim_location`, `dim_level` — conformed dimensions.
- `dim_employee` — employee profile with clear as-of/current meaning; do **not** claim SCD Type 2 without historical department changes.
- `fct_workforce_snapshot` — Month × Department × Location × Level, additive over non-time dimensions, **semi-additive over time**.
- `fct_employee_events` — employee events (date, employee, event type, department/location as recorded at event).
- `fct_salary_versions`, `fct_performance_reviews`, `fct_engagement_surveys`, `fct_absences` — employee-grain histories.
- `fct_recruitment_monthly` and `fct_workforce_targets` — both at Month × Department.

## Safe modeling rules
1. Join snapshot to targets **after** aggregating snapshot by Month × Department; joining fact-to-fact at different grains duplicates measures.
2. Do not join monthly snapshot directly to employee-level performance/survey/compensation: there is no shared EmployeeID in the snapshot.
3. Salary analysis needs effective-date as-of logic and employee employment eligibility, not SUM of all historical salary versions.
4. Historical headcount by department comes from the snapshot; current DimEmployee department must not be treated as historical assignment.
5. Filter employee-level facts by event time; for retention analyses use only pre-termination measurements and comparable cohort windows.
6. Model `PlanningScenario` as a dimension/attribute; distinguish baseline from post-restructuring reset.
7. Build narrow report marts (e.g. `mart_workforce_monthly`, `mart_attrition_monthly`, `mart_workforce_plan_vs_actual`, `mart_retention_pre_exit`, `mart_recruitment_monthly`).

## Reconciliation flags from source
- Dec 2025 snapshot HC=999 vs Employee active=994. Independent interpretation or source inconsistency: unresolved (five-person difference).
- Jan 2023 snapshot HC=622, matching employee-derived HC at Jan 31; Dec 2024 and Dec 2025 are five higher than employee-derived HC.
- DimDate spans 2023-2025, but hire events start in 2018.
- Salary budget cost unit/cadence must be confirmed before valid comparison with `AnnualSalary`.
