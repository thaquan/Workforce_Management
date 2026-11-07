-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "department_id",
    "department",
    "function",
    "cost_center"
from {{ source('raw_hr', 'dim_department') }}
