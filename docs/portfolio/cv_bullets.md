# CV / LinkedIn Project Copy

Use only claims verified by the repository and current tests; do not describe planned features as implemented. Adjust the title and time period to fit your CV.

## Data Engineer-oriented (English)

**HR Workforce Intelligence | Python, PostgreSQL, dbt Core, Docker, GitHub Actions, Power BI**

- Built an end-to-end HR analytics pipeline processing **29,728 historical source records** across **12 Excel sheets**, with schema validation, transactional PostgreSQL ingestion, content-based idempotency and auditable SHA-256 source checks.
- Designed a dimensional analytics warehouse using **36 dbt models** (staging, intermediate, five dimensions, eight facts and seven business marts), supported by **83 full-dataset tests** and documented grain/KPI contracts.
- Implemented **18 pipeline data-quality gates**, historical reconciliation checks and failure/rollback recovery workflows; kept **33/36 source headcount mismatches** visible as REVIEW rather than silently correcting the source.
- Automated GitHub Actions validation against an **isolated synthetic PostgreSQL database**; validated **116 dbt build/test steps** and separate Python regression tests without publishing employee-level data.
- Built offline **synthetic-only** incremental, orchestration and lakehouse portability exercises: Dagster assets, immutable Parquet batches, source-offset/version handling, and a checksum-verified Bronze/Silver/Gold export (not deployed to any cloud account).

## Data Analyst / BI-oriented (English)

**Workforce Planning & People Analytics | Power BI, DAX, SQL**

- Developed a **six-page Power BI report** covering executive workforce trends, plan-versus-actual staffing, attrition, retention cohorts, recruitment operations and data trust, with **51 DAX measures** and consistent visual design.
- Applied explicit month/department metric grains and **stock-versus-flow** semantics, reducing the risk of misleading headcount totals, recruitment backlog aggregation and provisional attrition interpretation.
- Produced diagnostic visualizations including workforce waterfalls, month×department heatmaps, engagement/performance department bubbles and data-quality reconciliation trends; paired observations with documented caveats rather than causal claims.
- Added automated offline checks for semantic-model relationships, report bindings, six distinct dashboard pages, and public portfolio assets; documented SQL-versus-DAX acceptance scenarios.

## Vietnamese explanation for interviews

- **Data Engineering:** Tôi xây dựng pipeline từ Excel qua Python/PostgreSQL đến dbt, có kiểm tra schema, chống nạp trùng, rollback, audit và CI bằng dữ liệu synthetic.
- **Data Analytics:** Tôi xây dựng sáu trang Power BI và 51 DAX measures, giải thích đúng grain của KPI, phân biệt stock/flow, đồng thời công khai giới hạn dữ liệu.
- **Điểm khác biệt:** Không che giấu 33/36 tháng mismatch của nguồn dữ liệu để tạo dashboard “đẹp”; tách PASS kỹ thuật khỏi REVIEW nghiệp vụ.

## Claims to avoid

- “Reduced attrition by X%” — not measured.
- “Improved HR business results by X%” — no causal/business impact study.
- “Real-time HR analytics” — Power BI is Import mode; source ends December 2025.
- “Real-time streaming, Spark, Kafka or a production cloud lakehouse” — the Dagster and Parquet extensions are offline/synthetic demos, not deployed production services.
- “Predictive retention model” — only descriptive endpoint cohort comparisons are implemented.

See [case study](case_study.md), [architecture](architecture.md), [gallery](README.md) and [demo script](demo_walkthrough.md).
