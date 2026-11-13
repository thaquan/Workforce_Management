"""Fail-closed, verified synthetic PostgreSQL target check."""
import os

from src.phase2.ingest import connect_db, read_local_env


def require_synthetic_target():
    cfg = read_local_env()
    allowed = (
        os.environ.get("HR_PHASE8_ALLOW_WRITE") == "YES"
        and os.environ.get("HR_SYNTHETIC_DB") == "YES"
        and cfg.get("POSTGRES_DB") == "workforce_ci"
        and cfg.get("POSTGRES_HOST", "127.0.0.1") in ("127.0.0.1", "localhost")
        and str(cfg.get("POSTGRES_PORT", "5433")) == "5433"
    )
    if not allowed:
        raise RuntimeError(
            "Phase 8 writes require HR_PHASE8_ALLOW_WRITE=YES, "
            "HR_SYNTHETIC_DB=YES, local port 5433 and POSTGRES_DB=workforce_ci"
        )
    with connect_db() as conn:
        name = conn.execute("SELECT current_database()").fetchone()[0]
    if name != "workforce_ci":
        raise RuntimeError("Connected database is not the isolated workforce_ci database")
