"""Offline contract tests; no PostgreSQL server is required."""
import unittest
from datetime import date
from decimal import Decimal

from src.phase2.quality import SourceValidationError, normalize_and_validate
from src.phase2.schema_contract import (
    BUSINESS_KEYS, SHEET_COLUMNS, coerce_value, snake_case, sql_type
)


class Phase2ContractTests(unittest.TestCase):
    def test_twelve_explicit_sheet_contracts(self):
        self.assertEqual(len(SHEET_COLUMNS), 12)
        self.assertEqual(set(SHEET_COLUMNS), set(BUSINESS_KEYS))
        self.assertEqual(len(SHEET_COLUMNS["DimEmployee"]), 19)
        self.assertEqual(len(SHEET_COLUMNS["FactMonthlySnapshot"]), 9)

    def test_snake_case_and_types(self):
        self.assertEqual(snake_case("FactMonthlySnapshot"), "fact_monthly_snapshot")
        self.assertEqual(snake_case("EmployeeID"), "employee_id")
        self.assertEqual(snake_case("ResponseRatePct"), "response_rate_pct")
        self.assertEqual(sql_type("Month"), "DATE")
        self.assertEqual(sql_type("AnnualSalary"), "NUMERIC(20,6)")
        self.assertEqual(sql_type("Headcount"), "INTEGER")
        self.assertEqual(sql_type("ManagerID"), "TEXT")

    def test_excel_serial_date(self):
        self.assertEqual(coerce_value("HireDate", 43105), date(2018, 1, 5))
        self.assertIsNone(coerce_value("TerminationDate", None))
        self.assertEqual(coerce_value("FTE", 0.8), Decimal("0.8"))

    def test_reject_invalid_value_without_echoing_data(self):
        with self.assertRaises(ValueError):
            coerce_value("Headcount", 1.5)
        with self.assertRaises(ValueError):
            coerce_value("HireDate", "2023-01-01")
        with self.assertRaises(ValueError):
            coerce_value("FTE", float("nan"))

    def test_incomplete_workbook_fails_closed(self):
        with self.assertRaisesRegex(SourceValidationError, "Wrong worksheet set"):
            normalize_and_validate({"DimEmployee": []})


if __name__ == "__main__":
    unittest.main()
