"""Generate the credential-free Power BI model and reusable DAX measure library.

The model reads PostgreSQL marts via Import mode. No private data is written.
The model.bim is an offline semantic model, not a finished report.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "powerbi"
MODEL = OUT / "WorkforceIntelligence.SemanticModel"
INT = "int64"
NUM = "double"
DATE = "dateTime"
TEXT = "string"
BOOL = "boolean"

# Only required columns are exposed; no individual employee identifier or salary.
TABLES = {
    "Dim Month": ("SELECT DISTINCT month, year, month_number, to_char(month,'YYYY-MM') AS year_month FROM marts.dim_date WHERE month BETWEEN DATE '2023-01-01' AND DATE '2025-12-01' ORDER BY month",
                  {"month": DATE, "year": INT, "month_number": INT, "year_month": TEXT}),
    "Dim Department": ("SELECT department_id, department, department_function FROM marts.dim_department",
                       {"department_id": TEXT, "department": TEXT, "department_function": TEXT}),
    "Dim Location": ("SELECT location_id, location, country, region FROM marts.dim_location",
                     {"location_id": TEXT, "location": TEXT, "country": TEXT, "region": TEXT}),
    "Dim Level": ("SELECT level FROM marts.dim_level", {"level": TEXT}),
    "Fact Workforce": ("SELECT month, department_id, location_id, level, headcount, fte, avg_tenure_months FROM marts.mart_workforce_monthly",
                       {"month": DATE, "department_id": TEXT, "location_id": TEXT, "level": TEXT, "headcount": INT, "fte": NUM, "avg_tenure_months": NUM}),
    "Fact Planning": ("SELECT month, department_id, planning_scenario, actual_headcount, planned_headcount, actual_fte, budgeted_fte FROM marts.mart_workforce_plan_vs_actual",
                      {"month": DATE, "department_id": TEXT, "planning_scenario": TEXT, "actual_headcount": INT, "planned_headcount": INT, "actual_fte": NUM, "budgeted_fte": NUM}),
    "Fact Attrition": ("SELECT month, department_id, average_headcount, hires, terminations, voluntary_terminations, involuntary_terminations, rate_quality_status FROM marts.mart_attrition_monthly",
                       {"month": DATE, "department_id": TEXT, "average_headcount": NUM, "hires": INT, "terminations": INT, "voluntary_terminations": INT, "involuntary_terminations": INT, "rate_quality_status": TEXT}),
    "Fact Recruitment": ("SELECT month, department_id, open_requisitions, filled_requisitions, cancelled_requisitions, weighted_days_to_fill_numerator, avg_days_to_fill FROM marts.mart_recruitment_monthly",
                         {"month": DATE, "department_id": TEXT, "open_requisitions": INT, "filled_requisitions": INT, "cancelled_requisitions": INT, "weighted_days_to_fill_numerator": NUM, "avg_days_to_fill": NUM}),
    "Fact Retention": ("""SELECT current_department_id, exited, COUNT(*) AS employee_count,
COUNT(last_pre_exit_engagement_score) AS engagement_count,
SUM(last_pre_exit_engagement_score) AS engagement_sum,
COUNT(last_pre_exit_performance_rating) AS performance_count,
SUM(last_pre_exit_performance_rating) AS performance_sum,
SUM(absence_days_prior_365) AS absence_days_sum
FROM marts.mart_retention_analysis GROUP BY current_department_id, exited""",
                       {"current_department_id": TEXT, "exited": BOOL, "employee_count": INT, "engagement_count": INT, "engagement_sum": NUM, "performance_count": INT, "performance_sum": NUM, "absence_days_sum": NUM}),
    "Fact Reconciliation": ("SELECT month, snapshot_headcount, employee_asof_headcount, headcount_difference, reconciliation_status FROM marts.mart_workforce_reconciliation",
                           {"month": DATE, "snapshot_headcount": INT, "employee_asof_headcount": INT, "headcount_difference": INT, "reconciliation_status": TEXT}),
    "Pipeline Runs": ("SELECT pipeline_run_id, status, run_mode, stage, started_at, finished_at FROM audit.pipeline_runs",
                      {"pipeline_run_id": INT, "status": TEXT, "run_mode": TEXT, "stage": TEXT, "started_at": DATE, "finished_at": DATE}),
    "Quality Results": ("SELECT pipeline_run_id, check_id, status, affected_count FROM audit.data_quality_results",
                        {"pipeline_run_id": INT, "check_id": TEXT, "status": TEXT, "affected_count": INT}),
}

MEASURES = []
def add(folder, name, expr, fmt="#,0", description=""):
    MEASURES.append({"name": name, "expression": expr, "formatString": fmt,
                     "displayFolder": folder, "description": description})

PCT = "0.0%;-0.0%;0.0%"
DEC = "#,0.0"
def ending(table, column):
    return f"""VAR LastMonth = MAX ( 'Dim Month'[month] )
