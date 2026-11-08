"""Read aggregated pipeline status and alert signals from PostgreSQL audit."""
import json
from src.phase2.ingest import connect_db
from src.phase4.pipeline import bootstrap


def health_summary():
    with connect_db() as conn:
        bootstrap(conn)
        latest = conn.execute(
            """SELECT pipeline_run_id,status,run_mode,stage,started_at,finished_at
               FROM audit.pipeline_runs ORDER BY pipeline_run_id DESC LIMIT 1"""
        ).fetchone()
        counts = dict(conn.execute(
            """SELECT status,COUNT(*) FROM audit.pipeline_runs GROUP BY status"""
        ).fetchall())
        stale = conn.execute(
            """SELECT COUNT(*) FROM audit.pipeline_runs
                WHERE status='RUNNING' AND started_at < NOW()-INTERVAL '2 hours'"""
        ).fetchone()[0]
        last_load_age = conn.execute(
            """SELECT EXTRACT(EPOCH FROM (NOW()-MAX(finished_at)))/3600
                 FROM audit.load_batches WHERE status='SUCCEEDED'"""
        ).fetchone()[0]
    return {
        "latest_run_id": latest[0] if latest else None,
        "latest_run_status": latest[1] if latest else "NONE",
        "latest_run_mode": latest[2] if latest else None,
        "latest_run_stage": latest[3] if latest else None,
        "run_counts": counts,
        "running_over_2h": stale,
        "last_successful_ingest_age_hours":
            round(float(last_load_age), 2) if last_load_age is not None else None,
        "note": "Historical source periods are not used as operational freshness.",
    }


if __name__ == "__main__":
    print(json.dumps(health_summary()))
