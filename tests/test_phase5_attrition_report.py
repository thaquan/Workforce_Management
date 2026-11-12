"""Static quality gates for Page 03 Attrition Analysis PBIR visual contracts."""
import json
import unittest

from src.phase5.build_attrition_report import PAGE, PAGE_ID, PAGES
from src.phase5.build_executive_report import make_id
from src.phase5.build_model import TABLES, MEASURES


class AttritionReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = json.loads((PAGE / "page.json").read_text(encoding="utf-8"))
        cls.pages = json.loads((PAGES / "pages.json").read_text(encoding="utf-8"))
        cls.visuals = {
            obj["name"]: obj
            for path in (PAGE / "visuals").glob("*/visual.json")
            for obj in [json.loads(path.read_text(encoding="utf-8"))]
        }

    def get(self, name):
        return self.visuals[make_id(name)]

    def test_pages_and_design_identity(self):
        self.assertEqual(self.pages["pageOrder"][:3], [
            "e2eaca09131b49558568", "b79c0259a8f046bca574", PAGE_ID,
        ])
        self.assertIn(self.pages["activePageName"], self.pages["pageOrder"])
        self.assertEqual(self.page["displayName"], "03 Attrition Analysis")
        self.assertEqual((self.page["width"], self.page["height"]), (1280, 720))
        rail = self.get("attrition_sidebar")["position"]
        self.assertEqual((rail["x"], rail["y"], rail["width"], rail["height"]),
                         (0, 0, 276, 720))
        for name, x, label in (
            ("attrition Year", 857, "'Year'"),
            ("attrition Department", 1010, "'Department'"),
        ):
            v = self.get(name)
            self.assertEqual(v["position"]["x"], x)
            self.assertEqual(
                v["visual"]["objects"]["header"][0]["properties"]
                ["text"]["expr"]["Literal"]["Value"], label)

    def test_native_visuals_and_canvas_bounds(self):
        self.assertEqual(len(self.visuals), 30)
        types = [v["visual"]["visualType"] for v in self.visuals.values()]
        for name, count in (
            ("cardVisual", 5), ("slicer", 2), ("pivotTable", 1),
            ("clusteredColumnChart", 1), ("hundredPercentStackedBarChart", 1),
        ):
            self.assertEqual(types.count(name), count, name)
        self.assertNotIn("waterfallChart", types)
        self.assertNotIn("lineChart", types)
        for v in self.visuals.values():
            p = v["position"]
            self.assertGreaterEqual(p["x"], 0)
            self.assertGreaterEqual(p["y"], 0)
            self.assertLessEqual(p["x"] + p["width"], 1280)
            self.assertLessEqual(p["y"] + p["height"], 720)

    def test_all_visual_bindings_are_in_the_semantic_model(self):
        measures = {m["name"] for m in MEASURES}
        for v in self.visuals.values():
            groups = v["visual"].get("query", {}).get("queryState", {})
            for group in groups.values():
                for p in group["projections"]:
                    kind, info = next(iter(p["field"].items()))
                    table = info["Expression"]["SourceRef"]["Entity"]
                    name = info["Property"]
                    if kind == "Measure":
                        self.assertEqual(table, "_Measures")
                        self.assertIn(name, measures)
                    else:
                        self.assertEqual(kind, "Column")
                        self.assertIn(name, TABLES[table][1])

    def test_heatmap_has_correct_grain_and_rate_rules(self):
        matrix = self.get("attrition_month_department_heatmap")["visual"]
        self.assertEqual(matrix["query"]["queryState"]["Rows"]["projections"][0]
                         ["queryRef"], "Dim Department.department")
        self.assertEqual(matrix["query"]["queryState"]["Columns"]["projections"][0]
                         ["queryRef"], "Dim Month.year_month")
        self.assertEqual(matrix["query"]["queryState"]["Values"]["projections"][0]
                         ["queryRef"], "_Measures.Monthly Attrition %")
        entry = matrix["objects"]["values"][0]
        self.assertEqual(entry["selector"]["metadata"], "_Measures.Monthly Attrition %")
        conditional = entry["properties"]["backColor"]["solid"]["color"]["expr"]["Conditional"]
        cases = conditional["Cases"]
        self.assertEqual([c["Condition"]["Comparison"]["Right"]["Literal"]["Value"]
                          for c in cases], ["0.08D", "0.02D", "0D"])
        self.assertEqual([c["Value"]["Literal"]["Value"] for c in cases],
                         ["'#F7A99B'", "'#FDE6A5'", "'#DDF3F0'"])
        self.assertEqual(conditional["DefaultValue"]["Literal"]["Value"], "'#FFFFFF'")
        self.assertEqual(self.get("attrition_color_legend")["visual"]["visualType"], "textbox")

    def test_event_charts_have_distinct_business_meaning(self):
        flow = self.get("attrition_monthly_flow_columns")["visual"]["query"]["queryState"]
        mix = self.get("attrition_exit_type_composition")["visual"]["query"]["queryState"]
        self.assertEqual({p["nativeQueryRef"] for p in flow["Y"]["projections"]},
                         {"Hires", "Terminations"})
        self.assertEqual({p["nativeQueryRef"] for p in mix["Y"]["projections"]},
                         {"Voluntary Terminations", "Involuntary Terminations"})
        self.assertEqual(mix["Category"]["projections"][0]["queryRef"],
                         "Dim Department.department")

    def test_quality_and_privacy_guardrails(self):
        text = json.dumps(self.visuals).lower()
        for required in ("33/36", "jan 2023", "provisional"):
            self.assertIn(required, text)
        for forbidden in ("employee_id", "annual_salary_eur", "postgres_password",
                          "password=", "data/raw", "personal_email"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
