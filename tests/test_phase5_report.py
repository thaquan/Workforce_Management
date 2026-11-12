"""Validate the checked-in Power BI report structure (read-only PBIR)."""

import unittest

from src.phase5.report_validation import (
    EXPECTED_PAGES, PAGES, inspect_project, read_json,
)


class PowerBIReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = read_json(PAGES / "pages.json")
        cls.pages = {}
        for page_id in cls.index["pageOrder"]:
            path = PAGES / page_id
            name = read_json(path / "page.json")["displayName"]
            cls.pages[name] = [read_json(p) for p in (path / "visuals").glob("*/visual.json")]

    def test_report_source_is_valid_without_desktop(self):
        summary = inspect_project()
        self.assertEqual(summary["pages"], 6)
        self.assertEqual(summary["tables"], 13)
        self.assertEqual(summary["measures"], 51)
        self.assertEqual(summary["relationships"], 13)

    def test_all_six_report_pages_exist_in_expected_order(self):
        self.assertEqual(tuple(self.pages), EXPECTED_PAGES)

    def test_each_page_has_its_own_visual_design(self):
        kinds = {
            name: {v["visual"]["visualType"] for v in items}
            for name, items in self.pages.items()
        }
        self.assertIn("lineChart", kinds["01 Executive Overview"])
        self.assertTrue({"waterfallChart", "treemap", "gauge"} <= kinds["02 Workforce Planning"])
        self.assertIn("pivotTable", kinds["03 Attrition Analysis"])
        self.assertIn("scatterChart", kinds["04 Retention & Engagement"])
        self.assertIn("stackedAreaChart", kinds["05 Recruitment Performance"])
        self.assertIn("tableEx", kinds["06 Data Quality & Trust"])
        self.assertGreaterEqual(len(set(tuple(sorted(x)) for x in kinds.values())), 5)

    def test_slicers_reflect_supported_reporting_grains(self):
        def slicer_fields(name):
            fields = set()
            for visual in self.pages[name]:
                if visual["visual"]["visualType"] != "slicer":
                    continue
                for part in visual["visual"]["query"]["queryState"]["Values"]["projections"]:
                    fields.add(part["queryRef"])
            return fields

        self.assertEqual(slicer_fields("02 Workforce Planning"),
                         {"Dim Month.year", "Dim Department.department"})
        self.assertEqual(slicer_fields("04 Retention & Engagement"),
                         {"Dim Department.department"})
        self.assertEqual(slicer_fields("06 Data Quality & Trust"),
                         {"Dim Month.year", "Pipeline Runs.pipeline_run_id"})

    def test_source_quality_caveats_are_visible(self):
        for name, required in (
            ("03 Attrition Analysis", "33/36"),
            ("04 Retention & Engagement", "not causal"),
            ("05 Recruitment Performance", "not candidate funnel"),
            ("06 Data Quality & Trust", "33/36"),
        ):
            self.assertIn(required.lower(), str(self.pages[name]).lower(), name)


if __name__ == "__main__":
    unittest.main()
