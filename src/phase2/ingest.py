"""Atomic, audited and idempotent Excel -> PostgreSQL raw ingestion."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.phase1.phase1_profiler import load_workbook  # noqa: E402
from src.phase2.quality import SourceValidationError, normalize_and_validate  # noqa: E402
from src.phase2.schema_contract import SHEET_COLUMNS, BUSINESS_KEYS, snake_case, sql_type  # noqa: E402

DEFAULT_SOURCE = ROOT / "data" / "raw" / "HR_Workforce_Planning_Attrition_Dataset.xlsx"
REPORT_DIR = ROOT / "reports" / "phase2"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def read_local_env():
    """Use environment variables first; read only the project's private .env."""
    result = {}
    envfile = ROOT / ".env"
    if envfile.exists():
        for line in envfile.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip().strip('"').strip("'")
    result.update({key: value for key, value in os.environ.items() if key.startswith("POSTGRES_")})
    return result


def connect_db():
    cfg = read_local_env()
    password = cfg.get("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("POSTGRES_PASSWORD is missing from the private .env / environment")
    return psycopg.connect(
        host=cfg.get("POSTGRES_HOST", "127.0.0.1"),
        port=int(cfg.get("POSTGRES_PORT", "5433")),
        dbname=cfg.get("POSTGRES_DB", "workforce_dw"),
        user=cfg.get("POSTGRES_USER", "hr_etl"),
        password=password,
        autocommit=True,
        connect_timeout=10,
    )


def file_sha256(path):
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def register_batch(path, digest):
    with connect_db() as conn, conn.transaction():
        source_id = conn.execute(
            """INSERT INTO audit.source_files(original_filename, sha256, byte_size)
               VALUES (%s, %s, %s)
               ON CONFLICT (sha256) DO UPDATE SET last_seen_at = NOW()
               RETURNING source_file_id""",
            (path.name, digest, path.stat().st_size),
        ).fetchone()[0]
        batch_id = conn.execute(
            """INSERT INTO audit.load_batches(source_file_id, status)
               VALUES (%s, 'RUNNING') RETURNING batch_id""", (source_id,)
        ).fetchone()[0]
    return batch_id


def raw_table(sheet):
    return snake_case(sheet)


def ensure_tables(cursor):
    for sheet, columns in SHEET_COLUMNS.items():
        name = raw_table(sheet)
        table = sql.Identifier("raw", name)
        col_defs = [
            sql.SQL("{} {}{}").format(
                sql.Identifier(snake_case(field)),
                sql.SQL(sql_type(field)),
                sql.SQL(" NOT NULL") if field in BUSINESS_KEYS[sheet] else sql.SQL(""),
            )
            for field in columns
        ]
        primary_key = sql.SQL("PRIMARY KEY ({})").format(
            sql.SQL(", ").join(sql.Identifier(snake_case(f)) for f in BUSINESS_KEYS[sheet])
        )
        cursor.execute(
            sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
                table, sql.SQL(", ").join([*col_defs, primary_key])
            )
        )
        # CREATE IF NOT EXISTS does not validate tables created by earlier versions.
        actual_columns = cursor.execute(
            """SELECT column_name, data_type, numeric_precision, numeric_scale, is_nullable
                 FROM information_schema.columns
                WHERE table_schema='raw' AND table_name=%s
                ORDER BY ordinal_position""",
            (name,),
        ).fetchall()
        expected_columns = []
        for field in columns:
            data_type = sql_type(field)
            if data_type == "NUMERIC(20,6)":
                expected_columns.append((snake_case(field), "numeric", 20, 6,
                                         "NO" if field in BUSINESS_KEYS[sheet] else "YES"))
            elif data_type == "INTEGER":
                expected_columns.append((snake_case(field), "integer", 32, 0,
                                         "NO" if field in BUSINESS_KEYS[sheet] else "YES"))
            else:
                expected_columns.append((snake_case(field), data_type.lower(),
                                         None, None,
                                         "NO" if field in BUSINESS_KEYS[sheet] else "YES"))
        # PostgreSQL exposes NULL precision/scale for non-numeric columns.
        if actual_columns != expected_columns:
            raise RuntimeError(f"Schema drift detected in raw.{name}")
        actual_key = cursor.execute(
            """SELECT kcu.column_name
                 FROM information_schema.table_constraints AS tc
                 JOIN information_schema.key_column_usage AS kcu
                   ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                  AND tc.table_name = kcu.table_name
                WHERE tc.table_schema='raw'
                  AND tc.table_name=%s AND tc.constraint_type='PRIMARY KEY'
                ORDER BY kcu.ordinal_position""",
            (name,),
        ).fetchall()
        if tuple(x[0] for x in actual_key) != tuple(snake_case(f) for f in BUSINESS_KEYS[sheet]):
            raise RuntimeError(f"Primary key drift detected in raw.{name}")


