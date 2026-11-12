"""Build Page 06 — Data Quality & Trust (monitoring and observability).

This is an *imported audit snapshot*, not an always-on live monitor. Technical
pipeline success and unresolved source-level REVIEW issues are shown side by
side. The page only adds PBIR definitions; no DAX or source data is changed.
"""
from src.phase5.build_executive_report import (
    DEFINITION, PALETTE, load, save, lid, color, shape, textbox, card,
    container, bind, measure, dimension, make_id,
)
from src.phase5.report_shell import shared_frame, shared_filter


PAGE_ID = "fb2e6a51b9a848ec95bb"
PAGES = DEFINITION / "pages"
PAGE = PAGES / PAGE_ID


def fixed_columns(table, fields):
    """Readable table columns within the 1280x720 control tower layout."""
    return {
        "columnHeaders": [{"properties": {
            "columnAdjustment": lid("'fixedWidth'"),
            "autoSizeColumnWidth": lid("false"),
            "fontSize": lid("9D"),
            "wordWrap": lid("false"),
        }}],
        "values": [{"properties": {"fontSize": lid("9D")}}],
        "columnWidth": [{
            "properties": {"value": lid(f"{width}D")},
            "selector": {"metadata": f"{table}.{field}"},
        } for field, width in fields],
    }


def concise_headers(chart, names):
    """Keep semantic-model queryRefs intact while shortening display aliases."""
    columns = chart["visual"]["query"]["queryState"]["Values"]["projections"]
    if len(columns) != len(names):
        raise ValueError("Table header count differs from projected fields")
    for column, label in zip(columns, names):
        column["nativeQueryRef"] = label
    return chart


def descending_sort(table, *columns):
    return {
        "sort": [{
            "field": {"Column": {
                "Expression": {"SourceRef": {"Entity": table}},
                "Property": column,
            }},
            "direction": "Descending",
        } for column in columns],
        "isDefaultSort": False,
    }


def reconciliation_timeline(label, x, y, w, h):
    """Company-wide monthly difference, including a June 2025 +98 spike."""
    return bind(container(label, "lineChart", x, y, w, h, z=1700,
                          chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Category": [dimension("Dim Month", "month")],
        "Y": [measure("Snapshot Reconciliation Difference")],
    })


def audit_runs_table(label, x, y, w, h):
    """History of imported audited pipeline runs, not live execution state."""
    chart = bind(container(label, "tableEx", x, y, w, h, z=1700,
                          objects=fixed_columns("Pipeline Runs", [
                              ("pipeline_run_id", 70),
                              ("status", 100),
                              ("finished_at", 152),
                          ]), chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Values": [
            dimension("Pipeline Runs", "pipeline_run_id"),
            dimension("Pipeline Runs", "status"),
            dimension("Pipeline Runs", "finished_at"),
        ],
    })
    concise_headers(chart, ["Run", "Status", "Finished"])
    chart["visual"]["query"]["sortDefinition"] = descending_sort(
        "Pipeline Runs", "pipeline_run_id")
    return chart


def quality_register(label, x, y, w, h):
    """All imported gate records with an Audit Run slicer for drill-down.

    Selecting a historical Audit Run filters this table through the existing
    one-to-many relationship. Latest-status KPI cards intentionally ignore
    that selector, and this difference is documented on the page.
    """
    chart = bind(container(label, "tableEx", x, y, w, h, z=1700,
                          objects=fixed_columns("Quality Results", [
                              ("pipeline_run_id", 67),
                              ("check_id", 277),
                              ("status", 78),
                              ("affected_count", 86),
                          ]), chrome={
                              "background": [{"properties": {
                                  "show": lid("true"),
                                  "color": color(PALETTE["white"]),
                              }}],
                              "title": [{"properties": {"show": lid("false")}}],
                          }), {
        "Values": [
            dimension("Quality Results", "pipeline_run_id"),
            dimension("Quality Results", "check_id"),
            dimension("Quality Results", "status"),
            dimension("Quality Results", "affected_count"),
        ],
    })
    concise_headers(chart, ["Run", "Gate / Check", "Status", "Rows"])
    chart["visual"]["query"]["sortDefinition"] = descending_sort(
        "Quality Results", "pipeline_run_id", "affected_count")
    return chart


