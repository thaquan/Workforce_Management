"""Build Page 04 Retention & Engagement as an endpoint-cohort research canvas.

The model contains only Department x Exited aggregate cohorts. This page does
not expose individual employees or imply that current department is a
historical assignment. Year is intentionally replaced by an endpoint label,
because the retention fact has no month relationship.
"""

from src.phase5.build_executive_report import (
    DEFINITION, PALETTE, load, save, lid, color, shape, textbox, card,
    container, bind, measure, dimension, make_id,
)
from src.phase5.report_shell import shared_frame


PAGE_ID = "dfa28b11977c461b8973"
PAGES = DEFINITION / "pages"
PAGE = PAGES / PAGE_ID


def department_bubbles(label, x, y, w, h):
    """One bubble per current department, sized by endpoint cohort population."""
    return bind(container(label, "scatterChart", x, y, w, h, z=1600,
                          objects={
                              "categoryLabels": [{"properties": {
                                  "show": lid("true"), "fontSize": lid("9D"),
                              }}],
                              "bubbles": [{"properties": {
                                  "bubbleSize": lid("9L"),
                                  "preventOverflow": lid("true"),
                              }}],
                          }, chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Category": [dimension("Dim Department", "department")],
        "X": [measure("Average Engagement Score")],
        "Y": [measure("Average Performance Rating")],
        "Size": [measure("Observed Employees")],
        "Tooltips": [measure("Average Prior 365d Absence Days")],
    })


def cohort_score_comparison(label, x, y, w, h):
    """Source exposed exited boolean; explanatory label decodes false/true."""
    return bind(container(label, "clusteredColumnChart", x, y, w, h,
                          z=1600, objects={
                              "categoryAxis": [{"properties": {
                                  "fontSize": lid("10D"),
                              }}],
                              "legend": [{"properties": {"show": lid("false")}}],
                          }, chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Category": [dimension("Fact Retention", "exited")],
        "Y": [measure("Average Engagement Score"),
              measure("Average Performance Rating")],
        "Tooltips": [measure("Observed Employees")],
    })


