-- Effective-dated salary versions; never sum across historical versions.
select employee_id, effective_date, annual_salary, level, currency
from {{ ref('stg_fact_compensation') }}
