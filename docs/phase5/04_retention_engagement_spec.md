# Page 04 — Retention & Engagement Lab

## Purpose and data scope

This page describes **observed endpoint cohorts**, not an annual employee
retention time series. It compares engagement, performance and absence
features for groups that are **Active** versus **Exited** at their respective
observation dates. It does **not** establish why anyone exited, predict an
individual's resignation, or infer historical job/department assignments.

The source is `marts.mart_retention_analysis`, published in Power BI as an
aggregate `Fact Retention` at **current_department_id × exited** grain.
Power BI imports only employee counts and sums/counts of non-identifying
features; employee IDs and compensation records remain excluded.

**Important date rule:** For active records, `observation_end` is the data
snapshot endpoint (2025-12-31); for exited records it is the termination
date. The report does not contain a relationship from `Dim Month` to `Fact
Retention`. A Year slicer on this page would be misleading because selecting
2024 would leave the retention population unchanged. Accordingly, the
standard Year position is replaced with a static, labeled **Observation
Endpoint: 31 Dec 2025**. The Department slicer remains functional but shows
the **current/last recorded department**, not historical department SCD2.

## Design and visual contract

Brand identity remains consistent with pages 01–03: Navy 276px sidebar,
Teal accent, Segoe UI, report title/number, and the Department selector in
the same header position. This page uses a **research-lab canvas** instead
of a heatmap, scorecard or waterfall:

| Section | Power BI visual | Source contract |
|---|---|---|
| Sidebar | Endpoint cohort cards | Observed Employees, Active Employees, Exited Employees, Average Engagement Score, Average Prior 365d Absence Days |
| Hero | **Scatter/bubble chart** | One dot per Department, X = Average Engagement Score, Y = Average Performance Rating, bubble size = Observed Employees |
| Upper-right | **Clustered columns** | Category = `Fact Retention[exited]` (False=Active; True=Exited), series = Average Engagement Score and Average Performance Rating |
| Lower-left | **100% horizontal stacked bars** | Department proportions from Active Employees and Exited Employees; not employee turnover rates |
| Lower-right | Interpretation panel | No monthly history; differing score coverage; current department only; no causal inference |

Scatter uses **department-level points**, not per-employee dots or small
department×cohort subgroups. This preserves a clean overview with eight
aggregate department bubbles. The two cohort profiles appear only in the
right-side summary. All charts are native Power BI visuals without paid
custom components.

## Grounded cohort facts

| Measure | Full observed cohort | Active | Exited |
|---|---:|---:|---:|
| Observed employees | 1,200 | 994 | 206 |
| Engagement available | 1,190 | 988 | 202 |
| Mean engagement score | 3.4874 | 3.5810 | 3.0297 |
| Performance available | 1,139 | 983 | 156 |
| Mean performance rating | 3.4460 | 3.4466 | 3.4423 |
| Mean prior 365d absence days | 4.3917 | 4.4819 | 3.9563 |

The engagement and performance denominators differ from the employee
denominator because not every person has an available survey/review. Scores
are **weighted by the number of observed scores**, not averaged across
department-level means. The exited cohort is sampled strictly before its
exit date, avoiding post-exit leakage; the two populations nonetheless have
different observation times and should not be interpreted as a controlled
comparison.

The 100% department bars show **composition of this endpoint sample**, not
annual attrition. Selecting one Department changes these endpoint aggregates
correctly. Department categories with no exited employees can show 100%
Active; this is not evidence about future retention.

## Validation and release gates

- PBIR structural validation: no errors/warnings.
- Power BI Desktop screenshot rendered real department bubbles, two-cohort
  score comparisons, Active/Exited composition and sidebar values.
- Live DAX verified overall, per-cohort, Engineering department and the
  deliberate fact that applying `Dim Month[year]` does not filter these
  endpoint data. There is **no exposed Year slicer** on this page.
- `tests/test_phase5_retention_report.py` verifies page order, shared shell,
  correct visual roles, no fake time slicer, privacy and all field bindings.
- No cloud publishing, automatic Git push, employee row export or paid
  Power BI add-ons are used.
