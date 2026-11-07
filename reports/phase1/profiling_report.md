# Phase 1 — Data Profiling Results

- Dataset: **HR_Workforce_Planning_Attrition_Dataset.xlsx**
- Total: **12 worksheets, 29,728 records** (excluding headers).
- DimEmployee: **994 active, 206 terminated**; event types: {'Hire': 1200, 'Termination': 206}.
- Period for snapshots & targets: **2023-01 to 2025-12**.
- January 2023: actual HC **622**, target **989**.
- December 2025: actual HC **999**, target **1079**.
- December 2025 active profile vs monthly snapshot: **994 vs 999**, investigate 5-person difference.
- Automated checks: **{'PASS': 39, 'REVIEW': 4}**.

## Important design implications
- FactMonthlySnapshot is aggregated by Month × Department × Location × Level, NOT Employee.
- Recruitment rows are department-month aggregates; ReqID is not proof of individual positions.
- DimDate begins in 2023 while hiring history begins before 2023: extend calendar for event-level analysis.
- Compensation is effective-dated; use as-of logic, not sum of historical salaries.
- Targets contain scenario labels. Compare at month-department grain; determine the budget unit.
- Cannot prove causality of attrition from engagement/performance/absence correlations.
- Retention driver analysis must use observations available BEFORE employee termination.

## Outputs
- `source_inventory.csv`: table sizes and exact duplicates.
- `column_profile.csv`: data types, missingness, cardinality and ranges.
- `quality_checks.csv`: executed checks and documented review items.
- `docs/phase1/source_to_target_mapping.csv`: raw-to-staging column mapping.

> Profiling reports are reproducible by running `python src/phase1/phase1_profiler.py` from the project root.
