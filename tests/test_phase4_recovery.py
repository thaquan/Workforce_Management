"""Run only in isolated workforce_ci after synthetic fixture/dbt build.

This suite intentionally mutates a marts row and restores it in finally.
It must never run against the main HR database.
"""
import os
from pathlib import Path
import tempfile
import unittest
from zipfile import BadZipFile

import psycopg

from src.phase2.ingest import connect_db, ensure_tables, ingest
from src.phase4.pipeline import execute


@unittest.skipUnless(
    os.getenv("HR_PHASE4_ISOLATED_TESTS") == "YES"
    and os.getenv("POSTGRES_DB") == "workforce_ci"
    and os.getenv("HR_SYNTHETIC_DB") == "YES",
    "Requires synthetic workforce_ci with explicit isolated test flags",
)
class Phase4RecoveryTests(unittest.TestCase):
    def test_01_baseline_quality_passes(self):
        result = execute("QUALITY_ONLY")
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["quality"]["FAIL"], 0)

    def test_02_corrupted_mart_blocks_run_and_restores(self):
        with connect_db() as conn:
            baseline = conn.execute(
                """SELECT fte FROM marts.mart_workforce_monthly
                   WHERE month=DATE '2023-01-01' AND department_id='TEST_D001'"""
            ).fetchone()[0]
            with conn.transaction():
                conn.execute(
                    """UPDATE marts.mart_workforce_monthly SET fte=-1
                       WHERE month=DATE '2023-01-01' AND department_id='TEST_D001'"""
                )
        try:
            blocked = execute("QUALITY_ONLY")
            self.assertEqual(blocked["status"], "FAILED")
            self.assertGreater(blocked["quality"]["FAIL"], 0)
            with connect_db() as conn:
                audited = conn.execute(
                    """SELECT COUNT(*) FROM audit.data_quality_results
                       WHERE pipeline_run_id=%s AND check_id='negative_hc_fte'
                         AND status='FAIL'""", (blocked["run_id"],)
                ).fetchone()[0]
            self.assertEqual(audited, 1)
        finally:
            with connect_db() as conn:
                with conn.transaction():
                    conn.execute(
                        """UPDATE marts.mart_workforce_monthly SET fte=%s
                           WHERE month=DATE '2023-01-01'
                             AND department_id='TEST_D001'""", (baseline,)
                    )
        restored = execute("QUALITY_ONLY")
        self.assertEqual(restored["status"], "SUCCEEDED")
        self.assertEqual(restored["quality"]["FAIL"], 0)

    def test_03_duplicate_raw_primary_key_rolls_back(self):
        with connect_db() as conn:
            before = conn.execute("SELECT COUNT(*) FROM raw.dim_department").fetchone()[0]
            with self.assertRaises(psycopg.errors.UniqueViolation):
                with conn.transaction():
                    conn.execute(
                        """INSERT INTO raw.dim_department(department_id,department)
                           VALUES ('TEST_D001','Duplicate fixture department')"""
                    )
            after = conn.execute("SELECT COUNT(*) FROM raw.dim_department").fetchone()[0]
        self.assertEqual(before, after)

    def test_04_corrupt_excel_is_audited_and_raw_kept(self):
        with connect_db() as conn:
            before = conn.execute("SELECT COUNT(*) FROM raw.dim_employee").fetchone()[0]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "corrupt_synthetic.xlsx"
            source.write_bytes(b"NOT_AN_EXCEL_FILE")
            with self.assertRaises(BadZipFile):
                ingest(source=source)
        with connect_db() as conn:
            after = conn.execute("SELECT COUNT(*) FROM raw.dim_employee").fetchone()[0]
            failed = conn.execute(
                """SELECT status FROM audit.load_batches ORDER BY batch_id DESC LIMIT 1"""
            ).fetchone()[0]
        self.assertEqual(before, after)
        self.assertEqual(failed, "FAILED")

    def test_05_schema_drift_detected_and_rolled_back(self):
        with connect_db() as conn:
            with self.assertRaisesRegex(RuntimeError, "Schema drift"):
                with conn.transaction():
                    conn.execute("ALTER TABLE raw.dim_department ADD COLUMN temporary_drift TEXT")
                    ensure_tables(conn)
            col_count = conn.execute(
                """SELECT COUNT(*) FROM information_schema.columns
                   WHERE table_schema='raw' AND table_name='dim_department'
                     AND column_name='temporary_drift'"""
            ).fetchone()[0]
        self.assertEqual(col_count, 0)

    def test_06_stuck_run_is_reported_and_cleaned_up(self):
        from src.phase4.health import health_summary
        with connect_db() as conn:
            old_run_id = conn.execute(
                """INSERT INTO audit.pipeline_runs
                   (run_mode,status,stage,started_at)
                   VALUES ('QUALITY_ONLY','RUNNING','SYNTHETIC_HANG',
                           NOW()-INTERVAL '3 hours')
                   RETURNING pipeline_run_id"""
            ).fetchone()[0]
        try:
            health = health_summary()
            self.assertGreaterEqual(health["running_over_2h"], 1)
        finally:
            with connect_db() as conn:
                conn.execute(
                    """UPDATE audit.pipeline_runs
                       SET status='FAILED',stage='RECOVERED_TEST',
                           finished_at=NOW(),error_type='SyntheticTimeout'
                       WHERE pipeline_run_id=%s""", (old_run_id,),
                )


if __name__ == "__main__":
    unittest.main()
