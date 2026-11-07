-- Extend beyond raw DimDate so hire events from 2018 resolve to valid calendar dates.
with bounds as (
    select
        least(
            (select min(hire_date) from {{ ref('stg_dim_employee') }}),
            (select min(event_date) from {{ ref('stg_fact_employee_events') }}),
            (select min("date") from {{ ref('stg_dim_date') }})
        ) as start_date,
        greatest(
            (select max("date") from {{ ref('stg_dim_date') }}),
            (select max(event_date) from {{ ref('stg_fact_employee_events') }})
        ) as end_date
),
calendar as (
    select day::date as date
    from bounds
    cross join lateral generate_series(start_date, end_date, interval '1 day') as day
)
select
    date,
    to_char(date, 'YYYYMMDD')::integer as date_key,
    date_trunc('month', date)::date as month,
    extract(year from date)::integer as year,
    extract(quarter from date)::integer as quarter_number,
    extract(month from date)::integer as month_number,
    to_char(date, 'Mon') as month_name,
    extract(isodow from date)::integer as weekday_number
from calendar
