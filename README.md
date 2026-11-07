# HR Workforce Intelligence — Phase 1

End-to-End HR Workforce Planning & Attrition Analytics portfolio project.

## Scope and reproducibility
- Source workbook: `data/raw/HR_Workforce_Planning_Attrition_Dataset.xlsx` (keep local; do not publish raw HR data).
- Phase 1 covers source profiling, relationship/grain design, data quality, KPI definitions and Phase 2 acceptance criteria.
- Run from repository root: `python src/phase1/phase1_profiler.py` (Python 3.10+, standard library only).
- Output reports: `reports/phase1/`; design documents: `docs/phase1/`.

## Verified baseline
- 12 sheets, 29,728 rows excluding headers; 1,200 employee records; 36 monthly periods (2023-01 to 2025-12).
- 39 automated PASS checks and four REVIEW items in `reports/phase1/quality_checks.csv`.
- December 2025: snapshot HC=999 / FTE=968.6, planned HC=1079 / budget FTE=1053.8; 994 active Employee profiles.

## Recommended stack (future phases)
Python -> PostgreSQL (raw/staging/marts) -> dbt Core -> Power BI. Add Dagster only after loading and dbt transformations work.

## Documents
1. `docs/phase1/01_business_requirements.md`
2. `docs/phase1/02_data_model.md`
3. `docs/phase1/03_kpi_definitions.md`
4. `docs/phase1/04_quality_and_mapping.md`
5. `docs/phase1/05_phase2_readiness.md`
6. `docs/phase1/hr_warehouse_erd.mmd`

**Data policy:** Employee, salary and review fields may be sensitive. Publish synthetic/anonymized samples or aggregated visuals only; verify license and permission.

## Phase 1 review / fixes (2026-11-07)

The source Excel is immutable. See [review decisions](docs/phase1/06_review_resolutions.md).
- 33 of 36 snapshot months differ from employee-as-of headcount; June 2025 has a +98 discrepancy equal to 98 June termination events in departments D002–D005.
- July 2025 targets for these four departments switch to post-restructuring planning.
- A full **derived calendar** for 2018-01-05 through 2025-12-31 (2,918 days) is generated locally under `data/processed/`. The original DimDate is unchanged.
- Salary-budget variance remains **blocked** pending budget currency/period/coverage confirmation; internal transfers are **unsupported** by the source.
- The profiler redacts all column example values in public reports.

**Reproduce the entire review on Windows:**

```powershell
python src/phase1/run_phase1.py
```

This runs both profiling scripts and six automated regression tests (Python standard library only). Published aggregate reports are in `reports/phase1/`. Source workbook and derived employee-level files remain excluded from Git.
