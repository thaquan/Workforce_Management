"""Bring Executive Overview into the shared report design system.

Page 01 retains its reporting purpose and analytics (trend, gap ranking,
department scorecard, quality monitoring) while adopting Page 02's
Navy left rail, consistent page numbering and shared filter placement.
This one-time conversion backs up the original page and never changes the
semantic model or the existing Page 02.
"""

from datetime import datetime
import shutil

from src.phase5.build_executive_report import (
    ROOT, PAGE, PALETTE, make_id, load, save, lid, color,
    shape, textbox, card, chart, matrix, dimension,
)
from src.phase5.report_shell import shared_frame


OLD_LABELS = (
    "navy_header", "teal_header_line", "brand_label", "page_title",
    "header_note", "filter_caption", "Year", "Department",
    "cards_back", "executive_kpis", "trend_heading", "dept_heading",
    "trend_back", "dept_back", "actual_plan_trend", "department_variance",
    "dept_matrix_header", "trust_heading", "scorecard_back", "trust_back",
    "department_matrix", "quality_review", "quality_fail", "quality_caveat",
)


def new_visuals():
    """An executive time-series composition inside the consistent shell."""
    items = shared_frame(
        1, "EXECUTIVE VIEW", ("EXECUTIVE", "OVERVIEW"),
        "Workforce at a glance", "HOW IS THE WORKFORCE EVOLVING?",
        "Monthly headcount, planning trend and departmental exceptions",
        "overview",
    )

    # KPI/quality rail: same hierarchy as Page 02, different measures.
    items += [
        textbox("overview_stock_label", "WORKFORCE METRICS", 20, 209,
                236, 21, 11, "#9FB3C8", bold=True),
        card("overview_hc_card", ["Ending Headcount"], 18, 239, 238),
        card("overview_plan_card", ["Planned Headcount"], 18, 326, 238),
        card("overview_gap_card", ["Headcount Gap"], 18, 413, 238),
        card("overview_fte_card", ["Ending FTE"], 18, 500, 238),
        textbox("overview_quality_label", "DATA QUALITY  /  TRUST", 20, 583,
                237, 21, 11, "#9FB3C8", bold=True),
        card("overview_review_card", ["Reconciliation Review Months"],
             18, 608, 115, label_alias="Review"),
        card("overview_fail_card", ["Latest Quality FAIL"],
             140, 608, 115, label_alias="Failures"),
        textbox("overview_quality_note", "Attrition remains provisional",
                20, 690, 236, 23, 10, "#F0B664"),

        # Unlike Page 02: a *dominant time-series*, followed by a ranked
        # horizontal comparison and a compact business scorecard.
        textbox("overview_trend_heading", "01   MONTHLY WORKFORCE TRAJECTORY",
                298, 112, 640, 29, 15, PALETTE["navy"], bold=True),
        shape("overview_trend_panel", 293, 144, 967, 284,
              PALETTE["white"], z=25),
        chart("overview_monthly_line", "lineChart", 298, 148, 957, 275,
              dimension("Dim Month", "month"),
              ["Ending Headcount", "Planned Headcount"]),

        textbox("overview_gap_heading", "02   DEPARTMENT HEADCOUNT VARIANCE",
                298, 448, 456, 27, 14, PALETTE["navy"], bold=True),
        textbox("overview_table_heading", "03   DEPARTMENT SCORECARD",
                755, 448, 505, 27, 14, PALETTE["navy"], bold=True),
        shape("overview_gap_panel", 293, 480, 445, 228,
              PALETTE["white"], z=25),
        shape("overview_table_panel", 749, 480, 511, 228,
              PALETTE["white"], z=25),
        chart("overview_gap_bar", "clusteredBarChart", 299, 484, 434, 219,
              dimension("Dim Department", "department"), ["Headcount Gap"]),
        overview_matrix("overview_department_matrix", 755, 484, 499, 219),
    ]
    return items


def overview_matrix(label, x, y, w, h):
    """Three headline dimensions fit a half-width panel without FTE scroll.

    FTE is already available as a sidebar KPI; a fourth numeric column in
    a 499 px matrix forced a horizontal scrollbar in the actual preview.
    """
    visual = matrix(label, x, y, w, h)
    projections = visual["visual"]["query"]["queryState"]["Values"]["projections"]
    visual["visual"]["query"]["queryState"]["Values"]["projections"] = [
        p for p in projections if p["nativeQueryRef"] != "Ending FTE"
    ]
    return visual


def redesign():
    page_info = load(PAGE / "page.json")
    if page_info["displayName"] != "01 Executive Overview":
        raise RuntimeError("Unexpected Page 01 identity; refusing to overwrite")
    visual_root = PAGE / "visuals"
    existing = {folder.name for folder in visual_root.iterdir() if folder.is_dir()}
    expected = {make_id(x) for x in OLD_LABELS}
    if existing != expected:
        raise RuntimeError("Page 01 has user changes; refusing unsafe redesign")
    visuals = new_visuals()
    if len({v["name"] for v in visuals}) != len(visuals):
        raise RuntimeError("Duplicate visual identifiers")

    backups = ROOT / "data" / "interim" / "phase5"
    backups.mkdir(parents=True, exist_ok=True)
    backup = backups / ("executive_page_v1_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copytree(PAGE, backup)
    # Replace Page 01 *only*; neither Page 02 nor semantic data is changed.
    shutil.rmtree(visual_root)
    visual_root.mkdir(parents=True)
    for visual in visuals:
        save(visual_root / visual["name"] / "visual.json", visual)
    print(f"Page 01 redesigned with {len(visuals)} visual elements")
    print("Backup:", backup)
    print("Page 02 and semantic model untouched")


if __name__ == "__main__":
    redesign()
