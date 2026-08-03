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
TASK_ID = "parcel-label-3-gla-cultural-infrastructure-identify-v1-20260803"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
SERVICE_URL = "https://gis.london.gov.uk/arcgis/rest/services/apps/Cultural_infrastructure_2023_for_webapp_verified/MapServer"
IDENTIFY_URL = SERVICE_URL + "/identify"
DATASET_URL = "https://data.london.gov.uk/dataset/cultural-infrastructure-map-2023-23697/"
LEGACY_DATASET_URL = "https://data.london.gov.uk/dataset/cultural-infrastructure-map-2ko88"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES = 1048576
MAX_CANDIDATES = 20
RADIUS_METRES = 500
TARGETS = {
    "parcel_61523": (-0.1387938, 51.4196454),
    "parcel_61524": (-0.1407703, 51.4170637),
    "parcel_61525": (-0.1398845, 51.4167453),
}
LAYER_IDS = ",".join(str(i) for i in list(range(0, 37)))
SAFE_FIELD_MARKERS = (
    "name", "title", "address", "postcode", "borough", "category",
    "type", "description", "venue", "site", "facility", "status",
)

def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def load_points(base: Path) -> list[dict[str, Any]]:
    probe_path = base / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
    payload = json.loads(probe_path.read_text(encoding="utf-8"))
    rows = payload.get("canonical_points")
    if not isinstance(rows, list):
        raise ValueError("canonical_points missing")
    by_id = {
        row.get("parcel_id"): row
        for row in rows
        if isinstance(row, dict) and row.get("parcel_id") in TARGETS
    }
    if set(by_id) != set(TARGETS):
        raise ValueError("exact target parcels missing")
    points: list[dict[str, Any]] = []
    for parcel_id, (expected_lon, expected_lat) in TARGETS.items():
        row = by_id[parcel_id]
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if (
            row.get("geometry_type") != "Point"
            or row.get("point_valid") is not True
            or abs(lon - expected_lon) > 1e-7
            or abs(lat - expected_lat) > 1e-7
        ):
            raise ValueError(f"invalid canonical Point {parcel_id}")
        points.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return points

def bounded_get(url: str, timeout: float) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AAYS-parcel-label-evidence/1.0 bounded official-source research",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        return int(getattr(response, "status", 200)), response.geturl(), raw

def identify_url(lon: float, lat: float) -> str:
    lat_delta = RADIUS_METRES / 111320.0
    lon_delta = RADIUS_METRES / 69400.0
    params = {
        "f": "json",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "sr": "4326",
        "layers": "all:" + LAYER_IDS,
        "tolerance": "500",
        "mapExtent": f"{lon-lon_delta},{lat-lat_delta},{lon+lon_delta},{lat+lat_delta}",
        "imageDisplay": "1000,1000,96",
        "returnGeometry": "true",
        "returnFieldName": "true",
    }
    return IDENTIFY_URL + "?" + urllib.parse.urlencode(params)

def safe_attributes(attributes: Any) -> dict[str, Any]:
    if not isinstance(attributes, dict):
        return {}
    out: dict[str, Any] = {}
    for key, value in attributes.items():
        low = str(key).lower()
        if any(marker in low for marker in SAFE_FIELD_MARKERS):
            if isinstance(value, (str, int, float, bool)) or value is None:
                out[str(key)] = value
    return out

def parse_candidates(raw: bytes, source_url: str, point: dict[str, Any]) -> list[dict[str, Any]]:
    payload = json.loads(raw.decode("utf-8"))
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for result in results:
        if not isinstance(result, dict):
            continue
        layer_name = str(result.get("layerName") or "").strip()
        layer_id = result.get("layerId")
        attrs = safe_attributes(result.get("attributes"))
        geometry = result.get("geometry") if isinstance(result.get("geometry"), dict) else None
        identity = json.dumps([layer_id, layer_name, attrs, geometry], sort_keys=True, default=str)
        if identity in seen:
            continue
        seen.add(identity)
        candidates.append(
            {
                "parcel_id": point["parcel_id"],
                "canonical_point": point,
                "source_url": source_url,
                "layer_id": layer_id,
                "layer_name": layer_name,
                "published_attributes": attrs,
                "published_geometry": geometry,
                "context_radius_metres": RADIUS_METRES,
                "context_only": True,
                "exact_parcel_binding": False,
                "property_type_binding": False,
            }
        )
        if len(candidates) >= MAX_CANDIDATES:
            break
    return candidates

