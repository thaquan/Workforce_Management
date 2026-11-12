"""Author the first Power BI PBIR page from a validated, empty report shell.

This tool does not touch model.bim, Desktop caches, credentials or imported
employee data. Deliberately refuse to overwrite a page with existing visuals.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from src.phase5.build_model import ROOT

REPORT = ROOT / "powerbi" / "WorkforceIntelligence.Report"
PAGE_ID = "e2eaca09131b49558568"
DEFINITION = REPORT / "definition"
PAGE = DEFINITION / "pages" / PAGE_ID
VISUAL_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/visualContainer/2.9.0/schema.json"
)
PALETTE = {
    "navy": "#102A43",
    "teal": "#087F8C",
    "canvas": "#F0F4F8",
    "white": "#FFFFFF",
    "subtle": "#627D98",
    "line": "#D9E2EC",
    "orange": "#D97706",
    "red": "#DC2626",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def lid(value):
    return {"expr": {"Literal": {"Value": value}}}


def color(value):
    return {"solid": {"color": lid(f"'{value}'")}}


def make_id(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()[:20]


def container(label, visual_type, x, y, w, h, z=1000, objects=None, chrome=None):
    if x < 0 or y < 0 or x + w > 1280 or y + h > 720:
        raise ValueError(f"{label}: visual extends beyond canvas")
    item = {
        "$schema": VISUAL_SCHEMA,
        "name": make_id(label),
        "position": {
            "x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z,
        },
        "visual": {"visualType": visual_type},
    }
    if objects:
        item["visual"]["objects"] = objects
    if chrome:
        item["visual"]["visualContainerObjects"] = chrome
    return item


def projection(table, field, kind):
    return {
        "field": {
            kind: {
                "Expression": {"SourceRef": {"Entity": table}},
                "Property": field,
            }
        },
        "queryRef": f"{table}.{field}",
        "nativeQueryRef": field,
    }


def bind(item, roles):
    item["visual"]["query"] = {
        "queryState": {
            role: {
                "projections": [projection(*spec) for spec in specs]
            }
            for role, specs in roles.items()
        }
    }
    return item


def measure(field):
    return ("_Measures", field, "Measure")


def dimension(table, field):
    return (table, field, "Column")


def shape(label, x, y, w, h, fill, z=20):
    return container(label, "shape", x, y, w, h, z, {
        "shape": [{"properties": {"tileShape": lid("'rectangle'")}}],
        "fill": [{
            "properties": {"fillColor": color(fill), "transparency": lid("0D")},
            "selector": {"id": "default"},
        }],
        "outline": [{
            "properties": {"show": lid("false")},
            "selector": {"id": "default"},
        }],
    }, {
        "background": [{"properties": {"show": lid("false")}}],
        "border": [{"properties": {"show": lid("false")}}],
        "padding": [{
            "properties": {a: lid("0D") for a in ("top", "bottom", "left", "right")}
        }],
    })


def textbox(label, message, x, y, w, h, size=16, fill="#102A43", z=2000, bold=False):
    return container(label, "textbox", x, y, w, h, z, {
        "general": [{
            "properties": {
                "paragraphs": [{
                    "textRuns": [{
                        "value": message,
                        "textStyle": {
                            "fontFamily": "Segoe UI Semibold" if bold else "Segoe UI",
                            "fontSize": f"{size}px",
                            "color": fill,
                        },
                    }],
                    "horizontalTextAlignment": "left",
                }],
            }
        }]
    }, {
        "background": [{"properties": {"show": lid("false")}}],
        "border": [{"properties": {"show": lid("false")}}],
        "padding": [{
            "properties": {a: lid("0D") for a in ("top", "bottom", "left", "right")}
        }],
    })


def card(label, fields, x, y, w, canvas_height=720, z=2100, label_alias=None):
    value_font = min(28, max(12, math.floor(canvas_height * .028)))
    label_font = min(14, max(8, math.floor(value_font * .55)))
    pad = 8
    content_height = (
        4 * pad + 2 + math.ceil(value_font * 1.5)
        + math.ceil(max(label_font, 12) * 1.5)
    )
    if content_height > int(canvas_height * .15):
        raise RuntimeError("Card exceeds 15% of page height")
    chart = bind(
        container(label, "cardVisual", x, y, w, content_height, z, {
            "value": [{
                "properties": {
                    "fontSize": lid(f"{value_font}D"),
                    # Disallow automatic abbreviation: show 1,079, not 1K.
                    # Power BI enum: 0=Auto, 1=None, 1000=Thousands.
                    "labelDisplayUnits": lid("1D"),
                },
                "selector": {"id": "default"},
            }],
            "label": [{
                "properties": {
                    "fontSize": lid(f"{label_font}D"),
                    **({"text": lid(f"'{label_alias}'")} if label_alias else {}),
                },
                "selector": {"id": "default"},
            }],
            "padding": [{
                "properties": {"paddingUniform": lid("8D")},
                "selector": {"id": "default"},
            }],
            "layout": [{
                "properties": {"paddingUniform": lid("0D")},
                "selector": {"id": "default"},
            }],
        }, {
            "padding": [{
                "properties": {a: lid("8D") for a in ("top", "bottom", "left", "right")},
                "selector": {"id": "default"},
            }],
            "background": [{
                "properties": {"show": lid("true"), "color": color(PALETTE["white"])},
            }],
            "border": [{"properties": {"show": lid("false")}}],
        }),
        {"Data": [measure(f) for f in fields]},
    )
    return chart


def chart(label, typ, x, y, w, h, axis, metrics):
    objects = {}
    if typ == "clusteredBarChart":
        # Eight departments must fit in a compact executive chart without
        # a vertical category scrollbar.
        objects["categoryAxis"] = [{
            "properties": {
                "preferredCategoryWidth": lid("13D"),
                "innerPadding": lid("5L"),
                "fontSize": lid("9D"),
            }
        }]
    return bind(
        container(label, typ, x, y, w, h, z=2000, objects=objects, chrome={
            "background": [{
                "properties": {"show": lid("true"), "color": color(PALETTE["white"])},
            }],
            "border": [{"properties": {"show": lid("false")}}],
            # The report already has editorial chart headings outside visuals.
            "title": [{"properties": {"show": lid("false")}}],
        }),
        {"Category": [axis], "Y": [measure(m) for m in metrics]},
    )


def matrix(label, x, y, w, h):
    return bind(container(label, "pivotTable", x, y, w, h, z=2000, objects={
        "columnHeaders": [{
            "properties": {
                "columnAdjustment": lid("'growToFit'"),
                "autoSizeColumnWidth": lid("true"),
            },
        }]
    }), {
        "Rows": [dimension("Dim Department", "department")],
        "Values": [measure(m) for m in (
            "Ending Headcount", "Planned Headcount", "Headcount Gap", "Ending FTE",
        )],
    })


def slicer(label, table, field, x, y, w):
    return bind(
        container(label, "slicer", x, y, w, 80, z=2000, objects={
            "data": [{"properties": {"mode": lid("'Dropdown'")}}],
            "header": [{
                "properties": {
                    "show": lid("true"),
                    "text": lid(f"'{label}'"),
                }
            }],
        }, chrome={
            "padding": [{
                "properties": {a: lid("8D") for a in ("top", "bottom", "left", "right")},
            }]
        }),
        {"Values": [dimension(table, field)]},
    )


def register_theme():
    source = load(ROOT / "powerbi" / "themes" / "workforce_theme.json")
    digest = hashlib.sha256(json.dumps(source, sort_keys=True).encode()).hexdigest()[:10]
    theme_file = f"WorkforceNavyTeal-{digest}.json"
    source["name"] = theme_file
    registered = REPORT / "StaticResources" / "RegisteredResources"
    registered.mkdir(parents=True, exist_ok=True)
    save(registered / theme_file, source)

    report_path = DEFINITION / "report.json"
    report = load(report_path)
    base = report["themeCollection"]["baseTheme"]["reportVersionAtImport"]
    report["themeCollection"]["customTheme"] = {
        "name": theme_file,
        "reportVersionAtImport": dict(base),
        "type": "RegisteredResources",
    }
    custom = next((p for p in report["resourcePackages"]
                   if p.get("name") == "RegisteredResources"), None)
    if custom is None:
        custom = {"name": "RegisteredResources", "type": "RegisteredResources", "items": []}
        report["resourcePackages"].append(custom)
    custom["items"] = [
        i for i in custom["items"]
        if not i.get("name", "").startswith("WorkforceNavyTeal-")
    ] + [{"name": theme_file, "path": theme_file, "type": "CustomTheme"}]
    save(report_path, report)


def build():
    if not PAGE.exists():
        raise FileNotFoundError("Scaffolded Model Preview page is missing")
    visual_root = PAGE / "visuals"
    if visual_root.exists() and any(visual_root.iterdir()):
        raise RuntimeError("Refusing to overwrite existing report visuals")
    p = PAGE / "page.json"
    page = load(p)
    if page["displayName"] != "Model Preview":
        raise RuntimeError("Page was edited; refusing to overwrite")
    if (page["width"], page["height"]) != (1280, 720):
        raise RuntimeError("Unexpected page dimensions")

    page["displayName"] = "01 Executive Overview"
    page["objects"] = {
        "background": [{
            "properties": {
                "color": color(PALETTE["canvas"]),
                "transparency": lid("0D"),
            }
        }]
    }
    visuals = [
        shape("navy_header", 0, 0, 1280, 82, PALETTE["navy"]),
        shape("teal_header_line", 0, 79, 1280, 3, PALETTE["teal"], z=30),
        textbox("brand_label", "WORKFORCE INTELLIGENCE  /  HR ANALYTICS",
                24, 12, 720, 25, 12, "#9FB3C8", bold=True),
        textbox("page_title", "Executive Overview",
                24, 34, 500, 44, 26, PALETTE["white"], bold=True),
        textbox("header_note", "MONTHLY SNAPSHOT  Â·  JAN 2023â€“DEC 2025",
                866, 46, 390, 22, 12, "#C3D5E2"),
        textbox("filter_caption", "FILTERS  /  USE DEPARTMENT AND YEAR TO EXPLORE",
                23, 112, 660, 26, 12, PALETTE["subtle"]),
        slicer("Year", "Dim Month", "year", 785, 86, 195),
        slicer("Department", "Dim Department", "department", 987, 86, 270),
        shape("cards_back", 20, 176, 1240, 82, PALETTE["white"], z=30),
        card("executive_kpis", ["Ending Headcount", "Planned Headcount",
                                "Headcount Gap", "Ending FTE"], 20, 176, 1240),
        textbox("trend_heading", "Workforce trajectory  /  Actual vs plan",
                22, 269, 755, 29, 16, PALETTE["navy"], bold=True),
        textbox("dept_heading", "Headcount variance by department",
                797, 269, 460, 29, 16, PALETTE["navy"], bold=True),
        shape("trend_back", 20, 299, 750, 207, PALETTE["white"], z=40),
        shape("dept_back", 790, 299, 470, 207, PALETTE["white"], z=40),
        chart("actual_plan_trend", "lineChart", 24, 302, 742, 200,
              dimension("Dim Month", "month"),
              ["Ending Headcount", "Planned Headcount"]),
        chart("department_variance", "clusteredBarChart", 794, 302, 460, 200,
              dimension("Dim Department", "department"),
              ["Headcount Gap"]),
        textbox("dept_matrix_header", "Department scorecard",
                22, 521, 770, 26, 16, PALETTE["navy"], bold=True),
        textbox("trust_heading", "DATA TRUST  /  PIPELINE HEALTH",
                917, 521, 340, 26, 13, PALETTE["teal"], bold=True),
        shape("scorecard_back", 20, 551, 875, 149, PALETTE["white"], z=40),
        shape("trust_back", 909, 551, 351, 149, PALETTE["white"], z=40),
        matrix("department_matrix", 25, 555, 866, 141),
        card("quality_review", ["Reconciliation Review Months"], 913, 559,
             172, label_alias="Review months"),
        card("quality_fail", ["Latest Quality FAIL"], 1090, 559,
             165, label_alias="Blocking failures"),
        textbox("quality_caveat",
                "REVIEW: 33/36 months mismatch  Â·  Attrition provisional",
                921, 654, 334, 32, 11, PALETTE["orange"]),
    ]

    register_theme()
    save(p, page)
    for visual in visuals:
        save(visual_root / visual["name"] / "visual.json", visual)
    print(f"Created Executive Overview: {len(visuals)} report visuals, 1 custom theme")
    print("No model files or source data were modified.")


if __name__ == "__main__":
    build()
