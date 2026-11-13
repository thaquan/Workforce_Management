"""Immutable Bronze/Silver/Gold Parquet handoff from Phase 8 fictional events.

This module has no database, network, workbook or Power BI integration.
"""
import hashlib
import json
import tempfile
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.phase8.contract import ContractError, STREAM, fingerprint, validate_batch
from src.phase8.fixture import batches


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / ".phase10_runtime"
DATASET_NAME = "synthetic_workforce_v1"
FORMAT_VERSION = 1

SCHEMAS = {
    "bronze/events.parquet": pa.schema([
        ("event_id", pa.string()), ("batch_id", pa.string()),
        ("source_offset", pa.int64()), ("employee_id", pa.string()),
        ("source_version", pa.int64()), ("event_time_utc", pa.string()),
        ("operation", pa.string()), ("department", pa.string()),
        ("fte_milli", pa.int32()), ("employment_status", pa.string()),
    ]),
    "silver/employee_state.parquet": pa.schema([
        ("employee_id", pa.string()), ("source_version", pa.int64()),
        ("source_offset", pa.int64()), ("department", pa.string()),
        ("fte_milli", pa.int32()), ("employment_status", pa.string()),
        ("deleted", pa.bool_()),
    ]),
    "gold/department_current.parquet": pa.schema([
        ("department", pa.string()), ("active_employees", pa.int64()),
        ("active_fte_milli", pa.int64()),
    ]),
}


def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _milli(value):
    return None if value is None else int(Decimal(str(value)) * 1000)


def build_dataset(source_batches=None):
    """Build exact fictional rows, keeping Phase 8 source-version semantics."""
    source_batches = batches() if source_batches is None else source_batches
    if not isinstance(source_batches, list) or not source_batches:
        raise ContractError("Expected nonempty fictional source batches")

    source_fingerprints = []
    batch_ids = set()
    events = []
    states = {}
    expected_offset = 1
    for raw in source_batches:
        batch = validate_batch(raw)
        if batch["batch_id"] in batch_ids:
            raise ContractError("Repeated synthetic batch ID")
        batch_ids.add(batch["batch_id"])
        source_fingerprints.append(fingerprint(batch))
        for event in batch["events"]:
            if event["source_offset"] != expected_offset:
                raise ContractError("Source offsets must be globally contiguous from 1")
            expected_offset += 1
            employee_id = event["employee_id"]
            current = states.get(employee_id)
            if current and event["source_version"] == current["source_version"]:
                raise ContractError("Repeated business version for employee")
            events.append({
                "event_id": event["event_id"],
                "batch_id": batch["batch_id"],
                "source_offset": event["source_offset"],
                "employee_id": employee_id,
                "source_version": event["source_version"],
                "event_time_utc": event["event_time"],
                "operation": event["operation"],
                "department": event["department"],
                "fte_milli": _milli(event["fte"]),
                "employment_status": event["status"],
            })
            if current is None or event["source_version"] > current["source_version"]:
                states[employee_id] = {
                    "employee_id": employee_id,
                    "source_version": event["source_version"],
                    "source_offset": event["source_offset"],
                    "department": event["department"],
                    "fte_milli": _milli(event["fte"]),
                    "employment_status": event["status"],
                    "deleted": event["operation"] == "DELETE",
                }

    silver = sorted(states.values(), key=lambda row: row["employee_id"])
    group = defaultdict(lambda: [0, 0])
    for row in silver:
        if row["deleted"]:
            continue
        group[row["department"]][0] += 1
        group[row["department"]][1] += row["fte_milli"]
    gold = [
        {"department": department, "active_employees": value[0],
         "active_fte_milli": value[1]}
        for department, value in sorted(group.items())
    ]
    data = {
        "bronze/events.parquet": events,
        "silver/employee_state.parquet": silver,
        "gold/department_current.parquet": gold,
    }
    source_digest = _sha256(_json_bytes(source_fingerprints))
    return data, source_digest, expected_offset - 1


def _metadata(layer, digest):
    return {
        b"format_version": str(FORMAT_VERSION).encode("ascii"),
        b"synthetic_only": b"true",
        b"source_stream": STREAM.encode("ascii"),
        b"source_digest": digest.encode("ascii"),
        b"layer": layer.encode("ascii"),
    }


