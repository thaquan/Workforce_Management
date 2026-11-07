-- Generated from the Phase 2 source contract; source grain is unchanged.
select
    "employee_id",
    "survey_date",
    "engagement_score",
    "response_rate_pct"
from {{ source('raw_hr', 'fact_engagement') }}
