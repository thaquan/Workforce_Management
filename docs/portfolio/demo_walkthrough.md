# Portfolio Demo Walkthrough — 3–5 Minutes

Audience: hiring manager, Data Engineer interviewer or Data Analyst / BI interviewer.

Before demonstrating, open the [six-page screenshot gallery](README.md), the [data engineering case study](case_study.md), or the editable local Power BI project (if the authorized data source is available). Public screenshots contain **aggregate information only**. If using Power BI Service, obtain a permission-appropriate viewer link from the owner; do not use a public publish-to-web URL unless the underlying data has been approved for public sharing.

## Suggested speaking sequence

**0:00–0:35 — Problem and outcome**

> I built an end-to-end workforce intelligence platform using Python, PostgreSQL, dbt Core and Power BI. It takes a twelve-sheet historical HR workbook through validated ingestion, a dimensional warehouse, 51 DAX measures and six management-focused report pages. Quality and reconciliation issues are explicitly tracked rather than hidden.

**0:35–1:20 — Data Engineering architecture**

Show the [architecture overview](architecture.md). Explain:
- Twelve typed raw tables, transactional ingestion and content-based idempotency.
- Staging/intermediate transformations and dimensional marts built by 36 dbt models.
- Technical BLOCK versus source REVIEW rules and persisted pipeline audits.
- GitHub Actions running synthetic-only tests, so raw HR data never reaches CI.

**1:20–2:10 — Executive and workforce planning decisions**

Open **Page 01** then **Page 02**. Use the December 2025 example: 999 ending HC vs 1,079 planned, gap **−80**. Move from the overall trend to the Planning waterfall and treemap. State that a source target reset occurred in July 2025, so plan comparisons need this context.

**2:10–2:55 — Diagnosing attrition and retention**

Open **Page 03** and point to the June 2025 exit spike: **98 recorded terminations**. Explain provisional attrition rates and why January 2023 is BLANK. Open **Page 04** and explain department-level engagement/performance bubbles and Active/Exited cohort composition. Do not interpret correlations as causes.

**2:55–3:35 — Recruitment operations**

Open **Page 05**. Distinguish the **latest-month stock** of open positions from **monthly flows** of filled and cancelled requisitions. Explain weighted Days to Fill rather than taking a simple average across unequal departments.

**3:35–4:15 — Reliability and limitations**

Open **Page 06**. Highlight the latest imported pipeline status **SUCCEEDED**, alongside **4 REVIEW** source issues and **33/36** months with historical headcount reconciliation mismatch. This is the core engineering tradeoff: successful execution does not certify business source completeness.

**4:15–5:00 — CI and next steps**

Show the [GitHub Actions workflow](../../.github/workflows/quality-ci.yml) and green hosted result (check the current badge in [README](../../README.md)). Finish with the incremental-load and Dagster plan. Do not state orchestration is implemented before the planned phase is completed.

## What to demonstrate live if you have access

1. Select **Year 2024/2025** on month-grained pages to illustrate DAX filter contexts.
2. Filter **Department** in the Executive/Planning and Recruiting pages; avoid implying location-level or month-level details that are absent from the related marts.
3. On the Retention page, show that **Observation Endpoint** replaces a false Year filter.
4. On the Data Quality page, select **Audit Run** to filter detail rows. The **Latest** cards always refer to the latest imported run.
5. Point out that the source workbook and employee identifiers are not included in GitHub; only aggregate screenshots are public.

## Questions to prepare for

| Interview question | Concise evidence-based response |
|---|---|
| Why not use Spark? | Current input is small (~30k source records); PostgreSQL/dbt is more economical and sufficient. A synthetic benchmark is planned before introducing distributed compute. |
| How do you avoid duplicate loads? | Content checksums, typed contracts, idempotent full-snapshot ingestion and transaction/rollback tests. |
| Why are there REVIEW states if CI passes? | CI verifies technical integrity with synthetic data. The historical source has unresolved business-definition and reconciliation gaps that should not be silently corrected. |
| Why separate raw, staging and marts? | Raw preserves provenance; staging normalizes contracts; marts expose stable reporting grains and measures. |
| How do you avoid wrong DAX totals? | Explicit stock-versus-flow behavior, non-additive ratios and date/department grain tests. |
| Is the dashboard live? | No. It uses Power BI Import mode and the data's latest source period ends December 2025. Service refresh requires gateway/connectivity configuration. |

**Do not overclaim:** Do not present this as a production HR service, individual retention risk engine, verified causal model, or actual percentage business improvement. It is a tested data/BI engineering portfolio built from historical records.
