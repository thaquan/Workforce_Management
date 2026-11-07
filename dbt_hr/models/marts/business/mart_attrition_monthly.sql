-- Company-level reconciliation flags are propagated into department rates.
-- January 2023 attrition is NULL: no December 2022 snapshot denominator exists.
with w as (
    select
        month,
        department_id,
        actual_headcount,
        actual_fte,
        lag(actual_headcount) over (
            partition by department_id order by month
        ) as previous_headcount
    from {{ ref('int_workforce_department_month') }}
),
joined as (
    select
        w.*,
        coalesce(e.hires, 0) as hires,
        coalesce(e.terminations, 0) as terminations,
        coalesce(e.voluntary_terminations, 0) as voluntary_terminations,
        coalesce(e.involuntary_terminations, 0) as involuntary_terminations,
        coalesce(rc.reconciliation_status, 'REVIEW') as current_reconciliation,
        coalesce(rp.reconciliation_status, 'REVIEW') as prior_reconciliation
    from w
    left join {{ ref('int_events_department_month') }} e
      on e.month = w.month and e.department_id = w.department_id
    left join {{ ref('int_snapshot_reconciliation_month') }} rc
      on rc.month = w.month
    left join {{ ref('int_snapshot_reconciliation_month') }} rp
      on rp.month = (w.month - interval '1 month')::date
)
select
    month, department_id, actual_headcount, actual_fte,
    previous_headcount,
    case when previous_headcount is null then null
         else (previous_headcount + actual_headcount)::numeric / 2
    end as average_headcount,
    hires, terminations, voluntary_terminations, involuntary_terminations,
    case when previous_headcount is null then null
         else 100 * terminations::numeric /
              nullif((previous_headcount + actual_headcount)::numeric / 2, 0)
    end as attrition_rate_pct,
    case when previous_headcount is null then null
         else 100 * voluntary_terminations::numeric /
              nullif((previous_headcount + actual_headcount)::numeric / 2, 0)
    end as voluntary_attrition_rate_pct,
    case when previous_headcount is null then null
         else 100 * involuntary_terminations::numeric /
              nullif((previous_headcount + actual_headcount)::numeric / 2, 0)
    end as involuntary_attrition_rate_pct,
    case when previous_headcount is null then 'NO_PRIOR_SNAPSHOT'
         when current_reconciliation = 'MATCHED'
          and prior_reconciliation = 'MATCHED' then 'REFERENCE_MATCHED'
         else 'PROVISIONAL_SOURCE_MISMATCH'
    end as rate_quality_status
from joined
