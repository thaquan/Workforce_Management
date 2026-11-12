# Page 06 — Data Quality & Trust Console

Power BI report: `powerbi/WorkforceIntelligence.pbip`, Page
`06 Data Quality & Trust`.

## Purpose and truthfulness

This is an **imported audit-snapshot monitoring console**, not a live
always-on monitor. It distinguishes **pipeline execution succeeded** from
**source analytics are fully validated**. A green operational result is not
evidence that every historical business record agrees with every source.

There are three independent source grains:

- `Pipeline Runs`: one row per audited execution, keyed by `pipeline_run_id`.
- `Quality Results`: one row per quality check per pipeline run; `status` is
  `PASS`, `REVIEW` or `FAIL`, and `affected_count` is the **count of items
  violating the check**, not a count of different employees.
- `Fact Reconciliation`: one row per **calendar month for the whole company**,
  showing snapshot headcount, employee-as-of count and their difference.

Because Power BI uses **Import** mode, its latest run is the most recent run
included by the last successful Desktop refresh. It is not guaranteed to be
the latest run currently in PostgreSQL. The historical workforce source ends
December 2025; an audit executed in November 2026 is not evidence that HR
events have been updated through November 2026.

## Common shell, intentionally different monitoring content

Page 6 retains the shared full-height 276px Navy rail, 3px Teal accent,
report title hierarchy, page 06/06 and selectors in the top-right positions.
The layout itself is an **observability console**, unlike the business
charts used on earlier pages.

| Section | Native visual | Grain / meaning |
|---|---|---|
| Sidebar | Latest Run ID and Latest Pipeline Status cards | Most recent imported pipeline audit |
| Sidebar | Review Months and Latest HC Difference cards | Whole-company monthly reconciliation |
| Top status strip | **Three quality-gate cards** | Latest Quality PASS / REVIEW / FAIL, independent of audit-run selector |
| Middle hero | **Monthly reconciliation line** | `Dim Month[month]`, DAX `[Snapshot Reconciliation Difference]` |
| Bottom left | **Pipeline run history table** | Run ID, status and finished date, newest first |
| Bottom right | **Quality-check register** | Run ID, check name, status and affected count, newest run and highest affected count first |

Pipeline and quality audit tables have fixed, compact column widths to keep
their data legible on the 1280×720 canvas. Each table scrolls **vertically**
for additional records. The register includes all checks, not just a
hand-selected list, and the Audit Run slicer can narrow it to one run.

## Filters: distinct source scopes

- **Year**, at the standard Year location, filters **only reconciliation**
  values and the monthly reconciliation chart (via `Dim Month` relationship).
  For 2023/2024/2025, REVIEW month counts are 10/11/12 respectively.
- **Audit Run**, replacing the normal Department selector, filters the two
  audit **tables**. `Pipeline Runs` is related to `Quality Results` by
  `pipeline_run_id`. The quality register can show one run when selected.
- KPI cards explicitly named **Latest** always show the most recently
  imported run, regardless of Audit Run selection, by using the existing
  DAX measures which remove filters as required.
- There is **no Department selector**. Headcount reconciliation is a
  company-wide validation and cannot be correctly allocated to a
  department. The two DAX measures return BLANK under department,
  location or level filters.

The scope separation is written directly above the status strip to avoid
suggesting that Year or Audit Run changes unrelated indicators.

## Verified local source facts (as of imported run #5)

| Audit/reconciliation check | Verified result |
|---|---|
| Latest imported audit | Run **#5**, `SUCCEEDED`, `FULL`, `COMPLETE` |
| Run #5 recorded finish | 2026-11-09 15:51:25 UTC (approx.) |
| Latest gate statuses | **14 PASS, 4 REVIEW, 0 FAIL** |
| Historical headcount reconciliation | **33 REVIEW / 36 months** |
| Source mismatch at June 2025 | **+98** (snapshot 1,021 vs employee-as-of 923) |
| Source mismatch at Dec 2025 | **+5** (snapshot 999 vs employee-as-of 994) |
| Latest 4 REVIEW types | `headcount_reference_mismatch` (33 months), `source_calendar_shortfall` (1), `salary_budget_semantics` (1), `no_transfer_events` (1) |
| Number of imported pipeline runs | 5; each has 18 quality checks |

The 4 reviews are **known source-data limitations**, not hidden
failed technical checks: historical headcount divergence, source calendar
not covering early employee history, unverified salary-budget units, and
missing transfer history. The Phase 3/4 warehouse preserves rather than
silently repairs them.

## Validation

- Original Power BI Desktop loaded this PBIR page and rendered all seven
  KPI cards, reconciliation curve, run history and quality register.
- Initial run history listed oldest first. Final version sorts run ID
  descending; quality register also sorts affected-count descending so the
  important REVIEW issues of the latest run are immediately visible.
- Long table columns were resized to avoid horizontal scrolling; source
  bindings and original DAX were preserved.
- Live DAX verified run #5, status, 14/4/0 gate counts, 33 review months,
  month-specific +98/+5 mismatches, Year filter 2023/2024/2025 and
  independence from the Audit Run slicer. No new measures were required.
- `tests/test_phase5_quality_report.py` validates six-page ordering,
  model field bindings, source scopes, chart families, sorting, source
  caveats and private-data exclusions.
- This page does not export employee rows, imported caches, passwords or
  workbooks. No hosted Power BI Service publication or GitHub push.
