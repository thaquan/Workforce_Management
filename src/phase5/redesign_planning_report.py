"""Redesign Page 02 as a distinct Planning Decision Cockpit.

Safe local-only conversion of the original (known) Page 02 PBIR visuals.
The previous page is backed up in ignored data/interim before replacement.
This intentionally leaves Page 01, model, imported data and credentials alone.
"""
from datetime import datetime
from pathlib import Path
import shutil

from src.phase5.build_executive_report import (
    ROOT, PALETTE, load, save, lid, color, shape, textbox, card, slicer,
    container, bind, measure, dimension, make_id,
)
from src.phase5.build_planning_report import PAGE, PAGE_ID, PAGES
from src.phase5.report_shell import shared_filter


def waterfall(label, x, y, w, h):
    return bind(container(label, "waterfallChart", x, y, w, h, z=1600,
                          objects={
                              "sentimentColors": [{"properties": {
                                  "increaseFill": color(PALETTE["teal"]),
                                  "decreaseFill": color(PALETTE["red"]),
                                  "totalFill": color(PALETTE["navy"]),
                              }}],
                          }, chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Category": [dimension("Dim Department", "department")],
        "Y": [measure("Headcount Gap")],
        "Tooltips": [measure("Headcount Attainment %")],
    })


def target_gauge(label, x, y, w, h):
    return bind(container(label, "gauge", x, y, w, h, z=1600,
                          objects={
                              "calloutValue": [{"properties": {
                                  "labelDisplayUnits": lid("1D"),
                              }}],
                              # All 288 source dept-month ratios are <=1.203.
                              # Explicit 0–125% scale avoids the default
                              # 2×-headcount auto range, with goal at 100%.
                              "axis": [{"properties": {
                                  "min": lid("0D"),
                                  "max": lid("1.25D"),
                                  "target": lid("1D"),
                              }}],
                          }, chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Y": [measure("Headcount Attainment %")],
    })


def plan_treemap(label, x, y, w, h):
    return bind(container(label, "treemap", x, y, w, h, z=1600,
                          objects={
                              "categoryLabels": [{"properties": {
                                  "show": lid("true"),
                              }}],
                          }, chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Group": [dimension("Dim Department", "department")],
        "Values": [measure("Planned Headcount")],
        "Tooltips": [measure("Headcount Gap")],
    })


def comparison_columns(label, x, y, w, h):
    return bind(container(label, "clusteredColumnChart", x, y, w, h,
                          z=1600, objects={
                              "categoryAxis": [{"properties": {
                                  "fontSize": lid("9D"),
                              }}],
                          }, chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Category": [dimension("Dim Department", "department")],
        "Y": [measure("Planning Actual Headcount"),
              measure("Planned Headcount")],
    })