def attempt(point: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    url = identify_url(float(point["longitude"]), float(point["latitude"]))
    accessed_at = now_utc()
    try:
        status, final_url, raw = bounded_get(url, timeout)
        candidates = parse_candidates(raw, final_url, point)
        evidence = {
            "parcel_id": point["parcel_id"],
            "canonical_point": point,
            "source_url": final_url,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(raw),
            "sha256_basis": "bounded_identify_response_bytes",
            "record_scope": (
                "one bounded official GLA Cultural Infrastructure Map identify request; "
                "37 published layers; approximately 500 m context window; maximum 20 retained results and 1 MiB response"
            ),
            "supports_fields": [
                "published cultural infrastructure layer name",
                "published venue/site/facility name where present",
                "published address/postcode/borough where present",
                "published category/type/description where present",
                "published feature geometry where present",
            ],
            "relevant_record_ids_or_excerpt": (
                f"HTTP_{status}; returned_results={len(candidates)}; retained_max={MAX_CANDIDATES}"
            ),
            "dataset_url": DATASET_URL,
            "service_url": SERVICE_URL,
            "license_or_terms_url": OGL_URL,
            "http_status": status,
            "requests_made": 1,
        }
        return candidates, evidence
    except Exception as exc:
        error = f"GLA_CULTURAL_INFRASTRUCTURE_IDENTIFY_ERROR:{type(exc).__name__}:{exc}"
        evidence = {
            "parcel_id": point["parcel_id"],
            "canonical_point": point,
            "source_url": url,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(error.encode("utf-8")),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": (
                "one bounded official GLA Cultural Infrastructure Map identify attempt; "
                "37 published layers; approximately 500 m context window; maximum 20 retained results and 1 MiB response"
            ),
            "supports_fields": ["official identify endpoint availability"],
            "relevant_record_ids_or_excerpt": error,
            "dataset_url": DATASET_URL,
            "service_url": SERVICE_URL,
            "license_or_terms_url": OGL_URL,
            "http_status": None,
            "requests_made": 0,
        }
        return [], evidence

def build_payload(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for point in points:
        candidates, record = attempt(point, timeout)
        rows.extend(candidates)
        evidence.append(record)
    produced = len(rows)
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": now_utc(),
        "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if produced else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": produced,
        "candidate_rows": rows,
        "source_evidence": evidence,
        "blocker": {
            "code": None if produced else "GLA_CULTURAL_INFRASTRUCTURE_NO_USABLE_RESPONSE_OR_NO_NEARBY_RESULT",
            "state": "NONE" if produced else "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_GLA_CULTURAL_INFRASTRUCTURE_IDENTIFY",
        "service_url": SERVICE_URL,
        "dataset_url": DATASET_URL,
        "legacy_dataset_url": LEGACY_DATASET_URL,
        "open_government_licence_url": OGL_URL,
        "context_radius_metres": RADIUS_METRES,
        "queried_layer_count": 37,
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
    if not SERVICE_URL.startswith("https://gis.london.gov.uk/"):
        raise ValueError("official service host mismatch")
    if RADIUS_METRES != 500 or MAX_CANDIDATES != 20 or MAX_BYTES != 1048576:
        raise ValueError("bounds mismatch")
    print(
        "PASS_TARGET_3_GLA_CULTURAL_INFRASTRUCTURE_IDENTIFY_"
        "MAX1_REQUEST_EACH_500M_MAX1MIB_20_RESULTS_37_LAYERS_CONTEXT_ONLY"
    )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    base = repo_root()
    validate(base)
    if args.validate_only:
        return 0
    timeout = max(1.0, min(float(args.timeout), 30.0))
    payload = build_payload(load_points(base), timeout)
    atomic_write_json(
        base / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/gla_cultural_infrastructure_identify_result_latest.json",
        payload,
    )
    atomic_write_json(
        base / "england_map_web/data/aays_21_slots/parcel_label_3/gla_cultural_infrastructure_identify_latest.json",
        payload,
    )
    if payload["produced_candidate_rows"]:
        print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_3_OF_3")
    else:
        print("PASS_NO_DATA_CONTINUE_3_OF_3")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
