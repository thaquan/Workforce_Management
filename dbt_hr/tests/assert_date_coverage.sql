-- Historical events (from 2018) must resolve to extended calendar dimension.
select e.event_id
from {{ ref('fct_employee_events') }} e
left join {{ ref('dim_date') }} d on d.date=e.event_date
where d.date is null
