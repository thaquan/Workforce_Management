"""Static checks for the PostgreSQL foundation (no server required)."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Phase2FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        cls.sql = (ROOT / "sql" / "00_bootstrap.sql").read_text(encoding="utf-8")
        cls.ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    def test_compose_is_local_only(self):
        self.assertIn("postgres:17-alpine", self.compose)
        self.assertIn('127.0.0.1:', self.compose)
        self.assertIn("pg_isready", self.compose)
        self.assertIn("postgres_data:", self.compose)
        self.assertIn("00_bootstrap.sql", self.compose)

    def test_credentials_not_hardcoded_in_compose(self):
        self.assertIn("POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?", self.compose)
        self.assertNotIn("CHANGE_ME_GENERATE_RANDOM_VALUE", self.compose)
        self.assertTrue((ROOT / ".env.example").exists())

    def test_four_schemas(self):
        for schema in ("raw", "staging", "marts", "audit"):
            self.assertRegex(self.sql, rf"(?i)CREATE\s+SCHEMA\s+IF\s+NOT\s+EXISTS\s+{schema}\s*;")

    def test_required_audit_tables(self):
        for table in ("source_files", "load_batches", "quality_results"):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS audit.{table}", self.sql)
        self.assertIn("REFERENCES audit.source_files", self.sql)
        self.assertIn("REFERENCES audit.load_batches", self.sql)
        self.assertIn("UNIQUE (batch_id, check_id)", self.sql)

    def test_idempotent_sql(self):
        self.assertEqual(self.sql.count("CREATE TABLE IF NOT EXISTS"), 3)
        self.assertEqual(self.sql.count("CREATE INDEX IF NOT EXISTS"), 2)
        self.assertIn("BEGIN;", self.sql)
        self.assertIn("COMMIT;", self.sql)

    def test_sensitive_data_excluded_from_git(self):
        self.assertRegex(self.ignore, r"(?m)^\.env$")
        self.assertIn("/data/raw/*", self.ignore)
        self.assertIn("/data/processed/", self.ignore)


if __name__ == "__main__":
    unittest.main()
