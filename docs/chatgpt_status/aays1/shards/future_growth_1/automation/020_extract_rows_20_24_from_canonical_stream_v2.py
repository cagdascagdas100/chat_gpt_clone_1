#!/usr/bin/env python3
"""Fail-closed streaming extractor for canonical future_growth_1 rows 20-24.

Revision 2 distinguishes the repository Git blob SHA-1 (40 hex) from the raw
file SHA-256 (64 hex). The prior revision compared a computed SHA-256 against a
Git blob SHA-1 and could never pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, BinaryIO, Iterable

SLOT_ID = "future_growth_1"
TARGET_ROWS = (20, 21, 22, 23, 24)
EXPECTED_CANONICAL_GIT_BLOB_SHA1 = "8afd1d2bac414cf0f6b9484014e7878a4ceff877"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


class ContractError(RuntimeError):
    pass


class HashingReader:
    def __init__(self, fh: BinaryIO, size_bytes: int, chunk_size: int = 1 << 16) -> None:
        self.fh = fh
        self.chunk_size = chunk_size
        self.raw_sha256 = hashlib.sha256()
        self.git_blob_sha1 = hashlib.sha1()
        self.git_blob_sha1.update(f"blob {size_bytes}\0".encode("ascii"))
        self.bytes_read = 0

    def read(self, size: int | None = None) -> bytes:
        data = self.fh.read(self.chunk_size if size is None else size)
        if data:
            self.raw_sha256.update(data)
            self.git_blob_sha1.update(data)
            self.bytes_read += len(data)
        return data


def _iter_features(reader: HashingReader) -> Iterable[dict[str, Any]]:
    decoder = json.JSONDecoder()
    buffer = ""
    pos = 0
    eof = False
    found_features = False
    array_done = False
    while not array_done:
        if not eof and len(buffer) - pos < 8192:
            chunk = reader.read()
            if chunk:
                buffer = buffer[pos:] + chunk.decode("utf-8")
                pos = 0
            else:
                eof = True
        if not found_features:
            marker = '"features"'
            idx = buffer.find(marker, pos)
            if idx < 0:
                if eof:
                    raise ContractError("features array not found")
                keep = max(0, len(buffer) - len(marker) - 8)
                buffer = buffer[keep:]
                pos = 0
                continue
            colon = buffer.find(":", idx + len(marker))
            bracket = buffer.find("[", colon + 1)
            if colon < 0 or bracket < 0:
                if eof:
                    raise ContractError("malformed features array")
                continue
            pos = bracket + 1
            found_features = True
        while True:
            while pos < len(buffer) and buffer[pos] in " \t\r\n,":
                pos += 1
            if pos < len(buffer) and buffer[pos] == "]":
                pos += 1
                array_done = True
                break
            if pos >= len(buffer):
                break
            try:
                obj, end = decoder.raw_decode(buffer, pos)
            except json.JSONDecodeError:
                if eof:
                    raise ContractError("truncated or malformed feature JSON")
                break
            if not isinstance(obj, dict) or obj.get("type") != "Feature":
                raise ContractError("non-Feature object in features array")
            yield obj
            pos = end
        if eof and not array_done:
            raise ContractError("features array did not terminate")
    while reader.read():
        pass


def _normalise_feature(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature.get("properties")
    geom = feature.get("geometry")
    if not isinstance(props, dict) or not isinstance(geom, dict):
        raise ContractError("feature missing properties or geometry")
    row_no = props.get("row_no")
    if not isinstance(row_no, int):
        raise ContractError("row_no must be integer")
    coords = geom.get("coordinates")
    if geom.get("type") != "Point" or not isinstance(coords, list) or len(coords) < 2:
        raise ContractError(f"row {row_no}: canonical geometry must be Point")
    lon, lat = coords[0], coords[1]
    if not all(isinstance(v, (int, float)) and math.isfinite(float(v)) for v in (lon, lat)):
        raise ContractError(f"row {row_no}: coordinates must be finite")
    parcel_id = props.get("parcel_id")
    hmlr_id = props.get("hmlr_inspire_id")
    if parcel_id != f"parcel_{row_no}":
        raise ContractError(f"row {row_no}: parcel_id mismatch")
    if hmlr_id in (None, ""):
        raise ContractError(f"row {row_no}: missing HMLR INSPIRE id")
    try:
        area = float(props.get("hmlr_area_m2"))
    except (TypeError, ValueError) as exc:
        raise ContractError(f"row {row_no}: invalid area") from exc
    if not math.isfinite(area) or area <= 0:
        raise ContractError(f"row {row_no}: non-positive or non-finite area")
    return {"row_no": row_no, "parcel_id": parcel_id, "hmlr_inspire_id": str(hmlr_id), "longitude": float(lon), "latitude": float(lat), "hmlr_area_m2": area, "london_authority": props.get("london_authority")}


def extract(path: Path, expected_git_blob_sha1: str, target_rows: tuple[int, ...] = TARGET_ROWS) -> dict[str, Any]:
    expected_git_blob_sha1 = expected_git_blob_sha1.strip().lower()
    if not HEX40.fullmatch(expected_git_blob_sha1):
        raise ContractError("expected Git blob SHA-1 must be 40 lowercase hex characters")
    size_bytes = path.stat().st_size
    found: dict[int, dict[str, Any]] = {}
    duplicates: list[int] = []
    feature_count = 0
    with path.open("rb") as fh:
        reader = HashingReader(fh, size_bytes)
        for feature in _iter_features(reader):
            feature_count += 1
            props = feature.get("properties") or {}
            row_no = props.get("row_no")
            if row_no in target_rows:
                if row_no in found:
                    duplicates.append(row_no)
                else:
                    found[row_no] = _normalise_feature(feature)
        canonical_sha256 = reader.raw_sha256.hexdigest()
        canonical_git_blob_sha1 = reader.git_blob_sha1.hexdigest()
        bytes_read = reader.bytes_read
    if bytes_read != size_bytes:
        raise ContractError(f"full-file scan mismatch: read={bytes_read} size={size_bytes}")
    if canonical_git_blob_sha1 != expected_git_blob_sha1:
        raise ContractError(f"canonical Git blob SHA-1 mismatch: {canonical_git_blob_sha1}")
    if duplicates:
        raise ContractError(f"duplicate target rows: {sorted(set(duplicates))}")
    missing = [row for row in target_rows if row not in found]
    if missing:
        raise ContractError(f"missing exact target rows: {missing}")
    ordered = [found[row] for row in target_rows]
    hmlr_ids = [row["hmlr_inspire_id"] for row in ordered]
    if len(set(hmlr_ids)) != len(hmlr_ids):
        raise ContractError("target HMLR INSPIRE ids are not unique")
    return {"schema_version": 2, "architecture_version": 3, "slot_id": SLOT_ID, "output_semantics": "EXACT_CANONICAL_ROWS_20_24_NOT_CANDIDATES_NOT_POLYGONS_NOT_SCORES", "canonical_path": str(path), "canonical_git_blob_sha1": canonical_git_blob_sha1, "canonical_sha256": canonical_sha256, "bytes_scanned": bytes_read, "features_scanned": feature_count, "target_rows": list(target_rows), "nearest_row_fallback_used": False, "rows": ordered, "actual_business_data_rows_written": 0, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("canonical_geojson", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument("--expected-git-blob-sha1", default=EXPECTED_CANONICAL_GIT_BLOB_SHA1)
    args = parser.parse_args()
    try:
        result = extract(args.canonical_geojson, args.expected_git_blob_sha1)
    except (ContractError, OSError, ValueError) as exc:
        print(json.dumps({"result": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": "PASS", "rows": len(result["rows"]), "git_blob_sha1": result["canonical_git_blob_sha1"], "sha256": result["canonical_sha256"], "output": str(args.output_json)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
