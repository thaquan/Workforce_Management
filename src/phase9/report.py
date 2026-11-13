"""Publish a local, offline dashboard from aggregate-only synthetic benchmark JSON."""
import argparse
import csv
from html import escape
import json
from pathlib import Path

from src.phase2.ingest import ROOT

RUNTIME = ROOT / ".phase9_runtime"
OUTPUT = ROOT / "reports" / "phase9"
COLUMNS = [
    "baseline_rows", "final_rows", "changed_rows", "parquet_zstd_bytes",
    "parquet_generation_ms", "duckdb_query_median_ms", "duckdb_query_p95_ms",
    "postgres_full_median_ms", "postgres_incremental_median_ms",
    "postgres_speed_ratio", "query_parity",
]


def read_aggregates(paths):
    """Use only safe aggregate metrics. Latest input wins for duplicate scales."""
    by_scale = {}
    for path in sorted(map(Path, paths)):
        obj = json.loads(path.read_text(encoding="utf-8"))
        if obj.get("synthetic") is not True or obj.get("mode") not in ("duckdb", "compare"):
            raise ValueError("Only Phase 9 synthetic benchmark result files are accepted")
        for result in obj["results"]:
            scale = result["baseline_rows"]
            if not isinstance(scale, int) or scale < 1000 or scale > 2_000_000:
                raise ValueError("Unexpected benchmark scale")
            if result["final_rows"] != scale + scale // 100:
                raise ValueError("Incorrect final row count")
            duck = result.get("duckdb_parquet")
            pg = result.get("postgresql")
            if not duck or not duck["query"]["samples_ms"]:
                raise ValueError("Missing DuckDB measured results")
            if pg and result.get("cross_engine_query_parity") != "PASS (count and sums)":
                raise ValueError("Cross-engine correctness is unverified")
            by_scale[scale] = {
                "baseline_rows": scale,
                "final_rows": result["final_rows"],
                "changed_rows": result["changed_rows"],
                "parquet_zstd_bytes": duck["size_bytes"],
                "parquet_generation_ms": duck["generation_ms"],
                "duckdb_query_median_ms": duck["query"]["median_ms"],
                "duckdb_query_p95_ms": duck["query"]["p95_ms"],
                "postgres_full_median_ms": pg["full_rebuild"]["median_ms"] if pg else "",
                "postgres_incremental_median_ms": pg["selective_upsert"]["median_ms"] if pg else "",
                "postgres_speed_ratio": pg["upsert_vs_rebuild_ratio"] if pg else "",
                "query_parity": result.get("cross_engine_query_parity", "DuckDB only"),
            }
    if not by_scale:
        raise ValueError("No synthetic results found")
    return [by_scale[key] for key in sorted(by_scale)]


