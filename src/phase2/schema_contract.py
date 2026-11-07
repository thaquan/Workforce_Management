"""Explicit column, grain and SQL type contract for the twelve Excel worksheets."""
from collections import OrderedDict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import csv
import re
from pathlib import Path

SHEET_COLUMNS = OrderedDict({
    "DimEmployee": "EmployeeID DepartmentID Department Role Level LocationID Location ManagerID Gender BirthYear AgeBand HireDate TerminationDate EmploymentStatus TerminationType TerminationReason FTE TenureMonthsAtExitOrEnd TenureBandAtExitOrEnd".split(),
    "FactMonthlySnapshot": "Month DepartmentID Department LocationID Location Level Headcount FTE AvgTenureMonths".split(),
    "FactEmployeeEvents": "EmployeeID EventDate EventType DepartmentID Department LocationID Location TerminationType TerminationReason".split(),
    "FactCompensation": "EmployeeID EffectiveDate AnnualSalary Level Currency".split(),
    "FactPerformance": "EmployeeID ReviewDate PerformanceRating ReviewType".split(),
    "FactEngagement": "EmployeeID SurveyDate EngagementScore ResponseRatePct".split(),
    "FactAbsence": "EmployeeID AbsenceDate AbsenceType DaysAbsent".split(),
    "FactRecruitment": "ReqID Month DepartmentID Department OpenRequisitions FilledRequisitions CancelledRequisitions AvgDaysToFill".split(),
    "WorkforceTargets": "Month DepartmentID Department PlannedHeadcount BudgetedFTE BudgetedSalaryCost PlanningScenario".split(),
    "DimDepartment": "DepartmentID Department Function CostCenter".split(),
    "DimLocation": "LocationID Location Country Region TimeZone Latitude Longitude".split(),
    "DimDate": "Date Month Year Quarter MonthNumber MonthName WeekdayNumber".split(),
})

BUSINESS_KEYS = {
    "DimEmployee": ("EmployeeID",),
    "FactMonthlySnapshot": ("Month", "DepartmentID", "LocationID", "Level"),
    "FactEmployeeEvents": ("EmployeeID", "EventDate", "EventType"),
    "FactCompensation": ("EmployeeID", "EffectiveDate"),
    "FactPerformance": ("EmployeeID", "ReviewDate"),
    "FactEngagement": ("EmployeeID", "SurveyDate"),
    "FactAbsence": ("EmployeeID", "AbsenceDate", "AbsenceType"),
    "FactRecruitment": ("Month", "DepartmentID"),
    "WorkforceTargets": ("Month", "DepartmentID"),
    "DimDepartment": ("DepartmentID",),
    "DimLocation": ("LocationID",),
    "DimDate": ("Date",),
}

INTEGER_COLUMNS = {
    "BirthYear", "TenureMonthsAtExitOrEnd", "Headcount",
    "OpenRequisitions", "FilledRequisitions", "CancelledRequisitions",
    "PlannedHeadcount", "Year", "MonthNumber", "WeekdayNumber",
}
DECIMAL_COLUMNS = {
    "FTE", "AvgTenureMonths", "AnnualSalary", "PerformanceRating",
    "EngagementScore", "ResponseRatePct", "DaysAbsent", "AvgDaysToFill",
    "BudgetedFTE", "BudgetedSalaryCost", "Latitude", "Longitude",
}
EXCEL_EPOCH = datetime(1899, 12, 30)


def snake_case(value: str) -> str:
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).lower()


def sql_type(field: str) -> str:
    if field == "Month" or field.endswith("Date"):
        return "DATE"
    if field in INTEGER_COLUMNS:
        return "INTEGER"
    if field in DECIMAL_COLUMNS:
        return "NUMERIC(20,6)"
    return "TEXT"


def coerce_value(field: str, value):
    if value is None or value == "":
        return None
    kind = sql_type(field)
    if kind == "DATE":
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if not isinstance(value, (int, float)) or int(value) != value:
            raise ValueError("Invalid Excel date serial")
        return (EXCEL_EPOCH + timedelta(days=int(value))).date()
    if kind == "INTEGER":
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
            raise ValueError("Invalid integer field")
        return int(value)
    if kind.startswith("NUMERIC"):
        if isinstance(value, bool):
            raise ValueError("Invalid numeric field")
        try:
            number = Decimal(str(value))
        except (InvalidOperation, TypeError):
            raise ValueError("Invalid numeric field") from None
        if not number.is_finite() or number.as_tuple().exponent < -6:
            raise ValueError("Unsupported numeric precision")
        return number
    if not isinstance(value, str):
        raise ValueError("Text field must be a string")
    return value


def export_mapping(path=None):
    """Publish schema metadata without exporting employee-level rows."""
    path = Path(path) if path else Path(__file__).resolve().parents[2] / "docs/phase2/source_to_raw_mapping.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["source_sheet", "source_column", "raw_table",
                         "raw_column", "postgres_type", "business_key"])
        for sheet, columns in SHEET_COLUMNS.items():
            for column in columns:
                writer.writerow([
                    sheet, column, "raw." + snake_case(sheet),
                    snake_case(column), sql_type(column), column in BUSINESS_KEYS[sheet]
                ])
    return path


if __name__ == "__main__":
    print(export_mapping())
