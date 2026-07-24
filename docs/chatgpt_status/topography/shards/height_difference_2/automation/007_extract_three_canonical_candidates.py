#!/usr/bin/env python3
"""Extract exactly three canonical identity/location seeds for height_difference_2.

The committed Topography GeoJSON is parsed as a binary feature-object stream.
The file is never loaded as one JSON document. The same pass computes SHA256,
checks every feature through EOF, and rejects missing, invalid, duplicate, or
non-distinct exact target rows. Legacy point elevation values are never promoted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

ROW_START = 30762
ROW_END = 61522
EXPECTED_RANGE_COUNT = 30761
TARGET_ROWS = (ROW_START, (ROW_START + ROW_END) // 2, ROW_END)
TARGET_ROW_SET = frozenset(TARGET_ROWS)
FEATURES_ARRAY_RE = re.compile(br'"features"\s*:\s*\[')
DEFAULT_CHUNK_BYTES = 1024 * 1024


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


def _valid_exact_seed(feature: dict[str, Any]) -> dict[str, Any] | None:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        return None
    row_no = _explicit_row_no(properties)
    if row_no not in TARGET_ROW_SET:
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
        "target_row_no": row_no,
        "distance_from_target_rows": 0,
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


def _scan_binary_feature_stream(source: Path, chunk_bytes: int) -> dict[str, Any]:
    digest = hashlib.sha256()
    raw_target_occurrences = {row: 0 for row in TARGET_ROWS}
    valid_by_target: dict[int, list[dict[str, Any]]] = {row: [] for row in TARGET_ROWS}
    metrics: dict[str, Any] = {
        "parser": "binary-feature-object-stream-v2",
        "chunk_bytes": chunk_bytes,
        "source_size_bytes": source.stat().st_size,
        "features_array_found": False,
        "features_seen": 0,
        "range_features_seen": 0,
        "max_feature_object_bytes": 0,
        "full_json_load_avoided": True,
        "scanned_through_features_array_end": False,
        "sha256_same_pass": True,
    }

    with source.open("rb") as handle:
        tail = b""
        pending = b""
        found_array = False
        parsing_done = False
        root_object = bytearray()
        depth = 0
        in_string = False
        escaped = False

        while True:
            chunk = handle.read(chunk_bytes)
            if not chunk:
                break
            digest.update(chunk)

            if parsing_done:
                continue

            if not found_array:
                data = tail + chunk
                match = FEATURES_ARRAY_RE.search(data)
                if match is None:
                    tail = data[-256:]
                    continue
                pending = data[match.end():]
                found_array = True
                metrics["features_array_found"] = True
                tail = b""
            else:
                pending = chunk

            position = 0
            while position < len(pending):
                byte = pending[position]
                position += 1

                if depth == 0:
                    if byte in b" \t\r\n,":
                        continue
                    if byte == ord("]"):
                        parsing_done = True
                        metrics["scanned_through_features_array_end"] = True
                        break
                    if byte != ord("{"):
                        raise ValueError(f"Unexpected feature token byte={byte}")
                    root_object = bytearray(b"{")
                    depth = 1
                    in_string = False
                    escaped = False
                    continue

                root_object.append(byte)
                if in_string:
                    if escaped:
                        escaped = False
                    elif byte == ord("\\"):
                        escaped = True
                    elif byte == ord('"'):
                        in_string = False
                    continue

                if byte == ord('"'):
                    in_string = True
                elif byte == ord("{"):
                    depth += 1
                elif byte == ord("}"):
                    depth -= 1
                    if depth != 0:
                        continue
                    metrics["features_seen"] += 1
                    metrics["max_feature_object_bytes"] = max(
                        metrics["max_feature_object_bytes"], len(root_object)
                    )
                    try:
                        feature = json.loads(root_object.decode("utf-8"))
                    except Exception as exc:
                        raise ValueError(
                            f"Feature JSON parse failed at feature {metrics['features_seen']}: {exc}"
                        ) from exc
                    root_object = bytearray()
                    if not isinstance(feature, dict):
                        continue
                    properties = feature.get("properties")
                    row_no = _explicit_row_no(properties) if isinstance(properties, dict) else None
                    if row_no is not None and ROW_START <= row_no <= ROW_END:
                        metrics["range_features_seen"] += 1
                    if row_no in TARGET_ROW_SET:
                        raw_target_occurrences[row_no] += 1
                    seed = _valid_exact_seed(feature)
                    if seed is not None:
                        valid_by_target[seed["row_no"]].append(seed)

        if not found_array:
            raise ValueError("GeoJSON features array not found")
        if not parsing_done:
            raise ValueError("Unexpected EOF before features array end")
        if depth != 0 or in_string:
            raise ValueError("Unbalanced feature object at EOF")

    metrics["source_sha256"] = digest.hexdigest()
    return {
        "metrics": metrics,
        "raw_target_occurrences": raw_target_occurrences,
        "valid_by_target": valid_by_target,
    }


def _build_payload(source: Path, scan: dict[str, Any]) -> dict[str, Any]:
    metrics = scan["metrics"]
    raw_target_occurrences = scan["raw_target_occurrences"]
    valid_by_target = scan["valid_by_target"]

    missing_target_rows = [row for row in TARGET_ROWS if raw_target_occurrences[row] == 0]
    duplicate_target_rows = [
        row
        for row in TARGET_ROWS
        if raw_target_occurrences[row] > 1 or len(valid_by_target[row]) > 1
    ]
    invalid_target_rows = [
        row
        for row in TARGET_ROWS
        if raw_target_occurrences[row] > 0 and len(valid_by_target[row]) == 0
    ]
    selected = [
        dict(valid_by_target[row][0])
        for row in TARGET_ROWS
        if raw_target_occurrences[row] == 1 and len(valid_by_target[row]) == 1
    ]
    selected.sort(key=lambda row: row["row_no"])
    for index, row in enumerate(selected, start=1):
        row["candidate_seed_rank"] = index

    distinct_parcel_ids = len({row["parcel_id"] for row in selected}) == len(selected)
    distinct_inspire_ids = len({row["hmlr_inspire_id"] for row in selected}) == len(selected)
    exact_row_set = {row["row_no"] for row in selected} == TARGET_ROW_SET
    complete = (
        len(selected) == 3
        and exact_row_set
        and distinct_parcel_ids
        and distinct_inspire_ids
        and not missing_target_rows
        and not invalid_target_rows
        and not duplicate_target_rows
    )

    return {
        "schema_version": 3,
        "slot_id": "height_difference_2",
        "parcel_partition": {
            "start": ROW_START,
            "end": ROW_END,
            "expected_count": EXPECTED_RANGE_COUNT,
        },
        "target_rows": list(TARGET_ROWS),
        "status": (
            "THREE_EXACT_CANONICAL_CANDIDATE_SEEDS_EXTRACTED"
            if complete
            else "BLOCKED_THREE_EXACT_CANONICAL_CANDIDATE_SEEDS_NOT_FOUND"
        ),
        "source_path": str(source),
        "source_sha256": metrics["source_sha256"],
        "stream_metrics": metrics,
        "features_seen": metrics["features_seen"],
        "range_features_seen": metrics["range_features_seen"],
        "raw_target_occurrences": {
            str(row): raw_target_occurrences[row] for row in TARGET_ROWS
        },
        "missing_target_rows": missing_target_rows,
        "invalid_target_rows": invalid_target_rows,
        "duplicate_target_rows": duplicate_target_rows,
        "candidate_seed_count": len(selected),
        "candidate_seeds": selected,
        "exact_target_rows_required": True,
        "exact_target_row_set_verified": exact_row_set,
        "distinct_parcel_ids_verified": distinct_parcel_ids,
        "distinct_hmlr_inspire_ids_verified": distinct_inspire_ids,
        "explicit_row_no_required": True,
        "row_order_inference_used": False,
        "nearest_row_fallback_used": False,
        "legacy_point_topography_values_promoted": False,
        "official_polygon_measurements_written": 0,
        "next_step": (
            "MATCH_HMLR_INSPIRE_GML_POLYGONS_THEN_SAMPLE_EA_DTM1M_"
            "AND_CROSSCHECK_OS_TERRAIN50"
        ),
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def extract(source: Path, chunk_bytes: int = DEFAULT_CHUNK_BYTES) -> dict[str, Any]:
    return _build_payload(source, _scan_binary_feature_stream(source, chunk_bytes))


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--web-output", type=Path)
    parser.add_argument("--chunk-bytes", type=int, default=DEFAULT_CHUNK_BYTES)
    args = parser.parse_args(argv)

    if args.chunk_bytes < 4096:
        raise SystemExit("--chunk-bytes must be at least 4096")

    if not args.source.is_file():
        payload = {
            "schema_version": 3,
            "slot_id": "height_difference_2",
            "status": "BLOCKED_CANONICAL_TOPOGRAPHY_GEOJSON_MISSING",
            "source_path": str(args.source),
            "target_rows": list(TARGET_ROWS),
            "candidate_seed_count": 0,
            "nearest_row_fallback_used": False,
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
        payload = extract(args.source, args.chunk_bytes)
    except Exception as exc:
        payload = {
            "schema_version": 3,
            "slot_id": "height_difference_2",
            "status": "BLOCKED_CANONICAL_CANDIDATE_EXTRACTION_ERROR",
            "source_path": str(args.source),
            "target_rows": list(TARGET_ROWS),
            "error": f"{type(exc).__name__}: {exc}",
            "candidate_seed_count": 0,
            "nearest_row_fallback_used": False,
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
    ok = payload.get("status") == "THREE_EXACT_CANONICAL_CANDIDATE_SEEDS_EXTRACTED"
    print(
        json.dumps(
            {
                "ok": ok,
                "status": payload.get("status"),
                "candidates": payload.get("candidate_seed_count", 0),
            }
        )
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
