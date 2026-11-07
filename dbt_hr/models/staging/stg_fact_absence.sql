-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "employee_id",
    "absence_date",
    "absence_type",
    "days_absent"
from {{ source('raw_hr', 'fact_absence') }}
