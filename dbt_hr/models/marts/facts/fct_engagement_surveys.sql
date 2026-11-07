select employee_id, survey_date, engagement_score, response_rate_pct
from {{ ref('stg_fact_engagement') }}