def visuals_v2():
    """Vertical strategy rail + distinct chart families (not Page 01 template)."""
    return [
        shape("decision_sidebar", 0, 0, 276, 720, PALETTE["navy"], z=10),
        shape("decision_rail_line", 273, 0, 3, 720, PALETTE["teal"], z=20),
        textbox("decision_brand", "WORKFORCE INTELLIGENCE", 20, 17, 240, 24,
                11, "#9FB3C8", bold=True),
        textbox("decision_chapter", "02 / 06  —  DECISION VIEW", 20, 54, 238,
                27, 13, "#52CBD1", bold=True),
        textbox("decision_title_a", "WORKFORCE", 20, 91, 245, 42,
                25, PALETTE["white"], bold=True),
        textbox("decision_title_b", "PLANNING", 20, 126, 245, 42,
                25, PALETTE["white"], bold=True),
        textbox("decision_subtitle", "Capacity & target allocation", 20, 180,
                237, 25, 12, "#C3D5E2"),
        textbox("decision_gap_label", "HEADCOUNT GAP", 20, 213, 238, 22,
                11, "#9FB3C8", bold=True),
        card("decision_gap_kpi", ["Headcount Gap"], 18, 236, 238),
        textbox("decision_gauge_label", "ATTAINMENT  /  100% GOAL", 20,
                323, 238, 25, 10, "#9FB3C8", bold=True),
        target_gauge("decision_target_gauge", 18, 350, 239, 143),
        card("decision_attainment_kpi", ["Planned Headcount"],
             18, 500, 238),
        card("decision_fte_gap_kpi", ["FTE Gap"], 18, 597, 238),

        textbox("decision_main_title", "WHERE IS THE PLAN OFF TRACK?", 294,
                25, 560, 38, 24, PALETTE["navy"], bold=True),
        textbox("decision_main_subtitle", "Workforce gaps, budgeted capacity and target allocation",
                296, 61, 550, 24, 12, PALETTE["subtle"]),
        textbox("decision_reset_context", "JUL 2025: four departments moved to a reset planning scenario",
                296, 84, 557, 21, 11, PALETTE["orange"]),
        shared_filter("Decision Year", "Year", "Dim Month", "year", 857, 145),
        shared_filter("Decision Department", "Department", "Dim Department",
                      "department", 1010, 251),

        textbox("decision_drivers_heading", "01   WHAT DRIVES THE HEADCOUNT GAP?",
                298, 111, 625, 27, 15, PALETTE["navy"], bold=True),
        textbox("decision_allocation_heading", "02   WHERE IS PLAN CAPACITY ALLOCATED?",
                937, 111, 329, 27, 13, PALETTE["navy"], bold=True),
        shape("decision_waterfall_panel", 293, 141, 627, 323,
              PALETTE["white"], z=25),
        shape("decision_treemap_panel", 934, 141, 326, 323,
              PALETTE["white"], z=25),
        waterfall("decision_waterfall", 298, 146, 617, 313),
        plan_treemap("decision_treemap", 939, 146, 316, 313),

        textbox("decision_comparison_heading", "03   ACTUAL VS PLANNED — DEPARTMENT COMPARISON",
                298, 480, 800, 30, 15, PALETTE["navy"], bold=True),
        shape("decision_columns_panel", 293, 516, 967, 192,
              PALETTE["white"], z=25),
        comparison_columns("decision_compare_columns", 298, 519, 957, 187),
    ]


def redesign():
    page_path = PAGE / "page.json"
    old = PAGE / "visuals"
    if not page_path.exists():
        raise RuntimeError("Page 02 does not exist")
    if load(page_path)["displayName"] != "02 Workforce Planning":
        raise RuntimeError("Page 02 has unexpected identity")
    old_names = {p.name for p in old.iterdir() if p.is_dir()}
    expected = {make_id(label) for label in [
        "plan_header", "plan_header_accent", "plan_brand", "plan_title",
        "plan_header_note", "plan_filter_label", "plan_reset_context",
        "Planning Year", "Planning Department", "plan_main_metrics_back",
        "plan_main_metrics", "plan_trend_heading", "plan_gap_heading",
        "plan_trend_back", "plan_gap_back", "plan_actual_vs_target",
        "plan_department_gap", "plan_scorecard_header", "plan_fte_header",
        "plan_scorecard_back", "plan_fte_back", "plan_department_scorecard",
        "plan_actual_fte", "plan_budgeted_fte", "plan_fte_gap",
    ]}
    if old_names != expected:
        raise RuntimeError("Existing Page 02 has been edited; refusing automatic redesign")

    # Back up only the known page files; stored under the project's ignored
    # interim directory, not the tracked PBIR definition.
    backup_root = ROOT / "data" / "interim" / "phase5"
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = backup_root / ("planning_page_v1_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copytree(PAGE, backup)
    new_visuals = visuals_v2()
    ids = [v["name"] for v in new_visuals]
    if len(set(ids)) != len(ids):
        raise RuntimeError("Duplicate visual IDs")
    # Replace only Page 02 visuals. Preserve its stable ID, background,
    # metadata/index, Page 01, and the entire semantic model.
    shutil.rmtree(old)
    old.mkdir(parents=True)
    for visual in new_visuals:
        save(old / visual["name"] / "visual.json", visual)
    print(f"Page 02 redesigned: {len(new_visuals)} visual elements")
    print("Backup:", backup)
    print("Page 01 and semantic model left unchanged")


if __name__ == "__main__":
    redesign()
