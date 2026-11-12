# Phase 5 — Power BI dashboard

## Goal

Build an interactive HR analytics report on top of the PostgreSQL/dbt data marts. The report is stored in an **editable Power BI Project (PBIP)** rather than a compiled PBIX file. Power BI Desktop is used to maintain the report and semantic model.

- **Entry point:** [`powerbi/WorkforceIntelligence.pbip`](../../powerbi/WorkforceIntelligence.pbip)
- **Semantic model:** `powerbi/WorkforceIntelligence.SemanticModel/model.bim`
- **Report definition:** `powerbi/WorkforceIntelligence.Report/definition/`
- **DAX source catalog:** [`powerbi/dax/`](../../powerbi/dax/)
- **Screenshots:** [Six-page gallery](../portfolio/README.md)
- **Testing and baseline evidence:** [Validation summary](../../reports/phase5/validation_summary.md)

## Report pages

| Page | Focus | Main visuals |
|---|---|---|
| 01 Executive Overview | Workforce size and gap to plan | Trend line, department variance bars, KPI cards |
| 02 Workforce Planning | Planned vs actual HC and FTE | Waterfall, gauge, treemap, comparison columns |
| 03 Attrition Analysis | Exits and provisional rates by month | Heatmap, monthly events, exit composition |
| 04 Retention & Engagement | Active/Exited observation cohorts | Department bubble scatter, cohort comparisons |
| 05 Recruitment Performance | Open demand, completed recruitment | Stacked area, bubble scatter, department bars |
| 06 Data Quality & Trust | Refresh audit and source limitations | Quality-status cards, reconciliation line, audit tables |

Each page follows the same Navy–Teal visual identity while using a layout suited to its question.

## Dataset and modeling rules

The semantic model imports **12 analytical data tables plus one measure table** and defines **51 DAX measures**. The warehouse supplies the calculations at known grains; DAX mainly handles filter context, last-period stocks and period totals.

- **Ending headcount, FTE, planned headcount and open requisitions** are stocks. They cannot be summed over months.
- **Hires, terminations, filled and cancelled requisitions** are flows and can be summed across the selected period.
- **Attrition** uses snapshot headcount denominators. January 2023 has no previous month and therefore remains BLANK. Other supported rates are provisional while the historical snapshot mismatch remains unresolved.
- **Retention** uses endpoint cohorts, not historical department assignments. Associations between engagement and exit status are not causal.
- **Quality** distinguishes a technically successful pipeline from source-data checks requiring business review.

See the more detailed [KPI semantics](../phase3/02_kpi_semantics.md) and [case study](../portfolio/case_study.md).

## How to edit the Power BI project

1. Start PostgreSQL with `docker compose up -d postgres`; make sure the data warehouse has been built (see the [root README](../../README.md)).
2. Open `powerbi/WorkforceIntelligence.pbip` with Power BI Desktop.
3. Configure credentials for PostgreSQL at `127.0.0.1:5433` / `workforce_dw`, then refresh if a source connection is available.
4. Edit visuals and DAX measures in Desktop, and **Save** the PBIP project.
5. Review Git changes under `powerbi/`. Commit only the intended report/semantic-model edits and never include `.pbi` caches or local credentials.
6. Run the portable source checks below before pushing.

The checked-in PBIR files are the report source of truth. The report can be edited and saved directly in Power BI Desktop.

## Validate without Power BI Desktop

```powershell
python -m src.phase5.report_validation
python -m unittest discover -s tests -p "test_phase5_*.py" -v
```

These checks inspect the static semantic-model/report source and gallery assets. They do **not** execute DAX measures against a live engine. For numerical validation, review [`powerbi/dax/validation_queries.dax`](../../powerbi/dax/validation_queries.dax) in Power BI Desktop's DAX Query View and compare to PostgreSQL marts. The optional read-only SQL baseline checks require the historical dataset:

```powershell
python -m src.phase5.validate_sources
```

## Known limitations

- 33 of 36 snapshot months require historical headcount reconciliation review, especially June 2025 (+98).
- No effective-dated department transfer history is present; internal mobility is not implemented.
- Salary-budget period/currency/coverage are not confirmed; salary-budget variance is disabled.
- The source ends in December 2025. Power BI Service refresh needs separate gateway and credential configuration; it does not update source records automatically.

The above limitations are intentionally documented rather than masked in the report.
