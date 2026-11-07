"""Evidence-based Phase 1 resolutions; never modifies the source workbook."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
import csv
import json

from phase1_profiler import ROOT, SOURCE, OUT, load_workbook, date_iso, write_csv

PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)


def excel_day(day):
    return (datetime.combine(day, datetime.min.time()) - datetime(1899, 12, 30)).days


def month_end(month):
    first = date.fromisoformat(month)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


def main():
    data = load_workbook(SOURCE)
    employees = data["DimEmployee"]
    snapshots = data["FactMonthlySnapshot"]
    events = data["FactEmployeeEvents"]
    targets = data["WorkforceTargets"]
    months = sorted({date_iso(r["Month"]) for r in snapshots})
    monthly_rows = []
    for month in months:
        cutoff = excel_day(month_end(month))
        profile_hc = sum(
            r["HireDate"] <= cutoff
            and (r["TerminationDate"] is None or r["TerminationDate"] > cutoff)
            for r in employees
        )
        month_rows = [r for r in snapshots if date_iso(r["Month"]) == month]
        reported_hc = sum(r["Headcount"] for r in month_rows)
        reported_fte = round(sum(r["FTE"] for r in month_rows), 2)
        event_counts = Counter(
            r["EventType"] for r in events
            if date_iso(r["EventDate"])[:7] == month[:7]
        )
        difference = reported_hc - profile_hc
        monthly_rows.append([
            month[:7], reported_hc, profile_hc, difference, reported_fte,
            event_counts["Hire"], event_counts["Termination"],
            "REVIEW" if difference else "PASS",
        ])
    write_csv(
        OUT / "monthly_reconciliation.csv",
        ["month", "snapshot_headcount", "asof_employee_headcount", "hc_difference",
         "snapshot_fte", "hires", "terminations", "status"],
        monthly_rows,
    )
    june = "2025-06-01"
    july = "2025-07-01"
    june_cutoff = excel_day(month_end(june))
    june_snapshot = defaultdict(int)
    june_profile = Counter()
    june_exits = Counter()
    for r in snapshots:
        if date_iso(r["Month"]) == june:
            june_snapshot[r["DepartmentID"]] += r["Headcount"]
    for r in employees:
        if (r["HireDate"] <= june_cutoff
                and (r["TerminationDate"] is None or r["TerminationDate"] > june_cutoff)):
            june_profile[r["DepartmentID"]] += 1
    for r in events:
        if r["EventType"] == "Termination" and date_iso(r["EventDate"])[:7] == "2025-06":
            june_exits[r["DepartmentID"]] += 1
    reset = {r["DepartmentID"] for r in targets
             if date_iso(r["Month"]) == july
             and r["PlanningScenario"] == "Post-restructuring reset"}
    department_rows = [
        [dept, june_snapshot[dept], june_profile[dept],
         june_snapshot[dept] - june_profile[dept], june_exits[dept],
         "YES" if dept in reset else "NO"]
        for dept in sorted(june_snapshot)
    ]
    write_csv(OUT / "restructuring_evidence.csv",
              ["department_id", "june_snapshot_hc", "june_asof_profile_hc",
               "june_hc_difference", "june_terminations", "july_plan_reset"],
              department_rows)
    first_day = date.fromisoformat(min(date_iso(r["EventDate"]) for r in events))
    last_day = month_end(months[-1])
    calendar_rows = []
    day = first_day
    while day <= last_day:
        calendar_rows.append([
            day.isoformat(), day.replace(day=1).isoformat(), day.year,
            "Q" + str((day.month - 1) // 3 + 1), day.month,
            day.strftime("%b"), day.isoweekday()
        ])
        day += timedelta(days=1)
    write_csv(PROCESSED / "dim_date_extended.csv",
              ["Date", "Month", "Year", "Quarter", "MonthNumber",
               "MonthName", "WeekdayNumber"], calendar_rows)
    june_diff = next(r[3] for r in monthly_rows if r[0] == "2025-06")
    july_diff = next(r[3] for r in monthly_rows if r[0] == "2025-07")
    if sum(june_exits.values()) != 98 or june_diff != 98:
        raise AssertionError("Expected June 2025 restructuring evidence changed.")
    if not all(int(r[3]) == int(r[4]) for r in department_rows):
        raise AssertionError("June departmental discrepancy needs re-review.")
    summary = {
        "monthly_periods": len(months), "months_with_hc_mismatch":
        sum(r[3] != 0 for r in monthly_rows),
        "june_2025_hc_difference": june_diff,
        "june_2025_terminations": sum(june_exits.values()),
        "july_2025_hc_difference": july_diff,
        "june_restructuring_departments": sorted(june_exits),
        "july_plan_reset_departments": sorted(reset),
        "extended_calendar_start": first_day.isoformat(),
        "extended_calendar_end": last_day.isoformat(),
        "extended_calendar_days": len(calendar_rows),
        "compensation_currency": sorted({r["Currency"] for r in data["FactCompensation"]}),
        "salary_budget_unit_verified": False,
        "event_types": dict(Counter(r["EventType"] for r in events)),
    }
    (OUT / "review_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    issue_rows = [
        ["HC_RECONCILIATION", "EXPLAINED_NOT_OVERWRITTEN",
         f"June difference {june_diff} equals 98 June exits; other monthly residuals retained"],
        ["DIMDATE_COVERAGE", "DERIVED_CALENDAR_CREATED",
         f"{first_day} through {last_day}; {len(calendar_rows)} days; original unchanged"],
        ["SALARY_BUDGET", "BLOCKED_UNVERIFIED",
         "Compensation currency EUR; target budget currency, period, coverage unverified"],
        ["TRANSFER_EVENTS", "UNSUPPORTED_BY_SOURCE",
         "Only Hire and Termination events; do not publish transfer metrics"],
    ]
    write_csv(OUT / "review_status.csv",
              ["issue", "resolution_status", "evidence_or_action"], issue_rows)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
