"""Static contract tests for the credential-free semantic model."""
import json
import re
import unittest
from src.phase5.build_model import MODEL, TABLES, MEASURES, build


class Phase5ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build()
        cls.model = json.loads((MODEL / "model.bim").read_text(encoding="utf-8"))["model"]
        cls.tables = {t["name"]:t for t in cls.model["tables"]}

    def test_measure_count_and_unique_names(self):
        self.assertEqual(len(MEASURES), 51)
        self.assertEqual(len({m["name"] for m in MEASURES}), 51)
        self.assertEqual(len(self.tables["_Measures"]["measures"]), 51)

    def test_all_measure_column_references_exist(self):
        for measure in MEASURES:
            for table,column in re.findall(r"'([^']+)'\[([^\]]+)\]", measure["expression"]):
                self.assertIn(table,self.tables,measure["name"])
                self.assertIn(column,{c["name"] for c in self.tables[table]["columns"]},measure["name"])

    def test_unqualified_measure_references_resolve(self):
        names = {m["name"] for m in MEASURES}
        for measure in MEASURES:
            expression = re.sub(r"'[^']+'\[[^\]]+\]", "", measure["expression"])
            for name in re.findall(r"\[([^\]]+)\]",expression):
                self.assertIn(name,names,measure["name"])

    def test_relationships_resolve_and_are_single_direction(self):
        relationships = self.model["relationships"]
        self.assertEqual(len(relationships),13)
        for r in relationships:
            for side in ("from","to"):
                self.assertIn(r[side+"Column"],{c["name"] for c in self.tables[r[side+"Table"]]["columns"]})
            self.assertEqual(r["crossFilteringBehavior"],"oneDirection")

    def test_no_raw_person_identifiers_or_credentials(self):
        for t in self.model["tables"]:
            self.assertNotIn("employee_id",{c["name"] for c in t["columns"]})
        serialized = json.dumps(self.model).lower()
        self.assertNotIn("postgres_password",serialized)
        self.assertNotIn("password=",serialized)
        self.assertNotIn("budgeted_salary_cost",serialized)
        self.assertNotIn("annual_salary",serialized)

    def test_stock_scope_and_temporal_guards(self):
        measures = {m["name"]:m["expression"] for m in MEASURES}
        for name in ("Ending Headcount","Ending FTE","Planned Headcount","Ending Open Requisitions"):
            self.assertIn("KEEPFILTERS",measures[name])
            self.assertIn("MAX ( 'Dim Month'[month] )",measures[name])
        self.assertIn("HASONEVALUE",measures["Monthly Average Headcount"])
        self.assertIn("COUNTROWS ( ValidMonths ) = N",measures["Period Attrition %"])
        self.assertIn("COUNTROWS ( WindowMonths ) = 12",measures["Rolling 12M Attrition %"])
        self.assertIn("ISCROSSFILTERED ( 'Dim Location' )",measures["Planned Headcount"])
        self.assertIn("CheckCount > 0",measures["Latest Quality FAIL"])

    def test_sources_use_only_documented_marts_and_audit(self):
        self.assertEqual(len(TABLES),12)
        for query,columns in TABLES.values():
            self.assertNotRegex(query,r"(?i)\braw\.")
            self.assertTrue(columns)

if __name__ == "__main__":
    unittest.main()
