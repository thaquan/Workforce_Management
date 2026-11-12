"""Add Page 05 — Recruitment Operations Board to the existing PBIR report.

Recruitment is summarized at Month × Department grain. Opening vacancies
are a month-end stock; filled and cancelled vacancies are period flows.
The report never claims these source aggregates are applicant funnel stages.
"""

from src.phase5.build_executive_report import (
    DEFINITION, PALETTE, load, save, lid, color,
    shape, textbox, card, container, bind, measure, dimension,
)
from src.phase5.report_shell import shared_frame


PAGE_ID = "e596cb074ac84ab2a1b9"
PAGES = DEFINITION / "pages"
PAGE = PAGES / PAGE_ID


def closed_requisition_area(label, x, y, w, h):
    """Monthly filled and cancelled outcomes, which are additive flows."""
    return bind(container(label, "stackedAreaChart", x, y, w, h, z=1600,
                          chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Category": [dimension("Dim Month", "month")],
        "Y": [measure("Filled Requisitions"),
              measure("Cancelled Requisitions")],
        "Tooltips": [measure("Fill Share of Closed Requisitions")],
    })


def recruiting_speed_bubbles(label, x, y, w, h):
    """One department per bubble: speed versus fill volume.

    Size is *current* open requisitions, while X and Y are period metrics.
    Each field's semantics are described explicitly above the visual.
    """
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
        "X": [measure("Weighted Days to Fill")],
        "Y": [measure("Filled Requisitions")],
        "Size": [measure("Ending Open Requisitions")],
        "Tooltips": [measure("Cancelled Requisitions")],
    })


