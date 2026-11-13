"""Dagster asset graph for independent synthetic incremental pipeline."""
import os
from pathlib import Path
from datetime import datetime, timezone

from dagster import (
    AssetSelection, DefaultScheduleStatus, Definitions, RetryRequested,
    ScheduleDefinition, asset, define_asset_job,
)
from psycopg import OperationalError

from src.phase2.ingest import ROOT
from src.phase8.contract import fingerprint
from src.phase8.fixture import batches
from src.phase8.incremental import apply_batch, initialize_schema, quality_summary
from src.phase8.parquet_batches import read_batch, write_batch
from src.phase8.safety import require_synthetic_target

RUNTIME_DIR = ROOT / ".phase8_runtime"
PARQUET_DIR = RUNTIME_DIR / "input"


def _mode():
    value = os.environ.get("HR_PHASE8_MODE", "dry_run")
    if value not in ("dry_run", "synthetic"):
        raise RuntimeError("Phase 8 supports only dry_run or synthetic")
    return value


def _retry_transient(error):
    if isinstance(error, (OperationalError, ConnectionError, TimeoutError)):
        raise RetryRequested(max_retries=2, seconds_to_wait=2) from error
    raise error


@asset(group_name="incremental_demo", description="Fingerprints three fictional event batches and prepares immutable Parquet.")
def synthetic_changes_prepared(context):
    run_mode = _mode()
    sources = batches()
    if run_mode == "synthetic":
        try:
            require_synthetic_target()
            paths = [
                str(write_batch(batch, PARQUET_DIR / (batch["batch_id"] + ".parquet")))
                for batch in sources
            ]
        except Exception as error:
            _retry_transient(error)
    else:
        paths = []
    counts = sum(len(batch["events"]) for batch in sources)
    hashes = [fingerprint(batch) for batch in sources]
    context.add_output_metadata({
        "mode": run_mode, "batch_count": len(sources),
        "synthetic_events": counts,
        "source_checksum_count": len(hashes),
        "source_period": "2025-10 through 2025-11",
    })
    return {"mode": run_mode, "files": paths, "batch_count": len(sources),
            "source_hashes": hashes, "events": counts}


@asset(group_name="incremental_demo", description="Atomically apply new source offsets and skip already committed batches.")
def incremental_batches_ingested(context, synthetic_changes_prepared: dict):
    if synthetic_changes_prepared["mode"] == "dry_run":
        return {"mode": "dry_run", "status": "PLANNED", "batches": []}
    try:
        require_synthetic_target()
        initialize_schema()
        outcomes = [
            apply_batch(read_batch(Path(path)))
            for path in synthetic_changes_prepared["files"]
        ]
    except Exception as error:
        _retry_transient(error)
    context.add_output_metadata({
        "applied_batches": sum(item["status"] == "APPLIED" for item in outcomes),
        "skipped_batches": sum(item["status"] == "SKIPPED_UNCHANGED" for item in outcomes),
        "watermark": outcomes[-1]["watermark"],
        "rows_applied": sum(item["state_changes"] for item in outcomes),
    })
    return {"mode": "synthetic", "status": "SUCCEEDED", "batches": outcomes}


@asset(group_name="incremental_demo", description="Read-only watermark, event ledger and workforce-state consistency checks.")
def incremental_quality_checked(context, incremental_batches_ingested: dict):
    if incremental_batches_ingested["mode"] == "dry_run":
        return {"mode": "dry_run", "status": "PLANNED", "checks": {}}
    try:
        require_synthetic_target()
        result = quality_summary()
    except Exception as error:
        _retry_transient(error)
    # Check this fixed synthetic fixture; not an assertion about the real HR dataset.
    expected = {
        "watermark": 8, "events_stored": 8, "batches_succeeded": 3,
        "late_events": 1, "active_employees": 3, "deleted_employees": 1,
        "active_fte": 2.55,
    }
    for key, value in expected.items():
        if result[key] != value:
            raise RuntimeError(f"Incremental synthetic quality gate failed: {key}")
    context.add_output_metadata(result)
    return {"mode": "synthetic", "status": "PASS", "checks": result}


@asset(group_name="incremental_demo", description="Ready marker; not a Power BI gateway refresh.")
def incremental_report_ready(context, incremental_quality_checked: dict):
    mode = incremental_quality_checked["mode"]
    marker = {
        "mode": mode,
        "status": "PLANNED" if mode == "dry_run" else "READY_SYNTHETIC",
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    context.add_output_metadata(marker)
    return marker


ASSETS = [
    synthetic_changes_prepared, incremental_batches_ingested,
    incremental_quality_checked, incremental_report_ready,
]
incremental_manual = define_asset_job("incremental_manual", selection=AssetSelection.all())
incremental_weekly = ScheduleDefinition(
    job=incremental_manual, cron_schedule="0 8 * * 1",
    execution_timezone="Asia/Ho_Chi_Minh",
    default_status=DefaultScheduleStatus.STOPPED,
)
defs = Definitions(assets=ASSETS, jobs=[incremental_manual], schedules=[incremental_weekly])
