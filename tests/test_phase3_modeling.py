"""Phase 3 project and warehouse regression checks.

Live checks are opt-in and query aggregate results only; they never export HR rows.
"""
import os
from pathlib import Path
import unittest

from src.phase2.schema_contract import SHEET_COLUMNS, snake_case


ROOT = Path(__file__).resolve().parents[1]
DBT = ROOT / "dbt_hr"


class Phase3StaticTests(unittest.TestCase):
    def test_source_to_staging_contract(self):
        sources = (DBT / "models/staging/_sources.yml").read_text(encoding="utf-8")
        for sheet in SHEET_COLUMNS:
            raw_name = snake_case(sheet)
            path = DBT / "models/staging" / f"stg_{raw_name}.sql"
            self.assertTrue(path.is_file(), path.name)
            statement = path.read_text(encoding="utf-8")
            self.assertIn(f"source('raw_hr', '{raw_name}')", statement)
            self.assertNotIn("select *", statement.lower())
            self.assertIn(f"- name: {raw_name}", sources)

    def test_required_business_marts(self):
        expected = {
            "mart_workforce_monthly", "mart_attrition_monthly",
            "mart_workforce_plan_vs_actual", "mart_recruitment_monthly",
            "mart_retention_analysis", "mart_workforce_reconciliation",
            "mart_salary_run_rate_monthly",
        }
        actual = {p.stem for p in (DBT / "models/marts/business").glob("*.sql")}
        self.assertEqual(actual, expected)

    def test_dbt_password_only_from_environment(self):
        profile = (DBT / "profiles.yml").read_text(encoding="utf-8")
        self.assertIn("env_var('POSTGRES_PASSWORD')", profile)
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in ("/dbt_hr/target/", "/dbt_hr/logs/", "/dbt_hr/.user.yml", ".env"):
            self.assertIn(pattern, ignore)

    def test_snapshot_does_not_fake_employee_grain(self):
        statement = (DBT / "models/marts/facts/fct_workforce_snapshot.sql").read_text()
        self.assertNotIn("employee_id", statement.lower())
        for field in ("month", "department_id", "location_id", "level"):
            self.assertIn(field, statement)

    def test_unverified_salary_budget_comparison_disabled(self):
        plan = (DBT / "models/marts/business/mart_workforce_plan_vs_actual.sql").read_text()
        salary = (DBT / "models/marts/business/mart_salary_run_rate_monthly.sql").read_text()
        self.assertIn("false as salary_budget_variance_enabled", plan)
        self.assertIn("false as can_compare_to_budget", salary)

    def test_retention_features_before_termination(self):
        statement = (DBT / "models/marts/business/mart_retention_analysis.sql").read_text()
        for expression in (
            "s.survey_date < e.termination_date",
            "p.review_date < e.termination_date",
            "a.absence_date < e.termination_date",
        ):
            self.assertIn(expression, statement)


@unittest.skipUnless(os.getenv("HR_PHASE3_INTEGRATION_TESTS") == "1",
                     "Set HR_PHASE3_INTEGRATION_TESTS=1 for local PostgreSQL checks")
class Phase3LiveTests(unittest.TestCase):
    def test_business_mart_counts(self):
        from src.phase2.ingest import connect_db
        expected = {
            "mart_workforce_monthly": 6826,
            "mart_attrition_monthly": 288,
            "mart_workforce_plan_vs_actual": 288,
            "mart_retention_analysis": 1200,
            "mart_recruitment_monthly": 288,
            "mart_workforce_reconciliation": 36,
            "mart_salary_run_rate_monthly": 36,
        }
        with connect_db() as conn:
            for name, count in expected.items():
                actual = conn.execute(f"SELECT COUNT(*) FROM marts.{name}").fetchone()[0]
                self.assertEqual(actual, count, name)

    def test_monthly_reconciliation(self):
        from src.phase2.ingest import connect_db
        with connect_db() as conn:
            rows = conn.execute(
                """SELECT month, headcount_difference
                   FROM marts.mart_workforce_reconciliation
                   WHERE reconciliation_status='REVIEW'"""
            ).fetchall()
        self.assertEqual(len(rows), 33)
        by_month = {m.isoformat(): difference for m, difference in rows}
        self.assertEqual(by_month["2025-06-01"], 98)
        self.assertEqual(by_month["2025-12-01"], 5)

    def test_attrition_flag_is_provisional(self):
        from src.phase2.ingest import connect_db
        with connect_db() as conn:
            counts = dict(conn.execute(
                """SELECT rate_quality_status, COUNT(*)
                   FROM marts.mart_attrition_monthly GROUP BY rate_quality_status"""
            ).fetchall())
        self.assertEqual(counts.get("NO_PRIOR_SNAPSHOT"), 8)
        self.assertEqual(counts.get("PROVISIONAL_SOURCE_MISMATCH"), 280)
        self.assertNotIn("VERIFIED", counts)

    def test_planning_totals_no_fanout(self):
        from src.phase2.ingest import connect_db
        with connect_db() as conn:
            actual = conn.execute(
                """SELECT SUM(actual_headcount), SUM(planned_headcount)
                   FROM marts.mart_workforce_plan_vs_actual
                   WHERE month=DATE '2025-12-01'"""
            ).fetchone()
        self.assertEqual(actual, (999, 1079))

    def test_extended_date_and_no_post_exit_features(self):
        from src.phase2.ingest import connect_db
        with connect_db() as conn:
            minimum = conn.execute("SELECT MIN(date) FROM marts.dim_date").fetchone()[0]
            failures = conn.execute(
                """SELECT COUNT(*) FROM marts.mart_retention_analysis
                   WHERE termination_date IS NOT NULL AND
                     (last_engagement_date >= termination_date OR
                      last_performance_date >= termination_date)"""
            ).fetchone()[0]
        self.assertEqual(minimum.isoformat(), "2018-01-05")
        self.assertEqual(failures, 0)


if __name__ == "__main__":
    unittest.main()
