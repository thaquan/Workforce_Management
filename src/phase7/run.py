"""Explicit local CLI for Phase 7. Dry-run is the default."""
import argparse
import json
import os

from pathlib import Path

from dagster import DagsterInstance, materialize

from src.phase3.dbt_runner import ROOT
from src.phase7.definitions import ASSETS, RUNTIME_DIR
from src.phase7.safety import assert_disposable_target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dry_run", "synthetic"), default="dry_run")
    parser.add_argument(
        "--allow-disposable-reset", action="store_true",
        help="Allow fixture loading only into an explicitly isolated workforce_ci database.",
    )
    args = parser.parse_args(argv)
    if args.mode == "synthetic" and not args.allow_disposable_reset:
        parser.error("synthetic mode requires --allow-disposable-reset")
    if args.mode == "dry_run" and args.allow_disposable_reset:
        parser.error("--allow-disposable-reset is only valid in synthetic mode")

    os.environ["HR_PHASE7_MODE"] = args.mode
    if args.mode == "synthetic":
        os.environ["HR_PHASE7_ALLOW_WRITE"] = "YES"
        assert_disposable_target()

    existing_home = os.environ.get("DAGSTER_HOME")
    if existing_home and Path(existing_home).resolve() != RUNTIME_DIR.resolve():
        parser.error("DAGSTER_HOME must point to .phase7_runtime for this CLI")
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    if "DAGSTER_HOME" not in os.environ:
        config = RUNTIME_DIR / "dagster.yaml"
        if not config.exists():
            config.write_text("telemetry:\n  enabled: false\n", encoding="utf-8")
        os.environ["DAGSTER_HOME"] = str(RUNTIME_DIR)
    instance = DagsterInstance.get()
    result = materialize(ASSETS, instance=instance, raise_on_error=False)
    summary = {"dagster_run_id": result.run_id, "success": result.success, "mode": args.mode}
    if result.success:
        summary.update(result.output_for_node("report_ready"))
        source = result.output_for_node("source_preflight")
        summary["source_sha256"] = source["sha256"]
        summary["source_period"] = source["source_period"]
        summary["raw_status"] = result.output_for_node("raw_ingested")["status"]
        summary["dbt_nodes"] = result.output_for_node("dbt_marts_built").get("dbt_nodes", 0)
        summary["quality"] = result.output_for_node("quality_gates_checked").get("quality", {})
    print(json.dumps(summary, sort_keys=True))
    return 0 if result.success else 2


if __name__ == "__main__":
    raise SystemExit(main())
