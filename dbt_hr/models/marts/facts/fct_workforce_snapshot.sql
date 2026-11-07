-- Source grain: month x department x location x level (NOT employee).
select
    month,
    (month + interval '1 month' - interval '1 day')::date as month_end,
    department_id,
    location_id,
    level,
    headcount,
    fte,
    avg_tenure_months
from {{ ref('stg_fact_monthly_snapshot') }}
