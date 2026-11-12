"""Read-only checks for the committed Power BI PBIP/PBIR source.

Power BI Desktop is the editor of record. This module does not generate,
rewrite, or synchronize report pages; it only inspects local JSON assets.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "powerbi" / "WorkforceIntelligence.Report"
MODEL_FILE = ROOT / "powerbi" / "WorkforceIntelligence.SemanticModel" / "model.bim"
PAGES = REPORT / "definition" / "pages"

EXPECTED_PAGES = (
    "01 Executive Overview",
    "02 Workforce Planning",
    "03 Attrition Analysis",
    "04 Retention & Engagement",
    "05 Recruitment Performance",
    "06 Data Quality & Trust",
)

PRIVATE_FIELDS = {"employee_id", "personal_email", "annual_salary_eur", "password"}


def read_json(path: Path) -> dict:
    """Read a UTF-8/UTF-8-BOM JSON source without changing it."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def inspect_project(root: Path = ROOT) -> dict:
    """Validate important source invariants; return counts for tests/CLI.

    This intentionally avoids exact visual counts or positions, so students
    can redesign individual Power BI pages without rewriting tests.
    """
    project = root / "powerbi"
    report = project / "WorkforceIntelligence.Report"
    definition = report / "definition"
    pages_root = definition / "pages"
    bim = read_json(project / "WorkforceIntelligence.SemanticModel" / "model.bim")
    model = bim["model"]
    tables = {t["name"]: t for t in model["tables"]}
    assert len(tables) == len(model["tables"]), "Duplicate model table names"
    assert "_Measures" in tables, "Missing measure table"
    measure_names = {
        measure["name"]
        for table in model["tables"]
        for measure in table.get("measures", [])
    }
    assert len(measure_names) >= 51, "Expected workforce DAX measures are missing"
    for relationship in model["relationships"]:
        for side in ("from", "to"):
            table = tables[relationship[side + "Table"]]
            assert relationship[side + "Column"] in {
                c["name"] for c in table["columns"]
            }, "Relationship references a missing model column"

    index = read_json(pages_root / "pages.json")
    ids = index["pageOrder"]
    assert len(ids) == 6 and len(set(ids)) == 6, "Expected six unique pages"
    assert index["activePageName"] in ids, "Active page is not in page order"
    seen = []
    visuals_count = 0
    for page_id in ids:
        page_dir = pages_root / page_id
        page = read_json(page_dir / "page.json")
        assert page["name"] == page_id
        assert (page["width"], page["height"]) == (1280, 720)
        seen.append(page["displayName"])
        names = set()
        for path in sorted((page_dir / "visuals").glob("*/visual.json")):
            visual = read_json(path)
            assert visual["name"] == path.parent.name
            assert visual["name"] not in names, "Duplicate visual ID"
            names.add(visual["name"])
            position = visual["position"]
            for coordinate in ("x", "y", "width", "height"):
                assert isinstance(position[coordinate], (int, float))
            assert position["x"] >= 0 and position["y"] >= 0
            assert position["width"] > 0 and position["height"] > 0
            assert position["x"] + position["width"] <= page["width"]
            assert position["y"] + position["height"] <= page["height"]
            for role in visual["visual"].get("query", {}).get("queryState", {}).values():
                for item in role.get("projections", []):
                    field = item.get("field", {})
                    if "Measure" in field:
                        obj = field["Measure"]
                        assert obj["Property"] in measure_names
                    elif "Column" in field:
                        obj = field["Column"]
                        table_name = obj["Expression"]["SourceRef"]["Entity"]
                        assert table_name in tables
                        col = obj["Property"]
                        assert col in {c["name"] for c in tables[table_name]["columns"]}
                        assert col.casefold() not in PRIVATE_FIELDS, (
                            "Private employee field exposed in public report", page_id, col
                        )
                    else:
                        raise AssertionError("Unexpected model field projection")
            visuals_count += 1
    assert tuple(seen) == EXPECTED_PAGES, (seen, EXPECTED_PAGES)
    assert visuals_count >= 6, "No report visuals found"
    theme = read_json(definition / "report.json")["themeCollection"]["customTheme"]
    assert theme["type"] == "RegisteredResources"
    assert (report / "StaticResources" / "RegisteredResources" / theme["name"]).exists()
    return {
        "pages": len(ids),
        "visuals": visuals_count,
        "tables": len(tables),
        "measures": len(measure_names),
        "relationships": len(model["relationships"]),
    }


if __name__ == "__main__":
    print(json.dumps(inspect_project(), indent=2))
