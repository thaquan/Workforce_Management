# Phase 1.1 — Business Requirements and Success Criteria

## Problem statement
HR leaders need a consistent view of workforce size, attrition, staffing targets, retention indicators, recruiting capacity and cost. Current data resides in 12 Excel worksheets at mixed grains and historic time windows. Build a curated and tested analytics layer for a maximum three-page Power BI report.

## Stakeholders
| Stakeholder | Core decision | Questions to answer |
|---|---|---|
| Executive / CFO | Headcount plan and budget | Is actual HC/FTE above or below plan? How is the gap evolving? |
| HR Business Partner | Retention | Which departments and cohorts have elevated terminations? Why do employees leave? |
| Talent Acquisition | Recruitment | Where do recruiting requisitions remain open? What is the weighted time to fill? |
| HR Operations | Data governance | Are monthly HC, hires/terminations and employee statuses reconciled? |

## Functional requirements (priority)
| ID | Requirement | Source | Acceptance |
|---|---|---|---|
| FR01 | Headcount/FTE trends by month, department, location and level | FactMonthlySnapshot | Month-end values; no summing months |
| FR02 | Monthly hires, terminations, voluntary/involuntary breakdown | FactEmployeeEvents | Correct event date, clear rate denominator |
| FR03 | Termination reasons by department/cohort | Employee events | Only termination rows; privacy-safe aggregation |
| FR04 | Staffing gap: actual vs planned HC/FTE | Snapshot + Targets | Compare at Month x Department; explain scenario switches |
| FR05 | Engagement, performance, absence vs retention | Engagement/Performance/Absence | Use observations before termination; label association not causation |
| FR06 | Recruitment demand and average days to fill | FactRecruitment | Aggregate at department-month; weighted avg by filled requisitions |
| FR07 | Salary run-rate vs budget (conditional) | Compensation + Targets | Only after validating comparable unit/coverage |
| FR08 | Department/location slicers, drill-down and tooltips | Curated marts | Explain cross-fact filter grain to stakeholders |

## Constraints and non-functional requirements
- Dashboard maximum three pages (including drill-through) and 16:9 canvas.
- Data size ~0.9 MB, so prioritize SQL correctness over distributed Spark/streaming overhead.
- Use Python, PostgreSQL, dbt Core, Power BI Desktop, optional Docker and Dagster.
- Repeatable full load; later simulate monthly batch loads with idempotent upserts.
- Quality checks must fail unsafe loads and document known reconciliation issues.
- Row-level salary and HR details must not appear in public screenshots/repository.

## Proposed BI pages
1. **Executive Workforce Overview** — HC, FTE, change, actual-vs-plan, trend.
2. **Attrition & Retention** — voluntary/involuntary exits, reasons, pre-exit engagement/performance.
3. **Recruitment & Workforce Planning** — demand, filled requisitions, vacancies, salary-budget assessment if units validated.

## Definition of done for Phase 1
All 12 sources profiled; business grain and keys documented; source-to-staging mapping provided; proposed marts, KPIs and known data limitations specified; executable audit script and report reproducible.
