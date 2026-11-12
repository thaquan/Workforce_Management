# Power BI — Workforce Intelligence

The **Power BI Project (PBIP)** in this directory is the editable reporting layer of the HR Workforce Intelligence portfolio. All six pages and the tabular semantic model are versioned as text definitions, so they can be reviewed in Git.

## Open the report

1. Follow the [project setup](../README.md) to start PostgreSQL and build the dbt data marts.
2. Open **`WorkforceIntelligence.pbip`** in **Power BI Desktop**.
3. If prompted, connect to PostgreSQL `127.0.0.1:5433`, database `workforce_dw`, using your local credentials. Refresh the Import model when needed.
4. Explore the report pages and edit visuals/measures in Desktop. Save the PBIP project before committing intended changes.

The source workbook and credentials are not stored in Git. The published Power BI Service copy is separate from this local project; its refresh depends on configured connectivity and gateway settings.

## Files

| Path | Purpose |
|---|---|
| `WorkforceIntelligence.pbip` | Entry point to open in Power BI Desktop |
| `WorkforceIntelligence.Report/` | Six report pages, theme and visual definitions (PBIR) |
| `WorkforceIntelligence.SemanticModel/model.bim` | Import model, tables, relationships and DAX measures |
| `dax/measures.dax` | Readable DAX measure definitions for study and review |
| `dax/validation_queries.dax` | DAX Query View examples to validate metric behavior |
| `dax/measure_catalog.md` | KPI list and formatting details |
| `themes/` | Navy–Teal report theme |

## Report content

| Page | Business analysis |
|---|---|
| **01 Executive Overview** | Headcount versus plan, overall workforce trends |
| **02 Workforce Planning** | Department plan gaps and capacity allocation |
| **03 Attrition Analysis** | Recorded exits, attrition heatmap and provisional rates |
| **04 Retention & Engagement** | Descriptive Active/Exited cohorts, engagement and performance |
| **05 Recruitment Performance** | Vacancy backlog and weighted recruitment throughput |
| **06 Data Quality & Trust** | Audit history and unresolved source reconciliation |

[View screenshots of all six pages](../docs/portfolio/README.md) · [Metric rules and source limitations](../docs/phase5/README.md)

## Run tests

```powershell
python -m src.phase5.report_validation
python -m unittest discover -s tests -p "test_phase5_*.py" -v
```

These are **offline structural tests**, not live DAX execution. Run `dax/validation_queries.dax` in the Power BI Desktop DAX Query View for live metric checks; optional SQL checks are provided by `python -m src.phase5.validate_sources` when the historical database is available.

**Source control:** Only commit intended PBIP/PBIR/model definitions. Never commit `.pbi` cache files, `.env`, source workbooks or employee-level exports. A Desktop save may touch many JSON files; inspect the Git diff before staging them.
