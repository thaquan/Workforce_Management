"""Offline PBIR contract tests, independent of Power BI Desktop or HR records."""
import json
import unittest

from src.phase5.build_executive_report import DEFINITION, PAGE, PAGE_ID, REPORT
from src.phase5.build_model import MEASURES, TABLES


class Phase5ExecutiveReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = json.loads((PAGE / "page.json").read_text(encoding="utf-8"))
        cls.visuals = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((PAGE / "visuals").glob("*/visual.json"))
        ]
        cls.report = json.loads((DEFINITION / "report.json").read_text(encoding="utf-8"))

    def test_expected_page_and_visual_count(self):
        self.assertEqual(self.page["displayName"], "01 Executive Overview")
        self.assertEqual(self.page["name"], PAGE_ID)
        self.assertEqual((self.page["width"], self.page["height"]), (1280, 720))
        self.assertEqual(len(self.visuals), 29)
        kinds = [v["visual"]["visualType"] for v in self.visuals]
        self.assertEqual(kinds.count("cardVisual"), 6)
        self.assertEqual(kinds.count("slicer"), 2)
        self.assertEqual(kinds.count("lineChart"), 1)
        self.assertEqual(kinds.count("clusteredBarChart"), 1)
        self.assertEqual(kinds.count("pivotTable"), 1)

    def test_unique_ids_and_canvas_bounds(self):
        self.assertEqual(len({v["name"] for v in self.visuals}), len(self.visuals))
        for v in self.visuals:
            pos = v["position"]
            self.assertGreaterEqual(pos["x"], 0)
            self.assertGreaterEqual(pos["y"], 0)
            self.assertLessEqual(pos["x"] + pos["width"], 1280)
            self.assertLessEqual(pos["y"] + pos["height"], 720)

    def test_all_query_projections_exist(self):
        measure_names = {m["name"] for m in MEASURES}
        for v in self.visuals:
            for role in v["visual"].get("query", {}).get("queryState", {}).values():
                for projection in role["projections"]:
                    kind, ref = next(iter(projection["field"].items()))
                    table = ref["Expression"]["SourceRef"]["Entity"]
                    name = ref["Property"]
                    if kind == "Measure":
                        self.assertEqual(table, "_Measures")
                        self.assertIn(name, measure_names)
                    else:
                        self.assertEqual(kind, "Column")
                        self.assertIn(name, TABLES[table][1])

    def test_stock_cards_and_trust_measures(self):
        cards = [
            v for v in self.visuals if v["visual"]["visualType"] == "cardVisual"
        ]
        metrics = {
            p["nativeQueryRef"]
            for v in cards
            for p in v["visual"]["query"]["queryState"]["Data"]["projections"]
        }
        self.assertEqual(metrics, {
            "Ending Headcount", "Planned Headcount", "Headcount Gap",
            "Ending FTE", "Reconciliation Review Months", "Latest Quality FAIL",
        })
        for v in cards:
            units = v["visual"]["objects"]["value"][0]["properties"]["labelDisplayUnits"]
            self.assertEqual(units["expr"]["Literal"]["Value"], "1D")

    def test_common_brand_shell_but_distinct_analytical_layout(self):
        from src.phase5.build_executive_report import make_id
        from src.phase5.build_planning_report import PAGE as planning_page

        planning = [json.loads(p.read_text(encoding="utf-8"))
                    for p in (planning_page / "visuals").glob("*/visual.json")]
        overview = {v["name"]: v for v in self.visuals}
        decision = {v["name"]: v for v in planning}
        left = overview[make_id("overview_sidebar")]["position"]
        right = decision[make_id("decision_sidebar")]["position"]
        for key in ("x", "y", "width", "height"):
            self.assertEqual(left[key], right[key])
        self.assertEqual(left["width"], 276)
        self.assertEqual(left["height"], 720)

        for page, names in ((overview, ("overview Year", "overview Department")),
                            (decision, ("Decision Year", "Decision Department"))):
            for label, expected_header, xpos in zip(names, ("'Year'", "'Department'"),
                                                     (857, 1010)):
                v = page[make_id(label)]
                self.assertEqual(v["position"]["x"], xpos)
                self.assertEqual(v["visual"]["objects"]["header"][0]
                                 ["properties"]["text"]["expr"]["Literal"]["Value"],
                                 expected_header)

        overview_types = {v["visual"]["visualType"] for v in self.visuals}
        planning_types = {v["visual"]["visualType"] for v in planning}
        self.assertTrue({"lineChart", "clusteredBarChart", "pivotTable"} <= overview_types)
        self.assertTrue({"waterfallChart", "treemap", "gauge",
                         "clusteredColumnChart"} <= planning_types)
        self.assertNotIn("waterfallChart", overview_types)

    def test_no_sensitive_detail_or_external_data_source(self):
        report_text = json.dumps({
            "page": self.page, "visuals": self.visuals, "report": self.report,
        }).lower()
        for forbidden in (
            "employee_id", "annual_salary_eur", "postgres_password",
            "password=", "data/raw", "personal_email",
        ):
            self.assertNotIn(forbidden, report_text)
        self.assertEqual(
            self.report["themeCollection"]["customTheme"]["type"],
            "RegisteredResources",
        )
        theme_name = self.report["themeCollection"]["customTheme"]["name"]
        self.assertTrue(
            (REPORT / "StaticResources" / "RegisteredResources" / theme_name).exists()
        )


if __name__ == "__main__":
    unittest.main()
