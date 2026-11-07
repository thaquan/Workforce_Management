-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "employee_id",
    "review_date",
    "performance_rating",
    "review_type"
from {{ source('raw_hr', 'fact_performance') }}
