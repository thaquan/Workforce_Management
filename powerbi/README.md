# Workforce Intelligence — Phase 5 semantic model (DAX-first milestone)

## Deliverables

- `WorkforceIntelligence.SemanticModel/model.bim`: credential-free
  Power BI tabular model, 13 tables, 13 one-direction relationships,
  51 measures in seven display folders.
- `dax/measures.dax`: complete readable measure definitions.
- `dax/measure_catalog.md`: measure inventory and format strings.
- `dax/validation_queries.dax`: DAX Query View acceptance queries.
- `../src/phase5/build_model.py`: reproducible model generator.
- `../src/phase5/validate_sources.py`: read-only SQL baseline checks.

## Scope and semantics

The model connects to local PostgreSQL `127.0.0.1:5433/workforce_dw`
in Import mode. No database credentials or cached data are included.
Twelve source projections use marts/audit; the thirteenth table is the
measure host. The reporting-month dimension covers the verified
January 2023–December 2025 snapshot period. The model must be updated if
the workbook is extended beyond that period.

Ending headcount, FTE, plans and open requisitions are stocks at the last
selected month. Hires, exits, fills and cancellations are flows. Period
attrition uses total exits divided by the mean monthly average workforce
for a contiguous period with complete denominators; January 2023 is
blank. Rolling 12M attrition requires 12 valid months.

Planning, attrition and recruitment cannot be allocated to location or
level; their measures return blank when those dimensions are filtered.
Company-wide reconciliation likewise cannot be allocated to departments.
Retention uses a department × exited aggregate (15 observed combinations)
without employee identifiers. It is an endpoint cohort, not a longitudinal
time series. The report must use separate slicers for retention and audit.
Salary-budget variance and internal mobility are intentionally excluded.

## Verification

```powershell
python -m src.phase5.build_model
python -m unittest discover -s tests -p 'test_phase5_model.py' -v
python -m src.phase5.validate_sources
```

Microsoft Power BI Modeling MCP loaded the offline BIM and confirmed
13 tables, 51 measures, 13 relationships. PostgreSQL source projections,
dimension keys, fact-to-dimension references and 10 historical KPI
baselines passed. **Offline MCP cannot execute or validate DAX queries.**
Before publishing a report, open/import the model in Power BI Desktop,
configure the PostgreSQL credential (prefer a dedicated read-only role),
refresh, and run the provided DAX validation queries on the live engine.
Do not interpret metadata load or SQL baselines as live DAX execution.

On 2026-11-11, the user successfully refreshed the Power BI Desktop model;
all 51 measures were then executed through the live MCP DAX engine. Key
KPI comparisons and filter-context checks passed. See
[`../reports/phase5/dax_live_acceptance.md`](../reports/phase5/dax_live_acceptance.md).

Open `WorkforceIntelligence.pbip` in Power BI Desktop to inspect the model.
The former blank Model Preview is now **01 Executive Overview**, redesigned
to use the same full-height Navy sidebar, Teal accent, page numbering and
Year/Department slicer placement as Page 02. Its executive-specific main
visuals remain a large monthly line chart, department gap bars and a
department scorecard. **02 Workforce Planning** has
been **redesigned as a distinct Decision Cockpit**, with a dark vertical rail,
waterfall gap attribution, 100% attainment gauge, planned allocation treemap,
clustered Actual vs Plan columns and a July 2025 plan-reset note.
**03 Attrition Analysis** adds a rate-colored Department × Month matrix
heatmap, Hires vs Terminations monthly event-flow chart and 100%-stacked
voluntary/involuntary composition chart, with the January 2023 missing-rate
and 33/36-month source-quality caveats clearly stated.
**04 Retention & Engagement** uses a department-level bubble scatter
(Engagement × Performance, sized by employee count), Active/Exited cohort
comparison and endpoint population composition with explicit methodology
warnings. The **Year filter is deliberately replaced by Observation Endpoint**
because the underlying retention fact is not month-grained; Department
remains a functional slicer in its usual position.
**05 Recruitment Performance** is an operations board combining stacked-area
monthly Filled/Cancelled closeouts, speed-versus-throughput department
bubbles, an open requisitions backlog ranking, and 100% filled/cancelled
composition by department. Opening requisitions are a latest-month **stock**;
filled and cancelled are period **flows**. Closing share is not a candidate
funnel conversion rate.
**06 Data Quality & Trust** finishes the six-page suite with an imported
audit-status control tower (latest run ID/status, quality PASS/REVIEW/FAIL),
the company-wide reconciliation gap timeline, sorted pipeline run history
and per-run quality check register. Year filters reconciliation only;
Audit Run filters audit details. Department is deliberately absent because
company reconciliation is not department-grained.
See [six distinct page designs](../docs/phase5/00_report_experience_blueprint.md).
All six dashboard pages are implemented. Optional `.pbit` export,
final packaging and any release/publishing decision are still pending.
Desktop refresh and live DAX execution have been verified.
Never commit import caches, local settings or credentials.

The implemented Executive Overview layout is specified in
`../docs/phase5/01_executive_overview_spec.md`; a standalone color palette is
available at `themes/workforce_theme.json` and registered in the PBIR
report. To generate Page 01 from an **empty scaffolded report**, use
`python -m src.phase5.build_executive_report`. Its initial layout is now
superseded by `python -m src.phase5.redesign_executive_shell` (a one-time,
safe conversion that backs up the known original and refuses to overwrite
an already redesigned or user-edited page). The shared frame is defined in
`src/phase5/report_shell.py` for reuse on all remaining pages.

To repeat the 51-measure live smoke test while Desktop is open, run
`python -m src.phase5.live_dax_smoke` from the repository root.

See [Workforce Planning specification](../docs/phase5/02_workforce_planning_spec.md)
and [live acceptance evidence](../reports/phase5/workforce_planning_acceptance.md).
The original Page 02 builder (`python -m src.phase5.build_planning_report`)
is retained for historical reproducibility, but its former visual layout
has been superseded. The one-time conversion is
`python -m src.phase5.redesign_planning_report`; it only accepts the known
old Page 02, backs it up under ignored `data/interim/phase5`, and refuses
to overwrite a redesign or any user-edited page.

Page 03 was added using `python -m src.phase5.build_attrition_report`.
It refuses to overwrite an existing Page 03 and never modifies previous
pages or the semantic model. See the
[Attrition specification](../docs/phase5/03_attrition_analysis_spec.md)
and [Page 03 acceptance report](../reports/phase5/attrition_analysis_acceptance.md).

Page 04 was added using `python -m src.phase5.build_retention_report`, a
create-only PBIR generator that refuses to overwrite the page. See the
[Retention specification](../docs/phase5/04_retention_engagement_spec.md)
and [Page 04 acceptance report](../reports/phase5/retention_engagement_acceptance.md).

Page 05 was created with `python -m src.phase5.build_recruitment_report`.
It is additive/create-only and preserves the existing PBIR pages and DAX.
See [Recruitment page specification](../docs/phase5/05_recruitment_performance_spec.md)
and [Page 05 acceptance report](../reports/phase5/recruitment_performance_acceptance.md).

Page 06 was added using `python -m src.phase5.build_quality_report`.
This create-only generator checks all five previous pages before authoring.
See [Data Quality & Trust specification](../docs/phase5/06_data_quality_trust_spec.md)
and [Page 06 acceptance report](../reports/phase5/data_quality_trust_acceptance.md).
