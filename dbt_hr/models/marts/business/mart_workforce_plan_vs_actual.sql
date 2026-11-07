-- Targets are Month x Department. Aggregate snapshots to that grain FIRST.
select
    t.month,
    t.department_id,
    d.department,
    t.planning_scenario,
    a.actual_headcount,
    t.planned_headcount,
    a.actual_headcount - t.planned_headcount as headcount_gap,
    100 * a.actual_headcount::numeric / nullif(t.planned_headcount, 0)
        as headcount_attainment_pct,
    a.actual_fte,
    t.budgeted_fte,
    a.actual_fte - t.budgeted_fte as fte_gap,
    a.weighted_avg_tenure_months,
    t.budgeted_salary_cost_unverified,
    false as salary_budget_variance_enabled
from {{ ref('fct_workforce_targets') }} t
left join {{ ref('int_workforce_department_month') }} a
  on a.month = t.month and a.department_id = t.department_id
left join {{ ref('dim_department') }} d
  on d.department_id = t.department_id
