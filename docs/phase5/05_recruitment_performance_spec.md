# Page 05 — Recruitment Operations Board

Power BI project: `powerbi/WorkforceIntelligence.pbip`.

## Goal and grain

This operational page answers *How many requisitions are still open, what
closeouts occurred, and which departments need recruiting attention?* Its
underlying fact is `marts.mart_recruitment_monthly` at **Month × Department**
grain. The page uses the existing 51-measure semantic model; there are no
applicant-level rows or additional Power BI paid visual dependencies.

**Critical stock/flow distinction:**

- **Ending Open Requisitions** is the stock in the *latest selected month*.
  Do not sum open requisitions over a year or across multiple months.
- **Filled Requisitions** and **Cancelled Requisitions** are flows summed
  over the selected reporting period.
- **Weighted Days to Fill** divides `SUM(filled × avg_days_to_fill)` by
  the number of fills with a known average time, not an unweighted mean
  across months or departments.
- **Fill Share of Closed Requisitions** is `filled / (filled + cancelled)`
  for observed closeouts, **not** a candidate-to-hire funnel conversion rate.

## Distinct visual layout, common brand

Page 5 retains the 276 px Navy sidebar, 3 px Teal accent, page index and
top-right Year / Department slicers in the same positions as Pages 1–3.
Its central content has its own **recruitment operations layout**, distinct
from the Executive timeline, Planning waterfall, Attrition heatmap and
Retention cohort lab.

| Region | Visual | Binding / interpretation |
|---|---|---|
| Left Navy rail | 5 KPI cards | Latest Open; period Filled, Cancelled; weighted Days to Fill; closed Fill Share |
| Top-left hero | **Stacked area chart** | Month, Filled and Cancelled requisitions. These are monthly closeout outcomes |
| Top-right | **Bubble scatter** | Current department; X = Weighted Days to Fill, Y = Filled Requisitions, bubble size = Ending Open Requisitions |
| Bottom-left | Ranked horizontal backlog bars | Department and latest Ending Open Requisitions |
| Bottom-right | **100% closed-outcome bars** | Department share of Filled versus Cancelled requisitions |

The bubble chart combines the department's selected-period pace/throughput
with its *latest-month* backlog. This is a diagnostic comparison, not a
time-series trend or a per-requisition scatter. Both bar charts support
vertical scrolling for additional departments on the compact canvas.

The first draft had a four-metric matrix that required horizontal scrolling
to reveal most columns. After a Power BI Desktop screenshot review, it was
replaced with the compact closed-outcome composition chart. The old matrix
PBIR is retained only in ignored `data/interim/phase5` as a local backup.

## Source and live DAX acceptance baselines

| Selection | Latest open | Filled flow | Cancelled flow | Weighted days to fill | Filled share of closed |
|---|---:|---:|---:|---:|---:|
| Entire Jan 2023–Dec 2025 | 49 | 890 | 356 | 50.0112 | 71.43% |
| Year 2024 | 42 | 303 | 88 | 50.8746 | 77.49% |
| Year 2025 | 49 | 272 | 172 | 48.2574 | 61.26% |
| December 2025 | 49 | 26 | 8 | 49.2308 | 76.47% |
| Engineering, entire period | 14 | 311 | 36 | 53.8392 | 89.63% |
| Engineering, December 2025 | 14 | 7 | 2 | 48.0 | 77.78% |

These are **source-specific historical baselines**, not current 2026 hiring
conditions. Recruitment mart ends in December 2025. Source contains 288
department-month rows and 43 rows without a known average time-to-fill;
none of those 43 rows reports positive fills, so all 890 observed fills
contribute to the verified weighted duration. Historical observations are
not inferred to be up-to-date recruiting demand.

## Quality and release conditions

- The stored PBIR report is structurally validated with no errors/warnings.
- Screenshots were inspected after an actual Desktop reload; all charts
  and KPI cards rendered with data, and the initial horizontally scrolling
  matrix was replaced with an interpretable percentage composition chart.
- Year 2024, Year 2025, December 2025 and Engineering DAX filter contexts
  were reconciled against SQL baselines above.
- Location or Level selection on Recruitment DAX measures returns BLANK,
  because the source does not support disaggregating those metrics there.
- A Page 5-specific offline regression suite confirms source fields,
  stock/flow visual roles, common shell and privacy exclusions.
- This is local PBIR only. No Power BI Service publishing or GitHub push.
