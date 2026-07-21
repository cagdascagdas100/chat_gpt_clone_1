#!/usr/bin/env python3
"""Extract three canonical identity/location seeds for height_difference_2.

Reads the committed program-layer Topography GeoJSON incrementally. It does not
promote the legacy point elevation values and never creates parcel geometry or
numeric measurements. Explicit row_no values are required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Iterator

ROW_START = 30762
ROW_END = 61522
EXPECTED_RANGE_COUNT = 30761
TARGET_ROWS = (ROW_START, (ROW_START + ROW_END) // 2, ROW_END)
KEEP_PER_TARGET = 12


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_feature_objects(path: Path, chunk_size: int = 1024 * 1024) -> Iterator[dict[str, Any]]:
    decoder = json.JSONDecoder()
    marker = '"features"'
    buffer = ""
    found_array = False
    eof = False
    with path.open("r", encoding="utf-8-sig") as handle:
        while True:
            if not eof and (not found_array or len(buffer) < chunk_size // 4):
                chunk = handle.read(chunk_size)
                if chunk:
                    buffer += chunk
                else:
                    eof = True
            if not found_array:
                pos = buffer.find(marker)
                if pos < 0:
                    if eof:
                        raise ValueError("GeoJSON features key not found")
                    buffer = buffer[-64:]
                    continue
                colon = buffer.find(":", pos + len(marker))
                if colon < 0:
                    if eof:
                        raise ValueError("GeoJSON features colon not found")
                    buffer = buffer[pos:]
                    continue
                bracket = buffer.find("[", colon + 1)
                if bracket < 0:
                    if eof:
                        raise ValueError("GeoJSON features array not found")
                    buffer = buffer[pos:]
                    continue
                buffer = buffer[bracket + 1 :]
                found_array = True
            buffer = buffer.lstrip()
            while buffer.startswith(","):
                buffer = buffer[1:].lstrip()
            if buffer.startswith("]"):
                return
            if not buffer:
                if eof:
                    raise ValueError("Unexpected EOF in features array")
                continue
            try:
                value, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                if eof:
                    raise
                chunk = handle.read(chunk_size)
                if chunk:
                    buffer += chunk
                else:
                    eof = True
                continue
            buffer = buffer[end:]
            if isinstance(value, dict):
                yield value


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _explicit_row_no(properties: dict[str, Any]) -> int | None:
    value = properties.get("row_no")
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _valid_seed(feature: dict[str, Any]) -> dict[str, Any] | None:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        return None
    row_no = _explicit_row_no(properties)
    if row_no is None or not (ROW_START <= row_no <= ROW_END):
        return None
    parcel_id = str(properties.get("parcel_id") or "").strip()
    inspire_id = str(properties.get("hmlr_inspire_id") or "").strip()
    if not parcel_id or not inspire_id:
        return None
    if str(properties.get("hmlr_geometry_accuracy") or "").strip() != "4/4":
        return None
    lon = _number(properties.get("hmlr_lon"))
    lat = _number(properties.get("hmlr_lat"))
    area = _number(properties.get("hmlr_area_m2"))
    if lon is None or lat is None or area is None or area <= 0:
        return None
    if not (-8.7 <= lon <= 2.1 and 49.7 <= lat <= 61.0):
        return None
    if geometry.get("type") != "Point":
        return None
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None
    glon, glat = _number(coordinates[0]), _number(coordinates[1])
    if glon is None or glat is None:
        return None
    if abs(glon - lon) > 1e-5 or abs(glat - lat) > 1e-5:
        return None
    return {
        "row_no": row_no,
        "parcel_id": parcel_id,
        "hmlr_row_id": str(properties.get("hmlr_row_id") or "").strip() or None,
        "hmlr_inspire_id": inspire_id,
        "hmlr_area_m2": area,
        "hmlr_lon": lon,
        "hmlr_lat": lat,
        "london_authority": str(properties.get("london_authority") or "").strip() or None,
        "hmlr_geometry_accuracy": "4/4",
        "source_geometry_type": "Point",
        "candidate_seed_only": True,
        "parcel_polygon_present": False,
        "measurement_eligible": False,
        "legacy_point_topography_values_discarded": True,
    }


def _insert_candidate(pool: list[tuple[int, int, dict[str, Any]]], target: int, seed: dict[str, Any]) -> None:
    pool.append((abs(seed["row_no"] - target), seed["row_no"], seed))
    pool.sort(key=lambda item: (item[0], item[1]))
    del pool[KEEP_PER_TARGET:]


def extract(source: Path) -> dict[str, Any]:
    pools: dict[int, list[tuple[int, int, dict[str, Any]]]] = {target: [] for target in TARGET_ROWS}
    features_seen = 0
    range_features_seen = 0
    valid_seed_rows_seen = 0
    for feature in _iter_feature_objects(source):
        features_seen += 1
        properties = feature.get("properties")
        if isinstance(properties, dict):
            row_no = _explicit_row_no(properties)
            if row_no is not None and ROW_START <= row_no <= ROW_END:
                range_features_seen += 1
        seed = _valid_seed(feature)
        if seed is None:
            continue
        valid_seed_rows_seen += 1
        for target in TARGET_ROWS:
            _insert_candidate(pools[target], target, seed)
    selected: list[dict[str, Any]] = []
    used_rows: set[int] = set()
    used_ids: set[str] = set()
    for target in TARGET_ROWS:
        choice = None
        for _, _, seed in pools[target]:
            if seed["row_no"] not in used_rows and seed["hmlr_inspire_id"] not in used_ids:
                choice = dict(seed)
                break
        if choice is None:
            continue
        choice["target_row_no"] = target
        choice["distance_from_target_rows"] = abs(choice["row_no"] - target)
        selected.append(choice)
        used_rows.add(choice["row_no"])
        used_ids.add(choice["hmlr_inspire_id"])
    selected.sort(key=lambda row: row["row_no"])
    for index, row in enumerate(selected, start=1):
        row["candidate_seed_rank"] = index
    complete = len(selected) == 3
    return {
        "schema_version": 1,
        "slot_id": "height_difference_2",
        "parcel_partition": {"start": ROW_START, "end": ROW_END, "expected_count": EXPECTED_RANGE_COUNT},
        "status": "THREE_CANONICAL_CANDIDATE_SEEDS_EXTRACTED" if complete else "BLOCKED_THREE_CANONICAL_CANDIDATE_SEEDS_NOT_FOUND",
        "source_path": str(source),
        "source_sha256": _sha256(source),
        "features_seen": features_seen,
        "range_features_seen": range_features_seen,
        "valid_seed_rows_seen": valid_seed_rows_seen,
        "candidate_seed_count": len(selected),
        "candidate_seeds": selected,
        "explicit_row_no_required": True,
        "row_order_inference_used": False,
        "legacy_point_topography_values_promoted": False,
        "official_polygon_measurements_written": 0,
        "next_step": "MATCH_HMLR_INSPIRE_GML_POLYGONS_THEN_SAMPLE_EA_DTM1M_AND_CROSSCHECK_OS_TERRAIN50",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--web-output", type=Path)
    args = parser.parse_args(argv)
    if not args.source.is_file():
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": "BLOCKED_CANONICAL_TOPOGRAPHY_GEOJSON_MISSING",
            "source_path": str(args.source),
            "candidate_seed_count": 0,
            "official_polygon_measurements_written": 0,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        _write(args.output, payload)
        if args.web_output:
            _write(args.web_output, payload)
        print(json.dumps({"ok": False, "status": payload["status"]}))
        return 2
    try:
        payload = extract(args.source)
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": "BLOCKED_CANONICAL_CANDIDATE_EXTRACTION_ERROR",
            "source_path": str(args.source),
            "error": f"{type(exc).__name__}: {exc}",
            "candidate_seed_count": 0,
            "official_polygon_measurements_written": 0,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    _write(args.output, payload)
    if args.web_output:
        _write(args.web_output, payload)
    ok = payload.get("status") == "THREE_CANONICAL_CANDIDATE_SEEDS_EXTRACTED"
    print(json.dumps({"ok": ok, "status": payload.get("status"), "candidates": payload.get("candidate_seed_count", 0)}))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
