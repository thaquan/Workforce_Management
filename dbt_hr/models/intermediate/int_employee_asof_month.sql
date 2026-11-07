-- Reference population computed solely from employment dates; not historical department.
with reporting_months as (
    select distinct month
    from {{ ref('stg_fact_monthly_snapshot') }}
),
asof as (
    select
        m.month,
        (m.month + interval '1 month' - interval '1 day')::date as month_end,
        e.employee_id
    from reporting_months m
    left join {{ ref('stg_dim_employee') }} e
      on e.hire_date <= (m.month + interval '1 month' - interval '1 day')::date
     and (e.termination_date is null or
          e.termination_date > (m.month + interval '1 month' - interval '1 day')::date)
)
select month, count(employee_id)::integer as employee_asof_headcount
from asof
group by month
