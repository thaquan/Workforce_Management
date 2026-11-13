"""Three immutable synthetic micro-batches, including a late business event."""
from src.phase8.contract import STREAM, validate_batch


def event(number, employee, version, when, operation="UPSERT",
          department="Synthetic Operations", fte=1.0, status="Active"):
    if operation == "DELETE":
        department = fte = status = None
    return {
        "event_id": f"TEST_EVT_{number:04d}", "source_offset": number,
        "employee_id": employee, "source_version": version,
        "event_time": when, "operation": operation,
        "department": department, "fte": fte, "status": status,
    }


def batches():
    values = [
        {
            "batch_id": "TEST_BATCH_001",
            "events": [
                event(1, "TEST_E001", 1, "2025-10-01T00:00:00Z"),
                event(2, "TEST_E002", 1, "2025-10-02T00:00:00Z",
                      department="Synthetic Engineering", fte=0.5),
                event(3, "TEST_E003", 1, "2025-10-03T00:00:00Z",
                      department="Synthetic Engineering"),
            ],
        },
        {
            "batch_id": "TEST_BATCH_002",
            "events": [
                event(4, "TEST_E001", 2, "2025-11-01T00:00:00Z",
                      department="Synthetic Engineering"),
                event(5, "TEST_E002", 2, "2025-11-03T00:00:00Z", operation="DELETE"),
                event(6, "TEST_E004", 1, "2025-11-04T00:00:00Z",
                      department="Synthetic Recruiting", fte=0.8),
            ],
        },
        {
            "batch_id": "TEST_BATCH_003",
            "events": [
                # Higher source offset, but older business version: keep E001 v2.
                event(7, "TEST_E001", 1, "2025-10-10T00:00:00Z"),
                event(8, "TEST_E003", 2, "2025-11-10T00:00:00Z",
                      department="Synthetic Engineering", fte=0.75, status="OnLeave"),
            ],
        },
    ]
    return [
        validate_batch({"stream": STREAM, "batch_id": batch["batch_id"], "events": batch["events"]})
        for batch in values
    ]
