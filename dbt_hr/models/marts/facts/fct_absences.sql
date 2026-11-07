select employee_id, absence_date, absence_type, days_absent
from {{ ref('stg_fact_absence') }}
