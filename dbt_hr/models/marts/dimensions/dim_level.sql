select distinct level
from (
    select level from {{ ref('stg_dim_employee') }}
    union
    select level from {{ ref('stg_fact_monthly_snapshot') }}
    union
    select level from {{ ref('stg_fact_compensation') }}
) levels
where level is not null
