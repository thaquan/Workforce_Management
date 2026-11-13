"""DuckDB / ZSTD Parquet analytic query on the SAME final synthetic rows."""
from pathlib import Path
from time import perf_counter

import duckdb

from src.phase9.workload import SELECT_FILTER, Scale, projection


def benchmark_duckdb(scale: Scale, repeats: int, folder):
    if not 2 <= repeats <= 10:
        raise ValueError("Repetitions must be 2..10")
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"synthetic_final_{scale.baseline}.parquet"
    if target.exists():
        raise RuntimeError("Refusing to overwrite existing Parquet benchmark data")
    with duckdb.connect(database=":memory:") as conn:
        conn.execute("SET threads = 2")
        conn.execute("SET memory_limit = '1GB'")
        projection_sql = projection(1, scale.final_rows, scale.baseline, final=True)
        target_sql = str(target.resolve()).replace("'", "''")
        started = perf_counter()
        conn.execute(
            f"COPY ({projection_sql}) TO '{target_sql}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        export_ms = (perf_counter() - started) * 1000
        total = conn.execute(
            "SELECT COUNT(*) FROM read_parquet(?)", [str(target)]
        ).fetchone()[0]
        if total != scale.final_rows:
            raise RuntimeError("Parquet export row count mismatch")
        sql = SELECT_FILTER.format(table="read_parquet(?)")
        expected = conn.execute(sql, [str(target)]).fetchone()  # warm-up
        samples = []
        for _ in range(repeats):
            started = perf_counter()
            value = conn.execute(sql, [str(target)]).fetchone()
            samples.append((perf_counter() - started) * 1000)
            if value != expected:
                raise RuntimeError("DuckDB query result changed between repetitions")
        return {
            "engine": "DuckDB / Parquet",
            "version": duckdb.__version__,
            "baseline_rows": scale.baseline,
            "final_rows": int(total),
            "parquet_zstd_bytes": target.stat().st_size,
            "parquet_generation_ms": round(export_ms, 3),
            "query_parquet_ms": samples,
            "query_result": [int(v) for v in expected],
            "threads": 2,
            "memory_limit": "1GB",
            "data": "fictional, deterministic, no employee PII",
        }
