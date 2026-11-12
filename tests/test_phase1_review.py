"""Regression checks for the Phase 1 published, aggregate-only artifacts."""
import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "phase1"


def csv_rows(name):
    with (REPORT / name).open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


class Phase1ReviewTests(unittest.TestCase):
    def test_source_inventory(self):
        rows = csv_rows("source_inventory.csv")
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(int(r["rows"]) for r in rows), 29728)

    def test_monthly_reconciliation(self):
        rows = csv_rows("monthly_reconciliation.csv")
        self.assertEqual(len(rows), 36)
        self.assertEqual(sum(r["status"] == "REVIEW" for r in rows), 33)
        june = next(r for r in rows if r["month"] == "2025-06")
        self.assertEqual(int(june["hc_difference"]), 98)
        self.assertEqual(int(june["terminations"]), 98)
    def test_june_restructuring_evidence(self):
        rows = csv_rows("restructuring_evidence.csv")
        affected = [r for r in rows if int(r["june_terminations"]) > 0]
        self.assertEqual({r["department_id"] for r in affected},
                         {"D002", "D003", "D004", "D005"})
        self.assertEqual(sum(int(r["june_terminations"]) for r in affected), 98)
        for row in rows:
            self.assertEqual(int(row["june_hc_difference"]),
                             int(row["june_terminations"]))

    def test_calendar_coverage(self):
        # The generated CSV is intentionally gitignored. Check the committed
        # profiling evidence so this test passes on a fresh clone as well.
        summary = json.loads((REPORT / "review_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["extended_calendar_days"], 2918)
        self.assertEqual(summary["extended_calendar_start"], "2018-01-05")
        self.assertEqual(summary["extended_calendar_end"], "2025-12-31")

    def test_public_profile_does_not_leak_values(self):
        rows = csv_rows("column_profile.csv")
        self.assertTrue(rows)
        self.assertTrue(all(r["example"] == "[REDACTED]" for r in rows))
    def test_unresolved_kpis_remain_blocked(self):
        rows = {r["issue"]: r for r in csv_rows("review_status.csv")}
        self.assertEqual(rows["DIMDATE_COVERAGE"]["resolution_status"],
                         "DERIVED_CALENDAR_CREATED")
        self.assertEqual(rows["SALARY_BUDGET"]["resolution_status"],
                         "BLOCKED_UNVERIFIED")
        self.assertEqual(rows["TRANSFER_EVENTS"]["resolution_status"],
                         "UNSUPPORTED_BY_SOURCE")
        summary = json.loads((REPORT / "review_summary.json").read_text())
        self.assertEqual(summary["june_restructuring_departments"],
                         summary["july_plan_reset_departments"])
        self.assertFalse(summary["salary_budget_unit_verified"])


if __name__ == "__main__":
    unittest.main()
