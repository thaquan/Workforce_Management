"""Phase 9 offline deterministic workload, result parity and access control."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.phase9.duckdb_benchmark import benchmark_duckdb
from src.phase9.report import dashboard_html, read_aggregates
from src.phase9.run import compile_summary, main, measurements
from src.phase9.safety import verify_benchmark_db
from src.phase9.workload import Scale, delta_projection, projection


class Phase9WorkloadTests(unittest.TestCase):
    def test_reproducible_scales_and_change_volume(self):
        for baseline in (1_000, 100_000, 500_000, 1_000_000):
            s = Scale(baseline)
            self.assertEqual(s.updated, baseline // 20)
            self.assertEqual(s.inserted, baseline // 100)
            self.assertEqual(s.changed_rows, 6 * baseline // 100)
            self.assertEqual(s.final_rows, baseline + baseline // 100)

    def test_limits_reject_invalid_or_giant_datasets(self):
        for value in (True, -1, 0, 99, 2_000_001, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Scale(value)

    def test_generator_is_deterministic_and_only_synthetic(self):
        s = Scale(1000)
        a = projection(1, s.final_rows, s.baseline, final=True)
        self.assertEqual(a, projection(1, s.final_rows, s.baseline, final=True))
        self.assertIn("generate_series", a)
        self.assertIn("CASE WHEN n <=", a)
        self.assertIn("UNION ALL", delta_projection(s))
        self.assertNotIn("raw.", delta_projection(s))
        with self.assertRaises(ValueError):
            projection(0, 100, 1000, False)

    def test_duckdb_parquet_correctness_and_rowcounts(self):
        with tempfile.TemporaryDirectory() as tempdir:
            result = benchmark_duckdb(Scale(1000), 2, tempdir)
            self.assertEqual(result["final_rows"], 1010)
            self.assertEqual(result["query_result"], [9, 3090231, 7020])
            self.assertEqual(len(result["query_parquet_ms"]), 2)
            self.assertGreater(result["parquet_zstd_bytes"], 0)
            with self.assertRaisesRegex(RuntimeError, "overwrite"):
                benchmark_duckdb(Scale(1000), 2, tempdir)

    def test_stats_have_median_and_interpolated_p95(self):
        value = measurements([5.0, 1.0, 3.0])
        self.assertEqual(value["median_ms"], 3.0)
        self.assertEqual(value["p95_ms"], 4.8)
        self.assertEqual(value["samples_ms"], [5.0, 1.0, 3.0])
        with self.assertRaises(ValueError):
            measurements([])

    def test_cross_engine_result_mismatch_fails(self):
        pg = {
            "parity": "PASS (every column, every row)",
            "full_reload_ms": [10, 10],
            "incremental_ms": [5, 5],
            "version": "17",
            "query_no_index_ms": [1, 1],
            "query_with_index_ms": [1, 1],
            "index_build_ms": 2,
            "explain_without_index": {"operations": ["Seq Scan"]},
            "explain_with_index": {"operations": ["Index Scan"]},
            "storage_bytes_full_before_index": 20,
            "storage_bytes_full_after_index": 30,
            "storage_bytes_incremental": 20,
            "query_result": [1, 2, 3],
        }
        duck = {
            "version": "1.5", "parquet_generation_ms": 3,
            "parquet_zstd_bytes": 200, "query_parquet_ms": [1, 1],
            "threads": 2, "query_result": [2, 3, 4],
        }
        with self.assertRaisesRegex(RuntimeError, "disagrees"):
            compile_summary(Scale(1000), pg, duck)
        duck["query_result"] = [1, 2, 3]
        summary = compile_summary(Scale(1000), pg, duck)
        self.assertEqual(summary["cross_engine_query_parity"], "PASS (count and sums)")

    def test_default_cli_plan_never_connects_to_db(self):
        with (
            patch("src.phase9.run.verify_benchmark_db", side_effect=AssertionError("db used")),
            patch("src.phase9.run.benchmark_postgres", side_effect=AssertionError("pg used")),
            patch("src.phase9.run.benchmark_duckdb", side_effect=AssertionError("duck used")),
        ):
            self.assertEqual(main(["--mode", "plan", "--rows", "100000", "500000"]), 0)

    def test_compare_requires_explicit_allow_flag(self):
        with self.assertRaises(SystemExit) as err:
            main(["--mode", "compare", "--rows", "1000", "--repeats", "2"])
        self.assertEqual(err.exception.code, 2)

    def test_refuse_live_warehouse_even_with_allow_flag(self):
        with patch.dict(os.environ, {
            "HR_PHASE9_ALLOW_WRITE": "YES",
            "HR_PHASE9_DISPOSABLE_ACK": "YES",
            "HR_SYNTHETIC_DB": "YES",
            "POSTGRES_DB": "workforce_dw",
        }):
            with self.assertRaisesRegex(RuntimeError, "refuses"):
                verify_benchmark_db()

    def test_refuse_missing_disposable_ack(self):
        with patch.dict(os.environ, {
            "HR_PHASE9_ALLOW_WRITE": "YES",
            "HR_PHASE9_DISPOSABLE_ACK": "NO",
            "HR_SYNTHETIC_DB": "YES",
            "POSTGRES_DB": "workforce_ci",
        }):
            with self.assertRaisesRegex(RuntimeError, "refuses"):
                verify_benchmark_db()

    def test_check_actual_connected_database(self):
        conn = MagicMock()
        conn.__enter__.return_value = conn
        conn.execute.return_value.fetchone.return_value = ("workforce_dw",)
        with (
            patch.dict(os.environ, {
                "HR_PHASE9_ALLOW_WRITE": "YES",
                "HR_PHASE9_DISPOSABLE_ACK": "YES",
                "HR_SYNTHETIC_DB": "YES",
            }),
            patch("src.phase9.safety.read_local_env", return_value={
                "POSTGRES_DB": "workforce_ci",
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5433",
            }),
            patch("src.phase9.safety.connect_db", return_value=conn),
        ):
            with self.assertRaisesRegex(RuntimeError, "not workforce_ci"):
                verify_benchmark_db()


    def test_aggregate_report_rejects_non_synthetic_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "untrusted.json"
            path.write_text('{"synthetic": false, "mode": "duckdb", "results": []}')
            with self.assertRaisesRegex(ValueError, "synthetic"):
                read_aggregates([path])

    def test_html_report_distinguishes_unmeasured_postgres(self):
        rows = [{
            "baseline_rows": 100000, "final_rows": 101000,
            "changed_rows": 6000, "parquet_zstd_bytes": 300000,
            "parquet_generation_ms": 30,
            "duckdb_query_median_ms": 7.0, "duckdb_query_p95_ms": 8.0,
            "postgres_full_median_ms": "", "postgres_incremental_median_ms": "",
            "postgres_speed_ratio": "", "query_parity": "DuckDB only",
        }]
        html = dashboard_html(rows)
        self.assertIn("not measured at this scale", html)
        self.assertIn("100,000 baseline records", html)
        self.assertIn("not a production benchmark", html)

    def test_pg_benchmark_only_creates_temp_tables(self):
        source = (Path(__file__).resolve().parents[1] /
                  "src" / "phase9" / "postgres_benchmark.py").read_text()
        self.assertIn("CREATE TEMP TABLE bench_full", source)
        self.assertIn("CREATE TEMP TABLE bench_inc", source)
        self.assertNotIn("DROP SCHEMA", source)
        self.assertNotIn("CREATE TABLE raw.", source)


if __name__ == "__main__":
    unittest.main()
