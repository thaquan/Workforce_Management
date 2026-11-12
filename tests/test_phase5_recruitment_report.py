"""Page05 recruitment operations visual and semantic safety acceptance tests."""
import json
import unittest

from src.phase5.build_recruitment_report import PAGE, PAGE_ID, PAGES
from src.phase5.build_executive_report import make_id
from src.phase5.build_model import MEASURES, TABLES


class RecruitmentReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = json.loads((PAGE / "page.json").read_text(encoding="utf-8"))
        cls.index = json.loads((PAGES / "pages.json").read_text(encoding="utf-8"))
        cls.visuals = {
            obj["name"]: obj
            for p in (PAGE / "visuals").glob("*/visual.json")
            for obj in [json.loads(p.read_text(encoding="utf-8"))]
        }

    def visual(self, label):
        return self.visuals[make_id(label)]

    def test_page_order_and_common_shell(self):
        expected = [
            "e2eaca09131b49558568", "b79c0259a8f046bca574",
            "c8d37ab121f64a1bb2ef", "dfa28b11977c461b8973", PAGE_ID,
        ]
        self.assertEqual(self.index["pageOrder"][:5], expected)
        self.assertEqual(self.page["displayName"], "05 Recruitment Performance")
        self.assertEqual(self.page["name"], PAGE_ID)
        self.assertEqual((self.page["width"], self.page["height"]), (1280, 720))
        rail = self.visual("recruitment_sidebar")["position"]
        self.assertEqual(tuple(rail[k] for k in ("x", "y", "width", "height")),
                         (0, 0, 276, 720))
        for label, x, text in (
            ("recruitment Year", 857, "'Year'"),
            ("recruitment Department", 1010, "'Department'"),
        ):
            v = self.visual(label)
            self.assertEqual(v["position"]["x"], x)
            self.assertEqual(
                v["visual"]["objects"]["header"][0]["properties"]
                 ["text"]["expr"]["Literal"]["Value"], text)

    def test_visual_families_and_bounds(self):
        self.assertEqual(len(self.visuals), 33)
        categories = [v["visual"]["visualType"] for v in self.visuals.values()]
        for visual_type, amount in (
            ("cardVisual", 5), ("slicer", 2), ("stackedAreaChart", 1),
            ("scatterChart", 1), ("clusteredBarChart", 1),
            ("hundredPercentStackedBarChart", 1),
        ):
            self.assertEqual(categories.count(visual_type), amount)
        self.assertNotIn("pivotTable", categories)
        self.assertNotIn("waterfallChart", categories)
        self.assertEqual(len(self.visuals), len(set(self.visuals)))
        for v in self.visuals.values():
            p = v["position"]
            self.assertGreaterEqual(p["x"], 0)
            self.assertGreaterEqual(p["y"], 0)
            self.assertLessEqual(p["x"] + p["width"], 1280)
            self.assertLessEqual(p["y"] + p["height"], 720)

    def test_all_chart_bindings_in_existing_semantic_model(self):
        allowed = {m["name"] for m in MEASURES}
        for v in self.visuals.values():
            for role in v["visual"].get("query", {}).get("queryState", {}).values():
                for p in role["projections"]:
                    kind, expression = next(iter(p["field"].items()))
                    table = expression["Expression"]["SourceRef"]["Entity"]
                    field = expression["Property"]
                    if kind == "Measure":
                        self.assertEqual(table, "_Measures")
                        self.assertIn(field, allowed)
                    else:
                        self.assertEqual(kind, "Column")
                        self.assertIn(field, TABLES[table][1])

    def test_distinguishes_stock_and_flow(self):
        area = self.visual("recruitment_monthly_closed_area")["visual"]["query"]["queryState"]
        self.assertEqual(area["Category"]["projections"][0]["queryRef"],
                         "Dim Month.month")
        self.assertEqual({p["nativeQueryRef"] for p in area["Y"]["projections"]},
                         {"Filled Requisitions", "Cancelled Requisitions"})
        self.assertNotIn("Ending Open Requisitions",
                         {p["nativeQueryRef"] for p in area["Y"]["projections"]})
        backlog = self.visual("recruitment_open_backlog")["visual"]["query"]["queryState"]
        self.assertEqual(backlog["Category"]["projections"][0]["queryRef"],
                         "Dim Department.department")
        self.assertEqual(backlog["Y"]["projections"][0]["nativeQueryRef"],
                         "Ending Open Requisitions")

    def test_speed_scatter_and_closed_outcome_mix(self):
        scatter = self.visual("recruitment_dept_speed_bubbles")["visual"]["query"]["queryState"]
        for axis, field in (("X", "Weighted Days to Fill"),
                            ("Y", "Filled Requisitions"),
                            ("Size", "Ending Open Requisitions")):
            self.assertEqual(scatter[axis]["projections"][0]["nativeQueryRef"], field)
        self.assertEqual(scatter["Category"]["projections"][0]["queryRef"],
                         "Dim Department.department")
        mix = self.visual("recruitment_department_closeout_mix")["visual"]["query"]["queryState"]
        self.assertEqual({p["nativeQueryRef"] for p in mix["Y"]["projections"]},
                         {"Filled Requisitions", "Cancelled Requisitions"})

    def test_sidebar_and_interpretation_caveats(self):
        cards = [v for v in self.visuals.values()
                 if v["visual"]["visualType"] == "cardVisual"]
        self.assertEqual({p["nativeQueryRef"] for v in cards
                          for p in v["visual"]["query"]["queryState"]["Data"]["projections"]},
                         {"Ending Open Requisitions", "Filled Requisitions",
                          "Cancelled Requisitions", "Weighted Days to Fill",
                          "Fill Share of Closed Requisitions"})
        content = json.dumps(self.visuals).lower()
        self.assertIn("not candidate funnel stages", content)
        self.assertIn("bubble size = ending open vacancies", content)
        for forbidden in ("employee_id", "personal_email", "annual_salary_eur",
                          "postgres_password", "password=", "data/raw"):
            self.assertNotIn(forbidden, content)


if __name__ == "__main__":
    unittest.main()
