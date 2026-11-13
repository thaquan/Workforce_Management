"""PostgreSQL benchmark parity in an authorized isolated workforce_ci only."""
import os
import tempfile
import unittest

from src.phase9.duckdb_benchmark import benchmark_duckdb
from src.phase9.postgres_benchmark import benchmark_postgres
from src.phase9.run import compile_summary
from src.phase9.workload import Scale

ISOLATED = (
    os.getenv("HR_PHASE9_INTEGRATION_TESTS") == "YES"
    and os.getenv("HR_PHASE9_ALLOW_WRITE") == "YES"
    and os.getenv("HR_PHASE9_DISPOSABLE_ACK") == "YES"
    and os.getenv("HR_SYNTHETIC_DB") == "YES"
    and os.getenv("POSTGRES_DB") == "workforce_ci"
)


@unittest.skipUnless(ISOLATED, "A disposable workforce_ci target is required")
class PostgresSyntheticPerformanceTests(unittest.TestCase):
    def test_temporary_full_vs_incremental_and_duckdb_parity(self):
        scale = Scale(2000)
        pg = benchmark_postgres(scale, repeats=2)
        with tempfile.TemporaryDirectory() as directory:
            duck = benchmark_duckdb(scale, repeats=2, folder=directory)
        result = compile_summary(scale, pg, duck)
        self.assertEqual(result["final_rows"], 2020)
        self.assertEqual(result["update_rows"], 100)
        self.assertEqual(result["new_rows"], 20)
        self.assertEqual(result["cross_engine_query_parity"], "PASS (count and sums)")
        self.assertEqual(pg["parity"], "PASS (every column, every row)")
        self.assertEqual(len(pg["full_reload_ms"]), 2)
        self.assertEqual(len(pg["incremental_ms"]), 2)
        self.assertGreater(pg["storage_bytes_full_after_index"], 0)
        self.assertTrue(pg["explain_without_index"]["operations"])
        self.assertTrue(pg["explain_with_index"]["operations"])


if __name__ == "__main__":
    unittest.main()
