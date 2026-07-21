#!/usr/bin/env python3
"""Stream the canonical and legacy GeoJSON matrices into bounded internet_access_2 inputs.

The source matrices are large minified FeatureCollections. This utility reads one
feature at a time, writes only rows 30762..61522, and never creates postcodes,
parcel geometry, coverage values, business scores, or database rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

SLOT_ID = "internet_access_2"
ROW_START = 30762
ROW_END = 61522
EXPECTED_CANONICAL_ROWS = 30761


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_feature_collection(path: Path, chunk_size: int = 1024 * 1024) -> Iterator[dict[str, Any]]:
    """Yield GeoJSON features without loading the entire FeatureCollection."""
    if chunk_size < 8:
        raise ValueError("chunk_size must be at least 8 bytes")
    decoder = json.JSONDecoder()
    buffer = ""
    position = 0

    with path.open("r", encoding="utf-8-sig") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                raise ValueError(f"features array not found: {path}")
            buffer += chunk
            marker = buffer.find('"features"')
            if marker < 0:
                if len(buffer) > chunk_size * 8:
                    buffer = buffer[-chunk_size * 4:]
                continue
            colon = buffer.find(":", marker + len('"features"'))
            bracket = buffer.find("[", colon + 1) if colon >= 0 else -1
            if bracket >= 0:
                position = bracket + 1
                break

        while True:
            while position < len(buffer) and buffer[position] in " \t\r\n,":
                position += 1
            if position < len(buffer) and buffer[position] == "]":
                return

            try:
                feature, end = decoder.raw_decode(buffer, position)
            except json.JSONDecodeError:
                if position:
                    buffer = buffer[position:]
                    position = 0
                chunk = handle.read(chunk_size)
                if not chunk:
                    raise ValueError(f"truncated or invalid GeoJSON near feature boundary: {path}")
                buffer += chunk
                continue

            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                raise ValueError(f"non-Feature item in features array: {path}")
            yield feature
            position = end
            if position > chunk_size * 4:
                buffer = buffer[position:]
                position = 0


def row_no(feature: dict[str, Any]) -> int | None:
    value = (feature.get("properties") or {}).get("row_no")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parcel_id(feature: dict[str, Any]) -> str | None:
    value = (feature.get("properties") or {}).get("parcel_id")
    return str(value).strip() if value not in (None, "") else None


def review_sample(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature.get("properties") or {}
    return {
        "row_no": row_no(feature),
        "parcel_id": parcel_id(feature),
        "hmlr_inspire_id": props.get("hmlr_inspire_id"),
        "legacy_internet_level_value": props.get("internet_level_value"),
        "sample_semantics": "INPUT_EVIDENCE_ONLY_NOT_CURRENT_R2_OUTPUT",
    }


def write_filtered_geojson(
    source: Path,
    target: Path,
    *,
    require_exact_count: bool,
    chunk_size: int,
) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    row_numbers: set[int] = set()
    parcel_ids: set[str] = set()
    first_rows: list[dict[str, Any]] = []
    last_rows: list[dict[str, Any]] = []
    last_row_number: int | None = None

    with target.open("w", encoding="utf-8", newline="\n") as output:
        output.write('{"type":"FeatureCollection","features":[')
        first = True
        for feature in iter_feature_collection(source, chunk_size=chunk_size):
            number = row_no(feature)
            if number is None or number < ROW_START or number > ROW_END:
                continue
            pid = parcel_id(feature)
            if require_exact_count and not pid:
                raise ValueError(f"canonical row {number} has no parcel_id")
            if number in row_numbers:
                raise ValueError(f"duplicate row_no {number} in {source}")
            if pid and pid in parcel_ids:
                raise ValueError(f"duplicate parcel_id {pid} in {source}")
            if last_row_number is not None and number <= last_row_number:
                raise ValueError(f"non-increasing row order at {number} in {source}")
            last_row_number = number
            row_numbers.add(number)
            if pid:
                parcel_ids.add(pid)
            if not first:
                output.write(",")
            output.write(json.dumps(feature, ensure_ascii=False, separators=(",", ":")))
            first = False
            count += 1
            sample = review_sample(feature)
            if len(first_rows) < 3:
                first_rows.append(sample)
            last_rows.append(sample)
            if len(last_rows) > 3:
                last_rows.pop(0)
        output.write("]}\n")

    if require_exact_count:
        if count != EXPECTED_CANONICAL_ROWS:
            raise ValueError(f"expected {EXPECTED_CANONICAL_ROWS} canonical rows, found {count}")
        if row_numbers != set(range(ROW_START, ROW_END + 1)):
            raise ValueError("canonical slot row range has a gap")
        if len(parcel_ids) != EXPECTED_CANONICAL_ROWS:
            raise ValueError("canonical slot parcel IDs are not unique and complete")

    return {
        "source": str(source),
        "source_sha256": sha256_file(source),
        "output": str(target),
        "output_sha256": sha256_file(target),
        "rows": count,
        "unique_row_numbers": len(row_numbers),
        "unique_parcel_ids": len(parcel_ids),
        "first_rows": first_rows,
        "last_rows": last_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument("--legacy-internet", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--chunk-size", type=int, default=1024 * 1024)
    args = parser.parse_args()

    canonical_output = args.output_dir / "internet_access_2_canonical_slice_latest.geojson"
    legacy_output = args.output_dir / "internet_access_2_legacy_slice_latest.geojson"
    canonical = write_filtered_geojson(
        args.canonical, canonical_output, require_exact_count=True, chunk_size=args.chunk_size
    )
    legacy = write_filtered_geojson(
        args.legacy_internet, legacy_output, require_exact_count=False, chunk_size=args.chunk_size
    )
    manifest = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "row_partition": {"start": ROW_START, "end": ROW_END, "expected": EXPECTED_CANONICAL_ROWS},
        "canonical": canonical,
        "legacy_internet": legacy,
        "streaming_chunk_size": args.chunk_size,
        "output_semantics": "BOUNDED_INPUT_SLICE_ONLY_NO_CURRENT_R2_OR_BUSINESS_VALUES",
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "internet_access_2_stream_slice_manifest_latest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
