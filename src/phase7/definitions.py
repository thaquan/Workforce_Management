"""Five auditable Dagster assets, backed by existing Phase 2-4 code."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

from dagster import (
    AssetSelection, DefaultScheduleStatus, Definitions, RetryRequested,
    ScheduleDefinition, asset, define_asset_job,
)
from psycopg import OperationalError

from src.phase2.ingest import connect_db, ensure_tables, raw_tables_match
from src.phase2.quality import normalize_and_validate
from src.phase3.dbt_runner import DBT_DIR, ROOT, environment
from src.phase4 import pipeline
from src.phase4.synthetic_fixture import sample_rows, seed
from src.phase7.safety import assert_disposable_target, mode

RUNTIME_DIR = ROOT / ".phase7_runtime"


def _fixture_identity():
    rows = sample_rows()
    payload = json.dumps(rows, sort_keys=True, default=str).encode("utf-8")
    newest = max(row["Month"] for row in rows["FactMonthlySnapshot"])
    return sha256(payload).hexdigest(), sum(map(len, rows.values())), newest.isoformat()[:7]


def _retry_if_transient(error):
    if isinstance(error, (OperationalError, ConnectionError, TimeoutError)):
        raise RetryRequested(max_retries=2, seconds_to_wait=2) from error
    raise error


@asset(group_name="workforce_orchestration", description="Read-only synthetic fixture fingerprint and target validation.")
def source_preflight(context):
    run_mode = mode()
    digest, count, latest_period = _fixture_identity()
    if run_mode == "synthetic":
        try:
            assert_disposable_target()
        except Exception as error:
            _retry_if_transient(error)
    context.add_output_metadata({
        "mode": run_mode, "source_sha256": digest,
        "source_rows": count, "latest_source_period": latest_period,
    })
    return {"mode": run_mode, "sha256": digest, "rows": count, "source_period": latest_period}


@asset(group_name="workforce_orchestration", description="Ensure synthetic raw tables match the fixture; never use the private workbook.")
def raw_ingested(context, source_preflight: dict):
    if source_preflight["mode"] == "dry_run":
        return {"mode": "dry_run", "status": "PLANNED", "rows": source_preflight["rows"]}

    try:
        assert_disposable_target()
        # Existing Phase 2 comparison makes reruns read-only when inputs are unchanged.
        fixture, _ = normalize_and_validate(sample_rows())
        with connect_db() as conn:
            if conn.execute("SELECT to_regnamespace('raw')").fetchone()[0] is not None:
                ensure_tables(conn)
            unchanged = raw_tables_match(conn, fixture)
        if not unchanged:
            seed()  # Only after source_preflight has validated disposable access.
    except Exception as error:
        _retry_if_transient(error)

    status = "SKIPPED_UNCHANGED" if unchanged else "LOADED_SYNTHETIC"
    context.add_output_metadata({"status": status, "rows": source_preflight["rows"]})
    return {"mode": "synthetic", "status": status, "rows": source_preflight["rows"]}


def _run_dbt_synthetic():
    local_dbt = Path(sys.executable).with_name("dbt.exe" if os.name == "nt" else "dbt")
    dbt = str(local_dbt) if local_dbt.is_file() else shutil.which("dbt")
    if dbt is None:
        raise RuntimeError("dbt CLI is unavailable in the Phase 7 environment")
    target = RUNTIME_DIR / "dbt_target"
    logs = RUNTIME_DIR / "dbt_logs"
    command = [
        dbt, "build", "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR),
        "--target-path", str(target), "--log-path", str(logs),
        "--exclude", "tag:full_baseline",
    ]
    completed = subprocess.run(
        command, cwd=ROOT, env=environment(), capture_output=True,
        text=True, check=False, timeout=900,
    )
    if completed.returncode:
        raise RuntimeError("Synthetic dbt build failed; inspect .phase7_runtime/dbt_logs")
    results_path = target / "run_results.json"
    if not results_path.is_file():
        raise RuntimeError("Synthetic dbt build has no run_results.json")
    results = json.loads(results_path.read_text(encoding="utf-8"))["results"]
    if any(item["status"] not in ("success", "pass") for item in results):
        raise RuntimeError("Synthetic dbt build contains failed/skipped nodes")
    return len(results)


@asset(group_name="workforce_orchestration", description="Rebuild dbt models on an isolated synthetic database.")
def dbt_marts_built(context, raw_ingested: dict):
    if raw_ingested["mode"] == "dry_run":
        return {"mode": "dry_run", "status": "PLANNED"}
    try:
        assert_disposable_target()
        count = _run_dbt_synthetic()
    except Exception as error:
        _retry_if_transient(error)
    context.add_output_metadata({"dbt_nodes_successful": count})
    return {"mode": "synthetic", "status": "SUCCEEDED", "dbt_nodes": count}


@asset(group_name="workforce_orchestration", description="Reuse audited Phase 4 quality-only gates without touching the tracked health report.")
def quality_gates_checked(context, dbt_marts_built: dict):
    if dbt_marts_built["mode"] == "dry_run":
        return {"mode": "dry_run", "status": "PLANNED", "pipeline_run_id": None}
    try:
        assert_disposable_target()
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        with patch.object(pipeline, "REPORT", RUNTIME_DIR / "phase7_health.md"):
            audit = pipeline.execute("QUALITY_ONLY")
    except Exception as error:
        _retry_if_transient(error)
    if audit["status"] != "SUCCEEDED" or audit["quality"].get("FAIL", 0):
        raise RuntimeError("Phase 4 blocking quality gate failed; report_ready is blocked")
    context.add_output_metadata({
        "pipeline_run_id": audit["run_id"],
        "quality_pass": audit["quality"].get("PASS", 0),
        "quality_review": audit["quality"].get("REVIEW", 0),
        "quality_fail": audit["quality"].get("FAIL", 0),
    })
    return {
        "mode": "synthetic", "status": "SUCCEEDED",
        "pipeline_run_id": audit["run_id"], "quality": audit["quality"],
    }


@asset(group_name="workforce_orchestration", description="Materialize a marker only after successful upstream data quality.")
def report_ready(context, quality_gates_checked: dict):
    run_mode = quality_gates_checked["mode"]
    status = "PLANNED" if run_mode == "dry_run" else "READY_SYNTHETIC"
    result = {
        "mode": run_mode, "status": status,
        "pipeline_run_id": quality_gates_checked["pipeline_run_id"],
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    context.add_output_metadata({
        "status": status, "mode": run_mode,
        "pipeline_run_id": str(result["pipeline_run_id"] or "none"),
        "freshness_note": "Run time is not the last historical source period",
    })
    return result


ASSETS = [source_preflight, raw_ingested, dbt_marts_built, quality_gates_checked, report_ready]
workforce_manual = define_asset_job("workforce_manual", selection=AssetSelection.all())
weekly_schedule = ScheduleDefinition(
    job=workforce_manual, cron_schedule="0 7 * * 1",
    execution_timezone="Asia/Ho_Chi_Minh",
    default_status=DefaultScheduleStatus.STOPPED,
)
defs = Definitions(assets=ASSETS, jobs=[workforce_manual], schedules=[weekly_schedule])