def _manifest(data, digest, watermark, bundle):
    entries = {}
    for layer, rows in data.items():
        entries[layer] = {
            "rows": len(rows),
            "parquet_sha256": _file_sha256(bundle / layer),
            "rows_sha256": _sha256(_json_bytes(rows)),
        }
    return {
        "format_version": FORMAT_VERSION,
        "synthetic_only": True,
        "source_stream": STREAM,
        "source_generator": "src.phase8.fixture:batches",
        "source_digest": digest,
        "last_source_offset": watermark,
        "layers": entries,
    }


def verify_bundle(bundle):
    """Verify exact schema, manifest, Parquet hash and fictional content."""
    bundle = Path(bundle)
    if not bundle.is_dir() or bundle.is_symlink():
        raise ContractError("Missing or unsafe bundle directory")
    manifest_file = bundle / "manifest.json"
    if not manifest_file.is_file() or manifest_file.is_symlink():
        raise ContractError("Missing manifest")
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ContractError("Invalid JSON manifest") from exc
    expected, digest, watermark = build_dataset()
    if not isinstance(manifest, dict) or set(manifest) != {
        "format_version", "synthetic_only", "source_stream", "source_generator",
        "source_digest", "last_source_offset", "layers",
    }:
        raise ContractError("Unexpected manifest keys")
    if (manifest["format_version"] != FORMAT_VERSION
            or manifest["synthetic_only"] is not True
            or manifest["source_stream"] != STREAM
            or manifest["source_generator"] != "src.phase8.fixture:batches"
            or manifest["source_digest"] != digest
            or manifest["last_source_offset"] != watermark
            or not isinstance(manifest["layers"], dict)
            or set(manifest["layers"]) != set(SCHEMAS)):
        raise ContractError("Manifest does not match the fictional source contract")

    found_files = {
        path.relative_to(bundle).as_posix() for path in bundle.rglob("*") if path.is_file()
    }
    if found_files != set(SCHEMAS) | {"manifest.json"}:
        raise ContractError("Missing or unexpected bundle files")
    for layer, schema in SCHEMAS.items():
        path = bundle / layer
        if path.is_symlink() or path.parent.is_symlink():
            raise ContractError("Symlinked Parquet is not allowed")
        metadata = manifest["layers"][layer]
        if not isinstance(metadata, dict) or set(metadata) != {
            "rows", "parquet_sha256", "rows_sha256",
        }:
            raise ContractError("Unexpected layer metadata")
        if metadata["parquet_sha256"] != _file_sha256(path):
            raise ContractError("Parquet checksum mismatch")
        table = pq.read_table(path)
        if not table.schema.remove_metadata().equals(schema):
            raise ContractError("Parquet schema mismatch")
        if table.schema.metadata != _metadata(layer, digest):
            raise ContractError("Parquet lineage metadata mismatch")
        rows = table.to_pylist()
        if (metadata["rows"] != len(expected[layer])
                or metadata["rows_sha256"] != _sha256(_json_bytes(expected[layer]))
                or rows != expected[layer]):
            raise ContractError("Parquet rows differ from the fictional source")
    return {
        "status": "VERIFIED",
        "source_stream": STREAM,
        "last_source_offset": watermark,
        "layer_rows": {name: len(rows) for name, rows in expected.items()},
        "path": str(bundle),
    }


def export_bundle(runtime=RUNTIME):
    """Stage and publish once; never replace or mutate an existing bundle."""
    runtime = Path(runtime)
    if runtime.is_symlink():
        raise ContractError("Runtime directory cannot be a symlink")
    data, digest, watermark = build_dataset()
    destination = runtime / DATASET_NAME
    if destination.exists() or destination.is_symlink():
        verified = verify_bundle(destination)
        verified["status"] = "UNCHANGED"
        return verified
    runtime.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".phase10-stage-", dir=runtime) as temp:
        stage = Path(temp)
        for layer, rows in data.items():
            path = stage / layer
            path.parent.mkdir(parents=True, exist_ok=True)
            table = pa.Table.from_pylist(rows, schema=SCHEMAS[layer])
            table = table.replace_schema_metadata(_metadata(layer, digest))
            pq.write_table(table, path, compression="zstd")
        manifest = _manifest(data, digest, watermark, stage)
        (stage / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        verify_bundle(stage)
        if destination.exists() or destination.is_symlink():
            raise ContractError("Bundle was created concurrently; refusing overwrite")
        stage.rename(destination)
    verified = verify_bundle(destination)
    verified["status"] = "EXPORTED"
    return verified
