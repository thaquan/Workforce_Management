"""Audited batch orchestration: Phase 2 ingestion -> dbt -> Phase 4 gates."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

from src.phase2.ingest import connect_db, ingest
from src.phase3.dbt_runner import ROOT, DBT_DIR, dbt_executable, environment
from src.phase4.quality_contract import evaluate

DDL = ROOT / "sql" / "04_monitoring.sql"
REPORT = ROOT / "reports" / "phase4" / "latest_health.md"


class QualityGateFailure(RuntimeError):
    """One or more blocking quality rules failed."""


def bootstrap(conn):
    conn.execute(DDL.read_text(encoding="utf-8"))


def create_run(conn, mode):
    return conn.execute(
        """INSERT INTO audit.pipeline_runs(run_mode,status,stage)
           VALUES (%s,'RUNNING','START') RETURNING pipeline_run_id""",
        (mode,),
    ).fetchone()[0]


def set_stage(conn, run_id, stage, batch_id=None):
    conn.execute(
        """UPDATE audit.pipeline_runs SET stage=%s,
            ingest_batch_id=COALESCE(%s, ingest_batch_id)
           WHERE pipeline_run_id=%s""",
        (stage, batch_id, run_id),
    )


def set_finished(conn, run_id, success, stage, error=None):
    conn.execute(
        """UPDATE audit.pipeline_runs SET
              status=%s, stage=%s, finished_at=NOW(), error_type=%s
           WHERE pipeline_run_id=%s""",
        ("SUCCEEDED" if success else "FAILED", stage, error, run_id),
    )
    conn.execute(
        """INSERT INTO audit.pipeline_metrics(pipeline_run_id,metric_name,metric_value)
           SELECT pipeline_run_id, 'duration_seconds',
                  EXTRACT(EPOCH FROM (finished_at-started_at))
           FROM audit.pipeline_runs WHERE pipeline_run_id=%s
           ON CONFLICT (pipeline_run_id,metric_name)
           DO UPDATE SET metric_value=EXCLUDED.metric_value""", (run_id,),
    )


def save_metric(conn, run_id, name, value):
    conn.execute(
        """INSERT INTO audit.pipeline_metrics(pipeline_run_id,metric_name,metric_value)
           VALUES (%s,%s,%s)
           ON CONFLICT (pipeline_run_id,metric_name)
           DO UPDATE SET metric_value=EXCLUDED.metric_value""",
        (run_id, name, value),
    )


def save_quality(conn, run_id, results):
    for check_id, status, count, rationale in results:
        conn.execute(
            """INSERT INTO audit.data_quality_results(
                   pipeline_run_id,check_id,status,affected_count,details)
               VALUES (%s,%s,%s,%s,%s::jsonb)
               ON CONFLICT (pipeline_run_id,check_id)
               DO UPDATE SET status=EXCLUDED.status,
                             affected_count=EXCLUDED.affected_count,
                             details=EXCLUDED.details""",
            (run_id, check_id, status, count, json.dumps({"reason": rationale})),
        )


def run_dbt_build():
    command = [
        str(dbt_executable()), "build", "--quiet",
        "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR),
    ]
    completed = subprocess.run(command, cwd=ROOT, env=environment(), check=False)
    if completed.returncode != 0:
        raise RuntimeError("dbt build returned nonzero")
    results_path = DBT_DIR / "target" / "run_results.json"
    if not results_path.exists():
        raise RuntimeError("dbt build did not produce run_results.json")
    results = json.loads(results_path.read_text(encoding="utf-8"))["results"]
    # dbt uses 'success' for models and 'pass' for data tests.
    failed = sum(r["status"] not in ("success", "pass") for r in results)
    if failed:
        raise RuntimeError("dbt reported failed or skipped nodes")
    return len(results)


def status_summary(results):
    return {status: sum(row[1] == status for row in results)
            for status in ("PASS", "REVIEW", "FAIL")}


def write_report(result, checks=()):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    summary = result["quality"]
    lines = [
        "# Phase 4 — Latest Pipeline Health",
        "",
        f"- Pipeline run: **{result['run_id']}**",
        f"- Mode: **{result['mode']}**",
        f"- Status: **{result['status']}**",
        f"- Quality checks: {summary.get('PASS',0)} PASS, "
        f"{summary.get('REVIEW',0)} REVIEW, {summary.get('FAIL',0)} FAIL",
        f"- Verified at (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "Historic workforce exceptions are REVIEW; no employee-level rows are included.",
        "Freshness measures use ingestion audit timestamps, not the last historical event date.",
        "",
        "| Quality gate | Status | Affected count | Explanation |",
        "|---|---|---:|---|",
        *(f"| {check_id} | {status} | {count} | {reason} |"
          for check_id, status, count, reason in checks),
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def execute(mode="FULL"):
    """Return summary after durable DB finalization; report errors remain nonfatal."""
    with connect_db() as conn:
        bootstrap(conn)
        run_id = create_run(conn, mode)
        stage = "START"
        results = []
        try:
            if mode == "FULL":
                stage = "INGEST"
                set_stage(conn, run_id, stage)
                ingested = ingest()
                save_metric(conn, run_id, "source_rows", ingested["rows"])
                set_stage(conn, run_id, "DBT_BUILD", ingested["batch_id"])
                stage = "DBT_BUILD"
                dbt_start = perf_counter()
                dbt_nodes = run_dbt_build()
                save_metric(conn, run_id, "dbt_build_seconds", perf_counter()-dbt_start)
                save_metric(conn, run_id, "dbt_nodes_successful", dbt_nodes)
            stage = "QUALITY"
            set_stage(conn, run_id, stage)
            results = evaluate(conn)
            save_quality(conn, run_id, results)
            for status, count in status_summary(results).items():
                save_metric(conn, run_id, f"quality_{status.lower()}_checks", count)
            fact_rows = conn.execute(
                "SELECT COUNT(*) FROM marts.mart_workforce_monthly"
            ).fetchone()[0]
            save_metric(conn, run_id, "workforce_snapshot_rows", fact_rows)
            last_load = conn.execute(
                """SELECT EXTRACT(EPOCH FROM (NOW()-MAX(finished_at)))/3600
                   FROM audit.load_batches WHERE status='SUCCEEDED'"""
            ).fetchone()[0]
            if last_load is not None:
                save_metric(conn, run_id, "last_successful_ingest_age_hours", last_load)
            if any(row[1] == "FAIL" for row in results):
                raise QualityGateFailure("One or more blocking quality checks failed")
            set_finished(conn, run_id, True, "COMPLETE")
            status = "SUCCEEDED"
        except Exception as error:
            set_finished(conn, run_id, False, stage, type(error).__name__)
            status = "FAILED"
        summary = {
            "run_id": run_id, "mode": mode, "status": status,
            "quality": status_summary(results),
        }
    try:
        write_report(summary, results)
    except OSError:
        summary["report_warning"] = "ReportWriteError"
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality-only", action="store_true",
                        help="Check existing marts without modifying source tables or running dbt.")
    args = parser.parse_args()
    result = execute("QUALITY_ONLY" if args.quality_only else "FULL")
    print(json.dumps(result))
    return 0 if result["status"] == "SUCCEEDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
