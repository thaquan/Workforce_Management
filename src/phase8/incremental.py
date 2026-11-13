"""PostgreSQL incremental application; isolated from real HR raw/marts schemas."""
from pathlib import Path

from psycopg import OperationalError

from src.phase2.ingest import ROOT, connect_db
from src.phase8.contract import ContractError, STREAM, fingerprint, validate_batch
from src.phase8.safety import require_synthetic_target

DDL = ROOT / "sql" / "08_incremental_demo.sql"
EXPECTED_COLUMNS = {
    "stream_state": {"stream_name", "last_source_offset", "updated_at"},
    "batch_audit": {"batch_id", "stream_name", "batch_sha256", "status", "events_read",
                    "state_changes", "late_events", "watermark_after", "completed_at"},
    "employee_events": {"source_offset", "event_id", "batch_id", "employee_id", "source_version",
                        "event_time", "operation", "department", "fte", "employment_status"},
    "employee_state": {"employee_id", "source_version", "source_offset", "event_time",
                       "department", "fte", "employment_status", "deleted"},
}


def _verify_connection(conn):
    if conn.execute("SELECT current_database()").fetchone()[0] != "workforce_ci":
        raise RuntimeError("Incremental pipeline refuses non-synthetic database")


def _verify_schema(conn):
    for table, expected in EXPECTED_COLUMNS.items():
        cols = conn.execute(
            """SELECT column_name FROM information_schema.columns
               WHERE table_schema='incremental_demo' AND table_name=%s""",
            (table,),
        ).fetchall()
        if {row[0] for row in cols} != expected:
            raise RuntimeError(f"Schema drift in incremental_demo.{table}")
    for table, key in (
        ("stream_state", "stream_name"), ("batch_audit", "batch_id"),
        ("employee_events", "source_offset"), ("employee_state", "employee_id")
    ):
        primary = conn.execute(
            """SELECT a.attname
               FROM pg_constraint c
               JOIN pg_class t ON t.oid=c.conrelid
               JOIN pg_namespace n ON n.oid=t.relnamespace
               JOIN pg_attribute a ON a.attrelid=t.oid AND a.attnum=ANY(c.conkey)
               WHERE n.nspname='incremental_demo' AND t.relname=%s AND c.contype='p'""",
            (table,),
        ).fetchall()
        if [row[0] for row in primary] != [key]:
            raise RuntimeError(f"Primary key drift in incremental_demo.{table}")


def initialize_schema():
    """Safe, additive DDL for a verified disposable synthetic DB only."""
    require_synthetic_target()
    with connect_db() as conn, conn.transaction():
        _verify_connection(conn)
        conn.execute(DDL.read_text(encoding="utf-8-sig"))
        _verify_schema(conn)


