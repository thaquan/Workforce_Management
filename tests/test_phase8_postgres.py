"""Destructive-safe integration tests: ONLY synthetic workforce_ci, never workforce_dw."""
import copy
import os
import unittest

from src.phase2.ingest import connect_db
from src.phase8.contract import ContractError
from src.phase8.fixture import batches
from src.phase8.incremental import (
    _verify_schema, apply_batch, initialize_schema, quality_summary,
)

ISOLATED = (
    os.environ.get("HR_PHASE8_INTEGRATION_TESTS") == "YES"
    and os.environ.get("HR_PHASE8_ALLOW_WRITE") == "YES"
    and os.environ.get("HR_SYNTHETIC_DB") == "YES"
    and os.environ.get("POSTGRES_DB") == "workforce_ci"
)


@unittest.skipUnless(ISOLATED, "Explicit disposable workforce_ci permission required")
class Phase8PostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_schema()

    def test_01_rollback_on_partial_batch(self):
        batch = batches()[0]

        def fail_on_second(index):
            if index == 2:
                raise RuntimeError("synthetic injected failure")

        with self.assertRaisesRegex(RuntimeError, "injected failure"):
            apply_batch(batch, failure_hook=fail_on_second)
        with connect_db() as conn:
            self.assertEqual(
                conn.execute(
                    "SELECT last_source_offset FROM incremental_demo.stream_state"
                ).fetchone()[0], 0
            )
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM incremental_demo.employee_events"
            ).fetchone()[0], 0)
            self.assertEqual(conn.execute(
                "SELECT COUNT(*) FROM incremental_demo.batch_audit"
            ).fetchone()[0], 0)
        result = apply_batch(batch)
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(result["watermark"], 3)
        self.assertEqual(result["state_changes"], 3)

    def test_02_replay_does_not_duplicate_events(self):
        result = apply_batch(batches()[0])
        self.assertEqual(result["status"], "SKIPPED_UNCHANGED")
        self.assertEqual(quality_summary()["events_stored"], 3)
        self.assertEqual(quality_summary()["batches_succeeded"], 1)

    def test_03_checksum_conflict_and_source_gap_rejected(self):
        changed = copy.deepcopy(batches()[0])
        changed["events"][0]["fte"] = 0.25
        with self.assertRaisesRegex(ContractError, "different checksum"):
            apply_batch(changed)
        with self.assertRaisesRegex(ContractError, "Out-of-order"):
            apply_batch(batches()[2])
        self.assertEqual(quality_summary()["watermark"], 3)

    def test_04_update_delete_and_late_event(self):
        batch2, batch3 = batches()[1:]
        result = apply_batch(batch2)
        self.assertEqual(result["state_changes"], 3)
        self.assertEqual(result["watermark"], 6)
        late = apply_batch(batch3)
        self.assertEqual(late["late_events"], 1)
        self.assertEqual(late["state_changes"], 1)
        self.assertEqual(late["watermark"], 8)
        actual = quality_summary()
        self.assertEqual(actual["events_stored"], 8)
        self.assertEqual(actual["active_employees"], 3)
        self.assertEqual(actual["deleted_employees"], 1)
        self.assertEqual(actual["active_fte"], 2.55)
        self.assertEqual(actual["late_events"], 1)
        with connect_db() as conn:
            self.assertEqual(conn.execute(
                "SELECT source_version FROM incremental_demo.employee_state WHERE employee_id='TEST_E001'"
            ).fetchone()[0], 2)
            self.assertEqual(conn.execute(
                "SELECT deleted FROM incremental_demo.employee_state WHERE employee_id='TEST_E002'"
            ).fetchone()[0], True)

    def test_05_idempotent_complete_replay(self):
        for batch in batches():
            self.assertEqual(apply_batch(batch)["status"], "SKIPPED_UNCHANGED")
        state = quality_summary()
        self.assertEqual(state["events_stored"], 8)
        self.assertEqual(state["batches_succeeded"], 3)
        self.assertEqual(state["watermark"], 8)

    def test_06_schema_drift_rejected_and_rolled_back(self):
        with self.assertRaisesRegex(RuntimeError, "Schema drift"):
            with connect_db() as conn, conn.transaction():
                conn.execute(
                    "ALTER TABLE incremental_demo.employee_state ADD COLUMN injected_drift TEXT"
                )
                _verify_schema(conn)
        with connect_db() as conn:
            self.assertEqual(conn.execute(
                """SELECT COUNT(*) FROM information_schema.columns
                   WHERE table_schema='incremental_demo'
                     AND table_name='employee_state' AND column_name='injected_drift'"""
            ).fetchone()[0], 0)


    def test_07_read_only_quality_catches_state_corruption(self):
        # Inject a committed synthetic-state error, then restore in finally.
        with connect_db() as conn:
            conn.execute(
                "UPDATE incremental_demo.employee_state SET fte=0.125 WHERE employee_id='TEST_E001'"
            )
        try:
            with self.assertRaisesRegex(RuntimeError, "diverged from latest"):
                quality_summary()
        finally:
            with connect_db() as conn:
                conn.execute(
                    "UPDATE incremental_demo.employee_state SET fte=1 WHERE employee_id='TEST_E001'"
                )
        self.assertEqual(quality_summary()["status"], "PASS")



if __name__ == "__main__":
    unittest.main()
