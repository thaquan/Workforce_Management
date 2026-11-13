"""Phase 9 synthetic performance benchmark. PLAN is the safe default."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
from statistics import median
import tempfile
from time import perf_counter

import psutil

from src.phase2.ingest import ROOT
from src.phase9.duckdb_benchmark import benchmark_duckdb
from src.phase9.postgres_benchmark import benchmark_postgres
from src.phase9.safety import verify_benchmark_db
from src.phase9.workload import Scale

RUNTIME = ROOT / ".phase9_runtime"


def measurements(samples):
    if not samples or any(value < 0 for value in samples):
        raise ValueError("Invalid timing series")
    sorted_values = sorted(samples)
    location = (len(sorted_values) - 1) * 0.95
    before = int(location)
    after = min(before + 1, len(sorted_values) - 1)
    p95 = sorted_values[before] + (sorted_values[after] - sorted_values[before]) * (location - before)
    return {
        "repetitions": len(samples),
        "median_ms": round(median(samples), 3),
        "p95_ms": round(p95, 3),
        "samples_ms": [round(value, 3) for value in samples],
    }


def compile_summary(scale, postgres_result=None, duckdb_result=None):
    summary = {
        "synthetic": True,
        "baseline_rows": scale.baseline,
        "final_rows": scale.final_rows,
        "changed_rows": scale.changed_rows,
        "update_rows": scale.updated,
        "new_rows": scale.inserted,
    }
    if postgres_result:
        if postgres_result["parity"] != "PASS (every column, every row)":
            raise RuntimeError("PostgreSQL parity not established")
        full = measurements(postgres_result["full_reload_ms"])
        incremental = measurements(postgres_result["incremental_ms"])
        summary["postgresql"] = {
            "version": postgres_result["version"],
            "full_rebuild": full,
            "selective_upsert": incremental,
            "upsert_vs_rebuild_ratio": round(
                full["median_ms"] / incremental["median_ms"], 3
            ) if incremental["median_ms"] > 0 else None,
            "query_without_composite_index": measurements(postgres_result["query_no_index_ms"]),
            "query_with_composite_index": measurements(postgres_result["query_with_index_ms"]),
            "index_build_ms": postgres_result["index_build_ms"],
            "plan_without_index": postgres_result["explain_without_index"]["operations"],
            "plan_with_index": postgres_result["explain_with_index"]["operations"],
            "temp_relation_bytes_before_index": postgres_result["storage_bytes_full_before_index"],
            "temp_relation_bytes_after_index": postgres_result["storage_bytes_full_after_index"],
            "temp_relation_bytes_incremental": postgres_result["storage_bytes_incremental"],
            "query_result": postgres_result["query_result"],
            "correctness": postgres_result["parity"],
        }
    if duckdb_result:
        summary["duckdb_parquet"] = {
            "version": duckdb_result["version"],
            "generation_ms": duckdb_result["parquet_generation_ms"],
            "size_bytes": duckdb_result["parquet_zstd_bytes"],
            "query": measurements(duckdb_result["query_parquet_ms"]),
            "threads": duckdb_result["threads"],
            "query_result": duckdb_result["query_result"],
        }
    if postgres_result and duckdb_result:
        if postgres_result["query_result"] != duckdb_result["query_result"]:
            raise RuntimeError("Analytical query disagrees between PostgreSQL and DuckDB")
        summary["cross_engine_query_parity"] = "PASS (count and sums)"
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("plan", "duckdb", "compare"), default="plan")
    parser.add_argument("--rows", type=int, nargs="+", default=[100_000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--allow-disposable-db", action="store_true",
        help="Allow only ephemeral PostgreSQL TEMP tables in explicitly acknowledged workforce_ci.",
    )
    args = parser.parse_args(argv)
    if not 2 <= args.repeats <= 10:
        parser.error("--repeats must be 2..10")
    if args.mode == "compare" and not args.allow_disposable_db:
        parser.error("compare mode requires --allow-disposable-db")
    if args.mode != "compare" and args.allow_disposable_db:
        parser.error("Only compare mode accepts --allow-disposable-db")
    if len(args.rows) > 3 or len(set(args.rows)) != len(args.rows):
        parser.error("Use at most 3 distinct row scales")
    try:
        scales = [Scale(rows) for rows in args.rows]
    except ValueError as exc:
        parser.error(str(exc))
    if args.mode == "plan":
        print(json.dumps({
            "mode": "plan", "database_access": False,
            "synthetic": True, "repeats": args.repeats,
            "scales": [{
                "baseline": s.baseline, "final_rows": s.final_rows,
                "updates": s.updated, "inserts": s.inserted,
            } for s in scales],
        }, sort_keys=True))
        return 0

    if args.mode == "compare":
        os.environ["HR_PHASE9_ALLOW_WRITE"] = "YES"
        verify_benchmark_db()
    RUNTIME.mkdir(parents=True, exist_ok=True)
    cpu_start = psutil.Process().cpu_times()
    started = perf_counter()
    results = []
    for scale in scales:
        with tempfile.TemporaryDirectory(prefix="benchmark-", dir=RUNTIME) as tempdir:
            pg = benchmark_postgres(scale, args.repeats) if args.mode == "compare" else None
            duck = benchmark_duckdb(scale, args.repeats, tempdir)
            summary = compile_summary(scale, pg, duck)
            results.append(summary)
            print(json.dumps({"scale_complete": scale.baseline, "result": summary}, sort_keys=True))
    cpu_finish = psutil.Process().cpu_times()
    metadata = {
        "mode": args.mode,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "synthetic": True,
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "logical_cpu_count": psutil.cpu_count(logical=True),
        "client_process_rss_mb_at_completion": round(
            psutil.Process().memory_info().rss / 1024**2, 2
        ),
        "client_process_cpu_seconds": round(
            cpu_finish.user + cpu_finish.system - cpu_start.user - cpu_start.system, 3
        ),
        "total_wall_seconds": round(perf_counter() - started, 3),
        "notes": [
            "Synthetic in-database PostgreSQL DML workload, not timed Parquet-to-PostgreSQL ETL.",
            "Each timed incremental sample starts from an equivalent baseline (unmeasured setup).",
            "Full rebuild includes TEMP TRUNCATE plus final-state INSERT SELECT; selective UPSERT changes only 6%.",
            "Only query warm-up, not cold-cache measurements; query cost depends on caching and planner.",
            "DuckDB scans identical deterministic synthetic rows from ZSTD Parquet with 2 threads.",
            "Client RSS/CPU does not measure PostgreSQL server or Docker container memory/CPU.",
            "p95 is a descriptive interpolation across few samples, not a population SLO.",
            "Do not extrapolate results to real HR records, live CDC or a production environment.",
        ],
        "results": results,
    }
    path = RUNTIME / ("benchmark_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json")
    with path.open("x", encoding="utf-8") as output:
        json.dump(metadata, output, indent=2, ensure_ascii=True)
    print(json.dumps({"status": "PASS", "aggregate_file": str(path), "scales": len(results)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
