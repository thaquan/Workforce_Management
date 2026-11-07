"""Run both Phase 1 audits and the regression suite from any working directory."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable

for name in ("phase1_profiler.py", "review_fixes.py"):
    print(f"Running {name}...", flush=True)
    subprocess.run([PYTHON, str(ROOT / "src" / "phase1" / name)],
                   cwd=ROOT, check=True)

print("Running Phase 1 regression tests...", flush=True)
subprocess.run([
    PYTHON, "-m", "unittest", "discover",
    "-s", str(ROOT / "tests"), "-p", "test_phase1_review.py", "-v"
], cwd=ROOT, check=True)
print("Phase 1 checks completed successfully.", flush=True)
