# Workforce Intelligence — Six distinct analytical experiences

**Design principle:** Six pages share the same enterprise identity, but must
not share the same visual skeleton. Different pages answer different management
questions; each receives a distinct primary visual, page hierarchy and
interaction pattern. Recoloring an identical KPI/line/bar/matrix layout is
not acceptable.

## Shared identity (not a shared template)

- 1280 × 720 Power BI native canvas; Segoe UI, no paid visual add-ons
- Navy `#102A43`, Teal `#087F8C`, Canvas `#F0F4F8`
- Orange `#D97706` for data caveats, Red `#DC2626` for negative variance
- **Identical report shell on every page:** full-height 276 px Navy left rail,
  3 px Teal accent, WORKFORCE INTELLIGENCE brand at (20,17), page index
  at (20,54), two-line page title at (20,91)/(20,126), subtitle at (20,180),
  main headline at (294,25), common Year and Department dropdowns at
  (857,12) and (1010,12). Keep this frame stable across all six pages.
- Clear page identifier, filters by relevant grain, exact units and sources
- Accessible labels and tooltips; do not turn color into the sole explanation
- No employee-level rows, credentials, source workbooks or cache in Git

## Six pages: different structures and chart families

| Page | Primary question | Composition | Distinctive visuals | Filtering caveat |
|---|---|---|---|---|
| **01 Executive Overview** | What is the overall workforce position? | **Shared Navy left rail** with headline workforce & trust KPIs, dominant monthly trend in main area, bottom department gap ranking and compact matrix | KPI cards, large monthly line chart, horizontal gap bars, matrix | Company reconciliation must not imply department attribution |
| **02 Planning Decision Cockpit** | Where is the staffing plan off track and how is it allocated? | **Vertical dark decision rail**, one waterfall hero, right-side treemap, bottom comparative columns | **Waterfall, attainment gauge, treemap, clustered columns** | Targets only exist at Month × Department; no Location/Level breakdown |
| **03 Attrition Analysis** | When, where, and what exit types contribute to attrition? | **Implemented:** diagnostic workbench with a color-coded month×department rate heatmap, monthly Hires vs Exits chart and exit-type composition panel | **Rule-colored matrix heatmap**, clustered monthly flow columns, **100% stacked bars** | January 2023 monthly attrition BLANK; 33/36 months under REVIEW |
| **04 Retention & Engagement Lab** | How do observable cohort characteristics differ? | **Implemented:** research canvas with department-level bubble scatter as hero, cohort scores upper right and Active/Exited composition with methodological notes below | **Scatter** engagement × performance, bubble size employee count, cohort columns and 100% composition bars | Endpoint aggregate only; **Year replaced by observation endpoint**, no time-series attribution, no causality |
| **05 Recruitment Operations** | How do recruiting volumes and speed differ? | **Implemented:** operational board with stacked month-by-month closed-request area as hero, a department recruiting-speed bubble scatter, backlog ranking and closeout composition | **Stacked area**, ranked open-backlog bars, department **bubble scatter**, **100% filled/cancelled** composition | Open requisitions are stock; filled/cancelled are flows — not sequential funnel stages |
| **06 Data Quality & Trust** | Can the team trust the analytics refresh? | **Implemented:** observability console with latest imported run & gate-status cards, reconciliation spike timeline, sorted run history, per-run quality register | **Status strip**, company reconciliation line, two auditable history/quality tables | Import snapshot, not live monitoring; Year filters reconciliation, Audit Run filters audit tables, no Department allocation |

## Page 01, shared shell conversion

The original Page 01 used a full-width dark header and a horizontal KPI row,
which made it appear to belong to another report. It now uses the **same
sidebar, brand, page index, typography hierarchy and top-right Year /
Department slicers** as Page 02. Content remains different by design:
full-width, prominent 36-month workforce trajectory; department gap ranking
and department matrix below; 4 workforce + 2 data-trust cards in the rail.
The previous Page 01 was backed up in ignored
`data/interim/phase5/executive_page_v1_*`. Neither Page 02 nor the model
was modified during the conversion.

## Page 02, implemented redesign

The first Page 02 copied the Executive Overview layout and has been replaced.
Its original PBIR definition is safely retained under ignored
`data/interim/phase5/planning_page_v1_*`. The redesign uses a Navy vertical
sidebar with Headcount Gap and FTE Gap, a **percent attainment gauge** with a
100% target (axis 0–125%; all 288 verified source ratios are at most ~120.3%),
a **waterfall** summing department positive/negative Headcount Gap to -80,
a **treemap** sized by Planned Headcount, and a full-width **clustered column**
comparison of Actual and Planned Headcount by department.

This is not a collection of more widgets for its own sake:

- Waterfall: *which departments explain the net shortage?*
- Treemap: *where is planned capacity allocated?*
- Clustered columns: *which departments are above/below plan in absolute HC?*
- Gauge: *how close is the selected workforce slice to the approved goal?*
- Sidebar: *what are the selected Headcount and FTE gaps?*

The source indicates a July 2025 planning reset in four departments. This
is a source scenario transition, **not a claim that restructuring caused
headcount changes**. Salary budget variance is withheld until units and
coverage are verified.

## Review gate for each future page

1. Approve its analytical question and source grain, independent of styling.
2. Select an appropriate **primary visual family not duplicated as the
   previous page's main composition**.
3. Generate and schema-validate PBIR; then preview against the actual
   Power BI Desktop model and inspect a screenshot before acceptance.
4. Validate DAX in the expected filter contexts, totals and blank cases.
5. Check visual density, truncation, color contrast and source caveats.
6. Run regression checks on previous pages and keep employee data private.

All **six report pages are implemented and validated in local Power BI
Desktop**. Final template packaging (`.pbit`), optional publishing and
GitHub commit/push are separate release tasks, **not yet completed**.
