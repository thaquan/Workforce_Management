"""Offline Dagster graph, fail-closed and blocking-gate regression tests."""
import os
import unittest
from unittest.mock import MagicMock, patch

from dagster import RetryRequested, materialize, mem_io_manager

from src.phase7.definitions import ASSETS, _retry_if_transient, defs
from src.phase7.safety import assert_disposable_target, mode


class Phase7DagsterTests(unittest.TestCase):
    def test_graph_and_job_have_all_five_assets(self):
        self.assertEqual(
            [item.key.path[-1] for item in ASSETS],
            ["source_preflight", "raw_ingested", "dbt_marts_built",
             "quality_gates_checked", "report_ready"],
        )
        self.assertIsNotNone(defs.resolve_job_def("workforce_manual"))
        schedules = defs.schedules
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0].default_status.value, "STOPPED")

    def test_dry_run_never_calls_db_or_build(self):
        with (
            patch.dict(os.environ, {"HR_PHASE7_MODE": "dry_run"}),
            patch("src.phase7.definitions.assert_disposable_target", side_effect=AssertionError("database used")),
            patch("src.phase7.definitions.seed", side_effect=AssertionError("seed used")),
            patch("src.phase7.definitions._run_dbt_synthetic", side_effect=AssertionError("dbt used")),
            patch("src.phase7.definitions.pipeline.execute", side_effect=AssertionError("quality DB used")),
        ):
            result = materialize(
                ASSETS, resources={"io_manager": mem_io_manager},
                raise_on_error=False,
            )
        self.assertTrue(result.success)
        self.assertEqual(result.output_for_node("report_ready")["status"], "PLANNED")

    def test_target_guard_blocks_authoritative_database(self):
        with patch.dict(os.environ, {
            "HR_PHASE7_ALLOW_WRITE": "YES",
            "HR_SYNTHETIC_DB": "YES",
            "POSTGRES_DB": "workforce_dw",
        }):
            with self.assertRaisesRegex(RuntimeError, "write refused"):
                assert_disposable_target()

    def test_target_guard_requires_explicit_write_flag(self):
        with patch.dict(os.environ, {
            "HR_PHASE7_ALLOW_WRITE": "NO",
            "HR_SYNTHETIC_DB": "YES",
            "POSTGRES_DB": "workforce_ci",
        }):
            with self.assertRaisesRegex(RuntimeError, "write refused"):
                assert_disposable_target()

    def test_bad_mode_is_rejected(self):
        with patch.dict(os.environ, {"HR_PHASE7_MODE": "production"}):
            with self.assertRaises(ValueError):
                mode()

    @staticmethod
    def _fake_db():
        conn = MagicMock()
        conn.__enter__.return_value = conn
        return conn

    def _materialize_mocked_synthetic(self, audit):
        with (
            patch.dict(os.environ, {"HR_PHASE7_MODE": "synthetic"}),
            patch("src.phase7.definitions.assert_disposable_target"),
            patch("src.phase7.definitions.connect_db", return_value=self._fake_db()),
            patch("src.phase7.definitions.raw_tables_match", return_value=True),
            patch("src.phase7.definitions.ensure_tables"),
            patch("src.phase7.definitions.seed", side_effect=AssertionError("unchanged fixture reseeded")),
            patch("src.phase7.definitions._run_dbt_synthetic", return_value=116),
            patch("src.phase7.definitions.pipeline.execute", return_value=audit),
        ):
            return materialize(
                ASSETS, resources={"io_manager": mem_io_manager},
                raise_on_error=False,
            )

    def test_review_is_allowed_and_audit_id_is_retained(self):
        audit = {
            "status": "SUCCEEDED", "run_id": 123,
            "quality": {"PASS": 17, "REVIEW": 1, "FAIL": 0},
        }
        result = self._materialize_mocked_synthetic(audit)
        self.assertTrue(result.success)
        marker = result.output_for_node("report_ready")
        self.assertEqual(marker["pipeline_run_id"], 123)
        self.assertEqual(marker["status"], "READY_SYNTHETIC")

    def test_blocking_quality_failure_prevents_report_ready(self):
        audit = {
            "status": "FAILED", "run_id": 124,
            "quality": {"PASS": 17, "REVIEW": 0, "FAIL": 1},
        }
        result = self._materialize_mocked_synthetic(audit)
        self.assertFalse(result.success)
        materialized = {
            event.asset_key.path[-1]
            for event in result.get_asset_materialization_events()
        }
        self.assertNotIn("report_ready", materialized)

    def test_connected_database_name_is_checked(self):
        conn = self._fake_db()
        conn.execute.return_value.fetchone.return_value = ("workforce_dw",)
        with (
            patch.dict(os.environ, {"HR_PHASE7_ALLOW_WRITE": "YES", "HR_SYNTHETIC_DB": "YES"}),
            patch("src.phase7.safety.read_local_env", return_value={
                "POSTGRES_DB": "workforce_ci",
                "POSTGRES_HOST": "127.0.0.1",
                "POSTGRES_PORT": "5433",
            }),
            patch("src.phase7.safety.connect_db", return_value=conn),
        ):
            with self.assertRaisesRegex(RuntimeError, "connected database"):
                assert_disposable_target()

    def test_transient_preflight_failure_recovers_with_bounded_retry(self):
        audit = {
            "status": "SUCCEEDED", "run_id": 321,
            "quality": {"PASS": 18, "REVIEW": 0, "FAIL": 0},
        }
        with (
            patch.dict(os.environ, {"HR_PHASE7_MODE": "synthetic"}),
            patch("src.phase7.definitions.assert_disposable_target",
                  side_effect=[ConnectionError("temporary"), None, None, None, None]) as guard,
            patch("src.phase7.definitions.connect_db", return_value=self._fake_db()),
            patch("src.phase7.definitions.raw_tables_match", return_value=True),
            patch("src.phase7.definitions.ensure_tables"),
            patch("src.phase7.definitions.seed", side_effect=AssertionError("unexpected reload")),
            patch("src.phase7.definitions._run_dbt_synthetic", return_value=116),
            patch("src.phase7.definitions.pipeline.execute", return_value=audit),
        ):
            result = materialize(
                ASSETS, resources={"io_manager": mem_io_manager},
                raise_on_error=False,
            )
        self.assertTrue(result.success)
        self.assertGreaterEqual(guard.call_count, 5)
        self.assertEqual(result.output_for_node("report_ready")["pipeline_run_id"], 321)
    def test_only_transient_exceptions_are_retried(self):
        with self.assertRaises(RetryRequested):
            _retry_if_transient(ConnectionError("temporary"))
        with self.assertRaises(ValueError):
            _retry_if_transient(ValueError("schema drift"))


if __name__ == "__main__":
    unittest.main()
