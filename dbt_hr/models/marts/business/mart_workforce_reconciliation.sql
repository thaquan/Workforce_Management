select
    month,
    snapshot_headcount,
    employee_asof_headcount,
    headcount_difference,
    reconciliation_status,
    abs(headcount_difference) as absolute_difference
from {{ ref('int_snapshot_reconciliation_month') }}
