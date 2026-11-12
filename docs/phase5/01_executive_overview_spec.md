# Phase 5 — Executive Overview report specification

## Status

- **Model/DAX:** 51 measures executed on Power BI Desktop; key KPIs and
  filter-context behavior reconciled with PostgreSQL. See
  `reports/phase5/dax_live_acceptance.md`.
- **Report implementation:** Redesigned after user visual review. Page 01 now
  uses the **same Navy vertical sidebar, page identity, two-line title,
  main headline and Year/Department filter positions** as Page 02. Its
  29 PBIR elements retain an executive-specific large monthly line chart,
  department horizontal gap bars, scorecard, four workforce KPI cards and
  two data-trust cards. The previous layout was backed up under ignored
  `data/interim/phase5/executive_page_v1_*`.
- **Validation:** Power BI report schema passed with **0 errors / 0 warnings**;
  Desktop loaded the latest report and a screenshot confirmed the data-bound
  visuals. Department gap chart and matrix remain scrollable on 1280×720.
- **Publication:** Local development only. Do not publish employee-related
  data to Power BI Service or GitHub.

## Design identity

Product: **Workforce Intelligence — HR Executive Overview**

- Canvas: **1280 × 720**, 16:9, FitToPage
- Style: modern enterprise analytics, light canvas and restrained color
- Palette: Navy `#102A43`, Teal `#087F8C`, Canvas `#F0F4F8`, White
  `#FFFFFF`, Gray `#627D98`, Warning `#D97706`, Critical `#DC2626`
- Font: Segoe UI
- Desktop target: `powerbi/WorkforceIntelligence.pbip`
- No custom visuals or paid licenses

## Executive Overview visual contract

| Region (x,y,w,h) | Visual | Binding | Behavior |
|---|---|---|---|
| 0,0,276,720 | Shared Navy sidebar with Teal accent | Brand, page number, two-line page title | Same shell as Page 02 |
| 18,239,238,70 | Sidebar KPI | `[Ending Headcount]` | Last selected month |
| 18,326,238,70 | Sidebar KPI | `[Planned Headcount]` | Last selected month; Month×Department only |
| 18,413,238,70 | Sidebar KPI | `[Headcount Gap]` | Actual minus plan; signed value |
| 18,500,238,70 | Sidebar KPI | `[Ending FTE]` | Last selected month |
| 18,608,237,70 | Sidebar trust cards | `[Reconciliation Review Months]`, `[Latest Quality FAIL]` | Do not attribute to department |
| 857,12 / 1010,12 | Shared dropdowns | `Dim Month[year]`, `Dim Department[department]` | Same positions and labels as Page 02 |
| 298,148,957,275 | Large line chart | `Dim Month[month]`; `[Ending Headcount]`, `[Planned Headcount]` | Monthly trend; no summation of stock |
| 299,484,434,219 | Horizontal bar | `Dim Department[department]`; `[Headcount Gap]` | Variance by department; labels preserve sign |
| 755,484,499,219 | Department matrix | Department + actual HC, plan HC and gap | Correct grand totals; FTE appears in sidebar |

Section labels appear above charts and the matrix. Shared sidebar/navigation
elements match the planning cockpit, but the main analytical composition
intentionally differs. All KPI values remain bound to DAX measures.

## Interaction and trust rules

1. Default view uses the most recent reporting month (Dec 2025 for the
   verified workbook). Historical trend retains 36 monthly points.
2. Year and Department filters apply to relevant facts. No Location or
   Level slicer will be exposed on Executive Overview because planning
   is not available at those grains.
3. Department selection must not reattribute a company-wide reconciliation
   mismatch to a department. Disable chart-to-quality interactions or show
   a non-attributable label when department is selected.
4. Attrition is marked **Provisional — source headcount reconciliation**.
   Do not imply the 33 historical REVIEW months were repaired.
5. Employee-level retention profiles, individual salaries and other
   personal rows are not imported into this executive report.

## Known visual acceptance checks

- Full-year 2025 Ending HC card = **999**, not a sum of 12 months.
- Dec 2025 Planned HC = **1,079**, Gap = **-80**, Ending FTE = **968.6**.
- Department D001 at Dec 2025: HC = **346**, Plan = **350**.
- Quality card: **33** reconciliation review months; **0** latest
  blocking quality failures (for the latest verified pipeline audit).
- All report visuals bind to the live semantic model `_Measures` measures.
- PBIR schema and the fresh Desktop screenshot have both been reviewed.

## Follow-on pages (not implemented in this batch)

02 Workforce Planning; 03 Attrition; 04 Retention & Engagement;
05 Recruitment; 06 Data Quality & Trust.
