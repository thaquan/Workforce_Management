# Phase 5 — Attrition Analysis acceptance (local Power BI Desktop)

Date: 2026-11-11. Page: `03 Attrition Analysis` in
`powerbi/WorkforceIntelligence.pbip`.

## Data & DAX verification

| Source period/scenario | PostgreSQL | Live DAX | Result |
|---|---:|---:|---|
| Hires, Jan 2023–Dec 2025 | 597 | 597 | PASS |
| Terminations | 206 | 206 | PASS |
| Voluntary terminations | 81 | 81 | PASS |
| Involuntary terminations | 125 | 125 | PASS |
| Rolling 12M attrition, Dec 2025 | 14.7258% | 14.7258% | PASS — provisional |
| June 2025 hires / exits | 18 / 98 | 18 / 98 | PASS |
| June 2025 voluntary / involuntary exits | 2 / 96 | 2 / 96 | PASS |
| June 2025 Sales exits / rate | 42 / 19.95% | 42 / 19.95% | PASS |
| January 2023 monthly attrition | No prior HC | BLANK | PASS |
| Months requiring reconciliation REVIEW | 33 / 36 | Source warning in report | REVIEW by design |

## Visual acceptance

- Common Navy sidebar, Teal accent, page index, two-line title, Year and
  Department filters match the other two report pages.
- Page 3 has a distinct **color-coded department × month matrix heatmap**,
  **Hires vs Terminations clustered columns**, and **100% exit-type
  composition bars**. Native visuals only.
- Heatmap was verified on a real Power BI Desktop screenshot: the final
  rule-based color thresholds render light teal, amber and coral with
  visible numeric percentages. The first month with unavailable rate
  is not presented as a false 0%.
- The June 2025 spike is visible in the monthly event-flow chart; the
  source remains marked Provisional rather than silently reconciled.
- PBIR schema validation: **0 errors, 0 warnings**.
- Original Executive Overview and Workforce Planning pages preserved.

## Current limits

- User may select Year to reduce the 36-column heatmap to 12 months;
  horizontal scrolling is available for the All selection.
- The compact 100% exit mix chart scrolls to show all eight departments.
- Neither chart implies a causal interpretation of the June anomaly;
  no inferred internal transfers or salary-budget metrics are displayed.
- Remaining pages: 04 Retention & Engagement, 05 Recruitment Performance,
  06 Data Quality & Trust. No cloud publish or GitHub push performed.
