"""Phase 8 offline tests: no PostgreSQL access or real HR workbook required."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from dagster import RetryRequested, materialize, mem_io_manager

from src.phase8.contract import ContractError, EVENT_FIELDS, fingerprint, validate_batch
from src.phase8.definitions import ASSETS, _retry_transient, defs
from src.phase8.fixture import batches
from src.phase8.parquet_batches import read_batch, write_batch
from src.phase8.safety import require_synthetic_target


class Phase8ContractTests(unittest.TestCase):
    def test_three_synthetic_batches_and_offsets(self):
        values = batches()
        self.assertEqual(len(values), 3)
        self.assertEqual([len(item["events"]) for item in values], [3, 3, 2])
        self.assertEqual(
            [event["source_offset"] for item in values for event in item["events"]],
            list(range(1, 9)),
        )
        self.assertTrue(all(row["employee_id"].startswith("TEST_E")
                            for b in values for row in b["events"]))
        self.assertEqual(fingerprint(values[0]), fingerprint(copy.deepcopy(values[0])))

    def test_extra_private_columns_are_rejected(self):
        batch = copy.deepcopy(batches()[0])
        batch["events"][0]["EmployeeName"] = "not allowed"
        with self.assertRaises(ContractError):
            validate_batch(batch)

    def test_missing_offset_fails_closed(self):
        batch = copy.deepcopy(batches()[0])
        batch["events"][1]["source_offset"] = 8
        with self.assertRaisesRegex(ContractError, "gap-free"):
            validate_batch(batch)

    def test_invalid_fte_rejected(self):
        batch = copy.deepcopy(batches()[0])
        batch["events"][0]["fte"] = -1.0
        with self.assertRaisesRegex(ContractError, "FTE"):
            validate_batch(batch)

    def test_missing_utc_timezone_rejected(self):
        batch = copy.deepcopy(batches()[0])
        batch["events"][0]["event_time"] = "2025-10-01"
        with self.assertRaisesRegex(ContractError, "UTC"):
            validate_batch(batch)

    def test_delete_contract_and_late_business_version(self):
        value = batches()
        delete = value[1]["events"][1]
        self.assertEqual(delete["operation"], "DELETE")
        self.assertIsNone(delete["fte"])
        self.assertEqual(value[2]["events"][0]["source_version"], 1)
        self.assertLess(
            value[2]["events"][0]["event_time"],
            value[1]["events"][0]["event_time"],
        )

    def test_parquet_round_trip_and_idempotent_write(self):
        batch = batches()[0]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "batch.parquet"
            write_batch(batch, path)
            original = path.read_bytes()
            self.assertEqual(read_batch(path), batch)
            write_batch(batch, path)
            self.assertEqual(path.read_bytes(), original)
            changed = copy.deepcopy(batch)
            changed["events"][0]["fte"] = 0.75
            with self.assertRaisesRegex(ContractError, "different content"):
                write_batch(changed, path)
            self.assertEqual(path.read_bytes(), original)

    def test_corrupted_parquet_checksum_rejected(self):
        batch = batches()[0]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fixture.parquet"
            write_batch(batch, path)
            data = path.read_bytes()
            path.write_bytes(data[:-5])
            with self.assertRaises(Exception):
                read_batch(path)


class Phase8DagsterTests(unittest.TestCase):
    def test_asset_graph_and_disabled_schedule(self):
        self.assertEqual(
            [asset.key.path[-1] for asset in ASSETS],
            [
                "synthetic_changes_prepared",
                "incremental_batches_ingested",
                "incremental_quality_checked",
                "incremental_report_ready",
            ],
        )
        self.assertIsNotNone(defs.resolve_job_def("incremental_manual"))
        self.assertEqual(defs.schedules[0].default_status.value, "STOPPED")

    def test_dry_run_makes_no_db_writes(self):
        with (
            patch.dict(os.environ, {"HR_PHASE8_MODE": "dry_run"}),
            patch("src.phase8.definitions.require_synthetic_target", side_effect=AssertionError("db used")),
            patch("src.phase8.definitions.initialize_schema", side_effect=AssertionError("sql used")),
            patch("src.phase8.definitions.apply_batch", side_effect=AssertionError("writes used")),
            patch("src.phase8.definitions.write_batch", side_effect=AssertionError("Parquet written")),
        ):
            result = materialize(
                ASSETS, resources={"io_manager": mem_io_manager}, raise_on_error=False
            )
        self.assertTrue(result.success)
        self.assertEqual(result.output_for_node("incremental_report_ready")["status"], "PLANNED")

    def test_refuses_authoritative_database(self):
        with patch.dict(os.environ, {
            "HR_PHASE8_ALLOW_WRITE": "YES",
            "HR_SYNTHETIC_DB": "YES",
            "POSTGRES_DB": "workforce_dw",
        }):
            with self.assertRaisesRegex(RuntimeError, "require"):
                require_synthetic_target()

    def test_refuses_no_explicit_permission(self):
        with patch.dict(os.environ, {
            "HR_PHASE8_ALLOW_WRITE": "NO",
            "HR_SYNTHETIC_DB": "YES",
            "POSTGRES_DB": "workforce_ci",
        }):
            with self.assertRaisesRegex(RuntimeError, "require"):
                require_synthetic_target()

    def test_connected_name_mismatch_blocks(self):
        conn = MagicMock()
        conn.__enter__.return_value = conn
        conn.execute.return_value.fetchone.return_value = ("workforce_dw",)
        with (
            patch.dict(os.environ, {"HR_PHASE8_ALLOW_WRITE": "YES", "HR_SYNTHETIC_DB": "YES"}),
            patch("src.phase8.safety.read_local_env", return_value={
                "POSTGRES_DB": "workforce_ci",
                "POSTGRES_HOST": "127.0.0.1",
                "POSTGRES_PORT": "5433",
            }),
            patch("src.phase8.safety.connect_db", return_value=conn),
        ):
            with self.assertRaisesRegex(RuntimeError, "Connected database"):
                require_synthetic_target()

    def test_blocking_quality_prevents_ready_marker(self):
        bad_quality = {
            "status": "PASS", "watermark": 8, "events_stored": 8,
            "batches_succeeded": 3, "late_events": 1,
            "active_employees": 99, "deleted_employees": 1, "active_fte": 2.55,
        }
        with (
            patch.dict(os.environ, {"HR_PHASE8_MODE": "synthetic"}),
            patch("src.phase8.definitions.require_synthetic_target"),
            patch("src.phase8.definitions.write_batch", return_value=Path("ignored.parquet")),
            patch("src.phase8.definitions.initialize_schema"),
            patch("src.phase8.definitions.read_batch", return_value=batches()[0]),
            patch("src.phase8.definitions.apply_batch", return_value={
                "status": "SKIPPED_UNCHANGED", "state_changes": 0, "watermark": 8,
            }),
            patch("src.phase8.definitions.quality_summary", return_value=bad_quality),
        ):
            result = materialize(
                ASSETS, resources={"io_manager": mem_io_manager}, raise_on_error=False
            )
        self.assertFalse(result.success)
        produced = {
            event.asset_key.path[-1]
            for event in result.get_asset_materialization_events()
        }
        self.assertNotIn("incremental_report_ready", produced)

    def test_only_connection_errors_trigger_retry(self):
        with self.assertRaises(RetryRequested):
            _retry_transient(ConnectionError("temporary"))
        with self.assertRaises(ContractError):
            _retry_transient(ContractError("schema drift"))


if __name__ == "__main__":
    unittest.main()
