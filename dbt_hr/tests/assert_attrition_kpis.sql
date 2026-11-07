-- Attrition numerator and denominator checks; Jan 2023 has no prior snapshot.
select month, department_id
from {{ ref('mart_attrition_monthly') }}
where terminations <> voluntary_terminations + involuntary_terminations
   or (previous_headcount is null and
       (attrition_rate_pct is not null or rate_quality_status <> 'NO_PRIOR_SNAPSHOT'))
   or (previous_headcount is not null and
       abs(coalesce(attrition_rate_pct, -1) -
           100 * terminations::numeric / nullif(average_headcount, 0)) > 0.000001)
   or (previous_headcount is not null and average_headcount > 0 and
       attrition_rate_pct is null)
