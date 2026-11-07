-- One source row per month/department/location/level, and no fanout in the mart.
select month, department_id, location_id, level
from {{ ref('fct_workforce_snapshot') }}
group by 1,2,3,4
having count(*) > 1
union all
select month, department_id, location_id, level
from {{ ref('mart_workforce_monthly') }}
group by 1,2,3,4
having count(*) > 1