RETURN CALCULATE ( SUM ( '{table}'[{column}] ), KEEPFILTERS ( 'Dim Month'[month] = LastMonth ) )"""

def scoped(expr):
    # Plan, attrition and recruiting have no location/level allocation.
    return f"""IF ( ISCROSSFILTERED ( 'Dim Location' ) || ISCROSSFILTERED ( 'Dim Level' ), BLANK (), {expr} )"""

def company_scope(expr):
    return f"""IF ( ISCROSSFILTERED ( 'Dim Department' ) || ISCROSSFILTERED ( 'Dim Location' ) || ISCROSSFILTERED ( 'Dim Level' ), BLANK (), {expr} )"""

f = "01 Workforce"
add(f, "Ending Headcount", ending("Fact Workforce","headcount"), description="Stock at last selected reporting month; never sum across months.")
add(f, "Ending FTE", ending("Fact Workforce","fte"), DEC, "Stock at last selected reporting month.")
add(f, "Weighted Average Tenure Months", """VAR M = MAX ( 'Dim Month'[month] )
RETURN CALCULATE (
    DIVIDE ( SUMX ( 'Fact Workforce', 'Fact Workforce'[headcount] * 'Fact Workforce'[avg_tenure_months] ),
             SUMX ( FILTER ( 'Fact Workforce', NOT ISBLANK ( 'Fact Workforce'[avg_tenure_months] ) ), 'Fact Workforce'[headcount] ) ),
    KEEPFILTERS ( 'Dim Month'[month] = M ) )""", DEC, "Weighted by headcount, excluding unavailable tenure.")
add(f, "Prior Month Headcount", """VAR M = EDATE ( MAX ( 'Dim Month'[month] ), -1 )
RETURN CALCULATE ( [Ending Headcount], REMOVEFILTERS ( 'Dim Month' ), 'Dim Month'[month] = M )""")
add(f, "Headcount MoM Change", "IF ( NOT ISBLANK ( [Prior Month Headcount] ), [Ending Headcount] - [Prior Month Headcount] )")
add(f, "Headcount MoM %", "DIVIDE ( [Headcount MoM Change], [Prior Month Headcount] )", PCT)
add(f, "FTE per Headcount", "DIVIDE ( [Ending FTE], [Ending Headcount] )", "0.00")
add(f, "Headcount YoY Change", """VAR M = EDATE ( MAX ( 'Dim Month'[month] ), -12 )
VAR Prior = CALCULATE ( [Ending Headcount], REMOVEFILTERS ( 'Dim Month' ), 'Dim Month'[month] = M )
RETURN IF ( NOT ISBLANK ( Prior ), [Ending Headcount] - Prior )""")

f = "02 Planning"
add(f, "Planned Headcount", scoped("CALCULATE ( SUM ( 'Fact Planning'[planned_headcount] ), KEEPFILTERS ( 'Dim Month'[month] = MAX ( 'Dim Month'[month] ) ) )"))
add(f, "Planning Actual Headcount", scoped("CALCULATE ( SUM ( 'Fact Planning'[actual_headcount] ), KEEPFILTERS ( 'Dim Month'[month] = MAX ( 'Dim Month'[month] ) ) )"))
add(f, "Headcount Gap", "IF ( NOT ISBLANK ( [Planned Headcount] ) && NOT ISBLANK ( [Planning Actual Headcount] ), [Planning Actual Headcount] - [Planned Headcount] )")
add(f, "Headcount Attainment %", "DIVIDE ( [Planning Actual Headcount], [Planned Headcount] )", PCT)
add(f, "Budgeted FTE", scoped("CALCULATE ( SUM ( 'Fact Planning'[budgeted_fte] ), KEEPFILTERS ( 'Dim Month'[month] = MAX ( 'Dim Month'[month] ) ) )"), DEC)
add(f, "Planning Actual FTE", scoped("CALCULATE ( SUM ( 'Fact Planning'[actual_fte] ), KEEPFILTERS ( 'Dim Month'[month] = MAX ( 'Dim Month'[month] ) ) )"), DEC)
add(f, "FTE Gap", "IF ( NOT ISBLANK ( [Budgeted FTE] ) && NOT ISBLANK ( [Planning Actual FTE] ), [Planning Actual FTE] - [Budgeted FTE] )", DEC)

f = "03 Attrition"
for name,col in [("Hires","hires"),("Terminations","terminations"),("Voluntary Terminations","voluntary_terminations"),("Involuntary Terminations","involuntary_terminations")]:
    add(f,name,scoped(f"SUM ( 'Fact Attrition'[{col}] )"))
add(f,"Net Hires","IF ( NOT ISBLANK ( [Hires] ), [Hires] - [Terminations] )",description="Recorded hires less exits; not equivalent to snapshot headcount change.")
add(f,"Monthly Average Headcount",scoped("""IF ( HASONEVALUE ( 'Dim Month'[month] ) &&
    COUNTROWS ( FILTER ( 'Fact Attrition', ISBLANK ( 'Fact Attrition'[average_headcount] ) ) ) = 0,
    SUM ( 'Fact Attrition'[average_headcount] ) )"""),DEC)
for name,numerator in [("Monthly Attrition %","Terminations"),("Monthly Voluntary Attrition %","Voluntary Terminations"),("Monthly Involuntary Attrition %","Involuntary Terminations")]:
    add(f,name,f"DIVIDE ( [{numerator}], [Monthly Average Headcount] )",PCT,"One month only. Source reconciliation may be provisional.")
add(f,"Attrition Quality Status",scoped("""SWITCH ( TRUE (),
    COUNTROWS ( 'Fact Attrition' ) = 0, BLANK (),
    COUNTROWS ( FILTER ( 'Fact Attrition', 'Fact Attrition'[rate_quality_status] = "NO_PRIOR_SNAPSHOT" ) ) > 0, "Missing prior snapshot",
    COUNTROWS ( FILTER ( 'Fact Attrition', 'Fact Attrition'[rate_quality_status] = "PROVISIONAL_SOURCE_MISMATCH" ) ) > 0, "Provisional - source mismatch",
    "Reference matched" )"""),"", "Company-level source warning propagated into department rates.")

f = "04 Recruitment"
add(f,"Ending Open Requisitions",scoped("CALCULATE ( SUM ( 'Fact Recruitment'[open_requisitions] ), KEEPFILTERS ( 'Dim Month'[month] = MAX ( 'Dim Month'[month] ) ) )"))
for name,col in [("Filled Requisitions","filled_requisitions"),("Cancelled Requisitions","cancelled_requisitions")]:
    add(f,name,scoped(f"SUM ( 'Fact Recruitment'[{col}] )"))
add(f,"Weighted Days to Fill",scoped("""VAR Known = FILTER ( 'Fact Recruitment', 'Fact Recruitment'[filled_requisitions] > 0 && NOT ISBLANK ( 'Fact Recruitment'[avg_days_to_fill] ) )
RETURN DIVIDE ( SUMX ( Known, 'Fact Recruitment'[weighted_days_to_fill_numerator] ), SUMX ( Known, 'Fact Recruitment'[filled_requisitions] ) )"""),DEC,"Weighted by fills with a known duration.")
add(f,"Fill Share of Closed Requisitions","DIVIDE ( [Filled Requisitions], [Filled Requisitions] + [Cancelled Requisitions] )",PCT,"Share of observed closed requisitions; not a funnel conversion rate.")
add(f,"Prior Month Open Requisitions","""VAR M = EDATE ( MAX ( 'Dim Month'[month] ), -1 )
RETURN CALCULATE ( [Ending Open Requisitions], REMOVEFILTERS ( 'Dim Month' ), 'Dim Month'[month] = M )""")

f = "05 Retention"
add(f,"Observed Employees","SUM ( 'Fact Retention'[employee_count] )",description="Historical profile population at observation endpoint; not monthly headcount.")
add(f,"Exited Employees","CALCULATE ( [Observed Employees], KEEPFILTERS ( 'Fact Retention'[exited] = TRUE () ) )")
add(f,"Active Employees","CALCULATE ( [Observed Employees], KEEPFILTERS ( 'Fact Retention'[exited] = FALSE () ) )")
add(f,"Average Engagement Score","DIVIDE ( SUM ( 'Fact Retention'[engagement_sum] ), SUM ( 'Fact Retention'[engagement_count] ) )","0.00","Latest observed/pre-exit survey; excludes missing values.")
add(f,"Average Performance Rating","DIVIDE ( SUM ( 'Fact Retention'[performance_sum] ), SUM ( 'Fact Retention'[performance_count] ) )","0.00")
add(f,"Average Prior 365d Absence Days","DIVIDE ( SUM ( 'Fact Retention'[absence_days_sum] ), [Observed Employees] )",DEC)

f = "06 Time Intelligence"
add(f,"Headcount YoY %","""VAR M = EDATE ( MAX ( 'Dim Month'[month] ), -12 )
VAR Prior = CALCULATE ( [Ending Headcount], REMOVEFILTERS ( 'Dim Month' ), 'Dim Month'[month] = M )
RETURN DIVIDE ( [Headcount YoY Change], Prior )""",PCT)
add(f,"YTD Hires","""VAR M = MAX ( 'Dim Month'[month] )
RETURN CALCULATE ( [Hires], FILTER ( ALL ( 'Dim Month' ), 'Dim Month'[year] = YEAR ( M ) && 'Dim Month'[month] <= M ) )""")
add(f,"YTD Terminations","""VAR M = MAX ( 'Dim Month'[month] )
RETURN CALCULATE ( [Terminations], FILTER ( ALL ( 'Dim Month' ), 'Dim Month'[year] = YEAR ( M ) && 'Dim Month'[month] <= M ) )""")
add(f,"Period Attrition %",scoped("""VAR Months = VALUES ( 'Dim Month'[month] )
VAR ValidMonths = FILTER ( Months, NOT ISBLANK ( CALCULATE ( [Monthly Average Headcount] ) ) && CALCULATE ( [Monthly Average Headcount] ) > 0 )
VAR N = COUNTROWS ( Months )
VAR Span = DATEDIFF ( MIN ( 'Dim Month'[month] ), MAX ( 'Dim Month'[month] ), MONTH ) + 1
RETURN IF ( N > 0 && N = Span && COUNTROWS ( ValidMonths ) = N,
    DIVIDE ( [Terminations], AVERAGEX ( ValidMonths, CALCULATE ( [Monthly Average Headcount] ) ) ) )"""),PCT,"Selected contiguous period exits divided by mean monthly workforce; blank if any month lacks valid denominator.")
add(f,"Rolling 12M Attrition %","""VAR M = MAX ( 'Dim Month'[month] )
VAR WindowMonths = FILTER ( ALL ( 'Dim Month' ), 'Dim Month'[month] > EDATE ( M, -12 ) && 'Dim Month'[month] <= M )
RETURN IF ( COUNTROWS ( WindowMonths ) = 12, CALCULATE ( [Period Attrition %], WindowMonths ) )""",PCT,"Requires twelve consecutive valid monthly denominators.")
add(f,"Rolling 12M Terminations","""VAR M = MAX ( 'Dim Month'[month] )
VAR WindowMonths = FILTER ( ALL ( 'Dim Month' ), 'Dim Month'[month] > EDATE ( M, -12 ) && 'Dim Month'[month] <= M )
RETURN IF ( COUNTROWS ( WindowMonths ) = 12, CALCULATE ( [Terminations], WindowMonths ) )""")
add(f,"YTD Filled Requisitions","""VAR M = MAX ( 'Dim Month'[month] )
RETURN CALCULATE ( [Filled Requisitions], FILTER ( ALL ( 'Dim Month' ), 'Dim Month'[year] = YEAR ( M ) && 'Dim Month'[month] <= M ) )""")

f = "07 Data Quality"
add(f,"Snapshot Reconciliation Difference",company_scope(ending("Fact Reconciliation","headcount_difference")),description="Company-wide; blank when department, location or level is filtered.")
add(f,"Reconciliation Review Months",company_scope("COALESCE ( CALCULATE ( DISTINCTCOUNT ( 'Fact Reconciliation'[month] ), KEEPFILTERS ( 'Fact Reconciliation'[reconciliation_status] = \"REVIEW\" ) ), 0 )"))
add(f,"Latest Pipeline Run ID","MAXX ( ALL ( 'Pipeline Runs' ), 'Pipeline Runs'[pipeline_run_id] )")
add(f,"Latest Pipeline Status","""VAR R = [Latest Pipeline Run ID]
RETURN CALCULATE ( SELECTEDVALUE ( 'Pipeline Runs'[status] ), REMOVEFILTERS ( 'Pipeline Runs' ), 'Pipeline Runs'[pipeline_run_id] = R )""","")
for name,status in [("Latest Quality PASS","PASS"),("Latest Quality REVIEW","REVIEW"),("Latest Quality FAIL","FAIL")]:
    add(f,name,f"""VAR R = [Latest Pipeline Run ID]
