# Phase 5 — Recruitment Performance acceptance

Local Power BI Desktop. Page `05 Recruitment Performance`.

| Gate | Evidence | Result |
|---|---|---|
| Page 01–04 protected | Additive PBIR authoring; no previous pages or DAX modified | PASS |
| Brand shell | 276 px Navy sidebar, Teal edge, 05/06 numbering, aligned filters | PASS |
| Native visuals | Stacked area, bubble scatter, backlog horizontal bars, 100% closed-outcome bars | PASS |
| Year/Department filter logic | Source vs DAX checked for 2024, 2025, Dec 2025 and Engineering | PASS |
| Entire period closeouts | 890 Filled / 356 Cancelled | PASS |
| December 2025 open requisitions | 49 (latest month stock, not 36-month sum) | PASS |
| Duration across reporting period | 50.0112 weighted days to fill | PASS |
| Entire-period closeout share | 71.43% (not applicant conversion) | PASS |
| Location filter precision | No disaggregation: Open, Filled and Days return BLANK | PASS |
| Live Desktop screenshot | Chart data and KPI values inspected; compact chart replaced poorly fitting matrix | PASS |
| PBIR validation | 0 errors, 0 warnings | PASS |
| Page 5 offline test suite | 6/6 PASS | PASS |
| Phase 5 regression suite | 39/39 PASS | PASS |

**Source caveat:** Open is an ending *stock*. Filled and Cancelled are
observed *flows*. The 100% bars compare the share of two closure outcomes,
not candidate interview/hire stages. The data extends only to December
2025; no claim is made that these are today's opening counts. The report
does not expose employee records, applicant identifiers, salaries, local
database credentials or source workbook contents.

The first, narrow matrix was safely backed up in ignored
`data/interim/phase5/recruitment_original_scorecard.json` before the layout
refinement. The original screenshots used for local visual QA were not
committed to Git.

The next page is `06 Data Quality & Trust` (pipeline state, review checks,
source reconciliation and pipeline audit evidence). No cloud publication or
GitHub push has occurred.