def open_backlog_bars(label, x, y, w, h):
    """Rank current/open vacancies by department without summing months."""
    return bind(container(label, "clusteredBarChart", x, y, w, h, z=1600,
                          objects={
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
        "Y": [measure("Ending Open Requisitions")],
        "Tooltips": [measure("Filled Requisitions"),
                     measure("Weighted Days to Fill")],
    })


def recruiting_scorecard(label, x, y, w, h):
    """Per-department stock, flow and duration in a compact table."""
    return bind(container(label, "pivotTable", x, y, w, h, z=1600,
                          objects={
                              "columnHeaders": [{"properties": {
                                  "columnAdjustment": lid("'growToFit'"),
                                  "autoSizeColumnWidth": lid("true"),
                              }}],
                          }, chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Rows": [dimension("Dim Department", "department")],
        "Values": [measure("Ending Open Requisitions"),
                   measure("Filled Requisitions"),
                   measure("Cancelled Requisitions"),
                   measure("Weighted Days to Fill")],
    })


def department_closeout_mix(label, x, y, w, h):
    """Share of filled vs cancelled *closed* requisitions by department.

    This is not a candidate conversion funnel; the denominator comprises
    only recorded filled + cancelled requisitions over the selected period.
    """
    return bind(container(label, "hundredPercentStackedBarChart", x, y, w, h,
                          z=1600, objects={
                              "categoryAxis": [{"properties": {
                                  "preferredCategoryWidth": lid("12D"),
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
        "Y": [measure("Filled Requisitions"),
              measure("Cancelled Requisitions")],
        "Tooltips": [measure("Fill Share of Closed Requisitions")],
    })


def visuals():
    items = shared_frame(
        5, "OPERATIONS VIEW", ("RECRUITMENT", "OPERATIONS"),
        "Requisitions & cycle time", "HOW IS HIRING OPERATING?",
        "Closed demand, recruitment speed and outstanding positions",
        "recruitment",
    )
    items.extend([
        textbox("recruitment_rail_header", "OPEN BACKLOG  /  LATEST MONTH",
                20, 213, 239, 25, 11, "#9FB3C8", bold=True),
        card("recruitment_open_kpi", ["Ending Open Requisitions"],
             18, 241, 238, label_alias="Open requisitions"),
        textbox("recruitment_close_header", "CLOSED REQUESTS  /  SELECTED PERIOD",
                20, 323, 239, 23, 10, "#9FB3C8", bold=True),
        card("recruitment_filled_kpi", ["Filled Requisitions"],
             18, 351, 238, label_alias="Filled requisitions"),
        card("recruitment_cancelled_kpi", ["Cancelled Requisitions"],
             18, 439, 238, label_alias="Cancelled requisitions"),
        textbox("recruitment_cycle_header", "RECRUITMENT EFFICIENCY",
                20, 522, 238, 23, 11, "#9FB3C8", bold=True),
        card("recruitment_duration_kpi", ["Weighted Days to Fill"],
             18, 548, 238, label_alias="Weighted days to fill"),
        card("recruitment_closed_share_kpi", ["Fill Share of Closed Requisitions"],
             18, 635, 238, label_alias="Fill share of closed"),

        # High-value operational composition differs from the monthly event
        # columns and ratio heatmap on Attrition, as well as Planning's
        # waterfall/treemap and Retention's research scatter layout.
        textbox("recruitment_flow_heading", "01   MONTHLY CLOSED REQUISITIONS  /  OUTCOMES",
                298, 112, 660, 26, 15, PALETTE["navy"], bold=True),
        textbox("recruitment_scatter_heading", "02   SPEED VS FILL VOLUME",
                945, 112, 313, 26, 14, PALETTE["navy"], bold=True),
        textbox("recruitment_flow_context", "Filled + cancelled are period flows, not candidate funnel stages",
                298, 139, 618, 20, 11, PALETTE["subtle"]),
        textbox("recruitment_scatter_context", "Bubble size = ending open vacancies",
                944, 139, 310, 20, 10, PALETTE["subtle"]),
        shape("recruitment_flow_back", 293, 163, 628, 301,
              PALETTE["white"], z=25),
        shape("recruitment_scatter_back", 935, 163, 325, 301,
              PALETTE["white"], z=25),
        closed_requisition_area("recruitment_monthly_closed_area", 298, 168,
                                618, 290),
        recruiting_speed_bubbles("recruitment_dept_speed_bubbles", 941, 168,
                                 313, 290),

        textbox("recruitment_backlog_heading", "03   OPEN VACANCIES  /  DEPARTMENT",
                298, 478, 591, 27, 14, PALETTE["navy"], bold=True),
        textbox("recruitment_table_heading", "04   CLOSED REQUEST MIX  /  DEPT",
                844, 478, 416, 27, 14, PALETTE["navy"], bold=True),
        shape("recruitment_backlog_back", 293, 510, 533, 198,
              PALETTE["white"], z=25),
        shape("recruitment_table_back", 838, 510, 422, 198,
              PALETTE["white"], z=25),
        open_backlog_bars("recruitment_open_backlog", 299, 515, 522, 190),
        department_closeout_mix("recruitment_department_closeout_mix",
                                844, 515, 411, 190),
    ])
    return items


def build():
    if PAGE.exists():
        raise RuntimeError("Page 05 already exists: refusing to overwrite")
    metadata = PAGES / "pages.json"
    index = load(metadata)
    expected = [
        "e2eaca09131b49558568",
        "b79c0259a8f046bca574",
        "c8d37ab121f64a1bb2ef",
        "dfa28b11977c461b8973",
    ]
    if index.get("pageOrder") != expected:
        raise RuntimeError("Unexpected pages: refusing to edit the report")
    for page_id, name in zip(expected, (
        "01 Executive Overview", "02 Workforce Planning",
        "03 Attrition Analysis", "04 Retention & Engagement",
    )):
        if load(PAGES / page_id / "page.json")["displayName"] != name:
            raise RuntimeError("Existing page has unexpected identity")
    content = visuals()
    if len({v["name"] for v in content}) != len(content):
        raise RuntimeError("Page 05 contains duplicated visual identifiers")
    page = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": PAGE_ID,
        "displayName": "05 Recruitment Performance",
        "displayOption": "FitToPage", "width": 1280, "height": 720,
        "objects": {"background": [{"properties": {
            "color": color(PALETTE["canvas"]),
            "transparency": lid("0D"),
        }}]},
    }
    save(PAGE / "page.json", page)
    for v in content:
        save(PAGE / "visuals" / v["name"] / "visual.json", v)
    index["pageOrder"] = expected + [PAGE_ID]
    index["activePageName"] = PAGE_ID
    save(metadata, index)
    print(f"Created Page05 Recruitment Performance with {len(content)} PBIR elements")
    print("Pages 01-04 and semantic model were not modified")


if __name__ == "__main__":
    build()