VAR CheckCount = CALCULATE ( COUNTROWS ( 'Quality Results' ), REMOVEFILTERS ( 'Pipeline Runs' ), REMOVEFILTERS ( 'Quality Results' ), 'Quality Results'[pipeline_run_id] = R )
RETURN IF ( NOT ISBLANK ( R ) && CheckCount > 0, COALESCE ( CALCULATE ( COUNTROWS ( 'Quality Results' ), REMOVEFILTERS ( 'Pipeline Runs' ), REMOVEFILTERS ( 'Quality Results' ), 'Quality Results'[pipeline_run_id] = R, 'Quality Results'[status] = "{status}" ), 0 ) )""",description="Blank when the latest run has no completed quality checks; zero only after checks exist.")

def make_table(name, query, cols):
    columns = [{"name": k, "dataType": v, "sourceColumn": k, "summarizeBy": "none"}
               for k,v in cols.items()]
    # PostgreSQL returns the actual source schema; explicit M type conversion for timestamp/date fields.
    type_map = {INT:"Int64.Type",NUM:"type number",DATE:"type datetime",TEXT:"type text",BOOL:"type logical"}
    types = ", ".join('{"'+k+'", '+type_map[v]+'}' for k,v in cols.items())
    m = ['let', '    Source = PostgreSQL.Database("127.0.0.1:5433", "workforce_dw", [Query="' + query.replace('"','""').replace('\n',' ') + '"]),',
         '    Typed = Table.TransformColumnTypes(Source, {'+types+'})', 'in', '    Typed']
    return {"name":name,"columns":columns,"partitions":[{"name":name,"mode":"import","source":{"type":"m","expression":m}}]}

def rel(fact,col,dim,dcol):
    return {"name":fact.replace(" ","_")+"_"+col,"fromTable":fact,"fromColumn":col,
            "toTable":dim,"toColumn":dcol,"crossFilteringBehavior":"oneDirection"}

def build():
    MODEL.mkdir(parents=True,exist_ok=True)
    tables=[make_table(n,q,c) for n,(q,c) in TABLES.items()]
    tables.append({"name":"_Measures","columns":[{"name":"Placeholder","dataType":"int64","sourceColumn":"Placeholder","isHidden":True,"summarizeBy":"none"}],
                   "measures":MEASURES,"partitions":[{"name":"_Measures","mode":"import","source":{"type":"m","expression":["let","    Source = #table(type table [Placeholder = Int64.Type], {{1}})","in","    Source"]}}]})
    relationships=[]
    for fact in ("Fact Workforce","Fact Planning","Fact Attrition","Fact Recruitment","Fact Reconciliation"):
        relationships.append(rel(fact,"month","Dim Month","month"))
    for fact in ("Fact Workforce","Fact Planning","Fact Attrition","Fact Recruitment"):
        relationships.append(rel(fact,"department_id","Dim Department","department_id"))
    relationships += [rel("Fact Workforce","location_id","Dim Location","location_id"),rel("Fact Workforce","level","Dim Level","level"),
                      rel("Fact Retention","current_department_id","Dim Department","department_id"),
                      rel("Quality Results","pipeline_run_id","Pipeline Runs","pipeline_run_id")]
    model={"name":"WorkforceIntelligence","compatibilityLevel":1600,"model":{"culture":"en-US","defaultPowerBIDataSourceVersion":"powerBI_V3","tables":tables,"relationships":relationships}}
    (MODEL/"model.bim").write_text(json.dumps(model,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (MODEL/"definition.pbism").write_text(json.dumps({"version":"1.0","settings":{}},indent=2)+"\n",encoding="utf-8")
    out=OUT/"dax"
    out.mkdir(exist_ok=True)
    (out/"measures.dax").write_text("\n\n".join(
        f"// {m['displayFolder']}" + (f" | {m['description']}" if m['description'] else "")
        + f"\n{m['name']} =\n{m['expression']}" for m in MEASURES
    )+"\n",encoding="utf-8")
    (out/"measure_catalog.md").write_text("# Workforce Intelligence — DAX catalog\n\n| Folder | Measure | Format | Definition |\n|---|---|---|---|\n"+"\n".join(f"| {m['displayFolder']} | {m['name']} | {m['formatString']} | {m['description'] or 'See measures.dax.'} |" for m in MEASURES)+"\n",encoding="utf-8")
    print(f"Generated {len(MEASURES)} measures, {len(tables)} tables, {len(relationships)} relationships.")

if __name__=="__main__":
    build()
