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

TASK_ID = "parcel-label-3-lambeth-core-office-v1-20260801"
ENDPOINT = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethCoreOfficeBuildings/FeatureServer/0/query"
SERVICE_DIRECTORY = "https://gis.lambeth.gov.uk/arcgis/rest/services"
SERVICE_URL = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethCoreOfficeBuildings/FeatureServer"
OPEN_MAPPING = "https://www.lambeth.gov.uk/about-council/transparency-open-data/open-mapping-data"
LICENSE = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_core_office_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_core_office_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
RADIUS = 100
LIMIT = 25
SPACING = 1.2


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def load_points(repo: Path) -> list[dict]:
    payload = json.loads((repo / PROBE).read_text(encoding="utf-8-sig"))
    rows = payload.get("canonical_points")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("CANONICAL_POINT_COUNT_NOT_3")
    found: dict[str, dict] = {}
    for row in rows:
        parcel_id = row.get("parcel_id")
        if parcel_id not in IDS or row.get("geometry_type") != "Point" or not row.get("point_valid"):
            continue
        longitude = row.get("longitude")
        latitude = row.get("latitude")
        if not isinstance(longitude, (int, float)) or not isinstance(latitude, (int, float)):
            continue
        found[parcel_id] = {"parcel_id": parcel_id, "longitude": float(longitude), "latitude": float(latitude)}
    if tuple(found) != IDS:
        raise ValueError("CANONICAL_POINT_IDS_OR_ORDER_INVALID")
    return [found[parcel_id] for parcel_id in IDS]


def build_url(point: dict) -> str:
    parameters = {
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
    return ENDPOINT + "?" + urllib.parse.urlencode(parameters)


def request_one(point: dict, timeout: float) -> tuple[dict, list[dict]]:
    url = build_url(point)
    accessed_at = now()
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label/1.0 contact=repository-maintainer"})
    candidates: list[dict] = []
    evidence = {
        "parcel_id": point["parcel_id"],
        "source_url": url,
        "accessed_at": accessed_at,
        "query_sha256": sha256_bytes(url.encode("utf-8")),
        "http_status": None,
        "content_sha256": None,
        "sha256_basis": None,
        "relevant_record_ids_or_excerpt": None,
        "proven_fields": [],
        "query_scope": {"radius_metres": RADIUS, "result_limit": LIMIT, "layer": 0},
        "service_directory_url": SERVICE_DIRECTORY,
        "service_url": SERVICE_URL,
        "open_mapping_url": OPEN_MAPPING,
        "license_or_terms_url": LICENSE,
    }
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            evidence["http_status"] = getattr(response, "status", None)
            evidence["content_sha256"] = sha256_bytes(raw)
            evidence["sha256_basis"] = "raw_response_bytes"
        payload = json.loads(raw.decode("utf-8"))
        features = payload.get("features") if isinstance(payload, dict) else None
        if not isinstance(features, list):
            raise ValueError("ARCGIS_FEATURES_NOT_LIST")
        for feature in features[:LIMIT]:
            if not isinstance(feature, dict):
                continue
            attributes = feature.get("attributes")
            geometry = feature.get("geometry")
            if not isinstance(attributes, dict) or not isinstance(geometry, dict):
                continue
            candidates.append({
                "parcel_id": point["parcel_id"],
                "candidate_only": True,
                "source_url": url,
                "attributes": attributes,
                "geometry": geometry,
                "exact_parcel_binding": False,
                "uprn_claimed": False,
                "normalized_property_type_claimed": False,
            })
        evidence["relevant_record_ids_or_excerpt"] = f"features={len(features)};accepted_candidates={len(candidates)}"
        evidence["proven_fields"] = ["raw ArcGIS attributes", "raw ArcGIS geometry", "query URL", "access time", "response SHA-256"]
    except Exception as exc:  # fail closed with bounded evidence
        bounded = f"LAMBETH_CORE_OFFICE_ERROR:{type(exc).__name__}"
        evidence["content_sha256"] = sha256_bytes(bounded.encode("utf-8"))
        evidence["sha256_basis"] = "bounded_error_evidence_string"
        evidence["relevant_record_ids_or_excerpt"] = bounded
        evidence["proven_fields"] = ["query URL", "access time", "query SHA-256", "bounded error type"]
    return evidence, candidates


def validate(repo: Path) -> dict:
    points = load_points(repo)
    assert len(points) == 3
    assert all(not Path(path).is_absolute() for path in (PROBE, *OUTPUTS))
    assert RADIUS == 100 and LIMIT == 25 and SPACING >= 1.2
    return {
        "state": "VALID",
        "task_id": TASK_ID,
        "target_count": len(points),
        "resource_class": "network_fetch",
        "relative_paths": True,
        "radius_metres": RADIUS,
        "result_limit": LIMIT,
        "request_spacing_seconds": SPACING,
    }


def run(repo: Path, timeout: float) -> dict:
    points = load_points(repo)
    evidence: list[dict] = []
    candidates: list[dict] = []
    for index, point in enumerate(points):
        if index:
            time.sleep(SPACING)
        item_evidence, item_candidates = request_one(point, timeout)
        evidence.append(item_evidence)
        candidates.extend(item_candidates)
    completed = len(evidence)
    target = len(points)
    progress = completed / target * 100 if target else 0.0
    state = "CANDIDATE_DATA" if candidates else "NO_DATA_CONTINUE"
    blocker = None if candidates else {
        "code": "LAMBETH_CORE_OFFICE_NO_USABLE_RESPONSE",
        "state": "NO_DATA_CONTINUE",
        "candidate_research_blocked": False,
        "manual_action_required": False,
        "retry_unchanged_route": False,
    }
    result = {
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
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_CORE_OFFICE",
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        write_json(repo / output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    payload = validate(repo) if args.validate_only else run(repo, args.timeout)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
