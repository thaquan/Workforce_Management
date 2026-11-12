"""Author Page 03 — Attrition Diagnostic in the shared PBIR design system.

The page is additive: it does not modify Page 01, Page 02, semantic model,
Power BI import cache, database credentials or source workbook.
"""
from src.phase5.build_executive_report import (
    DEFINITION, PALETTE, load, save, lid, color, shape, textbox, card,
    container, bind, measure, dimension,
)
from src.phase5.report_shell import shared_frame


PAGE_ID = "c8d37ab121f64a1bb2ef"
PAGES = DEFINITION / "pages"
PAGE = PAGES / PAGE_ID


def heatmap(label, x, y, w, h):
    """Native matrix with threshold-colored department×month attrition rates.

    January 2023 is BLANK (missing prior headcount), not a fabricated zero.
    Rules are sourced from Monthly Attrition %, not static cell colors.
    """
    target = "_Measures.Monthly Attrition %"
    rate_measure = {
        "Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}},
                    "Property": "Monthly Attrition %"}
    }
    def case(bound, fill):
        return {
            "Condition": {"Comparison": {
                "ComparisonKind": 2, "Left": rate_measure,
                "Right": {"Literal": {"Value": bound}},
            }},
            "Value": {"Literal": {"Value": f"'{fill}'"}},
        }
    # Fixed, interpretable percentage thresholds, comparing decimals:
    # 8%+ coral; 2%-8% amber; 0%-2% cool teal. Unknown/null stays uncolored.
    colors = {"Conditional": {
        "Cases": [case("0.08D", "#F7A99B"),
                  case("0.02D", "#FDE6A5"),
                  case("0D", "#DDF3F0")],
        "DefaultValue": {"Literal": {"Value": "'#FFFFFF'"}},
    }}
    objects = {
        "columnHeaders": [{"properties": {
            "columnAdjustment": lid("'growToFit'"),
            "autoSizeColumnWidth": lid("true"),
        }}],
        "values": [{
            "properties": {"backColor": {"solid": {"color": {"expr": colors}}}},
            "selector": {
                "data": [{"dataViewWildcard": {"matchingOption": 1}}],
                "metadata": target,
            },
        }],
    }
    return bind(container(label, "pivotTable", x, y, w, h, z=1700,
                          objects=objects, chrome={
                              "background": [{"properties": {
                                  "show": lid("true"), "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Rows": [dimension("Dim Department", "department")],
        "Columns": [dimension("Dim Month", "year_month")],
        "Values": [measure("Monthly Attrition %")],
    })


def monthly_flows(label, x, y, w, h):
    """Hires and exits are separate recorded monthly event flows."""
    return bind(container(label, "clusteredColumnChart", x, y, w, h,
                          z=1700, chrome={
                              "background": [{"properties": {
                                  "show": lid("true"), "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Category": [dimension("Dim Month", "month")],
        "Y": [measure("Hires"), measure("Terminations")],
        "Tooltips": [measure("Voluntary Terminations"),
                     measure("Involuntary Terminations")],
    })


def exit_mix(label, x, y, w, h):
    """Compare voluntary/involuntary composition per department.

    Native 100%-stacked bars normalize *within each department*, so this
    visual is a composition comparison and not a count ranking.
    """
    return bind(container(label, "hundredPercentStackedBarChart", x, y, w, h,
                          z=1700, objects={
                              "categoryAxis": [{"properties": {
                                  "preferredCategoryWidth": lid("15D"),
                                  "innerPadding": lid("6L"),
                                  "fontSize": lid("9D"),
                              }}],
                          }, chrome={
                              "background": [{"properties": {
                                  "show": lid("true"), "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Category": [dimension("Dim Department", "department")],
        "Y": [measure("Voluntary Terminations"),
              measure("Involuntary Terminations")],
        "Tooltips": [measure("Terminations")],
    })


def visuals():
    items = shared_frame(
        3, "ATTRITION VIEW", ("ATTRITION", "ANALYSIS"),
        "Recorded exits & risk signals", "WHEN AND WHERE DO EXITS CLUSTER?",
        "Event flows, exit mix and monthly department attrition",
        "attrition",
    )
    items.extend([
        textbox("attrition_rail_label", "REPORTING PERIOD EVENTS", 20, 215,
                238, 23, 11, "#9FB3C8", bold=True),
        card("attrition_exits_kpi", ["Terminations"], 18, 243, 238),
        card("attrition_hires_kpi", ["Hires"], 18, 331, 238),
        card("attrition_voluntary_kpi", ["Voluntary Terminations"],
             18, 419, 238),
        card("attrition_involuntary_kpi", ["Involuntary Terminations"],
             18, 507, 238),
        textbox("attrition_rate_label", "ROLLING 12M ATTRITION", 20, 590,
                238, 23, 11, "#9FB3C8", bold=True),
        card("attrition_rolling_kpi", ["Rolling 12M Attrition %"],
             18, 617, 238),
        textbox("attrition_rail_warning", "Provisional: source HC mismatch",
                20, 694, 236, 20, 10, "#F0B664"),

        # The heatmap is the hero, not a copy of Planning's waterfall or
        # Executive's time-series line chart.
        textbox("attrition_heat_heading", "01   ATTRITION RATE  /  DEPARTMENT × MONTH",
                298, 112, 726, 26, 15, PALETTE["navy"], bold=True),
        textbox("attrition_heat_note", "DATA REVIEW: 33/36 months mismatch  |  Jan 2023 rate missing  |  Select Year",
                298, 139, 621, 20, 10, PALETTE["orange"]),
        textbox("attrition_color_legend", "RATE BANDS: teal <2%  |  amber 2-8%  |  coral 8%+",
                922, 139, 333, 20, 10, PALETTE["subtle"]),
        shape("attrition_heat_panel", 293, 165, 967, 279,
              PALETTE["white"], z=25),
        heatmap("attrition_month_department_heatmap", 298, 170, 957, 269),

        textbox("attrition_flow_heading", "02   HIRES VS TERMINATIONS  /  MONTHLY EVENTS",
                298, 458, 603, 27, 14, PALETTE["navy"], bold=True),
        textbox("attrition_mix_heading", "03   EXIT MIX BY DEPARTMENT",
                914, 458, 348, 27, 14, PALETTE["navy"], bold=True),
        shape("attrition_flow_panel", 293, 492, 606, 213,
              PALETTE["white"], z=25),
        shape("attrition_mix_panel", 911, 492, 349, 213,
              PALETTE["white"], z=25),
        monthly_flows("attrition_monthly_flow_columns", 298, 497, 598, 203),
        exit_mix("attrition_exit_type_composition", 916, 497, 338, 203),
    ])
    return items


def build():
    if PAGE.exists():
        raise RuntimeError("Page 03 already exists; refusing to overwrite")
    index_path = PAGES / "pages.json"
    index = load(index_path)
    expected = ["e2eaca09131b49558568", "b79c0259a8f046bca574"]
    if index.get("pageOrder") != expected:
        raise RuntimeError("Unexpected page order; protect existing report pages")
    for ident, name in zip(expected, ("01 Executive Overview", "02 Workforce Planning")):
        if load(PAGES / ident / "page.json").get("displayName") != name:
            raise RuntimeError("Expected prior page not found")
    page = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": PAGE_ID,
        "displayName": "03 Attrition Analysis",
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
        "objects": {"background": [{"properties": {
            "color": color(PALETTE["canvas"]),
            "transparency": lid("0D"),
        }}]},
    }
    visual_list = visuals()
    if len({v["name"] for v in visual_list}) != len(visual_list):
        raise RuntimeError("Duplicate visual IDs")
    # Add the new page only: the model and older PBIR page folders are intact.
    save(PAGE / "page.json", page)
    for visual in visual_list:
        save(PAGE / "visuals" / visual["name"] / "visual.json", visual)
    index["pageOrder"] = [*expected, PAGE_ID]
    index["activePageName"] = PAGE_ID
    save(index_path, index)
    print(f"Created Page 03 Attrition Analysis with {len(visual_list)} PBIR visuals")
    print("Page 01, Page 02 and the 51-measure model were not modified")


if __name__ == "__main__":
    build()
