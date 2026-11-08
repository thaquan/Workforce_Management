{{ config(tags=['full_baseline']) }}
-- Catch row loss, fanout or unexpected changes to the verified baseline.
with checks as (
    select 'workforce month/location/level fact count' as problem
    where (select count(*) from {{ ref('mart_workforce_monthly') }}) <> 6826
    union all
    select 'attrition month/department count'
    where (select count(*) from {{ ref('mart_attrition_monthly') }}) <> 288
    union all
    select 'recruitment month/department count'
    where (select count(*) from {{ ref('mart_recruitment_monthly') }}) <> 288
    union all
    select 'retention employee count'
    where (select count(*) from {{ ref('mart_retention_analysis') }}) <> 1200
    union all
    select 'salary run-rate month count'
    where (select count(*) from {{ ref('mart_salary_run_rate_monthly') }}) <> 36
    union all
    select 'source events count'
    where (select count(*) from {{ ref('fct_employee_events') }}) <> 1406
    union all
    select 'date calendar extended coverage'
    where (select min(date) from {{ ref('dim_date') }}) > date '2018-01-05'
       or (select max(date) from {{ ref('dim_date') }}) < date '2025-12-31'
)
select * from checks
