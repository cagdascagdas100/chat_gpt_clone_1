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

TASK_ID = "parcel-label-3-lambeth-dma-v1-20260801"
ENDPOINT = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethDevelopmentManagementApplications/FeatureServer/0/query"
SERVICE_DIRECTORY = "https://gis.lambeth.gov.uk/arcgis/rest/services"
SERVICE_URL = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethDevelopmentManagementApplications/FeatureServer"
OPEN_MAPPING = "https://www.lambeth.gov.uk/about-council/transparency-open-data/open-mapping-data"
LICENSE = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_dma_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_dma_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
RADIUS = 100
LIMIT = 25
SPACING = 1.2


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def load_points(repo: Path) -> list[tuple[str, float, float]]:
    payload = json.loads((repo / PROBE).read_text(encoding="utf-8-sig"))
    rows = payload.get("canonical_points")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("CANONICAL_POINT_COUNT_NOT_3")
    points: list[tuple[str, float, float]] = []
    for row in rows:
        if (
            row.get("parcel_id") not in IDS
            or row.get("geometry_type") != "Point"
            or row.get("point_valid") is not True
        ):
            raise ValueError("INVALID_CANONICAL_POINT")
        points.append((row["parcel_id"], float(row["latitude"]), float(row["longitude"])))
    if tuple(point[0] for point in points) != IDS:
        raise ValueError("CANONICAL_ID_ORDER_MISMATCH")
    return points


def query_url(latitude: float, longitude: float) -> str:
    parameters = {
        "where": "1=1",
        "geometry": f"{longitude},{latitude}",
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo_root)
    points = load_points(repo)

    if args.validate_only:
        print(json.dumps({
            "state": "VALID",
            "target_count": len(points),
            "resource_class": "network_fetch",
            "radius_metres": RADIUS,
            "result_limit": LIMIT,
            "spacing_seconds": SPACING,
            "exact_read_paths": [PROBE],
            "exact_write_paths": list(OUTPUTS),
        }))
        return

    evidence: list[dict] = []
    candidates: list[dict] = []
    for index, (parcel_id, latitude, longitude) in enumerate(points):
        if index:
            time.sleep(SPACING)
        url = query_url(latitude, longitude)
        accessed_at = now()
        query_bytes = url.encode("utf-8")
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "TerraYield-AAYS/1.0 parcel-label research"},
            )
            with urllib.request.urlopen(request, timeout=args.timeout) as response:
                raw = response.read()
                http_status = getattr(response, "status", 200)
            data = json.loads(raw)
            features = data.get("features", []) if isinstance(data, dict) else []
            for feature in features:
                attributes = feature.get("attributes") if isinstance(feature, dict) else None
                geometry = feature.get("geometry") if isinstance(feature, dict) else None
                if isinstance(attributes, dict) and isinstance(geometry, dict):
                    candidates.append({
                        "parcel_id": parcel_id,
                        "attributes": attributes,
                        "geometry": geometry,
                        "candidate_only": True,
                        "exact_parcel_binding": False,
                    })
            record = {
                "parcel_id": parcel_id,
                "source_url": url,
                "accessed_at": accessed_at,
                "query_sha256": sha256(query_bytes),
                "http_status": http_status,
                "content_sha256": sha256(raw),
                "sha256_basis": "raw_response_bytes",
                "relevant_record_ids_or_excerpt": f"{len(features)} ArcGIS features",
                "proven_fields": ["raw development-management attributes", "ArcGIS geometry"],
            }
        except Exception as error:
            bounded = f"LAMBETH_DMA_ERROR:{type(error).__name__}".encode("utf-8")
            record = {
                "parcel_id": parcel_id,
                "source_url": url,
                "accessed_at": accessed_at,
                "query_sha256": sha256(query_bytes),
                "http_status": None,
                "content_sha256": sha256(bounded),
                "sha256_basis": "bounded_error_evidence_string",
                "relevant_record_ids_or_excerpt": bounded.decode("utf-8"),
                "proven_fields": ["query URL", "access time", "query SHA-256", "bounded error type"],
            }
        record.update({
            "query_scope": {"radius_metres": RADIUS, "result_limit": LIMIT, "layer": 0},
            "service_directory_url": SERVICE_DIRECTORY,
            "service_url": SERVICE_URL,
            "open_mapping_url": OPEN_MAPPING,
            "license_or_terms_url": LICENSE,
        })
        evidence.append(record)

    completed = len(evidence)
    target = len(points)
    progress = completed / target * 100 if target else 0.0
    state = "CANDIDATES_PUBLISHED" if candidates else "NO_DATA_CONTINUE"
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
        "blocker": {
            "code": None if candidates else "LAMBETH_DMA_NO_USABLE_RESPONSE",
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_DMA",
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for relative_path in OUTPUTS:
        write_json(repo / relative_path, payload)
    print(json.dumps({
        "state": state,
        "completed_count": completed,
        "target_count": target,
        "candidate_rows": len(candidates),
    }))


if __name__ == "__main__":
    main()
