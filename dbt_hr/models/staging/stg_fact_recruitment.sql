-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "req_id",
    "month",
    "department_id",
    "department",
    "open_requisitions",
    "filled_requisitions",
    "cancelled_requisitions",
    "avg_days_to_fill"
from {{ source('raw_hr', 'fact_recruitment') }}
