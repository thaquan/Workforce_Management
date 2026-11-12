"""Page04 PBIR tests: correct endpoint semantics, design and privacy."""
import json
import unittest

from src.phase5.build_retention_report import PAGE, PAGE_ID, PAGES
from src.phase5.build_executive_report import make_id
from src.phase5.build_model import TABLES, MEASURES


class RetentionReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = json.loads((PAGE / "page.json").read_text(encoding="utf-8"))
        cls.page_index = json.loads((PAGES / "pages.json").read_text(encoding="utf-8"))
        cls.visuals = {
            v["name"]: v
            for path in (PAGE / "visuals").glob("*/visual.json")
            for v in [json.loads(path.read_text(encoding="utf-8"))]
        }

    def get(self, name):
        return self.visuals[make_id(name)]

    def test_page_identity_and_common_shell(self):
        self.assertEqual(self.page["name"], PAGE_ID)
        self.assertEqual(self.page["displayName"], "04 Retention & Engagement")
        self.assertEqual((self.page["width"], self.page["height"]), (1280, 720))
        self.assertEqual(self.page_index["pageOrder"][:4], [
            "e2eaca09131b49558568", "b79c0259a8f046bca574",
            "c8d37ab121f64a1bb2ef", PAGE_ID,
        ])
        left = self.get("retention_sidebar")["position"]
        self.assertEqual(tuple(left[k] for k in ("x", "y", "width", "height")),
                         (0, 0, 276, 720))
        department = self.get("retention Department")
        self.assertEqual(department["position"]["x"], 1010)
        self.assertEqual(
            department["visual"]["query"]["queryState"]["Values"]["projections"][0]
            ["queryRef"], "Dim Department.department")

    def test_no_fake_year_slicer_for_endpoint_retention(self):
        self.assertNotIn(make_id("retention Year"), self.visuals)
        self.assertEqual(self.get("retention_endpoint_value")["visual"]["visualType"],
                         "textbox")
        text = json.dumps(self.visuals).lower()
        self.assertIn("31 dec 2025", text)
        self.assertIn("no monthly retention history", text)
        self.assertNotIn('"entity": "Dim Month"', text)

    def test_distinct_research_canvas_types_and_layout(self):
        self.assertEqual(len(self.visuals), 38)
        types = [v["visual"]["visualType"] for v in self.visuals.values()]
        self.assertEqual(types.count("scatterChart"), 1)
        self.assertEqual(types.count("clusteredColumnChart"), 1)
        self.assertEqual(types.count("hundredPercentStackedBarChart"), 1)
        self.assertEqual(types.count("cardVisual"), 5)
        self.assertEqual(types.count("slicer"), 1)
        self.assertNotIn("pivotTable", types)
        self.assertNotIn("waterfallChart", types)
        for v in self.visuals.values():
            p = v["position"]
            self.assertGreaterEqual(p["x"], 0)
            self.assertGreaterEqual(p["y"], 0)
            self.assertLessEqual(p["x"] + p["width"], 1280)
            self.assertLessEqual(p["y"] + p["height"], 720)

    def test_scatter_is_grouped_department_not_people(self):
        visual = self.get("retention_department_bubbles")["visual"]
        groups = visual["query"]["queryState"]
        self.assertEqual(groups["Category"]["projections"][0]["queryRef"],
                         "Dim Department.department")
        self.assertEqual(groups["X"]["projections"][0]["nativeQueryRef"],
                         "Average Engagement Score")
        self.assertEqual(groups["Y"]["projections"][0]["nativeQueryRef"],
                         "Average Performance Rating")
        self.assertEqual(groups["Size"]["projections"][0]["nativeQueryRef"],
                         "Observed Employees")
        self.assertNotIn("Series", groups)

    def test_cohort_comparison_and_population_shares(self):
        compare = self.get("retention_cohort_scores")["visual"]["query"]["queryState"]
        composition = self.get("retention_department_cohort_mix")["visual"]["query"]["queryState"]
        self.assertEqual(compare["Category"]["projections"][0]["queryRef"],
                         "Fact Retention.exited")
        self.assertEqual({p["nativeQueryRef"] for p in compare["Y"]["projections"]},
                         {"Average Engagement Score", "Average Performance Rating"})
        self.assertEqual({p["nativeQueryRef"] for p in composition["Y"]["projections"]},
                         {"Active Employees", "Exited Employees"})

    def test_all_bindings_are_model_defined_and_no_private_rows(self):
        measures = {m["name"] for m in MEASURES}
        for v in self.visuals.values():
            for group in v["visual"].get("query", {}).get("queryState", {}).values():
                for proj in group["projections"]:
                    kind, ref = next(iter(proj["field"].items()))
                    table = ref["Expression"]["SourceRef"]["Entity"]
                    col = ref["Property"]
                    if kind == "Measure":
                        self.assertEqual(table, "_Measures")
                        self.assertIn(col, measures)
                    else:
                        self.assertEqual(kind, "Column")
                        self.assertIn(col, TABLES[table][1])
        content = json.dumps(self.visuals).lower()
        for forbidden in ("employee_id", "annual_salary_eur", "postgres_password",
                          "password=", "personal_email", "data/raw"):
            self.assertNotIn(forbidden, content)
        for required in ("not causal", "department is current", "coverage"):
            self.assertIn(required, content)


if __name__ == "__main__":
    unittest.main()
