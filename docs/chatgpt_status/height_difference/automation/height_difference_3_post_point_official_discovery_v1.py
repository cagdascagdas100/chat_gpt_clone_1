#!/usr/bin/env python3
"""Fail-closed post-point transformation and EA catalogue discovery for height_difference_3.

This script never calculates elevation. It consumes the accepted three-point
canonical output, audits coordinate semantics and PROJ grid availability, and
queries the official Environment Agency FeatureServer only when the task carries
explicit WGS84/ETRS89 epoch provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pathlib
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from typing import Any, Iterable

EXPECTED_PARCELS = ("parcel_61523", "parcel_61524", "parcel_61525")
EXPECTED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EA_ROOT = "https://environment.data.gov.uk/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/LIDAR_Tiles_Catalogues/FeatureServer"
MAX_HTTP_BYTES = 32 * 1024 * 1024
ACCEPTED_EPOCH_POLICIES = {
    "ETRS89_EQUIVALENCE_PROVEN",
    "WGS84_TO_ETRS89_TRANSFORM_PROVEN",
}


class ContractError(RuntimeError):
    """Fail-closed contract violation."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = pathlib.Path(tmp.name)
    os.replace(tmp_path, path)


def validate_points_document(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = doc.get("canonical_point_rows")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ContractError("CANONICAL_POINT_ROW_COUNT_FAILED")
    source = doc.get("source") or {}
    blob_sha = source.get("git_blob_sha") or doc.get("source_blob_sha")
    if blob_sha != EXPECTED_BLOB_SHA:
        raise ContractError("CANONICAL_BLOB_SHA_FAILED")
    observed = []
    for row in rows:
        parcel_id = row.get("parcel_id")
        geom_type = row.get("geometry_type")
        lon = row.get("longitude")
        lat = row.get("latitude")
        if parcel_id not in EXPECTED_PARCELS:
            raise ContractError("UNEXPECTED_PARCEL_ID")
        if geom_type != "Point":
            raise ContractError("CANONICAL_GEOMETRY_NOT_POINT")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ContractError("CANONICAL_COORDINATE_NOT_NUMERIC")
        if not math.isfinite(lon) or not math.isfinite(lat):
            raise ContractError("CANONICAL_COORDINATE_NOT_FINITE")
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ContractError("CANONICAL_COORDINATE_OUT_OF_RANGE")
        observed.append(parcel_id)
    if tuple(observed) != EXPECTED_PARCELS:
        raise ContractError("CANONICAL_PARCEL_ORDER_FAILED")
    if len(set(observed)) != 3:
        raise ContractError("CANONICAL_PARCEL_DUPLICATE")
    return rows


def chunks(values: list[int], size: int) -> Iterable[list[int]]:
    if size < 1:
        raise ContractError("INVALID_BATCH_SIZE")
    for index in range(0, len(values), size):
        yield values[index:index + size]


def http_json(
    url: str,
    params: dict[str, Any],
    raw_path: pathlib.Path,
    timeout_seconds: int = 60,
) -> tuple[dict[str, Any], dict[str, Any]]:
    encoded = urllib.parse.urlencode(params, doseq=True).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "AAYS-height-difference-3/1.0",
        },
    )
    started = time.time()
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        status = int(response.status)
        content_type = response.headers.get("Content-Type", "")
        data = response.read(MAX_HTTP_BYTES + 1)
    if len(data) > MAX_HTTP_BYTES:
        raise ContractError("EA_HTTP_RESPONSE_TOO_LARGE")
    if status < 200 or status >= 300:
        raise ContractError(f"EA_HTTP_STATUS_{status}")
    if "json" not in content_type.lower() and not data.lstrip().startswith((b"{", b"[")):
        raise ContractError("EA_HTTP_CONTENT_TYPE_INVALID")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(data)
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ContractError("EA_HTTP_JSON_INVALID") from exc
    if not isinstance(payload, dict):
        raise ContractError("EA_HTTP_JSON_ROOT_INVALID")
    if "error" in payload:
        error = payload.get("error") or {}
        raise ContractError(f"EA_ARCGIS_ERROR_{error.get('code', 'UNKNOWN')}")
    audit = {
        "url": url,
        "request_parameters_sha256": sha256_bytes(canonical_json_bytes(params)),
        "response_sha256": sha256_bytes(data),
        "response_bytes": len(data),
        "http_status": status,
        "content_type": content_type,
        "elapsed_seconds": round(time.time() - started, 6),
        "raw_path": raw_path.as_posix(),
    }
    return payload, audit


