"""Offline contract tests for Phase 4 gates and private-data-safe reporting."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.phase4.quality_contract import GATES, Gate, evaluate
from src.phase4.pipeline import execute, status_summary, write_report
from src.phase4.synthetic_fixture import sample_rows, seed
from src.phase2.quality import normalize_and_validate
from src.phase2.schema_contract import SHEET_COLUMNS


class _Cursor:
    def __init__(self, result):
        self.result = result

    def fetchone(self):
        return (self.result,)


class _Conn:
    def __init__(self, results):
        self.results = results

    def execute(self, _query):
        value = next(self.results)
        if isinstance(value, Exception):
            raise value
        return _Cursor(value)


class Phase4QualityTests(unittest.TestCase):
    def test_unique_gate_ids_and_severity(self):
        self.assertGreaterEqual(len(GATES), 15)
        self.assertEqual(len({x.check_id for x in GATES}), len(GATES))
        self.assertEqual({x.severity for x in GATES}, {"BLOCK", "REVIEW"})

    def test_zero_violations_is_pass(self):
        gates = (Gate("one", "BLOCK", "SELECT 0", "test"),)
        self.assertEqual(evaluate(_Conn(iter([0])), gates)[0][1], "PASS")

    def test_source_warning_is_review_not_fail(self):
        gates = (Gate("known_discrepancy", "REVIEW", "SELECT 33", "source"),)
        self.assertEqual(evaluate(_Conn(iter([33])), gates)[0][1:3], ("REVIEW", 33))

    def test_blocking_violation_is_fail(self):
        gates = (Gate("bad", "BLOCK", "SELECT 2", "test"),)
        self.assertEqual(evaluate(_Conn(iter([2])), gates)[0][1:3], ("FAIL", 2))

    def test_sql_error_masks_private_exception(self):
        gates = (Gate("bad_sql", "BLOCK", "INVALID SQL", "test"),)
        result = evaluate(_Conn(iter([RuntimeError("private@sample.invalid")])), gates)
        self.assertEqual(result[0][1], "FAIL")
        self.assertNotIn("private@sample.invalid", str(result))

    def test_counts_and_report_aggregate_only(self):
        outcomes = [("x", "PASS", 0, "okay"), ("y", "REVIEW", 12, "expected")]
        self.assertEqual(status_summary(outcomes), {"PASS": 1, "REVIEW": 1, "FAIL": 0})
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "health.md"
            with patch("src.phase4.pipeline.REPORT", target):
                write_report(dict(run_id=1, mode="QUALITY_ONLY", status="SUCCEEDED",
                                  quality=status_summary(outcomes)))
            content = target.read_text(encoding="utf-8")
            self.assertIn("1 PASS, 1 REVIEW, 0 FAIL", content)
            self.assertNotIn("EmployeeID", content)

    def test_synthetic_fixture_meets_all_source_contracts(self):
        data = sample_rows()
        self.assertEqual(set(data), set(SHEET_COLUMNS))
        normalized, _ = normalize_and_validate(data)
        self.assertEqual(sum(len(x) for x in normalized.values()), 22)
        self.assertTrue(all(r["EmployeeID"].startswith("TEST_")
                            for r in data["DimEmployee"]))

    def test_fixture_requires_isolated_database(self):
        with patch.dict(os.environ, {"POSTGRES_DB": "workforce_dw", "HR_SYNTHETIC_DB": "YES"}):
            with self.assertRaisesRegex(RuntimeError, "Refusing synthetic fixture"):
                seed()

    def test_only_fixture_dependent_dbt_tests_tagged(self):
        root = Path(__file__).resolve().parents[1] / "dbt_hr" / "tests"
        baseline_tests = {"assert_reconciliation_baseline.sql",
                          "assert_mart_counts.sql", "assert_planning_kpis.sql"}
        for name in baseline_tests:
            self.assertIn("config(tags=['full_baseline'])",
                          (root / name).read_text(encoding="utf-8"))

    def test_unavailable_postgres_fails_closed(self):
        # No database means no durable audit is possible; do not report success.
        with patch("src.phase4.pipeline.connect_db", side_effect=ConnectionError("offline")):
            with self.assertRaises(ConnectionError):
                execute("QUALITY_ONLY")


if __name__ == "__main__":
    unittest.main()
