# Monitoring, Failure Handling & Recovery

## Data model

SQL migration: `sql/04_monitoring.sql`, safe to re-run via
`src.phase4.pipeline.bootstrap()`.

| Metadata table | Grain | Useful fields |
|---|---|---|
| `audit.pipeline_runs` | One attempted Phase 4 execution | mode, status, stage, timestamps, linked ingest batch, sanitized error type |
| `audit.data_quality_results` | Run × gate | PASS/REVIEW/FAIL, affected count, static rationale |
| `audit.pipeline_metrics` | Run × metric name | duration, ingest rows, dbt successes/build seconds, checks, freshness age |

Audit results are written before the optional Markdown health report.
If writing the report fails, the completed database state stays accurate.
No employee-level data or exception payload is persisted to the audit tables.

## Monitoring commands

```powershell
python -m src.phase4.health
python -m src.phase4.pipeline --quality-only
```

The health CLI shows latest run status, per-status historical counts,
stage, whether a run has been RUNNING for over two hours, and the last
successful ingestion age in hours. **Detection is not automatic paging**:
this Phase 4 local project has no scheduled daemon, cloud monitoring
email/Slack alerting.

Diagnostic SQL:

```sql
SELECT pipeline_run_id, run_mode, status, stage, started_at, finished_at
FROM audit.pipeline_runs ORDER BY pipeline_run_id DESC LIMIT 10;

SELECT check_id, status, affected_count
FROM audit.data_quality_results
WHERE pipeline_run_id = (SELECT MAX(pipeline_run_id) FROM audit.pipeline_runs)
ORDER BY status, check_id;

SELECT metric_name, metric_value
FROM audit.pipeline_metrics
WHERE pipeline_run_id = (SELECT MAX(pipeline_run_id) FROM audit.pipeline_runs)
ORDER BY metric_name;
```

## Isolated failure and recovery coverage

`tests/test_phase4_recovery.py` is guarded by **both**
`POSTGRES_DB=workforce_ci` and `HR_SYNTHETIC_DB=YES`. It tests:

1. A synthetic baseline passes the quality gate.
2. Deliberately corrupting a synthetic mart FTE triggers a logged FAILED
   pipeline, then restoring the value makes the next run SUCCEEDED.
3. A duplicate raw primary key is rejected and rolled back.
4. A corrupt synthetic XLSX is registered as FAILED without changing raw rows.
5. Preexisting raw schema drift is detected and the test transaction rolls back.
6. A synthetic RUNNING process older than two hours is detected, then closed.

The **actual source data is not used** in fault injection. Never run these
tests against the real `workforce_dw` database.

## Important transactional boundary

Phase 2 ingestion replaces all 12 raw tables in a single PostgreSQL
transaction. In contrast, **dbt materializes models individually**; the
entire dbt build is *not* one atomic 36-model transaction. If dbt fails
mid-build, existing marts may represent a partially refreshed state.
Consumers must treat `audit.pipeline_runs.status='FAILED'` as **not ready**,
resolve the issue, rerun `dbt build` and the quality gate, and only then
refresh Power BI. Do not claim an automatic warehouse-wide rollback.

If PostgreSQL itself is offline, an audit record cannot be persisted.
The CLI fails closed; external process/CI exit status is then the evidence.