def load_rows(cursor, normalized, failure_hook=None):
    for i, (sheet, columns) in enumerate(SHEET_COLUMNS.items(), start=1):
        table = sql.Identifier("raw", raw_table(sheet))
        column_sql = sql.SQL(", ").join(sql.Identifier(snake_case(field)) for field in columns)
        statement = sql.SQL("COPY {} ({}) FROM STDIN").format(table, column_sql)
        with cursor.copy(statement) as copy:
            for record in normalized[sheet]:
                copy.write_row(tuple(record[field] for field in columns))
        loaded = cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}").format(table)
        ).fetchone()[0]
        if loaded != len(normalized[sheet]):
            raise RuntimeError(f"Row count mismatch in {sheet}")
        if failure_hook is not None:
            failure_hook(sheet, i)


def raw_tables_match(cursor, normalized):
    """Compare full raw content, not only row counts, before skipping a batch."""
    for sheet, rows in normalized.items():
        name = raw_table(sheet)
        if cursor.execute("SELECT to_regclass(%s)", (f"raw.{name}",)).fetchone()[0] is None:
            return False
        count = cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier("raw", name))
        ).fetchone()[0]
        if count != len(rows):
            return False
        columns = SHEET_COLUMNS[sheet]
        key_fields = BUSINESS_KEYS[sheet]
        key_positions = tuple(columns.index(field) for field in key_fields)
        query = sql.SQL("SELECT {} FROM {}").format(
            sql.SQL(", ").join(sql.Identifier(snake_case(field)) for field in columns),
            sql.Identifier("raw", name),
        )
        database_rows = cursor.execute(query).fetchall()
        by_key = {tuple(row[i] for i in key_positions): row for row in database_rows}
        if len(by_key) != len(rows):
            return False
        for record in rows:
            key = tuple(record[field] for field in key_fields)
            expected_values = tuple(record[field] for field in columns)
            if by_key.get(key) != expected_values:
                return False
    return True


def log_failed_batch(batch_id, error):
    # Database messages may include source values: do not persist full exceptions.
    message = str(error) if isinstance(error, SourceValidationError) else type(error).__name__
    with connect_db() as conn, conn.transaction():
        conn.execute(
            """UPDATE audit.load_batches
               SET status='FAILED', finished_at=NOW(), error_message=%s
               WHERE batch_id=%s""", (message[:300], batch_id)
        )
        conn.execute(
            """INSERT INTO audit.quality_results(batch_id, check_id, status, affected_count, details)
               VALUES (%s,'ingestion_transaction','FAIL',1,%s::jsonb)
               ON CONFLICT (batch_id, check_id) DO NOTHING""",
            (batch_id, json.dumps({"error_class": type(error).__name__})),
        )


def record_quality(cursor, batch_id, checks):
    for check_id, status, affected_count, details in checks:
        cursor.execute(
            """INSERT INTO audit.quality_results(
                   batch_id, check_id, status, affected_count, details)
               VALUES (%s,%s,%s,%s,%s::jsonb)""",
            (batch_id, check_id, status, affected_count, json.dumps(details)),
        )


