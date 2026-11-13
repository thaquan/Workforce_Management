"""Reproducible PostgreSQL DML timings on session-scoped TEMP tables only."""
import json
from time import perf_counter

from src.phase2.ingest import connect_db
from src.phase9.safety import verify_benchmark_db
from src.phase9.workload import COLUMNS, SELECT_FILTER, Scale, delta_projection, projection

TABLE_DEF = """(
    employee_id BIGINT PRIMARY KEY,
    department_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    month_no INTEGER NOT NULL,
    salary_cents BIGINT NOT NULL,
    fte_milli INTEGER NOT NULL
) ON COMMIT PRESERVE ROWS"""
COLS = ", ".join(COLUMNS)
FULL = "pg_temp.bench_full"
INC = "pg_temp.bench_inc"


def _insert(conn, table, query):
    conn.execute(f"INSERT INTO {table} ({COLS}) {query}")


def _measure_query(conn, sql, repeats):
    """One cache warm-up; timed query includes result fetching/round-trip."""
    expected = conn.execute(sql).fetchone()
    times = []
    for _ in range(repeats):
        started = perf_counter()
        result = conn.execute(sql).fetchone()
        times.append((perf_counter() - started) * 1000)
        if result != expected:
            raise RuntimeError("SQL query results changed between repetitions")
    return [int(value) for value in expected], times


def _explain(conn, statement):
    value = conn.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + statement).fetchone()[0]
    if isinstance(value, str):
        value = json.loads(value)
    plan = value[0]["Plan"]
    operations = []

    def walk(node):
        operations.append(node["Node Type"])
        for child in node.get("Plans", []):
            walk(child)

    walk(plan)
    return {
        "operations": operations,
        "planning_ms": round(value[0].get("Planning Time", 0), 3),
        "execution_ms": round(value[0].get("Execution Time", 0), 3),
    }


def _compare_final_tables(conn):
    """Check every field for every fictional employee, not just row counts."""
    differences = conn.execute(
        """SELECT COUNT(*)
           FROM pg_temp.bench_full f
           FULL OUTER JOIN pg_temp.bench_inc i USING(employee_id)
           WHERE f.employee_id IS NULL OR i.employee_id IS NULL OR
                 ROW(f.department_id, f.location_id, f.month_no, f.salary_cents, f.fte_milli)
                 IS DISTINCT FROM
                 ROW(i.department_id, i.location_id, i.month_no, i.salary_cents, i.fte_milli)"""
    ).fetchone()[0]
    if differences:
        raise RuntimeError(f"Final row-by-row PostgreSQL parity failed: {differences} rows")


def benchmark_postgres(scale: Scale, repeats: int):
    if not 2 <= repeats <= 10:
        raise ValueError("Repetitions must be 2..10")
    verify_benchmark_db()
    n = scale.baseline
    full_query = projection(1, scale.final_rows, n, final=True)
    base_query = projection(1, n, n, final=False)
    change_query = delta_projection(scale)
    upsert_sql = (
        f"INSERT INTO {INC} ({COLS}) {change_query} "
        "ON CONFLICT (employee_id) DO UPDATE "
        "SET salary_cents = EXCLUDED.salary_cents"
    )
    full_ms, inc_ms = [], []
    with connect_db() as conn:
        if conn.execute("SELECT current_database()").fetchone()[0] != "workforce_ci":
            raise RuntimeError("PostgreSQL database changed after preflight")
        # No permanent tables/schemas are created. Closing this connection drops both.
        conn.execute("CREATE TEMP TABLE bench_full " + TABLE_DEF)
        conn.execute("CREATE TEMP TABLE bench_inc " + TABLE_DEF)
        for _ in range(repeats):
            # Re-establish the identical baseline outside the timed incremental path.
            with conn.transaction():
                conn.execute(f"TRUNCATE {INC}")
                _insert(conn, INC, base_query)
            started = perf_counter()
            with conn.transaction():
                conn.execute(f"TRUNCATE {FULL}")
                _insert(conn, FULL, full_query)
            full_ms.append((perf_counter() - started) * 1000)
            started = perf_counter()
            with conn.transaction():
                conn.execute(upsert_sql)
            inc_ms.append((perf_counter() - started) * 1000)
        _compare_final_tables(conn)

        final_count = conn.execute(f"SELECT COUNT(*) FROM {FULL}").fetchone()[0]
        if final_count != scale.final_rows:
            raise RuntimeError("Final row count does not match generated source")
        full_bytes = conn.execute(
            "SELECT pg_total_relation_size('pg_temp.bench_full'::regclass)"
        ).fetchone()[0]
        inc_bytes = conn.execute(
            "SELECT pg_total_relation_size('pg_temp.bench_inc'::regclass)"
        ).fetchone()[0]

        query = SELECT_FILTER.format(table=FULL)
        query_result, no_index_ms = _measure_query(conn, query, repeats)
        plan_before = _explain(conn, query)
        started = perf_counter()
        conn.execute("CREATE INDEX phase9_dept_month_idx ON bench_full(department_id, month_no)")
        index_ms = (perf_counter() - started) * 1000
        indexed_result, with_index_ms = _measure_query(conn, query, repeats)
        plan_after = _explain(conn, query)
        if indexed_result != query_result:
            raise RuntimeError("Index changed analytic result")
        indexed_bytes = conn.execute(
            "SELECT pg_total_relation_size('pg_temp.bench_full'::regclass)"
        ).fetchone()[0]
        return {
            "engine": "PostgreSQL",
            "database": "workforce_ci / TEMP tables",
            "version": conn.execute("SHOW server_version").fetchone()[0],
            "baseline_rows": n,
            "final_rows": final_count,
            "updates": scale.updated,
            "inserts": scale.inserted,
            "changed_rows": scale.changed_rows,
            "full_reload_ms": full_ms,
            "incremental_ms": inc_ms,
            "query_no_index_ms": no_index_ms,
            "query_with_index_ms": with_index_ms,
            "index_build_ms": round(index_ms, 3),
            "query_result": query_result,
            "explain_without_index": plan_before,
            "explain_with_index": plan_after,
            "storage_bytes_full_before_index": int(full_bytes),
            "storage_bytes_full_after_index": int(indexed_bytes),
            "storage_bytes_incremental": int(inc_bytes),
            "parity": "PASS (every column, every row)",
        }
