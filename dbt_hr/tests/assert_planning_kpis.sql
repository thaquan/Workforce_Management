{{ config(tags=['full_baseline']) }}
-- Planning facts must not be multiplied by snapshot Location/Level granularity.
with checks as (
    select 'planning row count' as problem
    where (select count(*) from {{ ref('mart_workforce_plan_vs_actual') }}) <> 288
    union all
    select 'January 2023 actual/plan headcount'
    where (select sum(actual_headcount) from {{ ref('mart_workforce_plan_vs_actual') }}
           where month=date '2023-01-01') is distinct from 622
       or (select sum(planned_headcount) from {{ ref('mart_workforce_plan_vs_actual') }}
           where month=date '2023-01-01') is distinct from 989
    union all
    select 'December 2025 actual/plan headcount'
    where (select sum(actual_headcount) from {{ ref('mart_workforce_plan_vs_actual') }}
           where month=date '2025-12-01') is distinct from 999
       or (select sum(planned_headcount) from {{ ref('mart_workforce_plan_vs_actual') }}
           where month=date '2025-12-01') is distinct from 1079
    union all
    select 'budget variance must be disabled'
    where exists(select 1 from {{ ref('mart_workforce_plan_vs_actual') }}
                 where salary_budget_variance_enabled)
)
select * from checks
