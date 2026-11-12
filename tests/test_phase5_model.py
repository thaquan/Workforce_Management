"""Semantic-model contract checks with no Power BI Desktop dependency."""

import json
import re
import unittest

from src.phase5.report_validation import MODEL_FILE, read_json


class SemanticModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = read_json(MODEL_FILE)["model"]
        cls.tables = {table["name"]: table for table in cls.model["tables"]}
        cls.measures = {
            m["name"]: "\n".join(m["expression"]) if isinstance(m["expression"], list)
                       else m["expression"]
            for table in cls.tables.values()
            for m in table.get("measures", [])
        }

    def test_measure_catalog_and_table_count(self):
        self.assertEqual(len(self.tables), 13)
        self.assertEqual(len(self.measures), 51)
        self.assertEqual(len(self.tables["_Measures"]["measures"]), 51)

    def test_dax_references_resolve_to_known_model_columns_and_measures(self):
        for name, expr in self.measures.items():
            for table, column in re.findall(r"'([^']+)'\[([^\]]+)\]", expr):
                self.assertIn(table, self.tables, name)
                self.assertIn(column, {c["name"] for c in self.tables[table]["columns"]}, name)
            cleaned = re.sub(r"'[^']+'\[[^\]]+\]", "", expr)
            for measure in re.findall(r"\[([^\]]+)\]", cleaned):
                self.assertIn(measure, self.measures, name)

    def test_relationships_and_filter_direction(self):
        self.assertEqual(len(self.model["relationships"]), 13)
        for relationship in self.model["relationships"]:
            # One-direction is the tabular default when the property is absent.
            self.assertEqual(relationship.get("crossFilteringBehavior", "oneDirection"),
                             "oneDirection")
            for side in ("from", "to"):
                table = self.tables[relationship[side + "Table"]]
                self.assertIn(relationship[side + "Column"],
                              {col["name"] for col in table["columns"]})

    def test_metric_semantics_for_non_additive_and_unavailable_data(self):
        for name in ("Ending Headcount", "Ending FTE", "Planned Headcount",
                     "Ending Open Requisitions"):
            self.assertIn("KEEPFILTERS", self.measures[name])
            self.assertIn("MAX ( 'Dim Month'[month] )", self.measures[name])
        self.assertIn("COUNTROWS ( WindowMonths ) = 12",
                      self.measures["Rolling 12M Attrition %"])
        self.assertIn("HASONEVALUE", self.measures["Monthly Average Headcount"])
        self.assertIn("ISCROSSFILTERED ( 'Dim Location' )",
                      self.measures["Planned Headcount"])

    def test_no_sensitive_columns_or_embedded_credentials(self):
        for table in self.tables.values():
            self.assertNotIn("employee_id", {col["name"] for col in table["columns"]})
        serialized = json.dumps(self.model).lower()
        for forbidden in ("postgres_password", "password=", "personal_email",
                          "annual_salary_eur", "budgeted_salary_cost"):
            self.assertNotIn(forbidden, serialized)
        for table in self.tables.values():
            for part in table.get("partitions", []):
                self.assertEqual(part.get("mode"), "import")


if __name__ == "__main__":
    unittest.main()