def visuals():
    frame = shared_frame(
        6, "TRUST VIEW", ("DATA QUALITY", "& TRUST"),
        "Audit & reconciliation", "IS THE DATA TRUSTWORTHY?",
        "Pipeline execution is not proof of source-data correctness",
        "trust",
    )
    # No department-level audit/reconciliation facts. A Department slicer
    # would falsely suggest that company-wide counts can be allocated.
    frame = [v for v in frame if v["name"] != make_id("trust Department")]
    frame.append(shared_filter("trust Audit Run", "Audit Run",
                               "Pipeline Runs", "pipeline_run_id", 1010, 251))

    frame.extend([
        textbox("trust_sidebar_heading", "LATEST IMPORTED RUN", 20, 210,
                238, 24, 11, "#9FB3C8", bold=True),
        card("trust_run_id", ["Latest Pipeline Run ID"], 18, 240, 238,
             label_alias="Pipeline run ID"),
        card("trust_run_status", ["Latest Pipeline Status"], 18, 333, 238,
             label_alias="Pipeline status"),
        textbox("trust_company_heading", "COMPANY-WIDE RECONCILIATION",
                20, 424, 237, 24, 11, "#9FB3C8", bold=True),
        card("trust_review_months", ["Reconciliation Review Months"],
             18, 451, 238, label_alias="Months under review"),
        card("trust_latest_gap", ["Snapshot Reconciliation Difference"],
             18, 544, 238, label_alias="Latest HC difference"),
        textbox("trust_warning_heading", "ATTENTION REQUIRED", 20, 635,
                235, 22, 11, "#F0B664", bold=True),
        textbox("trust_warning_1", "33/36 historical months REVIEW",
                20, 660, 236, 23, 11, "#F0B664"),
        textbox("trust_warning_2", "Imported data  /  refresh required",
                20, 688, 236, 23, 10, "#C3D5E2"),

        # A status strip is the central visual language of an observability
        # console; it deliberately differs from all other business pages.
        textbox("trust_gate_heading", "01   LATEST IMPORTED QUALITY GATES",
                298, 112, 610, 27, 15, PALETTE["navy"], bold=True),
        textbox("trust_scope_note", "Year filters reconciliation only. Audit Run filters audit tables; latest KPI cards always show latest.",
                298, 139, 957, 20, 10, PALETTE["orange"]),
        shape("trust_gate_strip", 293, 162, 967, 92,
              PALETTE["white"], z=25),
        card("trust_pass_card", ["Latest Quality PASS"], 298, 167, 300,
             label_alias="PASS  /  TECHNICAL"),
        card("trust_review_card", ["Latest Quality REVIEW"], 623, 167, 300,
             label_alias="REVIEW  /  SOURCE"),
        card("trust_fail_card", ["Latest Quality FAIL"], 948, 167, 306,
             label_alias="FAIL  /  BLOCKING"),

        textbox("trust_reconciliation_heading", "02   MONTHLY HEADCOUNT DIFFERENCE  /  SOURCE VS AS-OF",
                298, 269, 885, 27, 14, PALETTE["navy"], bold=True),
        textbox("trust_reconciliation_note", "Company-only | Jun 2025 +98 | Dec 2025 +5 | source mismatch is not silently repaired",
                298, 296, 940, 20, 10, PALETTE["subtle"]),
        shape("trust_reconciliation_back", 293, 321, 967, 184,
              PALETTE["white"], z=25),
        reconciliation_timeline("trust_monthly_reconciliation", 298, 325, 957, 174),

        textbox("trust_history_heading", "03   PIPELINE RUN HISTORY",
                298, 518, 375, 28, 14, PALETTE["navy"], bold=True),
        textbox("trust_checks_heading", "04   QUALITY REGISTER  /  FILTER AUDIT RUN",
                691, 518, 568, 28, 14, PALETTE["navy"], bold=True),
        shape("trust_history_back", 293, 549, 381, 160,
              PALETTE["white"], z=25),
        shape("trust_checks_back", 685, 549, 575, 160,
              PALETTE["white"], z=25),
        audit_runs_table("trust_pipeline_history_table", 298, 553, 372, 152),
        quality_register("trust_quality_register_table", 690, 553, 565, 152),
    ])
    return frame


def build():
    if PAGE.exists():
        raise RuntimeError("Page 06 already exists: refusing to overwrite")
    index_path = PAGES / "pages.json"
    index = load(index_path)
    expected = [
        "e2eaca09131b49558568", "b79c0259a8f046bca574",
        "c8d37ab121f64a1bb2ef", "dfa28b11977c461b8973",
        "e596cb074ac84ab2a1b9",
    ]
    if index.get("pageOrder") != expected:
        raise RuntimeError("Unexpected pages; refusing to alter report")
    for page_id, display in zip(expected, (
        "01 Executive Overview", "02 Workforce Planning", "03 Attrition Analysis",
        "04 Retention & Engagement", "05 Recruitment Performance",
    )):
        if load(PAGES / page_id / "page.json")["displayName"] != display:
            raise RuntimeError("Existing report page has unexpected identity")
    content = visuals()
    if len({v["name"] for v in content}) != len(content):
        raise RuntimeError("Page06 contains duplicated visual identifiers")
    page = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": PAGE_ID, "displayName": "06 Data Quality & Trust",
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
    save(index_path, index)
    print(f"Created Page06 Data Quality & Trust with {len(content)} PBIR elements")
    print("Pages 01-05 and the 51-measure semantic model were preserved")


if __name__ == "__main__":
    build()
