-- Observed employee-date population, latest eligible salary version only.
-- AnnualSalary is in EUR; NOT compared with unverified WorkforceTargets budget.
with reporting_months as (
    select distinct month,
        (month + interval '1 month' - interval '1 day')::date as month_end
    from {{ ref('stg_fact_monthly_snapshot') }}
),
eligible as (
    select m.month, m.month_end, e.employee_id
    from reporting_months m
    join {{ ref('dim_employee') }} e
      on e.hire_date <= m.month_end
     and (e.termination_date is null or e.termination_date > m.month_end)
),
salary_versions as (
    select
        e.month,
        e.employee_id,
        c.annual_salary,
        c.currency,
        row_number() over (
            partition by e.month, e.employee_id
            order by c.effective_date desc nulls last
        ) as version_rank
    from eligible e
    left join {{ ref('fct_compensation_versions') }} c
      on c.employee_id = e.employee_id
     and c.effective_date <= e.month_end
)
select
    month,
    count(*)::integer as eligible_employee_count,
    count(annual_salary)::integer as employees_with_salary,
    count(*) - count(annual_salary) as employees_missing_salary,
    sum(annual_salary) as annual_salary_run_rate_eur,
    100 * count(annual_salary)::numeric / nullif(count(*), 0) as salary_coverage_pct,
    false as can_compare_to_budget
from salary_versions
where version_rank = 1
group by month
