-- Aggregate the source snapshot before joining to Month x Department planning data.
select
    month,
    department_id,
    sum(headcount)::integer as actual_headcount,
    sum(fte)::numeric(20,6) as actual_fte,
    case when sum(headcount) = 0 then null
         else sum(avg_tenure_months * headcount) / sum(headcount)
    end as weighted_avg_tenure_months
from {{ ref('stg_fact_monthly_snapshot') }}
group by month, department_id
