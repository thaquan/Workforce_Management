"""PBIR contract and privacy tests for 06 Data Quality & Trust."""
import json
import unittest

from src.phase5.build_quality_report import PAGE, PAGE_ID, PAGES
from src.phase5.build_executive_report import make_id
from src.phase5.build_model import TABLES, MEASURES


class DataQualityReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = json.loads((PAGE / "page.json").read_text(encoding="utf-8"))
        cls.pages = json.loads((PAGES / "pages.json").read_text(encoding="utf-8"))
        cls.visuals = {
            v["name"]: v
            for p in (PAGE / "visuals").glob("*/visual.json")
            for v in [json.loads(p.read_text(encoding="utf-8"))]
        }

    def get(self, name):
        return self.visuals[make_id(name)]

    def test_all_six_pages_keep_order_and_identity(self):
        self.assertEqual(self.pages["pageOrder"], [
            "e2eaca09131b49558568", "b79c0259a8f046bca574",
            "c8d37ab121f64a1bb2ef", "dfa28b11977c461b8973",
            "e596cb074ac84ab2a1b9", PAGE_ID,
        ])
        self.assertEqual(self.pages["activePageName"], PAGE_ID)
        self.assertEqual(self.page["name"], PAGE_ID)
        self.assertEqual(self.page["displayName"], "06 Data Quality & Trust")
        self.assertEqual((self.page["width"], self.page["height"]), (1280, 720))

    def test_common_brand_but_company_scope_filters(self):
        p = self.get("trust_sidebar")["position"]
        self.assertEqual(tuple(p[x] for x in ("x", "y", "width", "height")),
                         (0, 0, 276, 720))
        self.assertNotIn(make_id("trust Department"), self.visuals)
        selectors = (
            ("trust Year", 857, "Dim Month.year", "'Year'"),
            ("trust Audit Run", 1010, "Pipeline Runs.pipeline_run_id", "'Audit Run'"),
        )
        for name, x, ref, header in selectors:
            v = self.get(name)
            self.assertEqual(v["position"]["x"], x)
            self.assertEqual(v["visual"]["query"]["queryState"]["Values"]
                             ["projections"][0]["queryRef"], ref)
            self.assertEqual(v["visual"]["objects"]["header"][0]
                             ["properties"]["text"]["expr"]["Literal"]["Value"], header)

    def test_visual_mix_and_canvas(self):
        self.assertEqual(len(self.visuals), 36)
        types = [v["visual"]["visualType"] for v in self.visuals.values()]
        for kind, count in (
            ("cardVisual", 7), ("tableEx", 2), ("lineChart", 1),
            ("slicer", 2), ("shape", 6), ("textbox", 18),
        ):
            self.assertEqual(types.count(kind), count, kind)
        self.assertNotIn("waterfallChart", types)
        self.assertNotIn("scatterChart", types)
        for v in self.visuals.values():
            pos = v["position"]
            self.assertGreaterEqual(pos["x"], 0)
            self.assertGreaterEqual(pos["y"], 0)
            self.assertLessEqual(pos["x"] + pos["width"], 1280)
            self.assertLessEqual(pos["y"] + pos["height"], 720)

    def test_dax_scope_for_current_kpis_and_reconciliation(self):
        expected = {
            "Latest Pipeline Run ID", "Latest Pipeline Status",
            "Latest Quality PASS", "Latest Quality REVIEW", "Latest Quality FAIL",
            "Reconciliation Review Months", "Snapshot Reconciliation Difference",
        }
        shown = {
            p["nativeQueryRef"]
            for v in self.visuals.values()
            if v["visual"]["visualType"] == "cardVisual"
            for p in v["visual"]["query"]["queryState"]["Data"]["projections"]
        }
        self.assertEqual(shown, expected)
        trend = self.get("trust_monthly_reconciliation")["visual"]["query"]["queryState"]
        self.assertEqual(trend["Category"]["projections"][0]["queryRef"],
                         "Dim Month.month")
        self.assertEqual(trend["Y"]["projections"][0]["nativeQueryRef"],
                         "Snapshot Reconciliation Difference")

    def test_latest_audits_first_and_review_issues_first(self):
        run = self.get("trust_pipeline_history_table")["visual"]
        qc = self.get("trust_quality_register_table")["visual"]
        self.assertEqual(
            [p["queryRef"] for p in run["query"]["queryState"]["Values"]["projections"]],
            ["Pipeline Runs.pipeline_run_id", "Pipeline Runs.status",
             "Pipeline Runs.finished_at"],
        )
        self.assertEqual(
            [p["queryRef"] for p in qc["query"]["queryState"]["Values"]["projections"]],
            ["Quality Results.pipeline_run_id", "Quality Results.check_id",
             "Quality Results.status", "Quality Results.affected_count"],
        )
        self.assertEqual([s["field"]["Column"]["Property"]
                          for s in run["query"]["sortDefinition"]["sort"]],
                         ["pipeline_run_id"])
        self.assertEqual([s["field"]["Column"]["Property"]
                          for s in qc["query"]["sortDefinition"]["sort"]],
                         ["pipeline_run_id", "affected_count"])
        for table in (run, qc):
            self.assertTrue(all(s["direction"] == "Descending"
                                for s in table["query"]["sortDefinition"]["sort"]))
            self.assertEqual(table["objects"]["columnHeaders"][0]["properties"]
                             ["autoSizeColumnWidth"]["expr"]["Literal"]["Value"], "false")

    def test_all_projection_fields_exist_in_the_model(self):
        defined = {m["name"] for m in MEASURES}
        for v in self.visuals.values():
            groups = v["visual"].get("query", {}).get("queryState", {})
            for details in groups.values():
                for item in details["projections"]:
                    kind, ref = next(iter(item["field"].items()))
                    table = ref["Expression"]["SourceRef"]["Entity"]
                    prop = ref["Property"]
                    if kind == "Measure":
                        self.assertEqual(table, "_Measures")
                        self.assertIn(prop, defined)
                    else:
                        self.assertEqual(kind, "Column")
                        self.assertIn(prop, TABLES[table][1])

    def test_monitoring_truth_and_privacy_caveats(self):
        source = json.dumps(self.visuals).lower()
        for required in (
            "pipeline execution is not proof", "33/36 historical months",
            "year filters reconciliation only", "latest kpi cards always show latest",
            "imported data", "company-only", "source mismatch is not silently repaired",
        ):
            self.assertIn(required, source)
        for disallowed in (
            "employee_id", "annual_salary_eur", "personal_email",
            "postgres_password", "password=", "data/raw",
        ):
            self.assertNotIn(disallowed, source)


if __name__ == "__main__":
    unittest.main()
