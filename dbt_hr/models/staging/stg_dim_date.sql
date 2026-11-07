-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "date",
    "month",
    "year",
    "quarter",
    "month_number",
    "month_name",
    "weekday_number"
from {{ source('raw_hr', 'dim_date') }}
