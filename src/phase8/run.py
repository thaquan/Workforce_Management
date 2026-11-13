"""Phase 8 CLI. Dry-run by default; PostgreSQL writes require explicit synthetic approval."""
import argparse
import json
import os
from pathlib import Path

from dagster import DagsterInstance, materialize

from src.phase8.definitions import ASSETS, RUNTIME_DIR
from src.phase8.safety import require_synthetic_target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dry_run", "synthetic"), default="dry_run")
    parser.add_argument(
        "--allow-synthetic-write", action="store_true",
        help="Allow writes ONLY to the isolated, disposable workforce_ci database.",
    )
    args = parser.parse_args(argv)
    if args.mode == "synthetic" and not args.allow_synthetic_write:
        parser.error("synthetic mode requires --allow-synthetic-write")
    if args.mode == "dry_run" and args.allow_synthetic_write:
        parser.error("--allow-synthetic-write only applies to synthetic mode")
    os.environ["HR_PHASE8_MODE"] = args.mode
    if args.mode == "synthetic":
        os.environ["HR_PHASE8_ALLOW_WRITE"] = "YES"
        require_synthetic_target()

    configured = os.environ.get("DAGSTER_HOME")
    if configured and Path(configured).resolve() != RUNTIME_DIR.resolve():
        parser.error("DAGSTER_HOME must point to .phase8_runtime for this command")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    if not configured:
        config = RUNTIME_DIR / "dagster.yaml"
        if not config.exists():
            config.write_text("telemetry:\n  enabled: false\n", encoding="utf-8")
        os.environ["DAGSTER_HOME"] = str(RUNTIME_DIR)

    result = materialize(ASSETS, instance=DagsterInstance.get(), raise_on_error=False)
    summary = {
        "dagster_run_id": result.run_id,
        "mode": args.mode, "success": result.success,
    }
    if result.success:
        marker = result.output_for_node("incremental_report_ready")
        upstream = result.output_for_node("incremental_batches_ingested")
        quality = result.output_for_node("incremental_quality_checked")
        summary.update({
            "status": marker["status"],
            "batch_results": upstream["batches"],
            "quality": quality["checks"],
        })
    print(json.dumps(summary, sort_keys=True))
    return 0 if result.success else 2


if __name__ == "__main__":
    raise SystemExit(main())
