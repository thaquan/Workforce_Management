# Phase 10 - Cloud-ready Lakehouse Handoff (Synthetic Only)

Phase 10 is an **offline, reproducible data portability exercise**. It prepares a
small, versioned Bronze/Silver/Gold Parquet bundle suitable for a future manual
trial in Microsoft Fabric or AWS. It **does not** create cloud resources, upload
files, connect to a remote service, or publish a Power BI dataset.

The export reads only the checked-in fictional Phase 8 event fixture. It does
not read the HR workbook, PostgreSQL warehouse, any real employee record, or
Power BI import data. This is a *cloud-readiness prototype*, not a cloud
deployment or an operational production pipeline.

## What it delivers

| Layer | File | Meaning | Fixture rows |
|---|---|---|---:|
| Bronze | `bronze/events.parquet` | All eight immutable, ordered fictional change events | 8 |
| Silver | `silver/employee_state.parquet` | Latest **business version** per fictional employee, including a deletion tombstone | 4 |
| Gold | `gold/department_current.parquet` | Department-level active headcount and FTE in integer thousandths | 2 |

The Gold snapshot contains three active fictional employees and 2.550 FTE:
Synthetic Engineering has two active employees (1.750 FTE), and Synthetic
Recruiting has one (0.800 FTE). A late event for `TEST_E001` is intentionally
ignored for current state because its business version is older, even though
its source offset is newer. This matches the Phase 8 policy.

The `manifest.json` contains a format version, `synthetic_only` marker,
generator provenance, canonical source-batch fingerprint, high watermark, row
counts, Parquet SHA-256 digests and canonical row digests. Each Parquet schema
is explicit and carries matching lineage metadata. FTE values are stored as
**integer thousandths**, not floating-point business sums.

## Run locally (no cloud account required)

From `D:\Workforce_Management` in PowerShell, after installing the existing
Phase 8 PyArrow dependencies:

```powershell
.\.venv-phase7\Scripts\python.exe -m src.phase10.run
.\.venv-phase7\Scripts\python.exe -m src.phase10.run --mode export
.\.venv-phase7\Scripts\python.exe -m src.phase10.run --mode verify
.\.venv-phase7\Scripts\python.exe -m unittest discover -s tests -p "test_phase10_*.py" -v
```

- Default `plan` mode performs **no file writes or network connections**.
- `export` stages all three ZSTD Parquet files and the manifest in a
  temporary directory, verifies them, then publishes the bundle once under
  `.phase10_runtime/synthetic_workforce_v1/`.
- Repeating an identical export returns `UNCHANGED` without rewriting files.
- Any missing file, schema drift, unexpected file/column, altered manifest,
  modified Parquet or inconsistent source lineage causes verification to fail.
  The exporter **refuses to replace** a pre-existing invalid bundle.
- `verify` performs a full check against the known fictional source.
- Only the ignored runtime directory receives generated files. There is no
  CLI argument accepting arbitrary source or destination paths.

These output files are **not committed to Git**. Use only synthetic files for
public portfolio demos; do not upload the actual HR workbook or employee-level
source tables to any shared cloud storage.

## Option A - Microsoft Fabric (manual future extension)

1. Confirm a workspace/lakehouse and its access permissions with the owner.
2. Run the offline `verify` command before any upload.
3. Upload this **synthetic bundle** to a private Lakehouse `Files` location,
   keeping Bronze/Silver/Gold paths and the manifest together.
4. Open a Fabric notebook attached to that Lakehouse, read the Gold Parquet
   file with Spark, and validate the two department aggregates against the
   manifest before creating **new** Delta tables.
5. If a Power BI semantic model is later connected, keep it explicitly
   labelled as **synthetic scenario data**, separate from the real HR report.

For example, in a Fabric notebook with the Lakehouse attached:

```python
gold = spark.read.parquet("Files/phase10/gold/department_current.parquet")
display(gold.orderBy("department"))
```

Plain Parquet in `Files` is **not automatically a queryable Lakehouse SQL
analytics endpoint table**. Converting it to a governed Delta table is a
separate, intentional step; Phase 10 does not do that.

Official references: [Fabric Lakehouse ingestion options](https://learn.microsoft.com/en-us/fabric/data-engineering/load-data-lakehouse),
[Lakehouse API and file/table distinction](https://learn.microsoft.com/fabric/data-engineering/lakehouse-api).

## Option B - AWS S3 + Athena (manual future extension)

1. Confirm an AWS account, region, budget alert, private S3 bucket and minimal
   permissions before any upload.
2. Upload **only the verified synthetic bundle** to a private prefix; leave
   the real HR dataset and credentials local.
3. Define the three schemas explicitly in AWS Glue Data Catalog, then query
   the Parquet tables using Athena. Register the Bronze/Silver/Gold prefixes
   separately to avoid accidentally mixing records and schemas.
4. Reconcile the Gold counts/FTE to the manifest; monitor storage and query
   charges. Remove test resources through the owner's normal cloud procedure.

Official references: [Athena and AWS Glue Data Catalog](https://docs.aws.amazon.com/athena/latest/ug/data-sources-glue.html),
[Athena Parquet format](https://docs.aws.amazon.com/athena/latest/ug/parquet-serde.html).

## Architecture decision and limits

| Question | Microsoft Fabric | AWS |
|---|---|---|
| Natural next demo | OneLake Files + notebook + Delta table | Private S3 + Glue Catalog + Athena |
| Power BI continuation | Closely aligned with the existing reporting stack | Separate connection/data modelling work |
| What Phase 10 has automated | Local Parquet and manifest only | Local Parquet and manifest only |
| Cloud credentials / billing | **Not provided or used** | **Not provided or used** |

Choose a provider and authorize a specific isolated destination before adding
any upload, managed orchestration, security policies or hosted integration CI.
No Spark, Kafka, Kubernetes or continuously running cloud service is necessary
for this exercise.

**Scope limits:** Three tiny fabricated micro-batches demonstrate data contracts,
incremental snapshot semantics, replay safety and portable columnar storage.
They are not performance evidence, true production CDC, large-scale storage
benchmarks, cross-provider interoperability certification, or migration of the
real HR workbook. The generated bundle is Parquet, **not a Delta table**.