def layer_metadata(layer_id: int, raw_dir: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload, audit = http_json(
        f"{EA_ROOT}/{layer_id}",
        {"f": "json"},
        raw_dir / f"layer_{layer_id}_metadata.json",
    )
    if payload.get("geometryType") != "esriGeometryPolygon":
        raise ContractError(f"EA_LAYER_{layer_id}_GEOMETRY_CHANGED")
    sr = payload.get("extent", {}).get("spatialReference", {})
    wkid = sr.get("latestWkid") or sr.get("wkid")
    if wkid != 27700:
        raise ContractError(f"EA_LAYER_{layer_id}_CRS_CHANGED")
    oid_field = payload.get("objectIdField")
    if not isinstance(oid_field, str) or not oid_field:
        raise ContractError(f"EA_LAYER_{layer_id}_OID_FIELD_MISSING")
    max_count = payload.get("maxRecordCount")
    if not isinstance(max_count, int) or max_count < 1:
        raise ContractError(f"EA_LAYER_{layer_id}_MAX_RECORD_COUNT_INVALID")
    return payload, audit


def query_object_ids(
    layer_id: int,
    easting: float,
    northing: float,
    raw_dir: pathlib.Path,
    parcel_id: str,
) -> tuple[list[int], dict[str, Any]]:
    payload, audit = http_json(
        f"{EA_ROOT}/{layer_id}/query",
        {
            "f": "json",
            "where": "1=1",
            "geometry": f"{easting:.8f},{northing:.8f}",
            "geometryType": "esriGeometryPoint",
            "inSR": 27700,
            "spatialRel": "esriSpatialRelIntersects",
            "returnIdsOnly": "true",
        },
        raw_dir / parcel_id / f"layer_{layer_id}_ids.json",
    )
    ids = payload.get("objectIds")
    if ids is None:
        ids = []
    if not isinstance(ids, list) or any(not isinstance(value, int) for value in ids):
        raise ContractError(f"EA_LAYER_{layer_id}_OBJECT_IDS_INVALID")
    if len(ids) != len(set(ids)):
        raise ContractError(f"EA_LAYER_{layer_id}_OBJECT_IDS_DUPLICATE")
    return sorted(ids), audit


def query_features_by_ids(
    layer_id: int,
    object_ids: list[int],
    oid_field: str,
    max_record_count: int,
    raw_dir: pathlib.Path,
    parcel_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not object_ids:
        return [], []
    batch_size = min(max_record_count, 1000)
    all_features: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    for batch_index, batch_ids in enumerate(chunks(object_ids, batch_size), start=1):
        payload, audit = http_json(
            f"{EA_ROOT}/{layer_id}/query",
            {
                "f": "json",
                "objectIds": ",".join(str(value) for value in batch_ids),
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": 27700,
                "returnZ": "false",
                "returnM": "false",
            },
            raw_dir / parcel_id / f"layer_{layer_id}_features_{batch_index:04d}.json",
        )
        features = payload.get("features")
        if not isinstance(features, list):
            raise ContractError(f"EA_LAYER_{layer_id}_FEATURE_LIST_INVALID")
        returned_ids: list[int] = []
        for feature in features:
            attributes = feature.get("attributes") if isinstance(feature, dict) else None
            if not isinstance(attributes, dict):
                raise ContractError(f"EA_LAYER_{layer_id}_FEATURE_ATTRIBUTES_INVALID")
            value = attributes.get(oid_field)
            if not isinstance(value, int):
                raise ContractError(f"EA_LAYER_{layer_id}_FEATURE_OID_INVALID")
            returned_ids.append(value)
        if sorted(returned_ids) != sorted(batch_ids):
            raise ContractError(f"EA_LAYER_{layer_id}_FEATURE_ID_RECONCILIATION_FAILED")
        all_features.extend(features)
        audits.append(audit)
    if len(all_features) != len(object_ids):
        raise ContractError(f"EA_LAYER_{layer_id}_FEATURE_TOTAL_FAILED")
    return all_features, audits


def transformer_audit(points: list[dict[str, Any]], epoch_policy: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if epoch_policy not in ACCEPTED_EPOCH_POLICIES:
        raise ContractError("CANONICAL_POINT_CRS_EPOCH_PROVENANCE_NOT_CONFIRMED")
    try:
        import pyproj
        from pyproj.transformer import TransformerGroup
    except Exception as exc:
        raise ContractError("PYPROJ_NOT_AVAILABLE") from exc
    group = TransformerGroup("EPSG:4326", "EPSG:27700", always_xy=True, allow_ballpark=False)
    unavailable = [str(item) for item in group.unavailable_operations]
    if not group.best_available or not group.transformers:
        raise ContractError("BEST_TRANSFORMATION_UNAVAILABLE")
    transformer = group.transformers[0]
    operation_text = " ".join(
        str(value) for value in (
            transformer.description,
            transformer.definition,
            getattr(transformer, "name", ""),
        )
    ).lower()
    if "ostn15" not in operation_text and "7709" not in operation_text:
        raise ContractError("OSTN15_OPERATION_NOT_PROVEN")
    transformed = []
    for row in points:
        easting, northing = transformer.transform(row["longitude"], row["latitude"], errcheck=True)
        if not math.isfinite(easting) or not math.isfinite(northing):
            raise ContractError("TRANSFORMED_POINT_NOT_FINITE")
        if not (-100000 <= easting <= 800000 and -100000 <= northing <= 1400000):
            raise ContractError("TRANSFORMED_POINT_OUT_OF_RANGE")
        transformed.append({
            "parcel_id": row["parcel_id"],
            "longitude": row["longitude"],
            "latitude": row["latitude"],
            "easting": easting,
            "northing": northing,
            "source_crs": "RFC7946_WGS84_LONGITUDE_LATITUDE",
            "target_crs": "EPSG:27700",
        })
    audit = {
        "pyproj_version": pyproj.__version__,
        "proj_version": getattr(pyproj, "proj_version_str", None),
        "best_available": group.best_available,
        "unavailable_operations": unavailable,
        "selected_description": transformer.description,
        "selected_definition": transformer.definition,
        "selected_accuracy": transformer.accuracy,
        "epoch_policy": epoch_policy,
        "ballpark_allowed": False,
    }
    return transformed, audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-points", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--raw-dir", required=True, type=pathlib.Path)
    parser.add_argument("--epoch-policy", required=True)
    args = parser.parse_args()

    report: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "task_version": "post-point-official-discovery-v1",
        "canonical_point_rows": 0,
        "transformed_point_rows": 0,
        "dtm_candidate_rows": 0,
        "dsm_candidate_rows": 0,
        "numeric_elevation_rows": 0,
        "actual_business_data_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
        "state": "STARTED",
        "blockers": [],
    }
    try:
        doc = json.loads(args.canonical_points.read_text(encoding="utf-8"))
        points = validate_points_document(doc)
        report["canonical_point_rows"] = len(points)
        transformed, transform_audit = transformer_audit(points, args.epoch_policy)
        report["transformed_point_rows"] = len(transformed)
        report["transformation"] = transform_audit

        metadata = {}
        layer_audits = []
        for layer_id in (0, 1):
            layer, audit = layer_metadata(layer_id, args.raw_dir)
            metadata[layer_id] = layer
            layer_audits.append(audit)

        parcel_rows = []
        request_audits = list(layer_audits)
        for row in transformed:
            parcel_result = {**row, "layers": {}}
            for layer_id, label in ((0, "dtm"), (1, "dsm")):
                ids, audit = query_object_ids(
                    layer_id, row["easting"], row["northing"], args.raw_dir, row["parcel_id"]
                )
                request_audits.append(audit)
                layer = metadata[layer_id]
                features, audits = query_features_by_ids(
                    layer_id,
                    ids,
                    layer["objectIdField"],
                    layer["maxRecordCount"],
                    args.raw_dir,
                    row["parcel_id"],
                )
                request_audits.extend(audits)
                parcel_result["layers"][label] = {
                    "object_ids": ids,
                    "object_ids_sha256": sha256_bytes(canonical_json_bytes(ids)),
                    "candidate_count": len(features),
                    "features": features,
                }
            parcel_rows.append(parcel_result)

        report["parcel_rows"] = parcel_rows
        report["request_audits"] = request_audits
        report["dtm_candidate_rows"] = sum(len(row["layers"]["dtm"]["features"]) for row in parcel_rows)
        report["dsm_candidate_rows"] = sum(len(row["layers"]["dsm"]["features"]) for row in parcel_rows)
        report["state"] = "OFFICIAL_CATALOGUE_DISCOVERY_COMPLETE_NO_ELEVATION"
        atomic_write_json(args.output, report)
        return 0
    except Exception as exc:
        report["state"] = "BLOCKED_FAIL_CLOSED"
        report["blockers"] = [str(exc)]
        atomic_write_json(args.output, report)
        return 3


if __name__ == "__main__":
    sys.exit(main())
