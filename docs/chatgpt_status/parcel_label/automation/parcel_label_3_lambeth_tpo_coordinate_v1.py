from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "parcel_label_3"
TASK_ID = "parcel-label-3-lambeth-tpo-coordinate-v1-20260803"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
POINT_SERVICE = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethTreePreservationOrderPoints/FeatureServer/0"
BOUNDARY_SERVICE = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethTreePreservationOrderBoundaries/FeatureServer/0"
GUIDANCE_URL = "https://www.lambeth.gov.uk/planning-building-control/trees/trees-private-property/tree-preservation-orders-tpos"
QUESTIONS_URL = "https://www.lambeth.gov.uk/planning-building-control/trees/trees-private-property/questions-tpos"
TERMS_URL = "https://www.lambeth.gov.uk/about-council/using-website/terms-conditions-disclaimer"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES = 1_048_576
MAX_FEATURES = 5
MAX_FIELDS = 12
POINT_DISTANCE_METRES = 25
POINTS = {
    "parcel_61523": (-0.1387938, 51.4196454),
    "parcel_61524": (-0.1407703, 51.4170637),
    "parcel_61525": (-0.1398845, 51.4167453),
}
SERVICES = (
    ("tpo_boundary", BOUNDARY_SERVICE, 0),
    ("tpo_point", POINT_SERVICE, POINT_DISTANCE_METRES),
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_points(base: Path) -> list[dict[str, Any]]:
    probe_path = base / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    rows = probe.get("canonical_points", [])
    found = {row.get("parcel_id"): row for row in rows if isinstance(row, dict) and row.get("parcel_id") in POINTS}
    if set(found) != set(POINTS):
        raise ValueError("exact target parcels missing from canonical probe")
    result: list[dict[str, Any]] = []
    for parcel_id, (expected_lon, expected_lat) in POINTS.items():
        row = found[parcel_id]
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical Point: {parcel_id}")
        if abs(lon - expected_lon) > 1e-7 or abs(lat - expected_lat) > 1e-7:
            raise ValueError(f"canonical coordinate mismatch: {parcel_id}")
        result.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return result


def open_bounded(url: str, timeout: float) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AAYS-parcel-label-evidence/1.0 bounded official-source research",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        return int(getattr(response, "status", 200)), response.geturl(), body


def safe_fields(metadata: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for field in metadata.get("fields", []):
        if not isinstance(field, dict):
            continue
        name = str(field.get("name") or "")
        ftype = str(field.get("type") or "")
        upper = name.upper()
        if not name or "GEOMETRY" in ftype.upper() or upper.startswith("SHAPE"):
            continue
        result.append(name)
        if len(result) >= MAX_FIELDS:
            break
    if not result:
        object_id = str(metadata.get("objectIdField") or "OBJECTID")
        result = [object_id]
    return result


def metadata_attempt(kind: str, service: str, timeout: float) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    url = service + "?" + urllib.parse.urlencode({"f": "pjson"})
    accessed = utcnow()
    try:
        status, final_url, body = open_bounded(url, timeout)
        parsed = json.loads(body.decode("utf-8"))
        fields = safe_fields(parsed)
        evidence = {
            "attempt_kind": "layer_metadata",
            "service_kind": kind,
            "source_url": final_url,
            "accessed_at": accessed,
            "content_sha256": sha256_bytes(body),
            "sha256_basis": "bounded_official_json_response_bytes",
            "record_scope": f"one bounded official Lambeth {kind} layer metadata request; maximum 1 MiB",
            "supports_fields": ["layer name", "geometry type", "object ID field", "query capability", *fields],
            "relevant_record_ids_or_excerpt": json.dumps({
                "name": parsed.get("name"),
                "geometryType": parsed.get("geometryType"),
                "objectIdField": parsed.get("objectIdField"),
                "selected_fields": fields,
            }, ensure_ascii=False, separators=(",", ":")),
            "terms_or_license_urls": [TERMS_URL, OGL_URL],
            "http_status": status,
            "requests_made": 1,
        }
        return parsed, evidence
    except Exception as exc:
        error = f"LAMBETH_TPO_METADATA_ERROR:{type(exc).__name__}:{exc}"
        return None, {
            "attempt_kind": "layer_metadata",
            "service_kind": kind,
            "source_url": url,
            "accessed_at": accessed,
            "content_sha256": sha256_bytes(error.encode("utf-8")),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": f"one bounded official Lambeth {kind} layer metadata request; maximum 1 MiB",
            "supports_fields": ["official layer metadata availability"],
            "relevant_record_ids_or_excerpt": error,
            "terms_or_license_urls": [TERMS_URL, OGL_URL],
            "http_status": None,
            "requests_made": 0,
        }


def query_attempt(
    kind: str,
    service: str,
    distance_metres: int,
    point: dict[str, Any],
    metadata: dict[str, Any] | None,
    timeout: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    parcel_id = point["parcel_id"]
    accessed = utcnow()
    fields = safe_fields(metadata or {})
    params: dict[str, str] = {
        "where": "1=1",
        "geometry": f"{point['longitude']},{point['latitude']}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": ",".join(fields),
        "returnGeometry": "false",
        "resultRecordCount": str(MAX_FEATURES),
        "f": "json",
    }
    if distance_metres:
        params["distance"] = str(distance_metres)
        params["units"] = "esriSRUnit_Meter"
    url = service + "/query?" + urllib.parse.urlencode(params)
    try:
        status, final_url, body = open_bounded(url, timeout)
        parsed = json.loads(body.decode("utf-8"))
        features = parsed.get("features", []) if isinstance(parsed, dict) else []
        candidates: list[dict[str, Any]] = []
        for feature in features[:MAX_FEATURES]:
            attrs = feature.get("attributes", {}) if isinstance(feature, dict) else {}
            candidates.append({
                "parcel_id": parcel_id,
                "canonical_point": point,
                "source_layer": kind,
                "source_url": final_url,
                "attributes": {key: attrs.get(key) for key in fields if key in attrs},
                "context_only": True,
                "exact_parcel_binding": False,
                "property_type_binding": False,
            })
        evidence = {
            "attempt_kind": "coordinate_query",
            "service_kind": kind,
            "parcel_id": parcel_id,
            "canonical_point": point,
            "source_url": final_url,
            "accessed_at": accessed,
            "content_sha256": sha256_bytes(body),
            "sha256_basis": "bounded_official_json_response_bytes",
            "record_scope": (
                f"one bounded official Lambeth {kind} coordinate query; maximum {MAX_FEATURES} features, "
                f"1 MiB response and {distance_metres}m distance" if distance_metres else
                f"one bounded official Lambeth {kind} exact-point intersection query; maximum {MAX_FEATURES} features and 1 MiB response"
            ),
            "supports_fields": fields,
            "relevant_record_ids_or_excerpt": json.dumps({"feature_count": len(features[:MAX_FEATURES]), "selected_fields": fields}, separators=(",", ":")),
            "terms_or_license_urls": [TERMS_URL, OGL_URL],
            "http_status": status,
            "requests_made": 1,
        }
        return candidates, evidence
    except Exception as exc:
        error = f"LAMBETH_TPO_COORDINATE_ERROR:{type(exc).__name__}:{exc}"
        return [], {
            "attempt_kind": "coordinate_query",
            "service_kind": kind,
            "parcel_id": parcel_id,
            "canonical_point": point,
            "source_url": url,
            "accessed_at": accessed,
            "content_sha256": sha256_bytes(error.encode("utf-8")),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": (
                f"one bounded official Lambeth {kind} coordinate query; maximum {MAX_FEATURES} features, "
                f"1 MiB response and {distance_metres}m distance" if distance_metres else
                f"one bounded official Lambeth {kind} exact-point intersection query; maximum {MAX_FEATURES} features and 1 MiB response"
            ),
            "supports_fields": fields,
            "relevant_record_ids_or_excerpt": error,
            "terms_or_license_urls": [TERMS_URL, OGL_URL],
            "http_status": None,
            "requests_made": 0,
        }


def build_payload(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    metadata_by_kind: dict[str, dict[str, Any] | None] = {}
    evidence: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for kind, service, _distance in SERVICES:
        metadata, record = metadata_attempt(kind, service, timeout)
        metadata_by_kind[kind] = metadata
        evidence.append(record)
    for kind, service, distance in SERVICES:
        for point in points:
            found, record = query_attempt(kind, service, distance, point, metadata_by_kind[kind], timeout)
            rows.extend(found)
            evidence.append(record)
    completed = len(evidence)
    target = 8
    if completed != target:
        raise ValueError(f"unexpected evidence count {completed}/{target}")
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": utcnow(),
        "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if rows else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": target,
        "previous_percent": 0.0,
        "progress_percent": completed / target * 100.0,
        "percent_increase": completed / target * 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": len(rows),
        "candidate_rows": rows,
        "source_evidence": evidence,
        "blocker": {
            "code": None if rows else "LAMBETH_TPO_NO_USABLE_RESPONSE_OR_NO_POINT_MATCH",
            "state": "NONE" if rows else "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_TPO_COORDINATE",
        "point_service_url": POINT_SERVICE,
        "boundary_service_url": BOUNDARY_SERVICE,
        "guidance_url": GUIDANCE_URL,
        "questions_url": QUESTIONS_URL,
        "terms_url": TERMS_URL,
        "open_government_licence_url": OGL_URL,
        "login_or_api_key_used": False,
        "bulk_download_performed": False,
        "full_dataset_scan_performed": False,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate(base: Path) -> None:
    points = load_points(base)
    if len(points) != 3:
        raise ValueError("target count mismatch")
    if len(SERVICES) != 2 or MAX_FEATURES != 5 or MAX_BYTES != 1_048_576:
        raise ValueError("bounded configuration mismatch")
    if not all(url.startswith("https://gis.lambeth.gov.uk/arcgis/rest/services/") for _, url, _ in SERVICES):
        raise ValueError("unofficial service URL")
    print("PASS_TARGET_8_LAMBETH_TPO_2_METADATA_PLUS_6_COORDINATE_QUERIES_MAX5_EACH_MAX1MIB_CONTEXT_ONLY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    base = repo_root()
    validate(base)
    if args.validate_only:
        return 0
    payload = build_payload(load_points(base), max(1.0, min(args.timeout, 30.0)))
    atomic_write(base / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_tpo_coordinate_result_latest.json", payload)
    atomic_write(base / "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_tpo_coordinate_latest.json", payload)
    if payload["produced_candidate_rows"]:
        print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_8_OF_8")
    else:
        print("PASS_NO_DATA_CONTINUE_8_OF_8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
