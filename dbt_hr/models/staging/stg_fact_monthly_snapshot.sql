-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "month",
    "department_id",
    "department",
    "location_id",
    "location",
    "level",
    "headcount",
    "fte",
    "avg_tenure_months"
from {{ source('raw_hr', 'fact_monthly_snapshot') }}
