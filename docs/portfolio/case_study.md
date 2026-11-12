# Case Study — From Workforce Excel to a Tested Analytics Platform

## Context / business problem

Workforce leaders need to compare headcount/FTE against staffing plans, investigate recorded hires and exits, evaluate recruitment workload and understand whether reported metrics are reliable. The available dataset arrived as a **12-sheet Excel workbook**, not as a maintained database or data warehouse.

The engineering challenge was to turn heterogeneous historical tabs into consistent, testable analytical facts and a Power BI experience without hiding known source-data inconsistencies. **This is a portfolio case study based on historical data, not evidence of a live deployment improving a company's HR outcomes.**

## Data scope and fidelity

- **29,728** source records across **12 sheets**, including employee profiles and historical facts.
- **1,200** source employee profiles; reporting snapshots span January 2023–December 2025.
- The source date dimension did not cover all historical employment events; the warehouse derives an extended calendar without editing source rows.
- **33/36** company headcount snapshot months disagree with employee-as-of reconciliation. June 2025 has a **+98** discrepancy. This is a documented **REVIEW**, not a hidden correction.

The original workbook is kept local and is **not** distributed with the public repository.

## Engineering approach

| Layer | What was implemented | Verification |
|---|---|---|
| Profiling | Sheet inventory, row-count checks, key/grain identification, source decisions | Phase 1 quality reports |
| Ingestion | Validated Python ingestion into PostgreSQL raw tables; transactional write, SHA-256 audit and idempotency | Phase 2 tests and recovery cases |
| Transformation | dbt Core staging/intermediate views, dimensional model and analytics marts | 36 dbt models, 83 full-data tests |
| Data quality | Contract checks, persisted run state, source reconciliation and recovery logic | 18 quality gates; BLOCK vs REVIEW policy |
| CI | GitHub Actions with disposable PostgreSQL and fabricated source rows | 116 synthetic dbt build/test steps; separate Python tests |
| BI | Power BI PBIP/PBIR report and semantic model | 51 DAX measures, six distinct analytical pages and automated offline tests |

The deployed architectural boundary is local PostgreSQL + Power BI. The **GitHub CI uses a separate synthetic database** and never pulls the original HR workbook.

## Analytics experience

The six Power BI pages were deliberately designed around different management questions, not copied and recolored templates. They share a Navy/Teal report shell and consistent terminology.

1. **Executive Overview:** monthly stock metrics, plan comparison and organizational gap.
2. **Workforce Planning:** waterfall and attainment gauge, including July 2025 target reset caveats.
3. **Attrition Analysis:** recorded exit composition and provisional rates; missing January 2023 rates remain BLANK.
4. **Retention & Engagement:** endpoint-based department cohorts and exploratory score comparisons without causal claims.
5. **Recruitment Performance:** period flows versus ending open-requisition stock; weighted time to fill.
6. **Data Quality & Trust:** independent operational and data-trust indicators, including audit run history and review issues.

[Explore screenshots of all six pages](README.md) · [Read the original Power BI model](../../powerbi/README.md)

## Verified analytical examples

| Observation | Why it matters | Limitation |
|---|---|---|
| Dec 2025 headcount **999** vs planned **1,079** | Summarizes the **−80** workforce gap | Uses supplied source snapshots |
| Dec 2025 FTE **968.6** vs budget FTE **1,053.8** | Exposes capacity gap beyond employee counts | Plan targets change in Jul 2025 for selected departments |
| Jun 2025 recorded **98 terminations** | Reveals an exceptional monthly event spike | Not proof of underlying cause or department transfer |
| 2023–2025 **890 filled / 356 cancelled** | Separates recruiting closeout events from vacancy backlog | Counts are historic, not current openings |
| Latest imported audit **14 PASS / 4 REVIEW / 0 FAIL** | Execution and source quality are presented separately | Import snapshot requires refresh; not live monitoring |

## Engineering tradeoffs and decisions

- **PostgreSQL + dbt Core instead of paid warehousing:** local, repeatable and affordable for the current scale; realistic dimensional modeling and testing.
- **Power BI Import mode:** interactive measures and curated model, but refresh requires access to the local database and, on Power BI Service, a configured gateway. Publishing a report does not automate the database.
- **Known inconsistencies stay visible:** the workflow distinguishes blocking technical failures from business-source review findings instead of “fixing” the data to make dashboards green.
- **No invented SCD Type 2 or internal-mobility metrics:** history of department transfers is unavailable.
- **No published row-level employee records:** public source control includes model code, schemas, documentation, synthetic test fixtures and aggregate screenshots.

## Validation strategy

The private-data path is validated locally against the historical workbook; source-specific baseline tests are not appropriate for synthetic data. GitHub Actions instead seeds a small, fabricated workforce dataset, builds the dbt warehouse and executes general integrity and recovery tests. The CI job also runs offline Power BI semantic-model/report tests without requiring Desktop or a real workbook.

**Last validated project baseline (November 2026):** six PBIR pages, 51 DAX measures, **49 Phase 5/portfolio offline tests**, dbt synthetic CI build **116/116**, and quality findings retained as REVIEW when appropriate. These are test results, **not** claims of measurable business impact.

## Practical portfolio takeaway

This project demonstrates a complete vertical slice from data profiling, transactional ingestion, dimensional modeling and automated quality gates through report UX and semantic-model design. The deliberately unresolved source exceptions are part of the engineering story: correct reporting requires clear data contracts, denominators and governance, not just visually attractive dashboards.

**Next technical investment:** orchestration with Dagster OSS, followed by incremental and performance testing on synthetic data. These are **planned**, not represented as delivered in the project baseline. See [the Dagster extension plan](../phase7/dagster_extension_plan.md).
