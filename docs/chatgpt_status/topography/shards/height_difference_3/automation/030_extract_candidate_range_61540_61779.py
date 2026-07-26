#!/usr/bin/env python3
"""Extract canonical source-backed candidate rows 61540..61779 without measuring elevation.

This is a resume helper for the existing height_difference_3 task. It reuses the
validated streaming extractor in automation/020, verifies the canonical source
Git blob SHA-1, and writes a small preview plus the full requested JSONL range.
It does not create or infer any height_difference value.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

DEFAULT_ROW_START = 61540
DEFAULT_ROW_END = 61779
DEFAULT_PREVIEW_COUNT = 12
DEFAULT_EXPECTED_GIT_BLOB_SHA = "8afd1d2bac414cf0f6b9484014e7878a4ceff877"


def git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_base_extractor(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("height_difference_3_stream_extract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base extractor: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-geojson", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--base-extractor",
        type=Path,
        default=Path(__file__).with_name("020_stream_extract_security_canonical.py"),
    )
    parser.add_argument("--row-start", type=int, default=DEFAULT_ROW_START)
    parser.add_argument("--row-end", type=int, default=DEFAULT_ROW_END)
    parser.add_argument("--preview-count", type=int, default=DEFAULT_PREVIEW_COUNT)
    parser.add_argument("--expected-git-blob-sha", default=DEFAULT_EXPECTED_GIT_BLOB_SHA)
    args = parser.parse_args()

    if args.row_start < 1 or args.row_end < args.row_start:
        raise ValueError("invalid row range")
    if args.preview_count < 1:
        raise ValueError("preview-count must be positive")
    if not args.source_geojson.is_file():
        raise FileNotFoundError(args.source_geojson)
    if not args.base_extractor.is_file():
        raise FileNotFoundError(args.base_extractor)

    actual_blob_sha = git_blob_sha1(args.source_geojson)
    expected_blob_sha = str(args.expected_git_blob_sha).strip().lower()
    if expected_blob_sha and actual_blob_sha.lower() != expected_blob_sha:
        raise RuntimeError(
            f"canonical source Git blob SHA mismatch: expected={expected_blob_sha} actual={actual_blob_sha}"
        )

    base = load_base_extractor(args.base_extractor.resolve())
    result = base.stream_extract(
        args.source_geojson.resolve(),
        args.output_dir.resolve(),
        row_start=args.row_start,
        row_end=args.row_end,
    )

    expected_rows = args.row_end - args.row_start + 1
    if result.get("shard_rows_exported") != expected_rows:
        raise RuntimeError(
            f"range extraction count mismatch: expected={expected_rows} actual={result.get('shard_rows_exported')}"
        )

    export_path = Path(result["export_path"])
    preview: list[dict[str, Any]] = []
    with export_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if len(preview) >= args.preview_count:
                break
            row = json.loads(line)
            if row.get("existing_verified_height_value") is not None:
                raise RuntimeError("range extraction unexpectedly contains a height value")
            preview.append(row)

    if not preview or preview[0].get("row_no") != args.row_start:
        raise RuntimeError("preview does not begin at requested row_start")

    resume_manifest = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "purpose": "CANONICAL_RANGE_EXTRACTION_ONLY_NO_NUMERIC_MEASUREMENT",
        "row_start": args.row_start,
        "row_end": args.row_end,
        "expected_rows": expected_rows,
        "preview_count": len(preview),
        "expected_source_git_blob_sha": expected_blob_sha,
        "actual_source_git_blob_sha": actual_blob_sha,
        "source_sha256": result.get("source_sha256"),
        "canonical_identity_sha256": result.get("canonical_identity_sha256"),
        "export_path": str(export_path),
        "row_order_inference_used": False,
        "nearest_fill_used": False,
        "measurement_values_written": 0,
        "final_ready": False,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "range_extraction_resume_manifest.json").write_text(
        json.dumps(resume_manifest, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / f"candidate_preview_{args.row_start}_{args.row_end}.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "slot_id": "height_difference_3",
                "candidates": preview,
                "measurement_values_written": 0,
                "final_ready": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "ok": True,
                "row_start": args.row_start,
                "row_end": args.row_end,
                "rows": expected_rows,
                "preview_rows": [row["row_no"] for row in preview],
                "source_git_blob_sha": actual_blob_sha,
                "measurement_values_written": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
