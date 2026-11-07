-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "employee_id",
    "event_date",
    "event_type",
    "department_id",
    "department",
    "location_id",
    "location",
    "termination_type",
    "termination_reason"
from {{ source('raw_hr', 'fact_employee_events') }}
