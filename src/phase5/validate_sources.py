"""Read-only SQL checks for the Power BI Import model and historical baselines.

SQL is read from the checked-in model.bim file; this tool never rewrites the
model, the report, or source records.
"""
from decimal import Decimal
import json
import re
from src.phase2.ingest import connect_db
from src.phase5.report_validation import MODEL_FILE, read_json


def model_queries():
    model = read_json(MODEL_FILE)["model"]
    queries = {}
    for table in model["tables"]:
        if table["name"] == "_Measures":
            continue
        source = table["partitions"][0]["source"]
        statement = source["expression"]
        statement = "\n".join(statement) if isinstance(statement, list) else statement
        match = re.search(r'\[Query="([^"]+)"\]', statement, re.S)
        assert match, f"No native SQL projection for {table['name']}"
        queries[table["name"]] = (
            match.group(1),
            tuple(column["name"] for column in table["columns"]),
        )
    return queries, sum(len(t.get("measures", [])) for t in model["tables"])


def main():
    TABLES, measure_count = model_queries()
    with connect_db() as conn:
        conn.execute("SET default_transaction_read_only = on")
        counts = {}
        for name, (query, columns) in TABLES.items():
            cursor = conn.execute(f"SELECT * FROM ({query}) AS p LIMIT 0")
            assert [c.name for c in cursor.description] == list(columns), name
            counts[name] = conn.execute(f"SELECT COUNT(*) FROM ({query}) AS p").fetchone()[0]
        for table, key in [("Dim Month","month"),("Dim Department","department_id"),
                           ("Dim Location","location_id"),("Dim Level","level"),("Pipeline Runs","pipeline_run_id")]:
            query = TABLES[table][0]
            n, distinct, nonnull = conn.execute(
                f"SELECT COUNT(*), COUNT(DISTINCT {key}), COUNT({key}) FROM ({query}) p").fetchone()
            assert n == distinct == nonnull, (table, n, distinct, nonnull)
        def scalar(sql):
            return conn.execute(sql).fetchone()[0]
        checks = {
            "January 2023 ending HC": (scalar("SELECT SUM(headcount) FROM marts.mart_workforce_monthly WHERE month='2023-01-01'"), 622),
            "December 2025 ending HC": (scalar("SELECT SUM(headcount) FROM marts.mart_workforce_monthly WHERE month='2025-12-01'"), 999),
            "December 2025 planned HC": (scalar("SELECT SUM(planned_headcount) FROM marts.mart_workforce_plan_vs_actual WHERE month='2025-12-01'"), 1079),
            "December 2025 HC gap": (scalar("SELECT SUM(actual_headcount)-SUM(planned_headcount) FROM marts.mart_workforce_plan_vs_actual WHERE month='2025-12-01'"), -80),
            "December 2025 FTE": (scalar("SELECT SUM(fte) FROM marts.mart_workforce_monthly WHERE month='2025-12-01'"), Decimal("968.6")),
            "January 2023 valid attrition denominators": (scalar("SELECT COUNT(average_headcount) FROM marts.mart_attrition_monthly WHERE month='2023-01-01'"), 0),
            "June 2025 reconciliation": (scalar("SELECT headcount_difference FROM marts.mart_workforce_reconciliation WHERE month='2025-06-01'"), 98),
            "Reconciliation review months": (scalar("SELECT COUNT(*) FROM marts.mart_workforce_reconciliation WHERE reconciliation_status='REVIEW'"), 33),
            "Observed employees": (scalar("SELECT COUNT(*) FROM marts.mart_retention_analysis"), 1200),
            "Exited employees": (scalar("SELECT COUNT(*) FROM marts.mart_retention_analysis WHERE exited"), 206),
        }
        for label,(actual,expected) in checks.items():
            assert abs(float(actual)-float(expected)) < 1e-6, (label, actual, expected)
        # Check that each fact-side key resolves to its dimension. A missing
        # key would produce Power BI's unexpected (Blank) dimension member.
        links=[]
        for fact in ("Fact Workforce","Fact Planning","Fact Attrition","Fact Recruitment","Fact Reconciliation"):
            links.append((fact,"month","Dim Month","month"))
        for fact in ("Fact Workforce","Fact Planning","Fact Attrition","Fact Recruitment"):
            links.append((fact,"department_id","Dim Department","department_id"))
        links.extend([("Fact Workforce","location_id","Dim Location","location_id"),
                      ("Fact Workforce","level","Dim Level","level"),
                      ("Fact Retention","current_department_id","Dim Department","department_id"),
                      ("Quality Results","pipeline_run_id","Pipeline Runs","pipeline_run_id")])
        for f,fk,d,dk in links:
            missing=scalar(f"SELECT COUNT(*) FROM ({TABLES[f][0]}) f LEFT JOIN ({TABLES[d][0]}) d ON f.{fk}=d.{dk} WHERE d.{dk} IS NULL")
            assert missing == 0, (f,fk,d,missing)
        print(json.dumps({"source_tables":len(counts),"rows":counts,
                          "dimension_keys_verified":5,"relationships_verified":len(links),
                          "baseline_checks":{k:float(v[0]) for k,v in checks.items()},
                          "measure_count":measure_count},indent=2))

if __name__=="__main__":
    main()
