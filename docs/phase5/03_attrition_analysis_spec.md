# Page 03 — Attrition Analysis

Power BI project: `powerbi/WorkforceIntelligence.pbip`

## Purpose and source grain

This is a **diagnostic page**, not another planning scorecard. It answers:
*When did the workforce experience employee exits, which departments
contributed, and what share were voluntary versus involuntary?*

Model: `Fact Attrition` from `marts.mart_attrition_monthly`, at **Month ×
Department** grain. The report uses existing tested `_Measures` measures;
it does not calculate headcount or attrition rates from individual employees
in Power BI. Year/Department slicers appear at the same positions as Page 01
and Page 02. Location/Level slicers are intentionally excluded because
attrition metrics are not available at those grains.

## Layout — distinct content with common branding

Shared shell: full-height 276 px Navy rail with a Teal accent, a consistent
page number (**03 / 06**), two-line page name, and common Year/Department
dropdowns. Main content differs from both earlier pages:

| Section | Native Power BI visual | Measure/field mapping |
|---|---|---|
| Sidebar period totals | Four separate cards | Hires, Terminations, Voluntary Terminations, Involuntary Terminations |
| Sidebar rate | Card | Rolling 12M Attrition % |
| Primary diagnostic | **Matrix heatmap** | Rows Department, Columns `Dim Month[year_month]`, Values Monthly Attrition % |
| Bottom left | **Clustered columns** | Month, Hires vs Terminations; voluntary and involuntary tooltip |
| Bottom right | **100% stacked horizontal bars** | Department, Voluntary vs Involuntary Terminations |
| Quality annotation | Text + explicit rate thresholds | 33/36 months under reconciliation review, January 2023 unavailable |

This differs from the Executive Overview's large workforce line chart and
the Planning Decision Cockpit's waterfall, treemap and attainment gauge.
Native visuals and local semantic model only; no paid custom visuals.

## Heatmap conditional formatting

The heatmap uses Power BI `pivotTable` with **rule-based conditional cell
formatting**, not a static screenshot or hand-colored cells:

| Monthly department attrition rate | Background | Interpretation |
|---|---|---|
| 0% to below 2% | Light teal `#DDF3F0` | Low observed rate |
| 2% to below 8% | Light amber `#FDE6A5` | Moderate observed rate |
| 8% and above | Light coral `#F7A99B` | High observed rate |
| BLANK | White/uncolored | Missing valid denominator; **not 0%** |

The rules compare raw DAX percentage decimals `0D`, `0.02D`, `0.08D`;
the values display with percent formatting. The actual matrix values and
colors were inspected in Power BI Desktop. A trial `FillRule` gradient
initially resulted in an empty matrix even though schema validation passed;
the final, rendered solution uses `Conditional.Cases[]`. Year selection
focuses the 36-month matrix on 12 months; the default All view permits
horizontal scrolling. January 2023, whose rates are all BLANK, may be
suppressed as a matrix column rather than falsely showing 0%.

## Source quality and baseline semantics

- 2023–2025 recorded facts: **597 hires** and **206 terminations**:
  **81 voluntary** and **125 involuntary**. The 597 hires are **not** the
  same as all historical hire events in the employee source.
- **June 2025:** 18 hires and **98 terminations**, comprising **2 voluntary**
  and **96 involuntary**. Among exits: Sales 42, Customer Success 25,
  Operations 19, Marketing 12. These are recorded-event counts, not
  causal explanations for the anomaly.
- The monthly attrition denominator is the average of prior and current
  monthly snapshot headcounts. **January 2023 is BLANK**, because December
  2022 is missing. The source does not support replacing the denominator
  with 1,200 employee profiles or treating missing rate as 0%.
- **33 of 36** company-wide months have reconciliation REVIEW flags. All
  280 department-month rates with a denominator are **Provisional**, since
  both current and prior company reconciliation status must match for a
  reference-matched rate. This caveat remains visible on Page 3.
- At December 2025, rolling 12-month attrition is **14.73%** based on the
  agreed, SQL-validated rate definition. It is provisional.
- Open events are **flows** (sums within the selected period), not monthly
  headcount stocks. Hires minus terminations is not a claimed reconciliation
  of snapshot headcount. The 100% bars illustrate **composition within each
  department**, not comparative employee counts.

## Verification and restrictions

- PBIR validation: **0 errors / 0 warnings**.
- Live DAX checks against PostgreSQL confirm full-period event totals, June
  2025 anomaly and January 2023 missing rate.
- Retains original 51-measure semantic model and prior two pages unchanged.
- Uses `tests/test_phase5_attrition_report.py` to check layout, bindings,
  rate band rules, common sidebar and privacy constraints.
- No employee-level rows, salary details, raw workbooks, credentials or
  imported cache in the committed-source candidate; no cloud publication.
