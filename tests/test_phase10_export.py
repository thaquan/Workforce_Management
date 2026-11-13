"""Offline, fictional-only lakehouse export checks."""
import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pyarrow.parquet as pq

from src.phase8.contract import ContractError
from src.phase8.fixture import batches
from src.phase10 import run
from src.phase10.export import (
    DATASET_NAME, FORMAT_VERSION, SCHEMAS, _file_sha256,
    build_dataset, export_bundle, verify_bundle,
)


class Phase10ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="phase10-test-")
        self.addCleanup(self.tmp.cleanup)
        self.runtime = Path(self.tmp.name)
        self.bundle = self.runtime / DATASET_NAME

    def export(self):
        return export_bundle(self.runtime)

    def manifest(self):
        return json.loads((self.bundle / "manifest.json").read_text(encoding="utf-8"))

    def save_manifest(self, manifest):
        (self.bundle / "manifest.json").write_text(
            json.dumps(manifest, sort_keys=True), encoding="utf-8"
        )

    def test_fictional_layers_have_expected_semantics(self):
        rows, digest, watermark = build_dataset()
        self.assertEqual(watermark, 8)
        self.assertEqual(len(digest), 64)
        self.assertEqual([len(rows[layer]) for layer in SCHEMAS], [8, 4, 2])
        state = {row["employee_id"]: row for row in rows["silver/employee_state.parquet"]}
        self.assertTrue(state["TEST_E002"]["deleted"])
        self.assertEqual(state["TEST_E001"]["source_version"], 2)
        self.assertEqual(state["TEST_E001"]["source_offset"], 4)
        self.assertFalse(state["TEST_E003"]["deleted"])
        gold = {row["department"]: row for row in rows["gold/department_current.parquet"]}
        self.assertEqual(gold["Synthetic Engineering"]["active_employees"], 2)
        self.assertEqual(gold["Synthetic Engineering"]["active_fte_milli"], 1750)
        self.assertEqual(gold["Synthetic Recruiting"]["active_fte_milli"], 800)

    def test_export_verify_and_exact_replay(self):
        first = self.export()
        self.assertEqual(first["status"], "EXPORTED")
        self.assertEqual(verify_bundle(self.bundle)["status"], "VERIFIED")
        files = [self.bundle / relative for relative in SCHEMAS]
        originals = [_file_sha256(path) for path in files]
        self.assertEqual(self.export()["status"], "UNCHANGED")
        self.assertEqual([_file_sha256(path) for path in files], originals)

    def test_manifest_is_portable_and_schema_is_pinned(self):
        self.export()
        manifest = self.manifest()
        self.assertEqual(manifest["format_version"], FORMAT_VERSION)
        self.assertIs(manifest["synthetic_only"], True)
        self.assertEqual(set(manifest["layers"]), set(SCHEMAS))
        self.assertNotIn("D:", (self.bundle / "manifest.json").read_text())
        for layer, schema in SCHEMAS.items():
            table = pq.read_table(self.bundle / layer)
            self.assertTrue(table.schema.remove_metadata().equals(schema))
            self.assertEqual(table.schema.metadata[b"synthetic_only"], b"true")
            self.assertEqual(pq.ParquetFile(self.bundle / layer).metadata.row_group(0).column(0).compression, "ZSTD")

    def test_corrupted_parquet_is_rejected_and_not_replaced(self):
        self.export()
        parquet = self.bundle / "bronze/events.parquet"
        with parquet.open("ab") as handle:
            handle.write(b"corruption")
        with self.assertRaisesRegex(ContractError, "checksum"):
            verify_bundle(self.bundle)
        before = _file_sha256(parquet)
        with self.assertRaises(ContractError):
            self.export()
        self.assertEqual(_file_sha256(parquet), before)

    def test_manifest_checksum_cannot_be_forged(self):
        self.export()
        manifest = self.manifest()
        manifest["layers"]["gold/department_current.parquet"]["rows_sha256"] = "0" * 64
        self.save_manifest(manifest)
        with self.assertRaisesRegex(ContractError, "fictional source"):
            verify_bundle(self.bundle)

    def test_schema_drift_is_rejected_even_with_fresh_file_checksum(self):
        self.export()
        layer = "silver/employee_state.parquet"
        parquet = self.bundle / layer
        table = pq.read_table(parquet).drop(["deleted"])
        pq.write_table(table, parquet, compression="zstd")
        manifest = self.manifest()
        manifest["layers"][layer]["parquet_sha256"] = _file_sha256(parquet)
        self.save_manifest(manifest)
        with self.assertRaisesRegex(ContractError, "schema"):
            verify_bundle(self.bundle)

    def test_unknown_file_is_rejected(self):
        self.export()
        (self.bundle / "other.csv").write_text("not part of this bundle", encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "unexpected bundle files"):
            verify_bundle(self.bundle)

    def test_incomplete_existing_bundle_is_not_overwritten(self):
        self.bundle.mkdir()
        marker = self.bundle / "keep_me.txt"
        marker.write_text("user-owned", encoding="utf-8")
        with self.assertRaises(ContractError):
            self.export()
        self.assertEqual(marker.read_text(encoding="utf-8"), "user-owned")

    def test_offset_gaps_are_rejected(self):
        source = copy.deepcopy(batches())
        source[1]["events"][0]["source_offset"] = 10
        with self.assertRaises(ContractError):
            build_dataset(source)

    def test_duplicate_batch_id_is_rejected(self):
        source = copy.deepcopy(batches())
        source[1]["batch_id"] = source[0]["batch_id"]
        with self.assertRaisesRegex(ContractError, "Repeated synthetic batch"):
            build_dataset(source)

    def test_duplicate_business_version_is_rejected(self):
        source = copy.deepcopy(batches())
        source[1]["events"][0]["source_version"] = 1
        with self.assertRaisesRegex(ContractError, "Repeated business version"):
            build_dataset(source)

    def test_private_or_extra_fields_are_rejected(self):
        source = copy.deepcopy(batches())
        source[0]["events"][0]["employee_name"] = "DO NOT EXPORT"
        with self.assertRaisesRegex(ContractError, "private columns"):
            build_dataset(source)

    def test_cli_plan_is_read_only(self):
        with patch.object(run, "RUNTIME", self.runtime / "absent"):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(run.main([]), 0)
        self.assertEqual(json.loads(out.getvalue())["status"], "PLANNED")
        self.assertFalse((self.runtime / "absent").exists())

    def test_cli_rejects_nonexistent_custom_output_argument(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                run.main(["--mode", "export", "--output", "private_data"])
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
