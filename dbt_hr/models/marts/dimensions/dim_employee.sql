-- Current/end-state employee profile only; no fabricated SCD2 assignment history.
select
    employee_id,
    department_id,
    role,
    level,
    location_id,
    manager_id,
    gender,
    birth_year,
    age_band,
    hire_date,
    termination_date,
    employment_status,
    termination_type,
    termination_reason,
    fte,
    tenure_months_at_exit_or_end,
    tenure_band_at_exit_or_end
from {{ ref('stg_dim_employee') }}
