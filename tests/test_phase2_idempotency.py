"""Offline regression tests for fingerprinting and safe skip rules."""
from pathlib import Path
import tempfile
import unittest

from src.phase2.ingest import file_sha256, raw_table, raw_tables_match
from src.phase2.schema_contract import SHEET_COLUMNS


class _Result:
    def __init__(self, value):
        self.value = value

    def fetchone(self):
        return (self.value,)


class _FakeCursor:
    def __init__(self, counts, absent=False):
        self.counts = counts
        self.absent = absent
        self.pending = iter(counts.values())

    def execute(self, statement, params=None):
        if params is not None:
            return _Result(None if self.absent else params[0])
        return _Result(next(self.pending))


class Phase2IdempotencyTests(unittest.TestCase):
    def test_sha256_is_stable_and_detects_modified_content(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "sample.bin"
            file.write_bytes(b"same-source")
            first = file_sha256(file)
            self.assertEqual(first, file_sha256(file))
            file.write_bytes(b"modified-source")
            self.assertNotEqual(first, file_sha256(file))

    def test_all_raw_names_are_distinct(self):
        names = [raw_table(name) for name in SHEET_COLUMNS]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("fact_monthly_snapshot", names)

    def test_missing_table_disables_skip(self):
        normalized = {"DimEmployee": [{}]}
        self.assertFalse(raw_tables_match(_FakeCursor({}, absent=True), normalized))

    def test_count_discrepancy_disables_skip(self):
        normalized = {"DimEmployee": [{}]}
        self.assertFalse(raw_tables_match(_FakeCursor({"dim_employee": 0}), normalized))

    def test_matching_table_count_allows_skip(self):
        normalized = {"DimEmployee": [{}]}
        self.assertTrue(raw_tables_match(_FakeCursor({"dim_employee": 1}), normalized))


if __name__ == "__main__":
    unittest.main()
