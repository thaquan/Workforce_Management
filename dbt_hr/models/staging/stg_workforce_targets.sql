-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "month",
    "department_id",
    "department",
    "planned_headcount",
    "budgeted_fte",
    "budgeted_salary_cost",
    "planning_scenario"
from {{ source('raw_hr', 'workforce_targets') }}
