"""Immutable Parquet micro-batches with canonical source checksums."""
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.phase8.contract import ContractError, EVENT_FIELDS, fingerprint, validate_batch

SCHEMA = pa.schema([
    ("event_id", pa.string()),
    ("source_offset", pa.int64()),
    ("employee_id", pa.string()),
    ("source_version", pa.int64()),
    ("event_time", pa.string()),
    ("operation", pa.string()),
    ("department", pa.string()),
    ("fte", pa.float64()),
    ("status", pa.string()),
])


def write_batch(batch, path):
    """Write once, never replace an existing Parquet file."""
    batch = validate_batch(batch)
    path = Path(path)
    if path.exists():
        if read_batch(path) != batch:
            raise ContractError("Immutable Parquet batch already exists with different content")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(batch["events"], schema=SCHEMA)
    metadata = {
        b"stream": batch["stream"].encode(),
        b"batch_id": batch["batch_id"].encode(),
        b"sha256": fingerprint(batch).encode(),
    }
    table = table.replace_schema_metadata(metadata)
    created = False
    try:
        with path.open("xb") as file:
            created = True
            pq.write_table(table, file, compression="zstd")
    except Exception:
        # Remove only a partial file that THIS call created, never an existing file.
        if created:
            path.unlink(missing_ok=True)
        raise
    return path


def read_batch(path):
    """Fail closed when a file's metadata, schema or contents differ."""
    table = pq.read_table(path)
    if not table.schema.remove_metadata().equals(SCHEMA):
        raise ContractError("Unexpected Parquet schema")
    meta = table.schema.metadata or {}
    if set(meta) != {b"stream", b"batch_id", b"sha256"}:
        raise ContractError("Parquet batch metadata missing or unexpected")
    try:
        batch = {
            "stream": meta[b"stream"].decode("ascii"),
            "batch_id": meta[b"batch_id"].decode("ascii"),
            "events": table.to_pylist(),
        }
    except (UnicodeDecodeError, KeyError) as error:
        raise ContractError("Invalid Parquet metadata") from error
    batch = validate_batch(batch)
    if fingerprint(batch) != meta[b"sha256"].decode("ascii"):
        raise ContractError("Parquet checksum mismatch")
    return batch
