"""Optional Parquet-only speed/memory exercise; not a database benchmark."""
import argparse
import json
from pathlib import Path
import tempfile
from time import perf_counter

from src.phase2.ingest import ROOT
from src.phase8.contract import STREAM, validate_batch
from src.phase8.fixture import event
from src.phase8.parquet_batches import read_batch, write_batch


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=10_000)
    args = parser.parse_args(argv)
    if not 1 <= args.rows <= 50_000:
        parser.error("Use between 1 and 50000 invented rows")
    batch = validate_batch({
        "stream": STREAM, "batch_id": "TEST_BATCH_999",
        "events": [
            event(i, f"TEST_E{i:07d}", 1, "2025-11-01T00:00:00Z")
            for i in range(1, args.rows + 1)
        ],
    })
    runtime = ROOT / ".phase8_runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=runtime) as folder:
        path = Path(folder) / "synthetic_benchmark.parquet"
        before = perf_counter()
        write_batch(batch, path)
        write_seconds = perf_counter() - before
        bytes_written = path.stat().st_size
        before = perf_counter()
        loaded = read_batch(path)
        read_seconds = perf_counter() - before
        if len(loaded["events"]) != args.rows:
            raise RuntimeError("Parquet benchmark row count mismatch")
    print(json.dumps({
        "data": "synthetic", "rows": args.rows,
        "parquet_bytes": bytes_written,
        "write_seconds": round(write_seconds, 4),
        "read_seconds": round(read_seconds, 4),
        "note": "Parquet I/O microbenchmark, not PostgreSQL vs full-reload evidence",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
