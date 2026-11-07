select
    department_id,
    department,
    "function" as department_function,
    cost_center
from {{ ref('stg_dim_department') }}
