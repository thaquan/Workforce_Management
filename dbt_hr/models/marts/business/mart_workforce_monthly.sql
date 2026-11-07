-- Month-end HC/FTE: additive within a month, semi-additive across months.
select
    f.month,
    f.month_end,
    f.department_id,
    d.department,
    f.location_id,
    l.location,
    f.level,
    f.headcount,
    f.fte,
    f.avg_tenure_months
from {{ ref('fct_workforce_snapshot') }} f
left join {{ ref('dim_department') }} d using (department_id)
left join {{ ref('dim_location') }} l using (location_id)