def apply_batch(batch, failure_hook=None):
    """Commit rows, state and watermark atomically. Exact replay is a no-op."""
    batch = validate_batch(batch)
    digest = fingerprint(batch)
    require_synthetic_target()
    with connect_db() as conn, conn.transaction():
        _verify_connection(conn)
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('phase8_incremental_v1'))")
        _verify_schema(conn)
        row = conn.execute(
            """SELECT last_source_offset FROM incremental_demo.stream_state
               WHERE stream_name=%s FOR UPDATE""", (STREAM,)
        ).fetchone()
        if row is None:
            raise RuntimeError("Missing synthetic stream state")
        watermark = int(row[0])
        previous = conn.execute(
            "SELECT batch_sha256, watermark_after FROM incremental_demo.batch_audit WHERE batch_id=%s",
            (batch["batch_id"],),
        ).fetchone()
        if previous is not None:
            if previous[0] != digest:
                raise ContractError("Batch ID reused with a different checksum")
            return {"batch_id": batch["batch_id"], "status": "SKIPPED_UNCHANGED",
                    "events_read": len(batch["events"]), "state_changes": 0,
                    "late_events": 0, "watermark": watermark}
        first_offset = batch["events"][0]["source_offset"]
        if first_offset != watermark + 1:
            raise ContractError(
                f"Out-of-order or missing offset: expected {watermark + 1}, received {first_offset}"
            )
        conn.execute(
            """INSERT INTO incremental_demo.batch_audit(
                    batch_id,stream_name,batch_sha256,status,events_read,
                    state_changes,late_events,watermark_after)
               VALUES (%s,%s,%s,'SUCCEEDED',%s,0,0,%s)""",
            (batch["batch_id"], STREAM, digest, len(batch["events"]), watermark),
        )
        applied = late = 0
        for index, event in enumerate(batch["events"], start=1):
            old = conn.execute(
                "SELECT source_version FROM incremental_demo.employee_state WHERE employee_id=%s",
                (event["employee_id"],),
            ).fetchone()
            if old is not None and int(old[0]) == event["source_version"]:
                raise ContractError("Duplicate business version for an employee")
            conn.execute(
                """INSERT INTO incremental_demo.employee_events(
                       source_offset,event_id,batch_id,employee_id,source_version,
                       event_time,operation,department,fte,employment_status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (event["source_offset"], event["event_id"], batch["batch_id"],
                 event["employee_id"], event["source_version"], event["event_time"],
                 event["operation"], event["department"], event["fte"], event["status"]),
            )
            changed = conn.execute(
                """INSERT INTO incremental_demo.employee_state(
                       employee_id,source_version,source_offset,event_time,
                       department,fte,employment_status,deleted)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (employee_id) DO UPDATE
                   SET source_version=EXCLUDED.source_version,
                       source_offset=EXCLUDED.source_offset,
                       event_time=EXCLUDED.event_time,
                       department=EXCLUDED.department,
                       fte=EXCLUDED.fte,
                       employment_status=EXCLUDED.employment_status,
                       deleted=EXCLUDED.deleted
                   WHERE employee_state.source_version < EXCLUDED.source_version""",
                (event["employee_id"], event["source_version"], event["source_offset"],
                 event["event_time"], event["department"], event["fte"], event["status"],
                 event["operation"] == "DELETE"),
            )
            applied += changed.rowcount
            late += int(changed.rowcount == 0)
            if failure_hook is not None:
                failure_hook(index)
        watermark = batch["events"][-1]["source_offset"]
        conn.execute(
            """UPDATE incremental_demo.stream_state
               SET last_source_offset=%s, updated_at=now() WHERE stream_name=%s""",
            (watermark, STREAM),
        )
        conn.execute(
            """UPDATE incremental_demo.batch_audit
               SET state_changes=%s,late_events=%s,watermark_after=%s WHERE batch_id=%s""",
            (applied, late, watermark, batch["batch_id"]),
        )
        return {"batch_id": batch["batch_id"], "status": "APPLIED",
                "events_read": len(batch["events"]), "state_changes": applied,
                "late_events": late, "watermark": watermark}


def quality_summary():
    """Read-only invariants; do not expose employee IDs in output."""
    require_synthetic_target()
    with connect_db() as conn, conn.transaction():
        _verify_connection(conn)
        conn.execute("SET TRANSACTION READ ONLY")
        _verify_schema(conn)
        offset = conn.execute(
            "SELECT last_source_offset FROM incremental_demo.stream_state WHERE stream_name=%s",
            (STREAM,),
        ).fetchone()[0]
        event_count, max_offset = conn.execute(
            "SELECT COUNT(*),COALESCE(MAX(source_offset),0) FROM incremental_demo.employee_events"
        ).fetchone()
        batch_count, late_count = conn.execute(
            "SELECT COUNT(*),COALESCE(SUM(late_events),0) FROM incremental_demo.batch_audit"
        ).fetchone()
        active, deleted, total_fte = conn.execute(
            """SELECT COUNT(*) FILTER (WHERE NOT deleted),
                      COUNT(*) FILTER (WHERE deleted),
                      COALESCE(SUM(fte) FILTER (WHERE NOT deleted),0)
               FROM incremental_demo.employee_state"""
        ).fetchone()
        if offset != max_offset or event_count != offset:
            raise RuntimeError("Incremental watermark and audit events do not reconcile")
        if active + deleted > event_count:
            raise RuntimeError("State contains more employees than events")
        inconsistent_batches = conn.execute(
            """SELECT COUNT(*)
                 FROM incremental_demo.batch_audit b
                 WHERE b.events_read <> (
                    SELECT COUNT(*) FROM incremental_demo.employee_events e
                    WHERE e.batch_id=b.batch_id
                 )"""
        ).fetchone()[0]
        if inconsistent_batches:
            raise RuntimeError("Batch audit and event ledger counts disagree")
        mismatched_state = conn.execute(
            """WITH latest AS (
                   SELECT DISTINCT ON (employee_id)
                       employee_id, source_version, source_offset,
                       operation, department, fte, employment_status
                   FROM incremental_demo.employee_events
                   ORDER BY employee_id, source_version DESC, source_offset DESC
               )
               SELECT COUNT(*)
               FROM latest e FULL JOIN incremental_demo.employee_state s USING(employee_id)
               WHERE e.employee_id IS NULL OR s.employee_id IS NULL
                  OR e.source_version IS DISTINCT FROM s.source_version
                  OR e.source_offset IS DISTINCT FROM s.source_offset
                  OR (e.operation='DELETE') IS DISTINCT FROM s.deleted
                  OR e.department IS DISTINCT FROM s.department
                  OR e.fte IS DISTINCT FROM s.fte
                  OR e.employment_status IS DISTINCT FROM s.employment_status"""
        ).fetchone()[0]
        if mismatched_state:
            raise RuntimeError("Employee state diverged from latest event versions")
        return {
            "watermark": int(offset), "events_stored": int(event_count),
            "batches_succeeded": int(batch_count), "late_events": int(late_count),
            "active_employees": int(active), "deleted_employees": int(deleted),
            "active_fte": float(total_fte),
            "status": "PASS",
        }
