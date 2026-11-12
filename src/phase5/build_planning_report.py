"""Add Phase 5 Page 02 Workforce Planning without changing the semantic model.

Safe-to-run-once PBIR authoring: refuses to overwrite existing Page 02 or
change an Executive Overview page. Run only after Desktop saves changes.
"""
import json
from pathlib import Path

from src.phase5.build_executive_report import (
    REPORT, DEFINITION, PALETTE, load, save, lid, color,
    shape, textbox, card, chart, matrix, slicer, bind, container,
    measure, dimension, make_id,
)

PAGE_ID = "b79c0259a8f046bca574"
PAGES = DEFINITION / "pages"
PAGE = PAGES / PAGE_ID
CANVAS = (1280, 720)


def planning_matrix(label, x, y, w, h):
    return bind(container(label, "pivotTable", x, y, w, h, z=2100, objects={
        "columnHeaders": [{
            "properties": {
                "columnAdjustment": lid("'growToFit'"),
                "autoSizeColumnWidth": lid("true"),
            }
        }],
    }, chrome={
        "background": [{"properties": {"show": lid("true"), "color": color(PALETTE["white"])}}],
        "border": [{"properties": {"show": lid("false")}}],
    }), {
        "Rows": [dimension("Dim Department", "department")],
        "Values": [measure(m) for m in (
            "Planning Actual Headcount", "Planned Headcount", "Headcount Gap",
            "Headcount Attainment %", "FTE Gap",
        )],
    })


def build():
    if PAGE.exists():
        raise RuntimeError("Page 02 exists; refusing to overwrite user edits")
    metadata = PAGES / "pages.json"
    pages = load(metadata)
    expected_first = "e2eaca09131b49558568"
    first = PAGES / expected_first / "page.json"
    if not first.exists() or load(first)["displayName"] != "01 Executive Overview":
        raise RuntimeError("Verified Executive Overview page not found")
    if pages["pageOrder"] != [expected_first]:
        raise RuntimeError("Unexpected page order; refusing to change existing pages")

    visuals = [
        shape("plan_header", 0, 0, 1280, 82, PALETTE["navy"]),
        shape("plan_header_accent", 0, 79, 1280, 3, PALETTE["teal"], z=30),
        textbox("plan_brand", "WORKFORCE INTELLIGENCE  /  HR ANALYTICS",
                24, 12, 710, 23, 12, "#9FB3C8", bold=True),
        textbox("plan_title", "Workforce Planning",
                24, 34, 680, 44, 26, PALETTE["white"], bold=True),
        textbox("plan_header_note", "ACTUAL VS PLAN  ·  MONTH × DEPARTMENT",
                844, 47, 412, 23, 12, "#C3D5E2"),
        textbox("plan_filter_label", "PLAN GAPS  /  SELECT YEAR OR DEPARTMENT",
                23, 111, 650, 25, 12, PALETTE["subtle"]),
        textbox("plan_reset_context",
                "SOURCE HISTORY: JUL 2025 TARGET RESET IN SALES, MARKETING, OPS & CUSTOMER SUCCESS",
                23, 139, 746, 23, 10, PALETTE["orange"]),
        slicer("Planning Year", "Dim Month", "year", 786, 86, 188),
        slicer("Planning Department", "Dim Department", "department", 982, 86, 276),
        shape("plan_main_metrics_back", 20, 174, 1240, 84, PALETTE["white"], z=30),
        card("plan_main_metrics", [
            "Planning Actual Headcount", "Planned Headcount",
            "Headcount Gap", "Headcount Attainment %",
        ], 20, 174, 1240),
        textbox("plan_trend_heading", "Workforce plan trajectory  /  Actual vs target",
                22, 266, 735, 27, 16, PALETTE["navy"], bold=True),
        textbox("plan_gap_heading", "Department headcount gaps",
                789, 266, 474, 27, 16, PALETTE["navy"], bold=True),
        shape("plan_trend_back", 20, 298, 750, 194, PALETTE["white"], z=30),
        shape("plan_gap_back", 788, 298, 472, 194, PALETTE["white"], z=30),
        chart("plan_actual_vs_target", "lineChart", 24, 301, 742, 187,
              dimension("Dim Month", "month"),
              ["Planning Actual Headcount", "Planned Headcount"]),
        chart("plan_department_gap", "clusteredBarChart", 794, 301, 460, 187,
              dimension("Dim Department", "department"), ["Headcount Gap"]),
        textbox("plan_scorecard_header", "Planning scorecard  /  Department detail",
                22, 501, 770, 27, 16, PALETTE["navy"], bold=True),
        textbox("plan_fte_header", "FTE  /  Capacity vs budget",
                911, 501, 335, 27, 15, PALETTE["teal"], bold=True),
        shape("plan_scorecard_back", 20, 532, 870, 170, PALETTE["white"], z=30),
        shape("plan_fte_back", 907, 532, 353, 170, PALETTE["white"], z=30),
        planning_matrix("plan_department_scorecard", 24, 535, 862, 163),
        card("plan_actual_fte", ["Planning Actual FTE"], 911, 536, 169),
        card("plan_budgeted_fte", ["Budgeted FTE"], 1086, 536, 169),
        card("plan_fte_gap", ["FTE Gap"], 911, 617, 345),
    ]

    page = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": PAGE_ID,
        "displayName": "02 Workforce Planning",
        "displayOption": "FitToPage",
        "height": CANVAS[1], "width": CANVAS[0],
        "objects": {
            "background": [{"properties": {
                "color": color(PALETTE["canvas"]),
                "transparency": lid("0D"),
            }}],
        },
    }

    # Write both new page and page index only after preflight checks.
    save(PAGE / "page.json", page)
    for v in visuals:
        save(PAGE / "visuals" / v["name"] / "visual.json", v)
    pages["pageOrder"] = [expected_first, PAGE_ID]
    pages["activePageName"] = PAGE_ID
    save(metadata, pages)
    print(f"Created 02 Workforce Planning with {len(visuals)} PBIR visuals")
    print("The Executive Overview and semantic model are unchanged.")


if __name__ == "__main__":
    build()
