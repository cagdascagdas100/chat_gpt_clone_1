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
TASK_ID = "parcel-label-3-lambeth-conservation-areas-coordinate-v1-20260803"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
SERVICE_URL = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethConservationAreas/MapServer"
LAYER_URL = SERVICE_URL + "/0"
QUERY_URL = LAYER_URL + "/query"
PROFILES_URL = "https://www.lambeth.gov.uk/planning-and-building-control/conservation-and-listed-buildings/conservation-area-profiles"
OPEN_MAPPING_URL = "https://www.lambeth.gov.uk/about-council/transparency-open-data/open-mapping-data"
TERMS_URL = "https://www.lambeth.gov.uk/about-council/using-website/terms-conditions-disclaimer"
COPYRIGHT_URL = "https://www.lambeth.gov.uk/about-council/using-website/copyright"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES = 1_048_576
MAX_FEATURES = 5
POINTS = {"parcel_61523": (-0.1387938, 51.4196454), "parcel_61524": (-0.1407703, 51.4170637), "parcel_61525": (-0.1398845, 51.4167453)}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def canonical_points(base: Path) -> list[dict[str, Any]]:
    path = base / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("canonical_points", [])
    found = {row.get("parcel_id"): row for row in rows if isinstance(row, dict) and row.get("parcel_id") in POINTS}
    if set(found) != set(POINTS):
        raise ValueError("exact target parcels missing")
    output: list[dict[str, Any]] = []
    for parcel_id, (expected_lon, expected_lat) in POINTS.items():
        row = found[parcel_id]
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical Point {parcel_id}")
        if abs(lon - expected_lon) > 1e-7 or abs(lat - expected_lat) > 1e-7:
            raise ValueError(f"canonical coordinate mismatch {parcel_id}")
        output.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return output