def cohort_by_department(label, x, y, w, h):
    """Shares within each department are descriptive endpoint cohort splits."""
    return bind(container(label, "hundredPercentStackedBarChart", x, y, w, h,
                          z=1600, objects={
                              "categoryAxis": [{"properties": {
                                  "preferredCategoryWidth": lid("14D"),
                                  "innerPadding": lid("5L"),
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
        "Y": [measure("Active Employees"), measure("Exited Employees")],
        "Tooltips": [measure("Observed Employees")],
    })


def visuals():
    frame = shared_frame(
        4, "COHORT VIEW", ("RETENTION", "ENGAGEMENT"),
        "Observation endpoint cohorts", "HOW DO OBSERVED COHORTS DIFFER?",
        "Engagement, performance and endpoint population by current department",
        "retention",
    )
    # Retention has NO time relationship. A real Year slicer would look like
    # it changed the results, but would simply leave them unchanged.
    frame = [v for v in frame if v["name"] != make_id("retention Year")]
    frame += [
        textbox("retention_endpoint_label", "OBSERVATION ENDPOINT", 856, 15,
                148, 22, 11, PALETTE["navy"], bold=True),
        textbox("retention_endpoint_value", "31 DEC 2025", 856, 40,
                148, 25, 13, PALETTE["subtle"]),
    ]
    frame.extend([
        textbox("retention_rail_heading", "ENDPOINT POPULATION", 20, 215,
                238, 23, 11, "#9FB3C8", bold=True),
        card("retention_population_card", ["Observed Employees"], 18, 243, 238),
        card("retention_active_card", ["Active Employees"], 18, 331, 238),
        card("retention_exited_card", ["Exited Employees"], 18, 419, 238),
        card("retention_engagement_card", ["Average Engagement Score"],
             18, 507, 238),
        textbox("retention_absence_heading", "PRIOR 365D ABSENCE DAYS / PERSON",
                20, 590, 238, 23, 10, "#9FB3C8", bold=True),
        card("retention_absence_card", ["Average Prior 365d Absence Days"],
             18, 617, 238, label_alias="Absence days / person"),
        textbox("retention_cohort_note", "Descriptive only  /  not causal",
                20, 694, 236, 20, 10, "#F0B664"),

        textbox("retention_scatter_heading", "01   DEPARTMENT PROFILE  /  ENGAGEMENT × PERFORMANCE",
                298, 112, 682, 26, 14, PALETTE["navy"], bold=True),
        textbox("retention_scatter_note", "Bubble size = employees  |  Each point is a department, not an individual",
                298, 139, 690, 20, 10, PALETTE["subtle"]),
        shape("retention_scatter_panel", 293, 162, 628, 295,
              PALETTE["white"], z=25),
        department_bubbles("retention_department_bubbles", 298, 167, 618, 285),

        textbox("retention_cohort_heading", "02   COHORT SCORE PROFILE",
                941, 112, 320, 26, 14, PALETTE["navy"], bold=True),
        textbox("retention_cohort_legend", "FALSE = ACTIVE   |   TRUE = EXITED",
                943, 139, 309, 20, 10, PALETTE["orange"]),
        shape("retention_cohort_panel", 936, 162, 324, 295,
              PALETTE["white"], z=25),
        cohort_score_comparison("retention_cohort_scores", 942, 167, 313, 265),
        textbox("retention_score_legend", "TEAL  Engagement     NAVY  Performance",
                945, 434, 310, 20, 10, PALETTE["subtle"]),

        textbox("retention_composition_heading", "03   ACTIVE VS EXITED  /  DEPARTMENT COHORT MIX",
                298, 471, 690, 26, 14, PALETTE["navy"], bold=True),
        textbox("retention_method_heading", "04   INTERPRETATION NOTES",
                952, 471, 305, 26, 13, PALETTE["navy"], bold=True),
        shape("retention_composition_panel", 293, 504, 642, 204,
              PALETTE["white"], z=25),
        shape("retention_notes_panel", 947, 504, 313, 204,
              PALETTE["white"], z=25),
        cohort_by_department("retention_department_cohort_mix", 298, 508,
                             633, 195),
        textbox("retention_method_1", "• No monthly retention history",
                958, 524, 294, 24, 11, PALETTE["navy"]),
        textbox("retention_method_2", "• Different survey/review coverage",
                958, 561, 294, 24, 11, PALETTE["navy"]),
        textbox("retention_method_3", "• Department is current, not historic",
                958, 598, 294, 24, 11, PALETTE["navy"]),
        textbox("retention_method_4", "• Associations do not imply causes",
                958, 635, 294, 24, 11, PALETTE["orange"]),
    ])
    return frame


def build():
    if PAGE.exists():
        raise RuntimeError("Page 04 already exists — refusing to overwrite edits")
    index_path = PAGES / "pages.json"
    index = load(index_path)
    expected = ["e2eaca09131b49558568", "b79c0259a8f046bca574",
                "c8d37ab121f64a1bb2ef"]
    if index.get("pageOrder") != expected:
        raise RuntimeError("Unexpected page list — refusing to modify report")
    for ident, display in zip(expected, (
        "01 Executive Overview", "02 Workforce Planning", "03 Attrition Analysis",
    )):
        if load(PAGES / ident / "page.json").get("displayName") != display:
            raise RuntimeError(f"Unexpected previous page: {ident}")
    result = visuals()
    if len({v["name"] for v in result}) != len(result):
        raise RuntimeError("Duplicate visual IDs")
    page = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": PAGE_ID, "displayName": "04 Retention & Engagement",
        "displayOption": "FitToPage", "height": 720, "width": 1280,
        "objects": {"background": [{"properties": {
            "color": color(PALETTE["canvas"]),
            "transparency": lid("0D"),
        }}]},
    }
    save(PAGE / "page.json", page)
    for v in result:
        save(PAGE / "visuals" / v["name"] / "visual.json", v)
    index["pageOrder"] = [*expected, PAGE_ID]
    index["activePageName"] = PAGE_ID
    save(index_path, index)
    print(f"Created 04 Retention & Engagement with {len(result)} PBIR visuals")
    print("Previous 3 pages and semantic model remain unchanged")


if __name__ == "__main__":
    build()
