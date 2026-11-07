-- Open requisitions are stock; do not sum across months in BI.
select
    r.month,
    r.department_id,
    d.department,
    r.open_requisitions,
    r.filled_requisitions,
    r.cancelled_requisitions,
    case when r.filled_requisitions > 0 then r.avg_days_to_fill else null end
        as avg_days_to_fill,
    r.filled_requisitions * coalesce(r.avg_days_to_fill, 0)
        as weighted_days_to_fill_numerator
from {{ ref('fct_recruitment_monthly') }} r
left join {{ ref('dim_department') }} d using (department_id)
