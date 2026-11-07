-- Dataset-specific baseline regressions; edits require review, not silent correction.
with checks as (
    select 'expected 36 reporting months' as problem
    where (select count(*) from {{ ref('mart_workforce_reconciliation') }}) <> 36
    union all
    select 'expected 33 mismatched snapshot months'
    where (select count(*) from {{ ref('mart_workforce_reconciliation') }}
           where reconciliation_status='REVIEW') <> 33
    union all
    select 'June 2025 restructuring discrepancy must remain visible'
    where (select headcount_difference from {{ ref('mart_workforce_reconciliation') }}
           where month=date '2025-06-01') is distinct from 98
    union all
    select 'December 2025 snapshot/profile discrepancy is 5'
    where (select headcount_difference from {{ ref('mart_workforce_reconciliation') }}
           where month=date '2025-12-01') is distinct from 5
)
select * from checks
