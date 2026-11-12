# Page 02 — Workforce Planning

**Phase 5 project:** `powerbi/WorkforceIntelligence.pbip`

## Purpose and grain

This page compares actual workforce with the source plan, using **Month × Department**
from `marts.mart_workforce_plan_vs_actual`. Neither planned headcount nor FTE
targets can be distributed by Location or Level without additional source data.
Accordingly, the page provides **Year** and **Department** slicers only.

Current-month stock measures use the latest month in the active filter context:

- Planning Actual Headcount; Planned Headcount; Headcount Gap;
  Headcount Attainment %
- Planning Actual FTE; Budgeted FTE; FTE Gap

Headcount and FTE are *stocks* at the final month in the selected year or
department filter. The redesigned page prioritizes **drivers and allocation**
instead of repeating Executive Overview's monthly trajectory.

## PBIR implementation

| Region | Visual | Bindings |
|---|---|---|
| Left vertical Navy rail | Headcount Gap card, 0–125% attainment gauge with 100% target, Planned HC and FTE Gap cards | Measures at last selected month |
| Top right | 2 dropdown slicers | `Dim Month[year]`, `Dim Department[department]` |
| Center-left hero | Waterfall with Total | `Dim Department[department]` vs `[Headcount Gap]` |
| Center-right | Treemap for approved capacity allocation | `Dim Department[department]` vs `[Planned Headcount]` |
| Bottom full width | Clustered column comparison | Actual HC versus Planned HC by department |
| Context note | Orange text beside subtitle | Historical July 2025 plan reset in four departments |

The page uses the existing Navy–Teal palette, 1280×720 canvas and native
Power BI visuals. Unlike Executive Overview's horizontal scorecard, line
chart, bars and matrix, this is a **decision cockpit with a vertical rail,
waterfall, gauge, treemap and clustered columns**. The waterfall's native
Total shows the net Gap rather than implying gaps are positive quantities.

## Verified source data and business context

| Reporting period | Actual HC | Planned HC | Gap | Actual FTE | Budgeted FTE |
|---|---:|---:|---:|---:|---:|
| January 2023 | 622 | 989 | -367 | 601.0 | 965.0 |
| June 2025 | 1,021 | 1,151 | -130 | 989.0 | 1,123.2 |
| July 2025 | 939 | 1,049 | -110 | 910.2 | 1,024.2 |
| December 2025 | 999 | 1,079 | -80 | 968.6 | 1,053.8 |

The source identifies a **Post-restructuring reset** scenario for Sales,
Marketing, Operations and Customer Success from July through December 2025
(4 departments × 6 months = 24 target rows). These are planning source facts;
the report makes **no causal claim** that restructuring created the observed
headcount change. Salary budget units/coverage are still unverified, so salary
budget variance is not shown.

## Quality checks

- PBIR validator: 0 errors and 0 warnings.
- Real Desktop load and screenshot inspected; values shown are from imported
  PostgreSQL data, not a fabricated image.
- Offline tests check 27 visual elements, distinct chart families, page
  order, canvas bounds, unique IDs and source-validated bindings.
- Live DAX checks compare source-month snapshots and DAX results. Retain the
  33-month reconciliation REVIEW caveat from earlier phases.

## Next page

Page 03 Attrition Analysis should emphasize monthly trends, voluntary and
involuntary exits, and **provisional rate quality** when employee-as-of and
snapshot headcount disagree. No inferred mobility or individual causality.
