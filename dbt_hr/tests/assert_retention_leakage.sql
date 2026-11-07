-- No exit cohort feature may refer to the exit date or later.
select employee_id
from {{ ref('mart_retention_analysis') }}
where (termination_date is not null
       and (last_engagement_date >= termination_date
         or last_performance_date >= termination_date))
   or absence_days_prior_365 < 0
   or (exited and termination_date is null)
