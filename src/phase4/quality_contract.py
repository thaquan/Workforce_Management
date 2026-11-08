"""Queries return the number of violating rows; never employee-level values."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Gate:
    check_id: str
    severity: str
    sql: str
    rationale: str


GATES = (
    Gate("raw_table_count", "BLOCK",
         "SELECT ABS(COUNT(*) - 12) FROM information_schema.tables "
         "WHERE table_schema='raw' AND table_type='BASE TABLE'",
         "Exactly twelve source tables must be present."),
    Gate("staging_view_count", "BLOCK",
         "SELECT ABS(COUNT(*) - 16) FROM information_schema.views WHERE table_schema='staging'",
         "All twelve staging and four intermediate views must exist."),
    Gate("marts_table_count", "BLOCK",
         "SELECT ABS(COUNT(*) - 20) FROM information_schema.tables "
         "WHERE table_schema='marts' AND table_type='BASE TABLE'",
         "Five dimensions, eight facts and seven business marts."),
    Gate("snapshot_to_mart_rows", "BLOCK",
         "SELECT ABS((SELECT COUNT(*) FROM raw.fact_monthly_snapshot) - "
         "(SELECT COUNT(*) FROM marts.mart_workforce_monthly))",
         "Source monthly snapshot rows must survive without fanout or loss."),
    Gate("employee_to_retention_rows", "BLOCK",
         "SELECT ABS((SELECT COUNT(*) FROM raw.dim_employee) - "
         "(SELECT COUNT(*) FROM marts.mart_retention_analysis))",
         "Exactly one retention feature row per source employee."),
    Gate("recruitment_to_mart_rows", "BLOCK",
         "SELECT ABS((SELECT COUNT(*) FROM raw.fact_recruitment) - "
         "(SELECT COUNT(*) FROM marts.mart_recruitment_monthly))",
         "Aggregated recruitment should not duplicate by joins."),
    Gate("targets_to_plan_rows", "BLOCK",
         "SELECT ABS((SELECT COUNT(*) FROM raw.workforce_targets) - "
         "(SELECT COUNT(*) FROM marts.mart_workforce_plan_vs_actual))",
         "Planning mart must remain Month x Department."),
    Gate("snapshot_grain", "BLOCK",
         "SELECT COUNT(*) FROM (SELECT month,department_id,location_id,level "
         "FROM marts.mart_workforce_monthly GROUP BY 1,2,3,4 HAVING COUNT(*)>1) d",
         "The workforce mart has one row per monthly source grain."),
    Gate("department_month_grain", "BLOCK",
         "SELECT COUNT(*) FROM (SELECT month,department_id FROM "
         "marts.mart_attrition_monthly GROUP BY 1,2 HAVING COUNT(*)>1) d",
         "Attrition mart must not fan out."),
    Gate("negative_hc_fte", "BLOCK",
         "SELECT COUNT(*) FROM marts.mart_workforce_monthly "
         "WHERE headcount<0 OR fte<0 OR fte>headcount OR fte IS NULL",
         "Headcount/FTE value bounds."),
    Gate("attrition_logic", "BLOCK",
         "SELECT COUNT(*) FROM marts.mart_attrition_monthly WHERE "
         "terminations <> voluntary_terminations + involuntary_terminations "
         "OR (previous_headcount IS NULL AND attrition_rate_pct IS NOT NULL) "
         "OR (average_headcount>0 AND "
         "ABS(attrition_rate_pct - 100*terminations/average_headcount)>0.000001)",
         "Terminations and monthly rate denominator agree."),
    Gate("retention_post_exit_leakage", "BLOCK",
         "SELECT COUNT(*) FROM marts.mart_retention_analysis WHERE "
         "termination_date IS NOT NULL AND "
         "(last_engagement_date >= termination_date OR "
         "last_performance_date >= termination_date)",
         "Retained feature values must precede termination strictly."),
    Gate("salary_budget_disabled", "BLOCK",
         "SELECT COUNT(*) FROM marts.mart_workforce_plan_vs_actual "
         "WHERE salary_budget_variance_enabled IS DISTINCT FROM FALSE",
         "Unverified budget units must never enable variance KPI."),
    Gate("date_coverage", "BLOCK",
         "SELECT COUNT(*) FROM raw.fact_employee_events e LEFT JOIN marts.dim_date d "
         "ON e.event_date=d.date WHERE d.date IS NULL",
         "Historical events must map into extended date dimension."),
    Gate("headcount_reference_mismatch", "REVIEW",
         "SELECT COUNT(*) FROM marts.mart_workforce_reconciliation "
         "WHERE reconciliation_status='REVIEW'",
         "Source snapshot and employee-as-of counts disagree; never auto-correct."),
    Gate("source_calendar_shortfall", "REVIEW",
         "SELECT CASE WHEN (SELECT MIN(date) FROM raw.dim_date) > "
         "(SELECT MIN(event_date) FROM raw.fact_employee_events) THEN 1 ELSE 0 END",
         "Source calendar starts after earliest hire; derived dim_date is extended."),
    Gate("salary_budget_semantics", "REVIEW", "SELECT 1",
         "Currency, period, and coverage of salary budget are unverified."),
    Gate("no_transfer_events", "REVIEW",
         "SELECT CASE WHEN EXISTS(SELECT 1 FROM raw.fact_employee_events "
         "WHERE event_type='Transfer') THEN 0 ELSE 1 END",
         "Internal transfers cannot be inferred without transfer history."),
)


def evaluate(conn, gates=GATES):
    """Return aggregate-only outcomes; errors from SQL are blocking failures."""
    results = []
    for gate in gates:
        try:
            count = conn.execute(gate.sql).fetchone()[0]
            if count is None or count < 0:
                raise ValueError("A quality gate returned an invalid count")
            status = "PASS" if count == 0 else ("REVIEW" if gate.severity == "REVIEW" else "FAIL")
            results.append((gate.check_id, status, int(count), gate.rationale))
        except Exception:
            # No exception text/source values in persisted results.
            results.append((gate.check_id, "FAIL", 1, "Quality SQL failed to execute"))
    return results
