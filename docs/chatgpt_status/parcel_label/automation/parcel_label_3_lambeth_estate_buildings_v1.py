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

TASK_ID = "parcel-label-3-lambeth-estate-buildings-v1-20260801"
ENDPOINT = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethEstateBuildings/FeatureServer/0/query"
SERVICE_DIRECTORY = "https://gis.lambeth.gov.uk/arcgis/rest/services"
SERVICE_URL = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethEstateBuildings/FeatureServer"
OPEN_MAPPING = "https://www.lambeth.gov.uk/about-council/transparency-open-data/open-mapping-data"
LICENSE = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_estate_buildings_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_estate_buildings_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
RADIUS = 100
LIMIT = 25
SPACING = 1.2

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load_points(repo_root: Path) -> list[dict]:
    payload = json.loads((repo_root / PROBE).read_text(encoding="utf-8"))
    index = {row.get("parcel_id"): row for row in payload.get("canonical_points", [])}
    points = []
    for parcel_id in IDS:
        row = index.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or not row.get("point_valid"):
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon, lat = row.get("longitude"), row.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        points.append({"parcel_id": parcel_id, "longitude": float(lon), "latitude": float(lat)})
    return points

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

def query_one(point: dict, timeout: int) -> tuple[list[dict], dict]:
    url = query_url(point)
    accessed_at = now()
    query_sha256 = sha(url)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "AAYS/parcel-label-3"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            status = getattr(response, "status", None)
        raw_sha256 = hashlib.sha256(raw).hexdigest()
        payload = json.loads(raw.decode("utf-8"))
        features = payload.get("features") if isinstance(payload, dict) else None
        candidates = []
        if isinstance(features, list):
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                attributes = feature.get("attributes")
                geometry = feature.get("geometry")
                if isinstance(attributes, dict) and isinstance(geometry, dict):
                    candidates.append({
                        "parcel_id": point["parcel_id"],
                        "source": "LambethEstateBuildings",
                        "candidate_only": True,
                        "raw_attributes": attributes,
                        "geometry": geometry,
                    })
        evidence = {
            "parcel_id": point["parcel_id"],
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": query_sha256,
            "http_status": status,
            "content_sha256": raw_sha256,
            "sha256_basis": "raw_response_bytes",
            "relevant_record_ids_or_excerpt": f"{len(candidates)} valid ArcGIS feature(s)",
            "proven_fields": ["query URL", "access time", "query SHA-256", "raw-response SHA-256", "valid feature count"],
            "query_scope": {"radius_metres": RADIUS, "result_limit": LIMIT, "layer": 0},
            "service_directory_url": SERVICE_DIRECTORY,
            "service_url": SERVICE_URL,
            "open_mapping_url": OPEN_MAPPING,
            "license_or_terms_url": LICENSE,
        }
        return candidates, evidence
    except Exception as exc:
        bounded = f"LAMBETH_ESTATE_BUILDINGS_ERROR:{type(exc).__name__}"
        evidence = {
            "parcel_id": point["parcel_id"],
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": query_sha256,
            "http_status": None,
            "content_sha256": sha(bounded),
            "sha256_basis": "bounded_error_evidence_string",
            "relevant_record_ids_or_excerpt": bounded,
            "proven_fields": ["query URL", "access time", "query SHA-256", "bounded error type"],
            "query_scope": {"radius_metres": RADIUS, "result_limit": LIMIT, "layer": 0},
            "service_directory_url": SERVICE_DIRECTORY,
            "service_url": SERVICE_URL,
            "open_mapping_url": OPEN_MAPPING,
            "license_or_terms_url": LICENSE,
        }
        return [], evidence

def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    os.replace(temp, path)

def validate(repo_root: Path) -> dict:
    points = load_points(repo_root)
    return {
        "state": "VALID",
        "target_count": len(points),
        "resource_class": "network_fetch",
        "relative_paths": True,
        "radius_metres": RADIUS,
        "result_limit": LIMIT,
        "spacing_seconds": SPACING,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    if args.validate_only:
        print(json.dumps(validate(repo_root), sort_keys=True))
        return 0
    points = load_points(repo_root)
    candidates, evidence = [], []
    for index, point in enumerate(points):
        rows, record = query_one(point, args.timeout)
        candidates.extend(rows)
        evidence.append(record)
        if index + 1 < len(points):
            time.sleep(SPACING)
    completed = len(evidence)
    target = len(points)
    progress = 100.0 * completed / target if target else 0.0
    state = "PUBLISHED_CANDIDATES" if candidates else "NO_DATA_CONTINUE"
    blocker = None if candidates else {
        "code": "LAMBETH_ESTATE_BUILDINGS_NO_USABLE_RESPONSE",
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
        "source_evidence": evidence,
        "blocker": blocker,
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_ESTATE_BUILDINGS",
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for relative in OUTPUTS:
        atomic_write(repo_root / relative, payload)
    print(json.dumps({"state": state, "completed_count": completed, "target_count": target, "candidate_rows": len(candidates)}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
