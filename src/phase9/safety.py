"""Phase 9 connects ONLY to explicitly authorized local synthetic PostgreSQL."""
import os

from src.phase2.ingest import connect_db, read_local_env


def verify_benchmark_db():
    cfg = read_local_env()
    permitted = (
        os.getenv("HR_PHASE9_ALLOW_WRITE") == "YES"
        and os.getenv("HR_PHASE9_DISPOSABLE_ACK") == "YES"
        and os.getenv("HR_SYNTHETIC_DB") == "YES"
        and cfg.get("POSTGRES_DB") == "workforce_ci"
        and cfg.get("POSTGRES_HOST", "127.0.0.1") in ("127.0.0.1", "localhost")
        and str(cfg.get("POSTGRES_PORT", "5433")) == "5433"
    )
    if not permitted:
        raise RuntimeError(
            "Phase 9 refuses database access: require explicit disposable acknowledgement, "
            "HR_SYNTHETIC_DB=YES and localhost:5433/workforce_ci"
        )
    with connect_db() as conn:
        current = conn.execute("SELECT current_database()").fetchone()[0]
    if current != "workforce_ci":
        raise RuntimeError("Connected database is not workforce_ci")
