"""Generate stable dbt source/staging files directly from the Phase 2 schema contract."""
from pathlib import Path

from src.phase2.schema_contract import BUSINESS_KEYS, SHEET_COLUMNS, snake_case

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "dbt_hr" / "models" / "staging"


def generate():
    STAGING.mkdir(parents=True, exist_ok=True)
    sources = [
        "version: 2",
        "",
        "sources:",
        "  - name: raw_hr",
        "    description: Immutable source replicas loaded by Phase 2 Python ingestion.",
        "    schema: raw",
        "    tables:",
    ]
    models = ["version: 2", "", "models:"]
    for sheet, cols in SHEET_COLUMNS.items():
        name = snake_case(sheet)
        sources.extend([
            f"      - name: {name}",
            f"        description: Source worksheet {sheet}; preserve original business grain.",
        ])
        model_name = f"stg_{name}"
        models.extend([
            f"  - name: {model_name}",
            f"    description: Typed, lossless staging view of source {sheet}.",
            "    columns:",
        ])
        for col in cols:
            col_name = snake_case(col)
            models.extend([
                f"      - name: {col_name}",
                f"        description: Source column {col}.",
            ])
            if col in BUSINESS_KEYS[sheet]:
                models.extend(["        data_tests:", "          - not_null"])
                if len(BUSINESS_KEYS[sheet]) == 1:
                    models.append("          - unique")
        projection = ",\n    ".join(f'"{snake_case(col)}"' for col in cols)
        sql = (
            "-- Generated from the Phase 2 source contract; source grain is unchanged.\n"
            f"select\n    {projection}\n"
            f"from {{{{ source('raw_hr', '{name}') }}}}\n"
        )
        (STAGING / f"{model_name}.sql").write_text(sql, encoding="utf-8")
    (STAGING / "_sources.yml").write_text("\n".join(sources) + "\n", encoding="utf-8")
    (STAGING / "_staging.yml").write_text("\n".join(models) + "\n", encoding="utf-8")
    print(f"Generated {len(SHEET_COLUMNS)} staging models and 2 YAML contracts.")


if __name__ == "__main__":
    generate()