def write_public_report(batch_id, status, normalized, digest):
    counts = {raw_table(sheet): len(rows) for sheet, rows in normalized.items()}
    text = [
        "# Phase 2 — Ingestion Reconciliation",
        "",
        f"- Batch ID: {batch_id}",
        f"- Status: **{status}**",
        f"- Source checksum SHA-256: `{digest}`",
        f"- Expected row count: **{sum(counts.values()):,}**",
        "",
        "| Raw table | Source rows |",
        "|---|---:|",
        *(f"| raw.{name} | {count:,} |" for name, count in counts.items()),
        "",
        "Source workbook remains unchanged. All counts are aggregate-only.",
        "Data quality exceptions from Phase 1 remain documented and are not silently corrected.",
    ]
    (REPORT_DIR / "ingest_reconciliation.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def ingest(source=DEFAULT_SOURCE, force=False, failure_hook=None):
    source = Path(source).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Source workbook not found: {source.name}")
    digest = file_sha256(source)
    batch_id = register_batch(source, digest)
    normalized = {}
    try:
        workbook = load_workbook(source)
        if file_sha256(source) != digest:
            raise SourceValidationError("Source workbook changed while being read")
        normalized, checks = normalize_and_validate(workbook)
        expected = sum(len(rows) for rows in normalized.values())
        with connect_db() as conn, conn.transaction():
            # One transaction guarantees rollback of all 12 tables on COPY failure.
            conn.execute("SELECT pg_advisory_xact_lock(hashtext('hr_phase2_full_load'))")
            previous = conn.execute(
                """SELECT sf.sha256
                   FROM audit.load_batches b
                   JOIN audit.source_files sf ON sf.source_file_id=b.source_file_id
                   WHERE b.status='SUCCEEDED'
                   ORDER BY b.finished_at DESC, b.batch_id DESC LIMIT 1""",
            ).fetchone()
            if previous and previous[0] == digest and not force and raw_tables_match(conn, normalized):
                conn.execute(
                    """UPDATE audit.load_batches SET status='SKIPPED',
                       rows_expected=%s, rows_loaded=0, finished_at=NOW()
                       WHERE batch_id=%s""", (expected, batch_id)
                )
                return {"batch_id": batch_id, "status": "SKIPPED", "rows": expected}

            with conn.cursor() as cur:
                ensure_tables(cur)
                cur.execute(
                    sql.SQL("TRUNCATE TABLE {}").format(sql.SQL(", ").join(
                        sql.Identifier("raw", raw_table(sheet)) for sheet in SHEET_COLUMNS
                    ))
                )
                load_rows(cur, normalized, failure_hook=failure_hook)
                record_quality(cur, batch_id, [
                    ("workbook_sheet_count", "PASS", 0, {"sheets": len(SHEET_COLUMNS)}),
                    ("workbook_total_rows", "PASS", 0, {"rows": expected}),
                    *checks,
                ])
                cur.execute(
                    """UPDATE audit.load_batches
                       SET status='SUCCEEDED', rows_expected=%s, rows_loaded=%s,
                           finished_at=NOW(), error_message=NULL
                       WHERE batch_id=%s""", (expected, expected, batch_id)
                )
    except Exception as error:
        log_failed_batch(batch_id, error)
        raise
    # Report writing happens after database commit; its failure must not rewrite
    # a successful database load as FAILED in audit.load_batches.
    result = {"batch_id": batch_id, "status": "SUCCEEDED", "rows": expected}
    try:
        write_public_report(batch_id, "SUCCEEDED", normalized, digest)
    except Exception as error:
        result["report_warning"] = type(error).__name__
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--force", action="store_true",
                        help="Reload same source checksum (atomic replacement).")
    args = parser.parse_args()
    result = ingest(args.source, args.force)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
