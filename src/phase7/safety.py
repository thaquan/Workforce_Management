"""Fail-closed controls for Phase 7 database access."""
import os

from src.phase2.ingest import connect_db, read_local_env


def mode():
    value = os.getenv("HR_PHASE7_MODE", "dry_run").lower()
    if value not in ("dry_run", "synthetic"):
        raise ValueError("Phase 7 mode must be dry_run or synthetic")
    return value


def assert_disposable_target():
    """Only an explicitly approved, local synthetic database may be modified."""
    cfg = read_local_env()
    safe = (
        os.getenv("HR_PHASE7_ALLOW_WRITE") == "YES"
        and os.getenv("HR_SYNTHETIC_DB") == "YES"
        and cfg.get("POSTGRES_DB") == "workforce_ci"
        and cfg.get("POSTGRES_HOST", "127.0.0.1") in ("127.0.0.1", "localhost")
        and str(cfg.get("POSTGRES_PORT", "5433")) == "5433"
    )
    if not safe:
        raise RuntimeError(
            "Phase 7 write refused: requires HR_PHASE7_ALLOW_WRITE=YES, "
            "HR_SYNTHETIC_DB=YES, local port 5433 and POSTGRES_DB=workforce_ci"
        )
    with connect_db() as conn:
        actual = conn.execute("SELECT current_database()").fetchone()[0]
    if actual != "workforce_ci":
        raise RuntimeError("Phase 7 write refused: connected database is not workforce_ci")
