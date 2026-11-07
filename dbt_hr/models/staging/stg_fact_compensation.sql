-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "employee_id",
    "effective_date",
    "annual_salary",
    "level",
    "currency"
from {{ source('raw_hr', 'fact_compensation') }}
