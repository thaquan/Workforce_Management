-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "employee_id",
    "department_id",
    "department",
    "role",
    "level",
    "location_id",
    "location",
    "manager_id",
    "gender",
    "birth_year",
    "age_band",
    "hire_date",
    "termination_date",
    "employment_status",
    "termination_type",
    "termination_reason",
    "fte",
    "tenure_months_at_exit_or_end",
    "tenure_band_at_exit_or_end"
from {{ source('raw_hr', 'dim_employee') }}
