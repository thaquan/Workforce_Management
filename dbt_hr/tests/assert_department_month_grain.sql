-- Prevent accidental duplication through joins with finer-grain facts.
select month, department_id from {{ ref('mart_attrition_monthly') }}
group by 1,2 having count(*) > 1
union all
select month, department_id from {{ ref('mart_workforce_plan_vs_actual') }}
group by 1,2 having count(*) > 1
union all
select month, department_id from {{ ref('mart_recruitment_monthly') }}
group by 1,2 having count(*) > 1
