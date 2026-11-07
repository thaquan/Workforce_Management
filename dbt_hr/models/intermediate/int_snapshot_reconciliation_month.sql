-- Source month-end headcount versus employee-date reference; never silently overwrite.
with snapshot as (
    select month, sum(headcount)::integer as snapshot_headcount
    from {{ ref('stg_fact_monthly_snapshot') }}
    group by month
),
employee_reference as (
    select month, employee_asof_headcount
    from {{ ref('int_employee_asof_month') }}
)
select
    s.month,
    s.snapshot_headcount,
    e.employee_asof_headcount,
    s.snapshot_headcount - e.employee_asof_headcount as headcount_difference,
    case when s.snapshot_headcount = e.employee_asof_headcount
        then 'MATCHED' else 'REVIEW' end as reconciliation_status
from snapshot s
join employee_reference e using (month)
