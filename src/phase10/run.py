"""Phase 10 offline synthetic cloud-readiness CLI. Defaults to read-only plan."""
import argparse
import json

from src.phase10.export import DATASET_NAME, RUNTIME, build_dataset, export_bundle, verify_bundle


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("plan", "export", "verify"), default="plan")
    args = parser.parse_args(argv)
    if args.mode == "plan":
        data, digest, watermark = build_dataset()
        result = {
            "status": "PLANNED",
            "synthetic_only": True,
            "source_digest": digest,
            "last_source_offset": watermark,
            "layer_rows": {name: len(rows) for name, rows in data.items()},
            "target": str(RUNTIME / DATASET_NAME),
        }
    elif args.mode == "export":
        result = export_bundle()
    else:
        result = verify_bundle(RUNTIME / DATASET_NAME)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
