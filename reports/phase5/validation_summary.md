# Power BI validation summary

The report is a historical HR analytics case study. The reproducible source of truth is the checked-in Power BI Project (`powerbi/WorkforceIntelligence.pbip`) and the dbt warehouse, not screenshots or one-time authoring logs.

## Model and report checks

| Check | Expected result | How to verify |
|---|---|---|
| Power BI report | Six distinct pages, valid relationships and bindings | `python -m src.phase5.report_validation` |
| Semantic model | 13 tables (including measure host), 13 relationships, 51 measures | `python -m unittest discover -s tests -p 'test_phase5_model.py' -v` |
| Public dashboard gallery | Six 16:9 aggregate screenshots and valid internal links | `python -m unittest discover -s tests -p 'test_phase5_portfolio.py' -v` |
| Offline project tests | Entire Power BI/portfolio suite passes without Desktop | `python -m unittest discover -s tests -p 'test_phase5_*.py' -v` |
| Live DAX calculations | Numerator, denominator, stock/flow and filter contexts | `powerbi/dax/validation_queries.dax` in Power BI Desktop |
| Warehouse historical baselines | Headcount, plan gaps, source reviews, recruitment flow | `python -m src.phase5.validate_sources` on an authorized local dataset |
| CI | Synthetic-only PostgreSQL/database tests | `.github/workflows/quality-ci.yml` |

The offline tests cannot prove a live Power BI Service refresh succeeded. For published reports, check gateway credentials, refreshed data period and permissions separately.

## Known historical results

| Subject | Value | Context |
|---|---:|---|
| December 2025 ending headcount | 999 | Latest workforce snapshot |
| December 2025 planned headcount | 1,079 | Latest planning scenario |
| December 2025 headcount gap | −80 | Actual less planned |
| December 2025 ending FTE | 968.6 | Latest actual |
| 2023–2025 hires recorded in event mart | 597 | Period flow |
| 2023–2025 terminations | 206 | 81 voluntary, 125 involuntary |
| June 2025 recorded terminations | 98 | 96 involuntary, 2 voluntary |
| Recruitment filled / cancelled | 890 / 356 | Period flows |
| December 2025 open requisitions | 49 | Month-end stock |
| Latest known quality gates in historical demo | 14 PASS / 4 REVIEW / 0 FAIL | Audit Import snapshot, not necessarily current |
| Source months with reconciliation mismatch | 33 / 36 | **REVIEW**, not silently fixed |

## Important interpretation notes

- **January 2023 attrition is BLANK**, because December 2022 is not in the reporting denominator history.
- Source employee-as-of and snapshot headcount disagree in most months. Attrition rates are provisional.
- Recruitment open requisitions are not additive over time; period fills and cancellations are.
- Retention engagement/performance comparisons are descriptive endpoint cohorts; no causal or individual risk claim is made.
- The original workbook and Power BI import cache are intentionally excluded from GitHub.

[Project README](../../README.md) · [Power BI setup](../../powerbi/README.md) · [Dashboard gallery](../../docs/portfolio/README.md)
