from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-lambeth-hmo-v1-20260801"
ENDPOINT = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethHomesofMultipleOccupancy/FeatureServer/0/query"
SERVICE_DIRECTORY = "https://gis.lambeth.gov.uk/arcgis/rest/services"
SERVICE_URL = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethHomesofMultipleOccupancy/FeatureServer"
OPEN_MAPPING = "https://www.lambeth.gov.uk/about-council/transparency-open-data/open-mapping-data"
LICENSE = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_hmo_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_hmo_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
RADIUS = 100
LIMIT = 25
SPACING = 1.2

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def atomic_json(path: str, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".part")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, target)

def load_points() -> list[dict]:
    payload = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    points = payload.get("canonical_points", [])
    indexed = {row.get("parcel_id"): row for row in points}
    selected = []
    for parcel_id in IDS:
        row = indexed.get(parcel_id)
        if not row:
            raise ValueError(f"missing canonical point: {parcel_id}")
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon, lat = row.get("longitude"), row.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        selected.append({"parcel_id": parcel_id, "longitude": float(lon), "latitude": float(lat)})
    return selected

def query_url(point: dict) -> str:
    params = {
        "where": "1=1",
        "geometry": f"{point['longitude']},{point['latitude']}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": str(RADIUS),
        "units": "esriSRUnit_Meter",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "resultRecordCount": str(LIMIT),
        "f": "json",
    }
    return ENDPOINT + "?" + urllib.parse.urlencode(params)

def validate_only() -> dict:
    points = load_points()
    assert len(points) == 3
    assert tuple(row["parcel_id"] for row in points) == IDS
    assert all(not Path(path).is_absolute() for path in (PROBE, *OUTPUTS))
    assert RADIUS == 100 and LIMIT == 25 and SPACING >= 1.2
    return {
        "state": "VALID",
        "target_count": len(points),
        "resource_class": "network_fetch",
        "relative_paths": True,
        "radius_metres": RADIUS,
        "result_limit": LIMIT,
        "spacing_seconds": SPACING,
    }

def run(timeout: float) -> dict:
    points = load_points()
    attempts = []
    candidates = []
    for index, point in enumerate(points):
        if index:
            time.sleep(SPACING)
        url = query_url(point)
        accessed_at = now()
        query_sha = sha256_bytes(url.encode("utf-8"))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label/1.0 (bounded open-data verification)"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
                http_status = getattr(response, "status", None)
            raw_sha = sha256_bytes(raw)
            parsed = json.loads(raw.decode("utf-8"))
            features = parsed.get("features", []) if isinstance(parsed, dict) else []
            valid_features = [
                feature for feature in features
                if isinstance(feature, dict)
                and isinstance(feature.get("attributes"), dict)
                and isinstance(feature.get("geometry"), dict)
            ]
            attempts.append({
                "parcel_id": point["parcel_id"],
                "source_url": url,
                "accessed_at": accessed_at,
                "query_sha256": query_sha,
                "http_status": http_status,
                "content_sha256": raw_sha,
                "sha256_basis": "raw_response_bytes",
                "relevant_record_ids_or_excerpt": [
                    feature.get("attributes", {}).get("OBJECTID")
                    for feature in valid_features[:LIMIT]
                ],
                "proven_fields": ["query URL", "access time", "query SHA-256", "raw response SHA-256", "returned candidate records"],
                "query_scope": {"radius_metres": RADIUS, "result_limit": LIMIT, "layer": 0},
                "service_directory_url": SERVICE_DIRECTORY,
                "service_url": SERVICE_URL,
                "open_mapping_url": OPEN_MAPPING,
                "license_or_terms_url": LICENSE,
            })
            for feature in valid_features:
                candidates.append({
                    "parcel_id": point["parcel_id"],
                    "source_url": url,
                    "source_accessed_at": accessed_at,
                    "query_sha256": query_sha,
                    "raw_response_sha256": raw_sha,
                    "attributes": feature["attributes"],
                    "geometry": feature["geometry"],
                    "candidate_only": True,
                    "exact_parcel_binding": False,
                    "uprn_claimed": False,
                    "normalized_property_type_claimed": False,
                })
        except Exception as exc:
            error = f"LAMBETH_HMO_ERROR:{type(exc).__name__}"
            error_sha = sha256_bytes(error.encode("utf-8"))
            attempts.append({
                "parcel_id": point["parcel_id"],
                "source_url": url,
                "accessed_at": accessed_at,
                "query_sha256": query_sha,
                "http_status": None,
                "content_sha256": error_sha,
                "sha256_basis": "bounded_error_evidence_string",
                "relevant_record_ids_or_excerpt": error,
                "proven_fields": ["query URL", "access time", "query SHA-256", "bounded error type"],
                "query_scope": {"radius_metres": RADIUS, "result_limit": LIMIT, "layer": 0},
                "service_directory_url": SERVICE_DIRECTORY,
                "service_url": SERVICE_URL,
                "open_mapping_url": OPEN_MAPPING,
                "license_or_terms_url": LICENSE,
            })
    completed = len(attempts)
    target = len(points)
    progress = round((completed / target) * 100, 10) if target else 0.0
    state = "CANDIDATES_PUBLISHED" if candidates else "NO_DATA_CONTINUE"
    blocker = None if candidates else {
        "code": "LAMBETH_HMO_NO_USABLE_RESPONSE",
        "state": "NO_DATA_CONTINUE",
        "candidate_research_blocked": False,
        "manual_action_required": False,
        "retry_unchanged_route": False,
    }
    payload = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": target,
        "previous_percent": 0.0,
        "progress_percent": progress,
        "percent_increase": progress,
        "produced_candidate_rows": len(candidates),
        "candidates": candidates,
        "source_evidence": attempts,
        "blocker": blocker,
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_HMO",
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        atomic_json(output, payload)
    return payload

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    result = validate_only() if args.validate_only else run(args.timeout)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
