select employee_id, review_date, performance_rating, review_type
from {{ ref('stg_fact_performance') }}