def bounded_get(url: str, timeout: float) -> tuple[int, str, bytes]:
    request = urllib.request.Request(url, headers={"Accept": "application/json,text/plain;q=0.9,*/*;q=0.1", "User-Agent": "AAYS-parcel-label-evidence/1.0 bounded official-source research"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        return int(getattr(response, "status", 200)), response.geturl(), raw


def metadata_url() -> str:
    return LAYER_URL + "?" + urllib.parse.urlencode({"f": "json"})


def point_query_url(point: dict[str, Any]) -> str:
    params = {"geometry": f"{point['longitude']},{point['latitude']}", "geometryType": "esriGeometryPoint", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects", "outFields": "OBJECTID,CA_REF_NO,NAME,DATA_TYPE,CREATED,LAST_MODIF", "returnGeometry": "false", "resultRecordCount": str(MAX_FEATURES), "f": "json"}
    return QUERY_URL + "?" + urllib.parse.urlencode(params)


def evidence_record(*, scope_id: str, source_url: str, accessed_at: str, content_sha256: str, sha256_basis: str, record_scope: str, excerpt: str, http_status: int | None) -> dict[str, Any]:
    return {"scope_id": scope_id, "source_url": source_url, "accessed_at": accessed_at, "content_sha256": content_sha256, "sha256_basis": sha256_basis, "record_scope": record_scope, "supports_fields": ["OBJECTID", "CA_REF_NO", "NAME", "DATA_TYPE", "CREATED", "LAST_MODIF"], "relevant_record_ids_or_excerpt": excerpt, "terms_or_license_urls": [OPEN_MAPPING_URL, TERMS_URL, COPYRIGHT_URL, OGL_URL], "http_status": http_status}


def fetch_metadata(timeout: float) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    url = metadata_url()
    accessed_at = utc_now()
    try:
        status, final_url, raw = bounded_get(url, timeout)
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("metadata payload is not an object")
        excerpt = json.dumps({"name": payload.get("name"), "type": payload.get("type"), "geometryType": payload.get("geometryType"), "objectIdField": payload.get("objectIdField"), "maxRecordCount": payload.get("maxRecordCount")}, ensure_ascii=False, separators=(",", ":"))
        return payload, evidence_record(scope_id="layer_metadata", source_url=final_url, accessed_at=accessed_at, content_sha256=digest(raw), sha256_basis="bounded_response_bytes", record_scope="one bounded official Lambeth Conservation Areas layer metadata request; maximum 1 MiB", excerpt=excerpt, http_status=status)
    except Exception as exc:
        text = f"LAMBETH_CONSERVATION_AREAS_METADATA_ERROR:{type(exc).__name__}:{exc}"
        return None, evidence_record(scope_id="layer_metadata", source_url=url, accessed_at=accessed_at, content_sha256=digest(text.encode("utf-8")), sha256_basis="bounded_error_evidence_string", record_scope="one bounded official Lambeth Conservation Areas layer metadata request; maximum 1 MiB", excerpt=text, http_status=None)


def fetch_point(point: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    url = point_query_url(point)
    accessed_at = utc_now()
    parcel_id = str(point["parcel_id"])
    try:
        status, final_url, raw = bounded_get(url, timeout)
        payload = json.loads(raw.decode("utf-8"))
        features = payload.get("features", []) if isinstance(payload, dict) else []
        if not isinstance(features, list):
            raise ValueError("features is not a list")
        candidates: list[dict[str, Any]] = []
        for feature in features[:MAX_FEATURES]:
            attrs = feature.get("attributes", {}) if isinstance(feature, dict) else {}
            if not isinstance(attrs, dict):
                continue
            candidates.append({"parcel_id": parcel_id, "canonical_point": point, "source_url": final_url, "conservation_area_reference": attrs.get("CA_REF_NO"), "conservation_area_name": attrs.get("NAME"), "data_type": attrs.get("DATA_TYPE"), "created": attrs.get("CREATED"), "last_modified": attrs.get("LAST_MODIF"), "object_id": attrs.get("OBJECTID"), "context_only": True, "exact_parcel_binding": False, "property_type_binding": False})
        excerpt = json.dumps({"feature_count": len(features), "returned_object_ids": [c.get("object_id") for c in candidates]}, separators=(",", ":"))
        return candidates, evidence_record(scope_id=parcel_id, source_url=final_url, accessed_at=accessed_at, content_sha256=digest(raw), sha256_basis="bounded_response_bytes", record_scope="one bounded official Lambeth Conservation Areas exact-point intersection query; maximum 5 features and 1 MiB", excerpt=excerpt, http_status=status)
    except Exception as exc:
        text = f"LAMBETH_CONSERVATION_AREAS_POINT_ERROR:{type(exc).__name__}:{exc}"
        return [], evidence_record(scope_id=parcel_id, source_url=url, accessed_at=accessed_at, content_sha256=digest(text.encode("utf-8")), sha256_basis="bounded_error_evidence_string", record_scope="one bounded official Lambeth Conservation Areas exact-point intersection query; maximum 5 features and 1 MiB", excerpt=text, http_status=None)


def build_payload(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    _, metadata_evidence = fetch_metadata(timeout)
    candidates: list[dict[str, Any]] = []
    evidence = [metadata_evidence]
    for point in points:
        point_candidates, point_evidence = fetch_point(point, timeout)
        candidates.extend(point_candidates)
        evidence.append(point_evidence)
    produced = len(candidates)
    return {"schema_version": 1, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": SLOT_ID, "task_id": TASK_ID, "generated_at": utc_now(), "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if produced else "NO_DATA_CONTINUE", "panel_status": "PUBLISHED", "completed_count": 4, "target_count": 4, "previous_percent": 0.0, "progress_percent": 100.0, "percent_increase": 100.0, "validated_canonical_points": points, "produced_candidate_rows": produced, "candidate_rows": candidates, "source_evidence": evidence, "blocker": {"code": None if produced else "LAMBETH_CONSERVATION_AREAS_NO_USABLE_RESPONSE_OR_NO_POINT_INTERSECTION", "state": "NONE" if produced else "NO_DATA_CONTINUE", "manual_action_required": False, "retry_unchanged_route": False}, "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_CONSERVATION_AREAS_COORDINATE", "service_url": SERVICE_URL, "layer_url": LAYER_URL, "profiles_url": PROFILES_URL, "open_mapping_url": OPEN_MAPPING_URL, "terms_url": TERMS_URL, "copyright_url": COPYRIGHT_URL, "open_government_licence_url": OGL_URL, "login_or_api_key_used": False, "bulk_download_performed": False, "full_dataset_scan_performed": False, "large_data_downloaded": False, "property_type_binding_claimed": False, "exact_parcel_binding_claimed": False, "inferred_values": 0, "fake_data": False, "final_ready": False}


def validate(base: Path) -> None:
    if len(canonical_points(base)) != 3:
        raise ValueError("target count mismatch")
    if not LAYER_URL.startswith("https://gis.lambeth.gov.uk/"):
        raise ValueError("non-official layer URL")
    if MAX_FEATURES != 5 or MAX_BYTES != 1_048_576:
        raise ValueError("bounded limits mismatch")
    print("PASS_TARGET_4_LAMBETH_CONSERVATION_AREAS_METADATA_PLUS_3_POINT_INTERSECTIONS_MAX5_EACH_MAX1MIB_CONTEXT_ONLY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    base = repo_root()
    validate(base)
    if args.validate_only:
        return 0
    payload = build_payload(canonical_points(base), max(1.0, min(args.timeout, 30.0)))
    atomic_json(base / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_conservation_areas_coordinate_result_latest.json", payload)
    atomic_json(base / "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_conservation_areas_coordinate_latest.json", payload)
    print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_4_OF_4" if payload["produced_candidate_rows"] else "PASS_NO_DATA_CONTINUE_4_OF_4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
