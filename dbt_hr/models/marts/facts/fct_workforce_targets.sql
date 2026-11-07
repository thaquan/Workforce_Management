select
    month,
    department_id,
    planned_headcount,
    budgeted_fte,
    budgeted_salary_cost as budgeted_salary_cost_unverified,
    planning_scenario
from {{ ref('stg_workforce_targets') }}
