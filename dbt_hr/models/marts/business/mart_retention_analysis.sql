-- Employee-level analytical FEATURES, not a predictive claim or a public export.
-- Exit cohort features are strictly pre-termination to avoid look-ahead leakage.
with people as (
    select
        employee_id, department_id, location_id, level,
        hire_date, termination_date, employment_status,
        coalesce(termination_date, (select max(date) from {{ ref('dim_date') }}))
            as observation_end
    from {{ ref('dim_employee') }}
)
select
    e.employee_id,
    e.department_id as current_department_id,
    e.location_id as current_location_id,
    e.level,
    e.hire_date,
    e.termination_date,
    e.employment_status,
    e.observation_end,
    (e.termination_date is not null) as exited,
    eng.survey_date as last_engagement_date,
    eng.engagement_score as last_pre_exit_engagement_score,
    perf.review_date as last_performance_date,
    perf.performance_rating as last_pre_exit_performance_rating,
    coalesce(a.absence_days_last_365, 0)::numeric as absence_days_prior_365
from people e
left join lateral (
    select s.survey_date, s.engagement_score
    from {{ ref('fct_engagement_surveys') }} s
    where s.employee_id = e.employee_id
      and s.survey_date <= e.observation_end
      and (e.termination_date is null or s.survey_date < e.termination_date)
    order by s.survey_date desc
    limit 1
) eng on true
left join lateral (
    select p.review_date, p.performance_rating
    from {{ ref('fct_performance_reviews') }} p
    where p.employee_id = e.employee_id
      and p.review_date <= e.observation_end
      and (e.termination_date is null or p.review_date < e.termination_date)
    order by p.review_date desc
    limit 1
) perf on true
left join lateral (
    select sum(a.days_absent) as absence_days_last_365
    from {{ ref('fct_absences') }} a
    where a.employee_id = e.employee_id
      and a.absence_date > (e.observation_end - interval '365 days')::date
      and a.absence_date <= e.observation_end
      and (e.termination_date is null or a.absence_date < e.termination_date)
) a on true
