-- Event-month values are flows; event DepartmentID is historical at event time.
select
    date_trunc('month', event_date)::date as month,
    department_id,
    count(*) filter (where event_type = 'Hire')::integer as hires,
    count(*) filter (where event_type = 'Termination')::integer as terminations,
    count(*) filter (
        where event_type = 'Termination' and termination_type = 'Voluntary'
    )::integer as voluntary_terminations,
    count(*) filter (
        where event_type = 'Termination' and termination_type = 'Involuntary'
    )::integer as involuntary_terminations
from {{ ref('stg_fact_employee_events') }}
group by 1, 2
