"""Run dbt from the project venv while reading local, ignored PostgreSQL secrets."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
DBT_DIR = ROOT / "dbt_hr"


def dbt_executable():
    executable = ROOT / ".venv" / ("Scripts/dbt.exe" if os.name == "nt" else "bin/dbt")
    if not executable.exists():
        raise RuntimeError("Local dbt is missing. Create .venv and install dbt-core/dbt-postgres.")
    return executable


def environment():
    cfg = os.environ.copy()
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            cfg.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    if not cfg.get("POSTGRES_PASSWORD"):
        raise RuntimeError("POSTGRES_PASSWORD missing. Configure the ignored .env file.")
    return cfg


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m src.phase3.dbt_runner debug|parse|build|test|docs generate")
    cmd = [
        str(dbt_executable()), *sys.argv[1:],
        "--project-dir", str(DBT_DIR),
        "--profiles-dir", str(DBT_DIR),
    ]
    raise SystemExit(subprocess.run(cmd, cwd=ROOT, env=environment(), check=False).returncode)


if __name__ == "__main__":
    main()
