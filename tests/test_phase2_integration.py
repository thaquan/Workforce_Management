"""Live PostgreSQL tests; enable with HR_INTEGRATION_TESTS=1."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET

from psycopg import sql

from src.phase1.phase1_profiler import load_workbook
from src.phase2.ingest import DEFAULT_SOURCE, connect_db, file_sha256, ingest, raw_table
from src.phase2.quality import SourceValidationError, normalize_and_validate
from src.phase2.schema_contract import SHEET_COLUMNS


@unittest.skipUnless(os.environ.get("HR_INTEGRATION_TESTS") == "1",
                     "Run with HR_INTEGRATION_TESTS=1 after starting PostgreSQL")
class Phase2DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected_counts = {
            "dim_employee": 1200,
            "fact_monthly_snapshot": 6826,
            "fact_employee_events": 1406,
            "fact_compensation": 2914,
            "fact_performance": 2741,
            "fact_engagement": 10200,
            "fact_absence": 2755,
            "fact_recruitment": 288,
            "workforce_targets": 288,
            "dim_department": 8,
            "dim_location": 6,
            "dim_date": 1096,
        }
        if not DEFAULT_SOURCE.is_file():
            raise RuntimeError("Local source workbook missing (not stored in Git).")

    def read_counts(self):
        result = {}
        with connect_db() as conn:
            for name in self.expected_counts:
                result[name] = conn.execute(
                    sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier("raw", name))
                ).fetchone()[0]
        return result

    def test_01_all_raw_rows(self):
        actual = self.read_counts()
        self.assertEqual(actual, self.expected_counts)
        self.assertEqual(sum(actual.values()), 29728)

    def test_02_repeated_source_is_skipped(self):
        previous = self.read_counts()
        result = ingest()
        self.assertEqual(result["status"], "SKIPPED")
        self.assertEqual(previous, self.read_counts())

    def test_03_rollback_on_mid_load_failure(self):
        previous = self.read_counts()
        def fail_after_four_tables(sheet, index):
            if index == 4:
                raise RuntimeError("Synthetic test failure (no source values)")
        with self.assertRaisesRegex(RuntimeError, "Synthetic test failure"):
            ingest(force=True, failure_hook=fail_after_four_tables)
        self.assertEqual(previous, self.read_counts())
        with connect_db() as conn:
            status = conn.execute(
                "SELECT status FROM audit.load_batches ORDER BY batch_id DESC LIMIT 1"
            ).fetchone()[0]
        self.assertEqual(status, "FAILED")

    def test_04_invalid_workbook_audited(self):
        previous = self.read_counts()
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "corrupt.xlsx"
            source.write_bytes(b"INVALID_ZIP_INPUT")
            with self.assertRaises(BadZipFile):
                ingest(source=source)
        self.assertEqual(previous, self.read_counts())
        with connect_db() as conn:
            row = conn.execute(
                """SELECT b.status, qr.status, qr.check_id
                   FROM audit.load_batches b
                   JOIN audit.quality_results qr ON qr.batch_id=b.batch_id
                   ORDER BY b.batch_id DESC LIMIT 1"""
            ).fetchone()
        self.assertEqual(row, ("FAILED", "FAIL", "ingestion_transaction"))

    def test_05_duplicate_business_key_rejected(self):
        workbook = load_workbook(DEFAULT_SOURCE)
        workbook["DimEmployee"][1]["EmployeeID"] = workbook["DimEmployee"][0]["EmployeeID"]
        with self.assertRaisesRegex(SourceValidationError, "duplicate business key"):
            normalize_and_validate(workbook)

    def test_06_missing_foreign_key_rejected(self):
        workbook = load_workbook(DEFAULT_SOURCE)
        workbook["FactPerformance"][0]["EmployeeID"] = "INVALID_EMPLOYEE_TEST"
        with self.assertRaisesRegex(SourceValidationError, "missing from DimEmployee"):
            normalize_and_validate(workbook)

    def test_07_changed_source_replaces_atomically(self):
        before = self.read_counts()
        with connect_db() as conn:
            old_total = conn.execute(
                "SELECT SUM(budgeted_salary_cost) FROM raw.workforce_targets"
            ).fetchone()[0]
        with tempfile.TemporaryDirectory() as tmp:
            corrected = Path(tmp) / "corrected_workforce.xlsx"
            try:
                with ZipFile(DEFAULT_SOURCE) as original, ZipFile(corrected, "w") as output:
                    updated = False
                    for member in original.infolist():
                        content = original.read(member.filename)
                        if member.filename == "xl/worksheets/sheet9.xml":
                            root = ET.fromstring(content)
                            namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
                            cell = root.find(f".//{namespace}c[@r='F2']/{namespace}v")
                            self.assertIsNotNone(cell)
                            cell.text = str(int(cell.text) + 1)
                            content = ET.tostring(root, encoding="utf-8", xml_declaration=True)
                            updated = True
                        output.writestr(member, content)
                    self.assertTrue(updated, "Expected target sheet path not found")
                result = ingest(source=corrected)
                self.assertEqual(result["status"], "SUCCEEDED")
                self.assertEqual(self.read_counts(), before)
                with connect_db() as conn:
                    new_total = conn.execute(
                        "SELECT SUM(budgeted_salary_cost) FROM raw.workforce_targets"
                    ).fetchone()[0]
                self.assertEqual(new_total, old_total + 1)
            finally:
                # Restore the verified original regardless of the modified-source result.
                ingest(source=DEFAULT_SOURCE, force=True)
        self.assertEqual(self.read_counts(), before)

    def test_08_modified_database_with_same_count_is_repaired(self):
        before = self.read_counts()
        with connect_db() as conn:
            original_sum = conn.execute(
                "SELECT SUM(budgeted_salary_cost) FROM raw.workforce_targets"
            ).fetchone()[0]
            with conn.transaction():
                conn.execute(
                    """UPDATE raw.workforce_targets SET budgeted_salary_cost = budgeted_salary_cost + 1
                        WHERE ctid = (SELECT ctid FROM raw.workforce_targets LIMIT 1)"""
                )
        try:
            repaired = ingest()
            self.assertEqual(repaired["status"], "SUCCEEDED")
            with connect_db() as conn:
                repaired_sum = conn.execute(
                    "SELECT SUM(budgeted_salary_cost) FROM raw.workforce_targets"
                ).fetchone()[0]
            self.assertEqual(repaired_sum, original_sum)
            self.assertEqual(self.read_counts(), before)
        finally:
            ingest(force=True)

    def test_09_report_failure_does_not_change_committed_audit_status(self):
        before = self.read_counts()
        with patch("src.phase2.ingest.write_public_report", side_effect=PermissionError("test")):
            result = ingest(force=True)
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual(result["report_warning"], "PermissionError")
        with connect_db() as conn:
            status = conn.execute(
                "SELECT status FROM audit.load_batches WHERE batch_id=%s",
                (result["batch_id"],)
            ).fetchone()[0]
        self.assertEqual(status, "SUCCEEDED")
        self.assertEqual(self.read_counts(), before)

    def test_10_source_checksum_change_during_read_is_rejected(self):
        before = self.read_counts()
        digest = file_sha256(DEFAULT_SOURCE)
        with patch("src.phase2.ingest.file_sha256", side_effect=[digest, "0" * 64]):
            with self.assertRaisesRegex(SourceValidationError, "changed while being read"):
                ingest(force=True)
        with connect_db() as conn:
            status = conn.execute(
                "SELECT status FROM audit.load_batches ORDER BY batch_id DESC LIMIT 1"
            ).fetchone()[0]
        self.assertEqual(status, "FAILED")
        self.assertEqual(self.read_counts(), before)


if __name__ == "__main__":
    unittest.main()
