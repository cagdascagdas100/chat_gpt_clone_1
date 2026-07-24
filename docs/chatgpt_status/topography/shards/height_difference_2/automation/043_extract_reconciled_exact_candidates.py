#!/usr/bin/env python3
"""Fail-closed exact candidate reconciliation for the existing F-host runner.

The canonical security Point collection is streamed through its complete features
array.  The same pass computes SHA-256 and Git blob SHA-1, validates the exact
feature count, and extracts only ordinals 30762, 46142 and 61522.  Previously
verified HMLR IDs are used only as deterministic seeds; the next stage must
re-download official HMLR GML and revalidate exact ID plus point-in-polygon.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "height_difference_2"
EXPECTED_GIT_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EXPECTED_FEATURE_COUNT = 92283
TARGET_ROWS = (30762, 46142, 61522)
TARGET_SET = frozenset(TARGET_ROWS)
FEATURES_RE = re.compile(br'"features"\s*:\s*\[')
DEFAULT_CHUNK_BYTES = 1024 * 1024


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: numeric value required") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name}: finite value required")
    return number


def _stream_points(source: Path, chunk_bytes: int) -> dict[str, Any]:
    size = source.stat().st_size
    git_sha = hashlib.sha1()
    git_sha.update(f"blob {size}\0".encode("ascii"))
    sha256 = hashlib.sha256()
    points: dict[int, dict[str, Any]] = {}
    metrics = {
        "parser": "binary-feature-object-stream-ordinal-v1",
        "source_size_bytes": size,
        "chunk_bytes": chunk_bytes,
        "features_array_found": False,
        "features_seen": 0,
        "scanned_through_features_array_end": False,
        "full_json_load_avoided": True,
        "sha256_same_pass": True,
        "git_blob_sha1_same_pass": True,
        "max_feature_object_bytes": 0,
    }
    tail = b""
    pending = b""
    found_array = False
    parsing_done = False
    depth = 0
    in_string = False
    escaped = False
    current = bytearray()

    with source.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_bytes)
            if not chunk:
                break
            git_sha.update(chunk)
            sha256.update(chunk)
            if parsing_done:
                continue
            if not found_array:
                data = tail + chunk
                match = FEATURES_RE.search(data)
                if match is None:
                    tail = data[-256:]
                    continue
                found_array = True
                metrics["features_array_found"] = True
                pending = data[match.end():]
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
                        raise ValueError(f"unexpected feature token byte={byte}")
                    current = bytearray(b"{")
                    depth = 1
                    in_string = False
                    escaped = False
                    continue
                current.append(byte)
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
                    ordinal = int(metrics["features_seen"])
                    metrics["max_feature_object_bytes"] = max(metrics["max_feature_object_bytes"], len(current))
                    if ordinal in TARGET_SET:
                        feature = json.loads(current.decode("utf-8"))
                        properties = feature.get("properties")
                        geometry = feature.get("geometry")
                        expected_id = f"parcel_{ordinal}"
                        if not isinstance(properties, dict) or properties.get("security_parcel_id") != expected_id:
                            raise ValueError(f"ordinal/security ID mismatch at {ordinal}")
                        if not isinstance(geometry, dict) or geometry.get("type") != "Point":
                            raise ValueError(f"Point geometry required at {ordinal}")
                        coordinates = geometry.get("coordinates")
                        if not isinstance(coordinates, list) or len(coordinates) != 2:
                            raise ValueError(f"two coordinates required at {ordinal}")
                        lon = _finite(coordinates[0], f"longitude {ordinal}")
                        lat = _finite(coordinates[1], f"latitude {ordinal}")
                        if not (-9 <= lon <= 3 and 49 <= lat <= 61):
                            raise ValueError(f"GB coordinate range failed at {ordinal}")
                        points[ordinal] = {"row_no": ordinal, "parcel_id": expected_id, "longitude": lon, "latitude": lat}
                    current = bytearray()

    if not found_array:
        raise ValueError("GeoJSON features array not found")
    if not parsing_done or depth != 0 or in_string:
        raise ValueError("features array did not terminate cleanly")
    metrics["source_sha256"] = sha256.hexdigest()
    metrics["source_git_blob_sha"] = git_sha.hexdigest()
    return {"metrics": metrics, "points": points}


def _load_rows(path: Path, label: str) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"{label}: rows array required")
    indexed: dict[int, dict[str, Any]] = {}
    for value in rows:
        if not isinstance(value, dict):
            raise ValueError(f"{label}: row object required")
        row_no = int(value["row_no"])
        if row_no in indexed:
            raise ValueError(f"{label}: duplicate row {row_no}")
        indexed[row_no] = dict(value)
    return payload, indexed


def reconcile(source: Path, point_evidence: Path, hmlr_evidence: Path, chunk_bytes: int) -> dict[str, Any]:
    scan = _stream_points(source, chunk_bytes)
    metrics = scan["metrics"]
    points: dict[int, dict[str, Any]] = scan["points"]
    if metrics["source_git_blob_sha"] != EXPECTED_GIT_BLOB_SHA:
        raise ValueError(f"canonical Git blob mismatch: {metrics['source_git_blob_sha']}")
    if metrics["features_seen"] != EXPECTED_FEATURE_COUNT:
        raise ValueError(f"canonical feature count mismatch: {metrics['features_seen']}")
    if set(points) != TARGET_SET:
        raise ValueError(f"exact target Point set mismatch: {sorted(points)}")

    point_payload, point_rows = _load_rows(point_evidence, "point evidence")
    hmlr_payload, hmlr_rows = _load_rows(hmlr_evidence, "HMLR evidence")
    if point_payload.get("source_git_blob_sha") != EXPECTED_GIT_BLOB_SHA:
        raise ValueError("point evidence source blob mismatch")
    if int(point_payload.get("source_feature_count", -1)) != EXPECTED_FEATURE_COUNT:
        raise ValueError("point evidence feature count mismatch")
    if set(point_rows) != TARGET_SET or set(hmlr_rows) != TARGET_SET:
        raise ValueError("evidence target row set mismatch")

    seeds: list[dict[str, Any]] = []
    inspire_ids: set[str] = set()
    for rank, row_no in enumerate(TARGET_ROWS, start=1):
        extracted = points[row_no]
        point = point_rows[row_no]
        hmlr = hmlr_rows[row_no]
        if point.get("parcel_id") != extracted["parcel_id"] or hmlr.get("parcel_id") != extracted["parcel_id"]:
            raise ValueError(f"parcel identity mismatch at {row_no}")
        if abs(float(point["longitude"]) - extracted["longitude"]) > 1e-9 or abs(float(point["latitude"]) - extracted["latitude"]) > 1e-9:
            raise ValueError(f"point evidence coordinate mismatch at {row_no}")
        if hmlr.get("unique_native_polygon_match") is not True or int(hmlr.get("match_count", 0)) != 1:
            raise ValueError(f"prior HMLR unique-match evidence missing at {row_no}")
        inspire_id = str(hmlr.get("hmlr_inspire_id") or "").strip()
        authority = str(hmlr.get("authority") or "").strip()
        matches = hmlr.get("matches")
        if not inspire_id or not authority or not isinstance(matches, list) or len(matches) != 1:
            raise ValueError(f"prior HMLR seed fields missing at {row_no}")
        match = matches[0]
        if not isinstance(match, dict) or match.get("point_in_polygon") is not True:
            raise ValueError(f"prior HMLR point-in-polygon evidence missing at {row_no}")
        if str(match.get("hmlr_inspire_id") or "").strip() != inspire_id:
            raise ValueError(f"prior HMLR ID mismatch at {row_no}")
        if inspire_id in inspire_ids:
            raise ValueError("duplicate HMLR INSPIRE ID")
        inspire_ids.add(inspire_id)
        seeds.append({
            "row_no": row_no,
            "target_row_no": row_no,
            "distance_from_target_rows": 0,
            "parcel_id": extracted["parcel_id"],
            "hmlr_row_id": None,
            "hmlr_inspire_id": inspire_id,
            "hmlr_area_m2": _finite(match.get("geometry_area_m2"), f"HMLR area {row_no}"),
            "hmlr_lon": extracted["longitude"],
            "hmlr_lat": extracted["latitude"],
            "london_authority": authority,
            "hmlr_download_url": str(hmlr.get("download_url") or "").strip(),
            "hmlr_zip_name": str(hmlr.get("zip_name") or "").strip(),
            "hmlr_geometry_accuracy": "4/4",
            "source_geometry_type": "Point",
            "candidate_seed_rank": rank,
            "candidate_seed_only": True,
            "parcel_polygon_present": False,
            "measurement_eligible": False,
            "legacy_point_topography_values_discarded": True,
            "prior_hmlr_id_used_as_seed_only": True,
            "fresh_official_gml_revalidation_required": True,
        })

    return {
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "status": "THREE_EXACT_RECONCILED_CANDIDATE_SEEDS_READY_FOR_FRESH_HMLR_REVALIDATION",
        "source_path": str(source),
        "source_git_blob_sha": metrics["source_git_blob_sha"],
        "source_sha256": metrics["source_sha256"],
        "source_feature_count": metrics["features_seen"],
        "stream_metrics": metrics,
        "target_rows": list(TARGET_ROWS),
        "candidate_seed_count": len(seeds),
        "candidate_seeds": seeds,
        "point_evidence_path": str(point_evidence),
        "hmlr_seed_evidence_path": str(hmlr_evidence),
        "hmlr_seed_evidence_sha256": hashlib.sha256(hmlr_evidence.read_bytes()).hexdigest(),
        "exact_target_row_set_verified": True,
        "distinct_parcel_ids_verified": True,
        "distinct_hmlr_inspire_ids_verified": True,
        "row_order_inference_used": False,
        "nearest_row_fallback_used": False,
        "fresh_official_gml_revalidation_required": True,
        "official_polygon_measurements_written": 0,
        "actual_business_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--point-evidence", type=Path, required=True)
    parser.add_argument("--hmlr-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--web-output", type=Path)
    parser.add_argument("--chunk-bytes", type=int, default=DEFAULT_CHUNK_BYTES)
    args = parser.parse_args(argv)
    try:
        if args.chunk_bytes < 4096:
            raise ValueError("chunk size must be at least 4096 bytes")
        for path in (args.source, args.point_evidence, args.hmlr_evidence):
            if not path.is_file() or path.stat().st_size == 0:
                raise FileNotFoundError(path)
        payload = reconcile(args.source, args.point_evidence, args.hmlr_evidence, args.chunk_bytes)
        code = 0
    except Exception as exc:
        payload = {
            "schema_version": 4,
            "slot_id": SLOT_ID,
            "status": "BLOCKED_RECONCILED_EXACT_CANDIDATE_EXTRACTION",
            "error": f"{type(exc).__name__}: {exc}",
            "candidate_seed_count": 0,
            "target_rows": list(TARGET_ROWS),
            "nearest_row_fallback_used": False,
            "actual_business_rows_written": 0,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "final_ready": False,
        }
        code = 2
    _write(args.output, payload)
    if args.web_output:
        _write(args.web_output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"], "candidates": payload.get("candidate_seed_count", 0)}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
