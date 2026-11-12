# Phase 5 — Workforce Planning acceptance

Date: 2026-11-11. Local project `WorkforceIntelligence.pbip`.

| Gate | Outcome |
|---|---|
| Existing Executive Overview preserved | PASS |
| New page `02 Workforce Planning` | PASS |
| PBIR schema | PASS — 0 errors, 0 warnings |
| Actual Power BI Desktop preview and screenshot reviewed | PASS |
| December 2025 Actual / Planned HC | 999 / 1,079 |
| December 2025 Headcount Gap / Attainment | -80 / 92.6% |
| December 2025 Actual / Budgeted FTE | 968.6 / 1,053.8 |
| December 2025 FTE Gap | -85.2 |
| July 2025 plan-reset departments | 4 — source verified |
| Live DAX June 2025 Actual / Planned / Gap | 1,021 / 1,151 / -130 — PASS |
| Live DAX July 2025 Actual / Planned / Gap | 939 / 1,049 / -110 — PASS |
| Live DAX December 2025 Actual / Planned / Gap | 999 / 1,079 / -80 — PASS |
| Live Department D008 Gap | -51 — PASS |
| Live Department D003 Gap | +10 — PASS |
| Live Post-restructuring rows | 24 — PASS |
| Planning PBIR offline regression tests | 8/8 PASS (redesigned composition) |
| Executive Overview regression tests | 5/5 PASS |
| Planning waterfall department gap total | -80, visual rendered |
| Gauge target and current attainment | 100% target / 92.6% actual |
| Treemap and clustered columns | Planned allocation & Actual/Plan comparison rendered |

**Redesigned after UX review.** The earlier layout repeated Executive
Overview's KPI row + monthly line chart + department bars + matrix. The
replacement uses a strongly different *vertical Navy decision rail* and
three complementary chart types: waterfall for net positive/negative gap,
treemap for planned-capacity allocation, and side-by-side clustered columns
for department actual-vs-plan comparison. A 100%-target gauge communicates
the current plan attainment accurately. Desktop screenshots confirm
Headcount Gap -80, Planned HC 1,079, 92.6% attainment and FTE Gap -85.2.

The old Page 02 definition was backed up to ignored
`data/interim/phase5/planning_page_v1_*`. Executive Overview and the
semantic model were not changed. No employee identifiers, record-level
compensation data or credentials were included.

Three monthly DAX test cases also verified exact **Actual FTE / Budgeted
FTE** pairs against SQL: 989.0 / 1,123.2 (June), 910.2 / 1,024.2 (July),
968.6 / 1,053.8 (December). The 24 post-restructuring rows correspond to
four departments over six months. The report does not treat this change
in planning scenario as a causal estimate of restructuring impacts.

No Power BI cloud publishing or GitHub push is part of this local milestone.
