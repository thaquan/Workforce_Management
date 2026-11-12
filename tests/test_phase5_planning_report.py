"""Validate Page 02 PBIR bindings/layout without opening private HR data."""
import json
import unittest

from src.phase5.build_model import MEASURES, TABLES
from src.phase5.build_planning_report import PAGE, PAGE_ID, PAGES


class PlanningReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = json.loads((PAGE / "page.json").read_text(encoding="utf-8"))
        cls.metadata = json.loads((PAGES / "pages.json").read_text(encoding="utf-8"))
        cls.visuals = [
            json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((PAGE / "visuals").glob("*/visual.json"))
        ]

    def test_page_order_keeps_executive(self):
        self.assertEqual(self.page["name"], PAGE_ID)
        self.assertEqual(self.page["displayName"], "02 Workforce Planning")
        self.assertEqual((self.page["width"], self.page["height"]), (1280, 720))
        self.assertEqual(self.metadata["pageOrder"][:2], [
            "e2eaca09131b49558568", PAGE_ID,
        ])
        self.assertIn(self.metadata["activePageName"], self.metadata["pageOrder"])

    def test_visual_count_and_required_native_types(self):
        self.assertEqual(len(self.visuals), 27)
        types = [v["visual"]["visualType"] for v in self.visuals]
        for kind, expected in {
            "cardVisual": 3,
            "slicer": 2,
            "gauge": 1,
            "waterfallChart": 1,
            "treemap": 1,
            "clusteredColumnChart": 1,
        }.items():
            self.assertEqual(types.count(kind), expected)
        for inherited_kind in ("lineChart", "clusteredBarChart", "pivotTable"):
            self.assertNotIn(inherited_kind, types)

    def test_layout_within_canvas_and_unique_ids(self):
        ids = [v["name"] for v in self.visuals]
        self.assertEqual(len(ids), len(set(ids)))
        for visual in self.visuals:
            p = visual["position"]
            self.assertGreaterEqual(p["x"], 0)
            self.assertGreaterEqual(p["y"], 0)
            self.assertLessEqual(p["x"] + p["width"], 1280)
            self.assertLessEqual(p["y"] + p["height"], 720)

    def test_bindings_reference_existing_measures_and_dimensions(self):
        measures = {m["name"] for m in MEASURES}
        for visual in self.visuals:
            roles = visual["visual"].get("query", {}).get("queryState", {})
            for group in roles.values():
                for projection in group["projections"]:
                    kind, field = next(iter(projection["field"].items()))
                    table = field["Expression"]["SourceRef"]["Entity"]
                    column = field["Property"]
                    if kind == "Measure":
                        self.assertEqual(table, "_Measures")
                        self.assertIn(column, measures)
                    elif kind == "Column":
                        self.assertIn(column, TABLES[table][1])
                    else:
                        self.fail(f"Unsupported projection kind: {kind}")

    def test_kpis_gauge_and_department_slicers(self):
        cards = [v for v in self.visuals if v["visual"]["visualType"] == "cardVisual"]
        all_metrics = {
            p["nativeQueryRef"]
            for card in cards
            for p in card["visual"]["query"]["queryState"]["Data"]["projections"]
        }
        self.assertEqual(all_metrics, {
            "Planned Headcount", "Headcount Gap", "FTE Gap",
        })
        gauges = [v for v in self.visuals if v["visual"]["visualType"] == "gauge"]
        self.assertEqual(gauges[0]["visual"]["query"]["queryState"]["Y"]["projections"][0]["nativeQueryRef"],
                         "Headcount Attainment %")
        self.assertEqual(gauges[0]["visual"]["objects"]["axis"][0]["properties"]["target"]["expr"]["Literal"]["Value"], "1D")
        self.assertEqual(gauges[0]["visual"]["objects"]["axis"][0]["properties"]["max"]["expr"]["Literal"]["Value"], "1.25D")
        self.assertEqual({v["visual"]["query"]["queryState"]["Values"]["projections"][0]["queryRef"]
                          for v in self.visuals if v["visual"]["visualType"] == "slicer"},
                         {"Dim Month.year", "Dim Department.department"})

    def test_each_analytics_visual_answers_a_distinct_question(self):
        waterfall = next(v for v in self.visuals if v["visual"]["visualType"] == "waterfallChart")
        treemap = next(v for v in self.visuals if v["visual"]["visualType"] == "treemap")
        compare = next(v for v in self.visuals if v["visual"]["visualType"] == "clusteredColumnChart")
        wf = waterfall["visual"]["query"]["queryState"]
        tm = treemap["visual"]["query"]["queryState"]
        cc = compare["visual"]["query"]["queryState"]
        self.assertEqual(wf["Y"]["projections"][0]["nativeQueryRef"], "Headcount Gap")
        self.assertEqual(tm["Values"]["projections"][0]["nativeQueryRef"], "Planned Headcount")
        self.assertEqual({x["nativeQueryRef"] for x in cc["Y"]["projections"]},
                         {"Planning Actual Headcount", "Planned Headcount"})

    def test_planning_has_distinct_composition_from_executive_overview(self):
        from src.phase5.build_executive_report import PAGE as executive_page
        executive = [json.loads(p.read_text(encoding="utf-8"))
                     for p in (executive_page / "visuals").glob("*/visual.json")]
        old_types = {v["visual"]["visualType"] for v in executive}
        new_types = {v["visual"]["visualType"] for v in self.visuals}
        self.assertTrue({"waterfallChart", "treemap", "gauge", "clusteredColumnChart"} <= new_types)
        self.assertTrue({"lineChart", "clusteredBarChart", "pivotTable"} <= old_types)
        self.assertFalse({"lineChart", "clusteredBarChart", "pivotTable"} & new_types)

    def test_no_fake_location_plan_or_private_rows(self):
        serialized = json.dumps(self.visuals).lower()
        for forbidden in (
            "dim location", "dim level", "employee_id", "salary_budget_variance",
            "postgres_password", "data/raw", "email_address",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertIn("JUL 2025", serialized.upper())


if __name__ == "__main__":
    unittest.main()
