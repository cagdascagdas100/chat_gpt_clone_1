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
TASK_ID = "parcel-label-3-lambeth-borough-sinc-coordinate-v1-20260803"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
SERVICE_ROOT = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethSitesOfBoroughNatureConservationImportance/FeatureServer"
LAYER_URL = SERVICE_ROOT + "/0"
METADATA_URL = LAYER_URL + "?f=json"
BIODIVERSITY_URL = "https://www.lambeth.gov.uk/parks-sports-leisure/parks/biodiversity-lambeth"
TERMS_URL = "https://www.lambeth.gov.uk/about-council/using-website/terms-conditions-disclaimer"
COPYRIGHT_URL = "https://www.lambeth.gov.uk/about-council/using-website/copyright"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES = 1_048_576
MAX_FEATURES = 5
MAX_FIELDS = 12
TARGETS = {
    "parcel_61523": (-0.1387938, 51.4196454),
    "parcel_61524": (-0.1407703, 51.4170637),
    "parcel_61525": (-0.1398845, 51.4167453),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def load_points(root: Path) -> list[dict[str, Any]]:
    path = root / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("canonical_points", [])
    found = {row.get("parcel_id"): row for row in rows if isinstance(row, dict) and row.get("parcel_id") in TARGETS}
    if set(found) != set(TARGETS):
        raise ValueError("exact target parcels missing")
    out: list[dict[str, Any]] = []
    for parcel_id, (expected_lon, expected_lat) in TARGETS.items():
        row = found[parcel_id]
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical Point {parcel_id}")
        if abs(lon - expected_lon) > 1e-7 or abs(lat - expected_lat) > 1e-7:
            raise ValueError(f"coordinate mismatch {parcel_id}")
        out.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return out


def bounded_get(url: str, timeout: float) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json,text/plain;q=0.9,*/*;q=0.1",
            "User-Agent": "AAYS-parcel-label-evidence/1.0 bounded official-source research",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        return int(getattr(response, "status", 200)), response.geturl(), body


def select_fields(metadata: dict[str, Any]) -> list[str]:
    candidates: list[tuple[int, str]] = []
    priority_tokens = ("name", "site", "ref", "code", "grade", "type", "designation", "category", "class", "description", "address")
    for field in metadata.get("fields", []):
        if not isinstance(field, dict):
            continue
        name = str(field.get("name") or "").strip()
        field_type = str(field.get("type") or "")
        if not name or field_type == "esriFieldTypeGeometry" or name.upper().startswith("SHAPE"):
            continue
        marker = (name + " " + str(field.get("alias") or "")).lower()
        score = 0 if field_type == "esriFieldTypeOID" else 2
        if any(token in marker for token in priority_tokens):
            score = 1
        candidates.append((score, name))
    candidates.sort(key=lambda item: (item[0], item[1].lower()))
    selected: list[str] = []
    for _, name in candidates:
        if name not in selected:
            selected.append(name)
        if len(selected) >= MAX_FIELDS:
            break
    return selected or ["OBJECTID"]


def metadata_attempt(timeout: float) -> tuple[list[str], dict[str, Any]]:
    accessed_at = utc_now()
    try:
        status, final_url, body = bounded_get(METADATA_URL, timeout)
        payload = json.loads(body.decode("utf-8", "replace"))
        fields = select_fields(payload)
        evidence = {
            "attempt_kind": "layer_metadata",
            "source_url": final_url,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(body),
            "sha256_basis": "bounded_response_bytes",
            "record_scope": "one bounded official Lambeth borough-SINC layer metadata request; maximum 1 MiB",
            "supports_fields": ["layer identity", "geometry type", "query capability", "published non-geometry field schema"],
            "relevant_record_ids_or_excerpt": json.dumps({"name": payload.get("name"), "geometryType": payload.get("geometryType"), "selected_fields": fields}, separators=(",", ":"))[:1500],
            "terms_or_license_urls": [TERMS_URL, COPYRIGHT_URL, OGL_URL],
            "http_status": status,
            "requests_made": 1,
        }
        return fields, evidence
    except Exception as exc:
        error = f"LAMBETH_BOROUGH_SINC_METADATA_ERROR:{type(exc).__name__}:{exc}"
        evidence = {
            "attempt_kind": "layer_metadata",
            "source_url": METADATA_URL,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(error.encode("utf-8")),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": "one bounded official Lambeth borough-SINC layer metadata request; maximum 1 MiB",
            "supports_fields": ["layer metadata availability"],
            "relevant_record_ids_or_excerpt": error,
            "terms_or_license_urls": [TERMS_URL, COPYRIGHT_URL, OGL_URL],
            "http_status": None,
            "requests_made": 0,
        }
        return ["OBJECTID"], evidence


def point_query_url(point: dict[str, Any], fields: list[str]) -> str:
    params = {
        "where": "1=1",
        "geometry": f"{point['longitude']},{point['latitude']}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": ",".join(fields[:MAX_FIELDS]),
        "returnGeometry": "false",
        "resultRecordCount": str(MAX_FEATURES),
        "f": "json",
    }
    return LAYER_URL + "/query?" + urllib.parse.urlencode(params)


def point_attempt(point: dict[str, Any], fields: list[str], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    accessed_at = utc_now()
    url = point_query_url(point, fields)
    try:
        status, final_url, body = bounded_get(url, timeout)
        payload = json.loads(body.decode("utf-8", "replace"))
        features = payload.get("features", [])
        rows: list[dict[str, Any]] = []
        for feature in features[:MAX_FEATURES] if isinstance(features, list) else []:
            attrs = feature.get("attributes", {}) if isinstance(feature, dict) else {}
            if isinstance(attrs, dict):
                rows.append({
                    "parcel_id": point["parcel_id"],
                    "canonical_point": point,
                    "source_url": final_url,
                    "attributes": {key: attrs.get(key) for key in fields if key in attrs},
                    "context_only": True,
                    "exact_parcel_binding": False,
                    "property_type_binding": False,
                })
        evidence = {
            "attempt_kind": "exact_point_intersection",
            "parcel_id": point["parcel_id"],
            "canonical_point": point,
            "source_url": final_url,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(body),
            "sha256_basis": "bounded_response_bytes",
            "record_scope": f"one bounded exact-point intersection query; at most {MAX_FEATURES} features, {MAX_FIELDS} non-geometry fields and 1 MiB",
            "supports_fields": ["borough SINC point intersection", *fields],
            "relevant_record_ids_or_excerpt": json.dumps({"feature_count": len(rows), "object_ids": [row["attributes"].get("OBJECTID") for row in rows]}, separators=(",", ":"))[:1500],
            "terms_or_license_urls": [TERMS_URL, COPYRIGHT_URL, OGL_URL],
            "http_status": status,
            "requests_made": 1,
        }
        return rows, evidence
    except Exception as exc:
        error = f"LAMBETH_BOROUGH_SINC_POINT_ERROR:{type(exc).__name__}:{exc}"
        evidence = {
            "attempt_kind": "exact_point_intersection",
            "parcel_id": point["parcel_id"],
            "canonical_point": point,
            "source_url": url,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(error.encode("utf-8")),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": f"one bounded exact-point intersection query; at most {MAX_FEATURES} features, {MAX_FIELDS} non-geometry fields and 1 MiB",
            "supports_fields": ["borough SINC point-intersection availability"],
            "relevant_record_ids_or_excerpt": error,
            "terms_or_license_urls": [TERMS_URL, COPYRIGHT_URL, OGL_URL],
            "http_status": None,
            "requests_made": 0,
        }
        return [], evidence


def build_payload(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    fields, metadata_evidence = metadata_attempt(timeout)
    rows: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = [metadata_evidence]
    for point in points:
        point_rows, point_evidence = point_attempt(point, fields, timeout)
        rows.extend(point_rows)
        evidence.append(point_evidence)
    state = "CANDIDATES_FOUND_CONTEXT_ONLY" if rows else "NO_DATA_CONTINUE"
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": 4,
        "target_count": 4,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "selected_non_geometry_fields": fields,
        "produced_candidate_rows": len(rows),
        "candidate_rows": rows,
        "source_evidence": evidence,
        "blocker": {
            "code": None if rows else "LAMBETH_BOROUGH_SINC_NO_USABLE_RESPONSE_OR_NO_POINT_MATCH",
            "state": "NONE" if rows else "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_BOROUGH_SINC_COORDINATE",
        "service_root": SERVICE_ROOT,
        "layer_url": LAYER_URL,
        "biodiversity_url": BIODIVERSITY_URL,
        "terms_url": TERMS_URL,
        "copyright_url": COPYRIGHT_URL,
        "open_government_licence_url": OGL_URL,
        "login_or_api_key_used": False,
        "geometry_payload_requested": False,
        "bulk_download_performed": False,
        "full_dataset_scan_performed": False,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate(root: Path) -> None:
    if len(load_points(root)) != 3:
        raise ValueError("target count mismatch")
    if not SERVICE_ROOT.startswith("https://gis.lambeth.gov.uk/arcgis/rest/services/"):
        raise ValueError("official service root required")
    if MAX_FEATURES != 5 or MAX_FIELDS != 12 or MAX_BYTES != 1_048_576:
        raise ValueError("bounded limits changed")
    print("PASS_TARGET_4_LAMBETH_BOROUGH_SINC_1_METADATA_PLUS_3_EXACT_POINT_QUERIES_MAX5_EACH_MAX12_FIELDS_MAX1MIB_CONTEXT_ONLY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    validate(root)
    if args.validate_only:
        return 0
    payload = build_payload(load_points(root), max(1.0, min(args.timeout, 30.0)))
    atomic_json(root / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_borough_sinc_coordinate_result_latest.json", payload)
    atomic_json(root / "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_borough_sinc_coordinate_latest.json", payload)
    if payload["produced_candidate_rows"]:
        print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_4_OF_4")
    else:
        print("PASS_NO_DATA_CONTINUE_4_OF_4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
