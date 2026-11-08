"""Tiny synthetic HR fixture for an isolated PostgreSQL database, never production.

Only runs when BOTH HR_SYNTHETIC_DB=YES and POSTGRES_DB=workforce_ci.
This fixture contains invented IDs, and must never read real source workbooks.
"""
from datetime import date
import os

from psycopg import sql

from src.phase2.ingest import ROOT, connect_db, ensure_tables
from src.phase2.quality import normalize_and_validate
from src.phase2.schema_contract import SHEET_COLUMNS, snake_case


def sample_rows():
    jan, feb = date(2023, 1, 1), date(2023, 2, 1)
    data = {
        "DimEmployee": [
            dict(EmployeeID="TEST_E001", DepartmentID="TEST_D001",
                 Department="Synthetic Operations", Role="Specialist", Level="L1",
                 LocationID="TEST_L001", Location="Synthetic HQ",
                 Gender="Unknown", HireDate=date(2022, 12, 1),
                 EmploymentStatus="Active", FTE=1.0),
            dict(EmployeeID="TEST_E002", DepartmentID="TEST_D001",
                 Department="Synthetic Operations", Role="Associate", Level="L1",
                 LocationID="TEST_L001", Location="Synthetic HQ",
                 Gender="Unknown", HireDate=date(2023, 1, 3),
                 TerminationDate=date(2023, 2, 10), EmploymentStatus="Terminated",
                 TerminationType="Voluntary", FTE=1.0),
        ],
        "FactMonthlySnapshot": [
            dict(Month=jan, DepartmentID="TEST_D001", Department="Synthetic Operations",
                 LocationID="TEST_L001", Location="Synthetic HQ", Level="L1",
                 Headcount=2, FTE=2, AvgTenureMonths=5),
            dict(Month=feb, DepartmentID="TEST_D001", Department="Synthetic Operations",
                 LocationID="TEST_L001", Location="Synthetic HQ", Level="L1",
                 Headcount=1, FTE=1, AvgTenureMonths=6),
        ],
        "FactEmployeeEvents": [
            dict(EmployeeID="TEST_E001", EventDate=date(2022,12,1), EventType="Hire",
                 DepartmentID="TEST_D001", Department="Synthetic Operations",
                 LocationID="TEST_L001", Location="Synthetic HQ"),
            dict(EmployeeID="TEST_E002", EventDate=date(2023,1,3), EventType="Hire",
                 DepartmentID="TEST_D001", Department="Synthetic Operations",
                 LocationID="TEST_L001", Location="Synthetic HQ"),
            dict(EmployeeID="TEST_E002", EventDate=date(2023,2,10), EventType="Termination",
                 DepartmentID="TEST_D001", Department="Synthetic Operations",
                 LocationID="TEST_L001", Location="Synthetic HQ",
                 TerminationType="Voluntary", TerminationReason="Synthetic departure"),
        ],
        "FactCompensation": [
            dict(EmployeeID="TEST_E001", EffectiveDate=jan,
                 AnnualSalary=60000, Level="L1", Currency="EUR"),
            dict(EmployeeID="TEST_E002", EffectiveDate=date(2023,1,3),
                 AnnualSalary=40000, Level="L1", Currency="EUR"),
        ],
        "FactPerformance": [
            dict(EmployeeID="TEST_E001", ReviewDate=date(2023,1,15),
                 PerformanceRating=4, ReviewType="Annual"),
            dict(EmployeeID="TEST_E002", ReviewDate=date(2023,1,20),
                 PerformanceRating=3, ReviewType="Annual"),
        ],
        "FactEngagement": [
            dict(EmployeeID="TEST_E001", SurveyDate=date(2023,1,10),
                 EngagementScore=4, ResponseRatePct=95),
            dict(EmployeeID="TEST_E002", SurveyDate=date(2023,2,1),
                 EngagementScore=2, ResponseRatePct=80),
        ],
        "FactAbsence": [
            dict(EmployeeID="TEST_E002", AbsenceDate=date(2023,2,5),
                 AbsenceType="Sick", DaysAbsent=1),
        ],
        "FactRecruitment": [
            dict(ReqID="TEST_R001", Month=jan, DepartmentID="TEST_D001",
                 Department="Synthetic Operations", OpenRequisitions=2,
                 FilledRequisitions=1, CancelledRequisitions=0, AvgDaysToFill=20),
            dict(ReqID="TEST_R002", Month=feb, DepartmentID="TEST_D001",
                 Department="Synthetic Operations", OpenRequisitions=1,
                 FilledRequisitions=1, CancelledRequisitions=0, AvgDaysToFill=15),
        ],
        "WorkforceTargets": [
            dict(Month=jan, DepartmentID="TEST_D001", Department="Synthetic Operations",
                 PlannedHeadcount=2, BudgetedFTE=2,
                 BudgetedSalaryCost=120000, PlanningScenario="Synthetic baseline"),
            dict(Month=feb, DepartmentID="TEST_D001", Department="Synthetic Operations",
                 PlannedHeadcount=1, BudgetedFTE=1,
                 BudgetedSalaryCost=70000, PlanningScenario="Synthetic baseline"),
        ],
        "DimDepartment": [
            dict(DepartmentID="TEST_D001", Department="Synthetic Operations",
                 Function="Operations", CostCenter="TEST_CC"),
        ],
        "DimLocation": [
            dict(LocationID="TEST_L001", Location="Synthetic HQ",
                 Country="Example", Region="Synthetic", TimeZone="UTC",
                 Latitude=0, Longitude=0),
        ],
        "DimDate": [
            dict(Date=jan, Month=jan, Year=2023, Quarter="Q1",
                 MonthNumber=1, MonthName="Jan", WeekdayNumber=7),
            dict(Date=feb, Month=feb, Year=2023, Quarter="Q1",
                 MonthNumber=2, MonthName="Feb", WeekdayNumber=3),
        ],
    }
    # The normalizer checks the exact source contract, including column order.
    return {
        name: [{field: value.get(field) for field in columns} for value in data[name]]
        for name, columns in SHEET_COLUMNS.items()
    }


def seed():
    if os.getenv("HR_SYNTHETIC_DB") != "YES" or os.getenv("POSTGRES_DB") != "workforce_ci":
        raise RuntimeError("Refusing synthetic fixture: requires isolated workforce_ci + HR_SYNTHETIC_DB=YES")
    data, _ = normalize_and_validate(sample_rows())
    with connect_db() as conn:
        conn.execute((ROOT / "sql" / "00_bootstrap.sql").read_text(encoding="utf-8"))
        with conn.transaction():
            ensure_tables(conn)
            conn.execute(
                sql.SQL("TRUNCATE TABLE {}").format(sql.SQL(",").join(
                    sql.Identifier("raw", snake_case(sheet)) for sheet in SHEET_COLUMNS
                ))
            )
            for sheet, columns in SHEET_COLUMNS.items():
                target = sql.Identifier("raw", snake_case(sheet))
                cols = sql.SQL(",").join(sql.Identifier(snake_case(c)) for c in columns)
                placeholders = sql.SQL(",").join(sql.Placeholder() for _ in columns)
                query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(target, cols, placeholders)
                for row in data[sheet]:
                    conn.execute(query, tuple(row[col] for col in columns))
    print(f"Synthetic fixture loaded into isolated workforce_ci: {sum(map(len, data.values()))} rows")


if __name__ == "__main__":
    seed()
