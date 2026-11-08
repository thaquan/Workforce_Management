# Quality Contract — PASS, REVIEW, FAIL

The source has known business ambiguities, so a data-quality score is not
equivalent to unconditional source truth.

| Outcome | Meaning | Action |
|---|---|---|
| PASS | Rule has no observed violations | Continue |
| REVIEW | Non-blocking ambiguity or unverified source semantics | Log and flag downstream |
| FAIL | Rule needed for safe analytics is violated, or SQL cannot execute | Fail the pipeline |

All 18 checks are declared centrally in
`src/phase4/quality_contract.py`. Each check returns **only the count**
of affected rows, not employee identifiers, salary values or sensitive details.
Results are persisted in `audit.data_quality_results` using unique
`(pipeline_run_id, check_id)`.

## Blocking dimensions

- **Completeness of warehouse objects:** 12 raw tables, 16 staging/intermediate
  views, and 20 marts/dimension/fact tables.
- **Completeness of facts:** Employee and snapshot counts match source-to-mart
  expectations; target and recruitment aggregates do not fan out.
- **Uniqueness:** One snapshot row per
  Month × Department × Location × Level and one attrition row per
  Month × Department.
- **Validity:** Nonnegative HC/FTE with FTE bounded by HC.
- **KPI accuracy:** Termination types reconcile to totals and attrition
  rates use the correct two-snapshot denominator.
- **Temporal integrity:** Events resolve to the extended reporting calendar,
  and retention features do not come from after a departure.
- **Governance:** Salary-versus-budget comparison remains explicitly disabled.

The **83 dbt data tests** in Phase 3 continue checking relationships, column
nullability, uniqueness, grains, and baseline-specific KPI assertions.
The Phase 4 gates are additional persisted operational checks, not a
replacement for those tests.

## Known source exceptions

- **Headcount reconciliation:** Source snapshot and employee-date population
  disagree in **33 of 36 months** in the verified workbook. This is REVIEW,
  not a silent data correction or automatic FAIL.
- **Raw DimDate coverage:** Source calendar omits earlier hire events; the
  derived `marts.dim_date` covers the earlier period.
- **Salary budget semantics:** Period, currency and coverage unverified, so
  variance stays blocked.
- **Transfers:** No Transfer event history; internal mobility unsupported.

The successful run on the verified source had **14 PASS, 4 REVIEW, 0 FAIL**.
Review flags must remain visible in the Phase 5 semantic model.

## Freshness definition

The workbook contains historical data (2018–2025). Do **not** fail freshness
based on the most recent business event date. Instead, record the age (hours)
of the latest `SUCCEEDED` ingestion in `audit.load_batches`, as well as
the last validated pipeline run and its status. No arbitrary SLA is enforced
for a static, manually refreshed source.

## Safe extensibility

When new files arrive, review source-to-target contract and known KPI
baselines before revising thresholds. Full-baseline dbt tests refer to this
historical workbook and are tagged `full_baseline`; synthetic CI intentionally
excludes only these three dataset-specific assertions.
