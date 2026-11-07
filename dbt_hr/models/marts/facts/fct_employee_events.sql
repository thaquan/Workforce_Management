select
    md5(employee_id || '|' || event_date::text || '|' || event_type) as event_id,
    employee_id,
    event_date,
    date_trunc('month', event_date)::date as month,
    event_type,
    department_id,
    location_id,
    termination_type,
    termination_reason
from {{ ref('stg_fact_employee_events') }}
