#!/usr/bin/env python3
"""Extract one canonical candidate range as a rollback-capable evidence bundle.

The canonical source and base extractor Git blob identities are pinned. Extraction
runs in a staging directory; the JSONL range, resume manifest and preview publish
as one transaction only after count/order/hash/no-numeric checks pass.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_ROW_START = 61540
DEFAULT_ROW_END = 61779
DEFAULT_PREVIEW_COUNT = 12
DEFAULT_EXPECTED_SOURCE_GIT_BLOB_SHA = "8afd1d2bac414cf0f6b9484014e7878a4ceff877"
DEFAULT_EXPECTED_EXTRACTOR_GIT_BLOB_SHA = "30931b747120d69fcec219a8160ddf1498c423a8"


def git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
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


def _write_json_fsync(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _publish_bundle(staged: dict[Path, Path], output_dir: Path) -> None:
    backup_dir = Path(tempfile.mkdtemp(prefix=".range_bundle_", suffix=".backup", dir=output_dir))
    moved: list[tuple[Path, Path]] = []
    published: list[Path] = []
    try:
        for target, stage in staged.items():
            if not stage.is_file() or stage.stat().st_size <= 0:
                raise ValueError(f"staged range output missing or empty: {stage}")
            if target.exists():
                backup = backup_dir / target.name
                target.replace(backup)
                moved.append((target, backup))
        try:
            for target, stage in staged.items():
                stage.replace(target)
                published.append(target)
        except Exception:
            for target in reversed(published):
                target.unlink(missing_ok=True)
            for target, backup in reversed(moved):
                if backup.exists():
                    backup.replace(target)
            raise
    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)


def _validate_jsonl(path: Path, row_start: int, row_end: int) -> tuple[list[dict[str, Any]], str]:
    expected_rows = list(range(row_start, row_end + 1))
    rows: list[dict[str, Any]] = []
    parcel_ids: set[str] = set()
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank JSONL record at line {line_no}")
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"JSONL line {line_no} is not an object")
            row_no = int(item.get("row_no"))
            parcel_id = str(item.get("parcel_id") or "").strip()
            inspire_id = str(item.get("hmlr_inspire_id") or "").strip()
            if not parcel_id or not inspire_id:
                raise ValueError(f"row {row_no} lacks parcel or INSPIRE identity")
            if parcel_id in parcel_ids:
                raise ValueError(f"duplicate parcel_id in extracted range: {parcel_id}")
            parcel_ids.add(parcel_id)
            if item.get("existing_verified_height_value") is not None:
                raise ValueError(f"row {row_no} unexpectedly contains a height value")
            rows.append(item)
    actual_rows = [int(item["row_no"]) for item in rows]
    if actual_rows != expected_rows:
        raise ValueError(f"extracted row set/order mismatch: expected={expected_rows[:3]}.. actual={actual_rows[:3]}..")
    return rows, sha256_file(path)


def run(
    source_geojson: Path,
    output_dir: Path,
    base_extractor: Path,
    *,
    row_start: int,
    row_end: int,
    preview_count: int,
    expected_source_git_blob_sha: str,
    expected_extractor_git_blob_sha: str,
) -> dict[str, Any]:
    source_geojson = source_geojson.resolve()
    base_extractor = base_extractor.resolve()
    output_dir = output_dir.resolve()
    if row_start < 1 or row_end < row_start:
        raise ValueError("invalid row range")
    expected_rows = row_end - row_start + 1
    if preview_count < 1 or preview_count > expected_rows:
        raise ValueError("preview-count must be within the requested range count")
    for label, path in (("source", source_geojson), ("base extractor", base_extractor)):
        if not path.is_file() or path.stat().st_size <= 0:
            raise FileNotFoundError(f"{label} is missing or empty: {path}")
    source_blob = git_blob_sha1(source_geojson)
    extractor_blob = git_blob_sha1(base_extractor)
    expected_source = expected_source_git_blob_sha.strip().lower()
    expected_extractor = expected_extractor_git_blob_sha.strip().lower()
    if expected_source and source_blob.lower() != expected_source:
        raise RuntimeError(f"canonical source Git blob mismatch: expected={expected_source} actual={source_blob}")
    if expected_extractor and extractor_blob.lower() != expected_extractor:
        raise RuntimeError(f"base extractor Git blob mismatch: expected={expected_extractor} actual={extractor_blob}")
    source_sha_before = sha256_file(source_geojson)
    output_dir.mkdir(parents=True, exist_ok=True)
    stage_dir = Path(tempfile.mkdtemp(prefix=".candidate_range_", suffix=".stage", dir=output_dir))
    try:
        base = load_base_extractor(base_extractor)
        result = base.stream_extract(source_geojson, stage_dir, row_start=row_start, row_end=row_end)
        if int(result.get("schema_version") or 0) < 2:
            raise ValueError("base extractor result schema is too old")
        if result.get("transactional_output_bundle") is not True:
            raise ValueError("base extractor did not report transactional output")
        if result.get("source_stability_verified") is not True:
            raise ValueError("base extractor did not verify source stability")
        if int(result.get("shard_rows_exported") or -1) != expected_rows:
            raise ValueError("base extractor range count mismatch")
        stage_shard = stage_dir / f"canonical_shard_{row_start}_{row_end}.jsonl"
        rows, export_sha = _validate_jsonl(stage_shard, row_start, row_end)
        if str(result.get("export_sha256") or "").lower() != export_sha:
            raise ValueError("base extractor export SHA-256 mismatch")
        source_sha_after = sha256_file(source_geojson)
        if source_sha_before != source_sha_after or str(result.get("source_sha256") or "").lower() != source_sha_after:
            raise ValueError("canonical source changed or hash binding failed")
        preview = rows[:preview_count]
        preview_payload = {
            "schema_version": 2,
            "slot_id": "height_difference_3",
            "purpose": "CANONICAL_RANGE_PREVIEW_NO_NUMERIC_MEASUREMENT",
            "row_start": row_start,
            "row_end": row_end,
            "candidate_count": len(preview),
            "canonical_export_sha256": export_sha,
            "candidates": preview,
            "measurement_values_written": 0,
            "final_ready": False,
            "fake_data": False,
        }
        stage_preview = stage_dir / f"candidate_preview_{row_start}_{row_end}.json"
        _write_json_fsync(stage_preview, preview_payload)
        preview_sha = sha256_file(stage_preview)
        resume_payload = {
            "schema_version": 2,
            "slot_id": "height_difference_3",
            "purpose": "CANONICAL_RANGE_EXTRACTION_ONLY_NO_NUMERIC_MEASUREMENT",
            "row_start": row_start,
            "row_end": row_end,
            "expected_rows": expected_rows,
            "preview_count": len(preview),
            "expected_source_git_blob_sha": expected_source,
            "actual_source_git_blob_sha": source_blob,
            "expected_base_extractor_git_blob_sha": expected_extractor,
            "actual_base_extractor_git_blob_sha": extractor_blob,
            "source_sha256": source_sha_after,
            "canonical_identity_sha256": result.get("canonical_identity_sha256"),
            "export_path": str(output_dir / stage_shard.name),
            "export_sha256": export_sha,
            "preview_sha256": preview_sha,
            "source_stability_verified": True,
            "transactional_output_bundle": True,
            "previous_valid_outputs_preserved_on_failure": True,
            "row_order_inference_used": False,
            "nearest_fill_used": False,
            "measurement_values_written": 0,
            "final_ready": False,
            "fake_data": False,
        }
        stage_resume = stage_dir / "range_extraction_resume_manifest.json"
        _write_json_fsync(stage_resume, resume_payload)
        final_shard = output_dir / stage_shard.name
        final_preview = output_dir / stage_preview.name
        final_resume = output_dir / stage_resume.name
        _publish_bundle(
            {final_shard: stage_shard, final_resume: stage_resume, final_preview: stage_preview},
            output_dir,
        )
        return {
            "row_start": row_start,
            "row_end": row_end,
            "rows": expected_rows,
            "preview_rows": [int(item["row_no"]) for item in preview],
            "source_git_blob_sha": source_blob,
            "base_extractor_git_blob_sha": extractor_blob,
            "export_sha256": export_sha,
            "preview_sha256": preview_sha,
            "measurement_values_written": 0,
        }
    finally:
        shutil.rmtree(stage_dir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-geojson", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--base-extractor", type=Path, default=Path(__file__).with_name("020_stream_extract_security_canonical.py"))
    parser.add_argument("--row-start", type=int, default=DEFAULT_ROW_START)
    parser.add_argument("--row-end", type=int, default=DEFAULT_ROW_END)
    parser.add_argument("--preview-count", type=int, default=DEFAULT_PREVIEW_COUNT)
    parser.add_argument("--expected-source-git-blob-sha", "--expected-git-blob-sha", dest="expected_source_git_blob_sha", default=DEFAULT_EXPECTED_SOURCE_GIT_BLOB_SHA)
    parser.add_argument("--expected-base-extractor-git-blob-sha", default=DEFAULT_EXPECTED_EXTRACTOR_GIT_BLOB_SHA)
    args = parser.parse_args()
    result = run(
        args.source_geojson, args.output_dir, args.base_extractor,
        row_start=args.row_start, row_end=args.row_end, preview_count=args.preview_count,
        expected_source_git_blob_sha=args.expected_source_git_blob_sha,
        expected_extractor_git_blob_sha=args.expected_base_extractor_git_blob_sha,
    )
    print(json.dumps({"ok": True, **result}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=os.sys.stderr)
        raise
