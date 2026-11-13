"""Strict, PII-free batch contract. Source offsets are NOT business event times."""
import hashlib
import json
import math
import re
from datetime import datetime, timedelta
from decimal import Decimal

STREAM = "synthetic_workforce_v1"
BATCH_FIELDS = frozenset({"stream", "batch_id", "events"})
EVENT_FIELDS = frozenset({
    "event_id", "source_offset", "employee_id", "source_version",
    "event_time", "operation", "department", "fte", "status",
})


class ContractError(ValueError):
    """Reject malformed or ambiguous synthetic change records."""


def validate_batch(batch):
    """Validate and return a plain canonical dict; never accept extra columns."""
    if not isinstance(batch, dict) or set(batch) != BATCH_FIELDS:
        raise ContractError("Unexpected batch envelope")
    if batch["stream"] != STREAM:
        raise ContractError("Only the synthetic stream is supported")
    if not isinstance(batch["batch_id"], str) or not re.fullmatch(r"TEST_BATCH_[0-9]{3,6}", batch["batch_id"]):
        raise ContractError("Batch ID must be synthetic")
    events = batch["events"]
    if not isinstance(events, list) or not 1 <= len(events) <= 50_000:
        raise ContractError("Event count out of bounds")
    seen_ids = set()
    offsets = []
    clean = []
    for event in events:
        if not isinstance(event, dict) or set(event) != EVENT_FIELDS:
            raise ContractError("Unexpected event fields (private columns are prohibited)")
        event_id = event["event_id"]
        employee = event["employee_id"]
        if not isinstance(event_id, str) or not re.fullmatch(r"TEST_EVT_[A-Za-z0-9_]{1,32}", event_id):
            raise ContractError("Event IDs must be fictional")
        if not isinstance(employee, str) or not re.fullmatch(r"TEST_E[A-Za-z0-9_]{1,30}", employee):
            raise ContractError("Employee IDs must be fictional")
        if event_id in seen_ids:
            raise ContractError("Duplicate event ID in batch")
        seen_ids.add(event_id)
        offset = event["source_offset"]
        version = event["source_version"]
        if type(offset) is not int or offset < 1 or type(version) is not int or version < 1:
            raise ContractError("Source offset and version must be positive integers")
        offsets.append(offset)
        timestamp = event["event_time"]
        if not isinstance(timestamp, str):
            raise ContractError("Event time must be ISO-8601 text")
        try:
            when = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ContractError("Invalid event timestamp") from exc
        if when.tzinfo is None or when.utcoffset() != timedelta(0):
            raise ContractError("Event timestamp must be UTC with an explicit offset")
        operation = event["operation"]
        if operation not in ("UPSERT", "DELETE"):
            raise ContractError("Unknown operation")
        if operation == "UPSERT":
            department = event["department"]
            fte = event["fte"]
            if not isinstance(department, str) or not department.startswith("Synthetic ") or len(department) > 80:
                raise ContractError("Use fictional department labels")
            if type(fte) not in (int, float) or not math.isfinite(fte):
                raise ContractError("FTE must be finite")
            if Decimal(str(fte)) <= 0 or Decimal(str(fte)) > 1 or Decimal(str(fte)).as_tuple().exponent < -3:
                raise ContractError("FTE must be in (0,1] with at most three decimals")
            if event["status"] not in ("Active", "OnLeave"):
                raise ContractError("Invalid synthetic workforce status")
        elif any(event[key] is not None for key in ("department", "fte", "status")):
            raise ContractError("DELETE events must omit state attributes")
        clean.append(dict(event))
    if offsets != list(range(offsets[0], offsets[0] + len(offsets))):
        raise ContractError("Offsets within a batch must be increasing and gap-free")
    return {"stream": STREAM, "batch_id": batch["batch_id"], "events": clean}


def fingerprint(batch):
    valid = validate_batch(batch)
    payload = json.dumps(valid, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
