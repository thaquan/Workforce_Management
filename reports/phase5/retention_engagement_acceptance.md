# Phase 5 — Retention & Engagement acceptance

Date: 2026-11-11. PBIP page: `04 Retention & Engagement`.

| Verification | Evidence | Result |
|---|---|---|
| Page 01–03 preserved | PBIR additive Page04 with four-page index | PASS |
| Shared design identity | Navy sidebar, Teal accent, page number, Department position | PASS |
| Main visual | Eight real department-level bubbles: mean engagement × mean performance, population sizing | PASS |
| Active–Exited comparison | Grouped score columns (False=Active, True=Exited), 100%-stacked department cohorts | PASS |
| Correct time semantics | Observation endpoint replaces Year; no false monthly trend | PASS |
| Overall sample | 1,200 observed = 994 Active + 206 Exited | PASS |
| Mean engagement score | 3.4874 overall, 3.5810 Active, 3.0297 Exited | PASS |
| Mean performance rating | 3.4460 overall, 3.4466 Active, 3.4423 Exited | PASS |
| Average prior-365d absence | 4.3917 days/person overall | PASS |
| Engineering cohort split | 385 total = 345 Active + 40 Exited | PASS |
| Null/missingness explained | Engagement 1,190/1,200; Performance 1,139/1,200 | PASS |
| Power BI Desktop preview | Original screenshot inspected, layout refined and recaptured | PASS |
| PBIR schema | 0 errors, 0 warnings | PASS |

All values were reconciled with PostgreSQL aggregate facts and live Power BI
DAX. The Page04 script changes no existing DAX measures or previous report
pages. The rendered scatter exposes no individual employee identifier; the
chart labels show department groups only.

**Interpretation warning:** “Exited” is an endpoint status. A lower mean
engagement score in the exited group **does not prove disengagement caused
departure**. Active and exited subjects have different observation dates,
different missingness and no controlled counterfactual.

Next work: `05 Recruitment Performance`, `06 Data Quality & Trust` and final
portfolio packaging. No Power BI Service publish or GitHub push occurred.
