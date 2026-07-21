#!/usr/bin/env python3
"""Fail-closed streaming extractor for canonical future_growth_1 rows 20-24.

Reads a GeoJSON FeatureCollection incrementally, computes SHA256 during the same
full-file pass, scans through the end of the features array, and accepts only
explicit target row numbers. It never performs nearest-row fallback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, BinaryIO, Iterable

TARGET_ROWS = (20, 21, 22, 23, 24)
EXPECTED_CANONICAL_SHA = "8afd1d2bac414cf0f6b9484014e7878a4ceff877"


class ContractError(RuntimeError):
    pass


class HashingReader:
    def __init__(self, fh: BinaryIO, chunk_size: int = 1 << 16) -> None:
        self.fh = fh
        self.chunk_size = chunk_size
        self.sha = hashlib.sha256()
        self.bytes_read = 0

    def read(self, size: int | None = None) -> bytes:
        data = self.fh.read(self.chunk_size if size is None else size)
        if data:
            self.sha.update(data)
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
        if not eof and (len(buffer) - pos < 8192):
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
    area_raw = props.get("hmlr_area_m2")
    try:
        area = float(area_raw)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"row {row_no}: invalid area") from exc
    return {
        "row_no": row_no,
        "parcel_id": parcel_id,
        "hmlr_inspire_id": str(hmlr_id),
        "longitude": float(lon),
        "latitude": float(lat),
        "hmlr_area_m2": area,
        "london_authority": props.get("london_authority"),
    }


def extract(path: Path, expected_sha: str, target_rows: tuple[int, ...] = TARGET_ROWS) -> dict[str, Any]:
    found: dict[int, dict[str, Any]] = {}
    duplicates: list[int] = []
    feature_count = 0
    with path.open("rb") as fh:
        reader = HashingReader(fh)
        for feature in _iter_features(reader):
            feature_count += 1
            props = feature.get("properties") or {}
            row_no = props.get("row_no")
            if row_no in target_rows:
                if row_no in found:
                    duplicates.append(row_no)
                else:
                    found[row_no] = _normalise_feature(feature)
        actual_sha = reader.sha.hexdigest()
        bytes_read = reader.bytes_read

    if actual_sha != expected_sha:
        raise ContractError(f"canonical SHA mismatch: {actual_sha}")
    if duplicates:
        raise ContractError(f"duplicate target rows: {sorted(set(duplicates))}")
    missing = [r for r in target_rows if r not in found]
    if missing:
        raise ContractError(f"missing exact target rows: {missing}")
    ordered = [found[r] for r in target_rows]
    hmlr_ids = [r["hmlr_inspire_id"] for r in ordered]
    if len(set(hmlr_ids)) != len(hmlr_ids):
        raise ContractError("target HMLR INSPIRE ids are not unique")
    return {
        "schema_version": 1,
        "slot_id": "future_growth_1",
        "output_semantics": "EXACT_CANONICAL_ROWS_20_24_NOT_CANDIDATES_NOT_POLYGONS_NOT_SCORES",
        "canonical_path": str(path),
        "canonical_sha256": actual_sha,
        "bytes_scanned": bytes_read,
        "features_scanned": feature_count,
        "target_rows": list(target_rows),
        "nearest_row_fallback_used": False,
        "rows": ordered,
        "final_ready": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("canonical_geojson", type=Path)
    p.add_argument("output_json", type=Path)
    p.add_argument("--expected-sha", default=EXPECTED_CANONICAL_SHA)
    args = p.parse_args()
    try:
        result = extract(args.canonical_geojson, args.expected_sha)
    except ContractError as exc:
        print(json.dumps({"result": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": "PASS", "rows": len(result["rows"]), "output": str(args.output_json)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
