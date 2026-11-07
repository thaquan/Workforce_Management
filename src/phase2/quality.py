"""Source contracts and privacy-safe preflight quality rules."""
from collections import Counter
from datetime import timedelta

from .schema_contract import BUSINESS_KEYS, SHEET_COLUMNS, coerce_value


class SourceValidationError(ValueError):
    """The input workbook violates a documented, blocking contract."""


FK_LINKS = (
    ("DimEmployee", "EmployeeID", ("FactEmployeeEvents", "FactCompensation", "FactPerformance", "FactEngagement", "FactAbsence")),
    ("DimDepartment", "DepartmentID", ("DimEmployee", "FactMonthlySnapshot", "FactEmployeeEvents", "FactRecruitment", "WorkforceTargets")),
    ("DimLocation", "LocationID", ("DimEmployee", "FactMonthlySnapshot", "FactEmployeeEvents")),
)


def normalize_and_validate(workbook):
    """Validate full workbook before any raw table is modified."""
    supplied = set(workbook)
    expected = set(SHEET_COLUMNS)
    if supplied != expected:
        raise SourceValidationError(
            f"Wrong worksheet set: {len(expected - supplied)} missing / {len(supplied - expected)} unexpected"
        )
    normalized = {}
    checks = []
    for sheet, columns in SHEET_COLUMNS.items():
        rows = workbook[sheet]
        if not rows or tuple(rows[0]) != tuple(columns):
            raise SourceValidationError(f"{sheet}: missing rows, reordered headers, or changed columns")
        duplicates = set()
        clean = []
        for row_number, row in enumerate(rows, start=2):
            if tuple(row) != tuple(columns):
                raise SourceValidationError(f"{sheet}: row {row_number}: inconsistent columns")
            result = {}
            for column in columns:
                try:
                    result[column] = coerce_value(column, row[column])
                except (ValueError, OverflowError) as error:
                    raise SourceValidationError(
                        f"{sheet}: row {row_number}, field {column}: {error}"
                    ) from None
            key = tuple(result[field] for field in BUSINESS_KEYS[sheet])
            if any(value is None for value in key):
                raise SourceValidationError(f"{sheet}: row {row_number}: null business key")
            if key in duplicates:
                raise SourceValidationError(f"{sheet}: row {row_number}: duplicate business key")
            duplicates.add(key)
            clean.append(result)
        normalized[sheet] = clean
        checks.append((f"source_key_{sheet}", "PASS", 0, {"rows": len(clean)}))

    for dim_sheet, key, dependents in FK_LINKS:
        valid = {row[key] for row in normalized[dim_sheet]}
        for fact in dependents:
            for row_number, row in enumerate(normalized[fact], start=2):
                if row[key] not in valid:
                    raise SourceValidationError(
                        f"{fact}: row {row_number}: {key} missing from {dim_sheet}"
                    )
        checks.append((f"fk_{key}", "PASS", 0, {"dependent_tables": len(dependents)}))

    events = normalized["FactEmployeeEvents"]
    event_keys = {(r["EmployeeID"], r["EventType"], r["EventDate"]) for r in events}
    for i, row in enumerate(events, start=2):
        if row["EventType"] not in ("Hire", "Termination"):
            raise SourceValidationError(f"FactEmployeeEvents: row {i}: invalid EventType")

    for i, row in enumerate(normalized["DimEmployee"], start=2):
        terminated = row["EmploymentStatus"] == "Terminated"
        if row["EmploymentStatus"] not in ("Active", "Terminated"):
            raise SourceValidationError(f"DimEmployee: row {i}: invalid EmploymentStatus")
        if row["HireDate"] is None:
            raise SourceValidationError(f"DimEmployee: row {i}: missing HireDate")
        if terminated != (row["TerminationDate"] is not None):
            raise SourceValidationError(f"DimEmployee: row {i}: inconsistent termination fields")
        if row["TerminationDate"] is not None and row["TerminationDate"] < row["HireDate"]:
            raise SourceValidationError(f"DimEmployee: row {i}: termination before hire")
        if (row["EmployeeID"], "Hire", row["HireDate"]) not in event_keys:
            raise SourceValidationError(f"DimEmployee: row {i}: missing hire event")
        if terminated and (row["EmployeeID"], "Termination", row["TerminationDate"]) not in event_keys:
            raise SourceValidationError(f"DimEmployee: row {i}: missing termination event")
    checks.append(("employment_event_consistency", "PASS", 0, {"employees": len(normalized["DimEmployee"])}))

    for i, row in enumerate(normalized["FactMonthlySnapshot"], start=2):
        if row["Headcount"] < 0 or row["FTE"] is None or row["FTE"] < 0 or row["FTE"] > row["Headcount"]:
            raise SourceValidationError(f"FactMonthlySnapshot: row {i}: invalid HC/FTE")
    checks.append(("snapshot_fte_bounds", "PASS", 0, {"rows": len(normalized["FactMonthlySnapshot"])}))

    for i, row in enumerate(normalized["FactRecruitment"], start=2):
        if any(row[field] is None or row[field] < 0 for field in
               ("OpenRequisitions", "FilledRequisitions", "CancelledRequisitions")):
            raise SourceValidationError(f"FactRecruitment: row {i}: invalid requisition counts")

    monthly = {}
    for row in normalized["FactMonthlySnapshot"]:
        monthly[row["Month"]] = monthly.get(row["Month"], 0) + row["Headcount"]
    mismatch = 0
    for first_day, reported_hc in sorted(monthly.items()):
        end_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        event_based_hc = sum(
            employee["HireDate"] <= end_day and
            (employee["TerminationDate"] is None or employee["TerminationDate"] > end_day)
            for employee in normalized["DimEmployee"]
        )
        mismatch += reported_hc != event_based_hc
    checks.append((
        "headcount_vs_employee_history", "REVIEW" if mismatch else "PASS", mismatch,
        {"periods_checked": len(monthly), "detail": "Source snapshot versus employee-as-of; never auto-correct"},
    ))

    earliest_event = min(row["EventDate"] for row in events)
    earliest_calendar = min(row["Date"] for row in normalized["DimDate"])
    calendar_gap = earliest_calendar > earliest_event
    checks.append((
        "source_dimdate_coverage", "REVIEW" if calendar_gap else "PASS", int(calendar_gap),
        {"first_event": earliest_event.isoformat(), "first_source_date": earliest_calendar.isoformat(),
         "detail": "Use the separately derived calendar if source date coverage is incomplete"},
    ))
    checks.append((
        "salary_budget_semantics", "REVIEW", 1,
        {"detail": "Budget currency, period and coverage unverified; variance KPI blocked"},
    ))
    types = Counter(row["EventType"] for row in events)
    checks.append((
        "transfer_history", "REVIEW" if "Transfer" not in types else "PASS",
        int("Transfer" not in types),
        {"event_types": sorted(types), "detail": "Do not infer internal mobility without event history"},
    ))
    return normalized, checks
