-- ReqID denotes a department-month aggregate row, not a candidate/requisition history.
select
    req_id,
    month,
    department_id,
    open_requisitions,
    filled_requisitions,
    cancelled_requisitions,
    avg_days_to_fill
from {{ ref('stg_fact_recruitment') }}