def dashboard_html(rows):
    max_query = max(row["duckdb_query_median_ms"] for row in rows)
    max_bytes = max(row["parquet_zstd_bytes"] for row in rows)
    blocks = []
    for row in rows:
        title = f"{row['baseline_rows']:,}"
        width = max(3, 100 * row["duckdb_query_median_ms"] / max_query)
        file_width = max(3, 100 * row["parquet_zstd_bytes"] / max_bytes)
        comparison = (
            f"Postgres rebuild: {row['postgres_full_median_ms']:.2f} ms / "
            f"UPSERT: {row['postgres_incremental_median_ms']:.2f} ms"
            if row["postgres_full_median_ms"] != "" else
            "PostgreSQL full vs incremental not measured at this scale"
        )
        blocks.append(
            f'<div class="scale"><div class="scale-top"><strong>{title} baseline records</strong>'
            f'<span>{row["final_rows"]:,} final · {row["changed_rows"]:,} changes</span></div>'
            '<div class="bar-row"><span>DuckDB scan</span>'
            f'<div class="track"><div class="bar teal" style="width:{width:.2f}%"></div></div>'
            f'<b>{row["duckdb_query_median_ms"]:.2f} ms</b></div>'
            '<div class="bar-row"><span>Parquet size</span>'
            f'<div class="track"><div class="bar blue" style="width:{file_width:.2f}%"></div></div>'
            f'<b>{row["parquet_zstd_bytes"]/1024/1024:.2f} MB</b></div>'
            f'<p class="note">{escape(comparison)}</p></div>'
        )
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport"
content="width=device-width,initial-scale=1">
<title>HR Workforce Intelligence | Synthetic Benchmark</title>
<style>
:root {color-scheme:dark; font-family:Inter,Segoe UI,Arial,sans-serif;}
* {box-sizing:border-box} body {margin:0;background:#071825;color:#e8f4f6;}
main {max-width:1020px;margin:auto;padding:64px 28px;}
header {border-bottom:1px solid #294553;padding-bottom:30px;margin-bottom:30px;}
small {text-transform:uppercase;letter-spacing:.18em;color:#6ed5c6;font-weight:700;}
h1 {font-size:clamp(34px,5vw,56px);line-height:1.1;margin:15px 0;}
.lead {color:#a2bdc7;font-size:16px;max-width:820px;line-height:1.7}
.callout {padding:20px 24px;border:1px solid #3d656c;border-left:4px solid #6ed5c6;
 border-radius:12px;margin:30px 0;background:#102b38}
h2 {font-size:22px;margin-top:44px}
.scale {padding:22px;margin:14px 0;border:1px solid #2c4a57;border-radius:15px;background:#102937}
.scale-top {display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:18px}
.scale-top span,.note {color:#aac3cd}.bar-row {display:grid;grid-template-columns:110px 1fr 100px;
 gap:14px;align-items:center;margin:13px 0;font-size:13px}
.track {height:14px;background:#254455;border-radius:5px;overflow:hidden}
.bar {height:100%;border-radius:5px}.teal{background:#6ed5c6}.blue{background:#6d9ff1}
.bar-row b{text-align:right}.note{font-size:12px;margin:15px 0 0}
table{width:100%;border-collapse:collapse;margin-top:18px;font-size:14px}
th,td{text-align:left;border-bottom:1px solid #294553;padding:12px 8px}
th{color:#8fcbd1} td{font-variant-numeric:tabular-nums}
footer{margin-top:42px;color:#9bb7c2;font-size:13px;line-height:1.7}
@media(max-width:600px){main{padding:32px 16px}.bar-row{grid-template-columns:84px 1fr 76px;gap:7px;font-size:11px}}
</style></head><body><main>
<header><small>HR Workforce Intelligence / Phase 09</small>
<h1>Benchmark without invented performance claims.</h1>
<p class="lead">Reproducible synthetic data, ZSTD Parquet and SQL query measurements.
All numbers below were measured locally; they are not a production benchmark
and do not describe the actual HR dataset.</p></header>
<div class="callout"><b>Experimental method.</b> Five-percent existing-row updates
and one-percent new records; deterministic integer-only synthetic records.
Each DuckDB query is warmed up, then timed three times for published scales.
The charts show per-scale query median and compressed file size, not full-pipeline latency.</div>
<h2>Analytical query and storage</h2>""" + "\n".join(blocks) + """
<h2>Interpretation</h2>
<p class="lead">Measured elapsed time depends on the machine, engine settings,
cache state and selectivity. Bar lengths compare scales within each metric only.
No speedup is claimed where PostgreSQL full-load and incremental workloads were not
measured. The separate PostgreSQL 1K smoke test checks correctness, not capacity.</p>
<footer><b>Privacy & integrity:</b> All source rows were generated from integer formulas.
No real names, salary records, IDs or original HR workbook were loaded.
Full-row PostgreSQL correctness and cross-engine aggregate equality must pass
before any comparative claims. See docs/phase9/README.md for commands.</footer>
</main></body></html>
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true",
                        help="Replace ONLY the two generated Phase 9 aggregate report files.")
    args = parser.parse_args(argv)
    rows = read_aggregates(args.inputs)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT / "benchmark_results.csv"
    html_path = OUTPUT / "benchmark_dashboard.html"
    if not args.overwrite and (csv_path.exists() or html_path.exists()):
        parser.error("Aggregate report exists; pass --overwrite for deliberate regeneration")
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    html_path.write_text(dashboard_html(rows), encoding="utf-8")
    print(json.dumps({
        "synthetic": True, "scales": [row["baseline_rows"] for row in rows],
        "csv": str(csv_path), "dashboard": str(html_path),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
