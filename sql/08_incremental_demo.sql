-- Synthetic-only demonstration. NEVER execute against workforce_dw.
CREATE SCHEMA IF NOT EXISTS incremental_demo;

CREATE TABLE IF NOT EXISTS incremental_demo.stream_state (
    stream_name TEXT PRIMARY KEY,
    last_source_offset BIGINT NOT NULL DEFAULT 0 CHECK (last_source_offset >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS incremental_demo.batch_audit (
    batch_id TEXT PRIMARY KEY,
    stream_name TEXT NOT NULL REFERENCES incremental_demo.stream_state(stream_name),
    batch_sha256 CHAR(64) NOT NULL,
    status TEXT NOT NULL CHECK (status = 'SUCCEEDED'),
    events_read INTEGER NOT NULL,
    state_changes INTEGER NOT NULL,
    late_events INTEGER NOT NULL,
    watermark_after BIGINT NOT NULL,
    completed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS incremental_demo.employee_events (
    source_offset BIGINT PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    batch_id TEXT NOT NULL REFERENCES incremental_demo.batch_audit(batch_id),
    employee_id TEXT NOT NULL,
    source_version BIGINT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('UPSERT','DELETE')),
    department TEXT,
    fte NUMERIC(6,3),
    employment_status TEXT
);

CREATE TABLE IF NOT EXISTS incremental_demo.employee_state (
    employee_id TEXT PRIMARY KEY,
    source_version BIGINT NOT NULL,
    source_offset BIGINT NOT NULL UNIQUE REFERENCES incremental_demo.employee_events(source_offset),
    event_time TIMESTAMPTZ NOT NULL,
    department TEXT,
    fte NUMERIC(6,3),
    employment_status TEXT,
    deleted BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO incremental_demo.stream_state(stream_name)
VALUES ('synthetic_workforce_v1')
ON CONFLICT (stream_name) DO NOTHING;
