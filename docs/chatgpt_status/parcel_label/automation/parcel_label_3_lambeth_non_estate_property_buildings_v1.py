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

TASK_ID = "parcel-label-3-lambeth-non-estate-property-buildings-v1-20260802"
LAYER_URL = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethNonEstatePropertyBuildings/FeatureServer/0/query"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_non_estate_property_buildings_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_non_estate_property_buildings_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024
MAX_RECORDS = 10
DISTANCE_METERS = 25

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha(value: str | bytes) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()

def repo_root() -> Path:
    return Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()

def load_points(root: Path) -> list[dict]:
    data = json.loads((root / PROBE).read_text(encoding="utf-8"))
    points = {row.get("parcel_id"): row for row in data.get("canonical_points", [])}
    selected = []
    for parcel_id in IDS:
        row = points.get(parcel_id)
        if not row:
            raise ValueError(f"MISSING_CANONICAL_POINT:{parcel_id}")
        if row.get("geometry_type") != "Point" or not row.get("point_valid"):
            raise ValueError(f"INVALID_CANONICAL_POINT:{parcel_id}")
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"OUT_OF_RANGE_CANONICAL_POINT:{parcel_id}")
        selected.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return selected

def build_url(point: dict) -> str:
    params = {
        "where": "1=1",
        "geometry": f'{point["longitude"]},{point["latitude"]}',
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": str(DISTANCE_METERS),
        "units": "esriSRUnit_Meter",
        "outFields": "*",
        "returnGeometry": "false",
        "resultRecordCount": str(MAX_RECORDS),
        "f": "json",
    }
    return LAYER_URL + "?" + urllib.parse.urlencode(params)

def fetch(url: str, timeout: float) -> tuple[int | None, bytes | None, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label-3/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                return getattr(response, "status", None), None, "RESPONSE_TOO_LARGE"
            return getattr(response, "status", None), raw, None
    except Exception as exc:
        return None, None, f"{type(exc).__name__}:{exc}"

def write_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)

def validate(root: Path) -> str:
    points = load_points(root)
    urls = [build_url(point) for point in points]
    if len(points) != 3 or len(set(urls)) != 3:
        raise ValueError("INVALID_TARGET_OR_QUERY_COUNT")
    for output in OUTPUTS:
        if Path(output).is_absolute() or ".." in Path(output).parts:
            raise ValueError("NON_RELATIVE_OUTPUT_PATH")
    return "PASS_TARGET_3_NETWORK_FETCH_RELATIVE_PATHS_LAMBETH_NON_ESTATE_25M_MAX10_MAX1MIB"

def run(root: Path, timeout: float) -> dict:
    points = load_points(root)
    evidence = []
    candidates = []
    for index, point in enumerate(points):
        url = build_url(point)
        accessed_at = now()
        status, raw, error = fetch(url, timeout)
        record = {
            "parcel_id": point["parcel_id"],
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": sha(url),
            "http_status": status,
            "record_scope": f"one bounded 25m Lambeth Non-Estate Property Buildings query; max {MAX_RECORDS} records",
            "proven_fields": ["query URL", "access time", "query SHA-256"],
        }
        if raw is None:
            bounded = f"LAMBETH_NON_ESTATE_PROPERTY_BUILDINGS_ERROR:{error}"
            record.update({
                "content_sha256": sha(bounded),
                "sha256_basis": "bounded_error_evidence_string",
                "relevant_record_ids_or_excerpt": bounded[:500],
                "candidate_count": 0,
            })
        else:
            record.update({
                "content_sha256": sha(raw),
                "sha256_basis": "raw_response_bytes",
            })
            try:
                payload = json.loads(raw.decode("utf-8"))
                if payload.get("error"):
                    bounded = json.dumps(payload["error"], sort_keys=True, separators=(",", ":"))[:1000]
                    record.update({
                        "relevant_record_ids_or_excerpt": bounded,
                        "candidate_count": 0,
                        "proven_fields": record["proven_fields"] + ["ArcGIS error response"],
                    })
                else:
                    features = payload.get("features") or []
                    record["candidate_count"] = len(features)
                    record["relevant_record_ids_or_excerpt"] = [
                        (feature.get("attributes") or {}).get("OBJECTID") for feature in features[:MAX_RECORDS]
                    ]
                    record["proven_fields"] = record["proven_fields"] + ["raw source attributes", "OBJECTID when present"]
                    for feature in features[:MAX_RECORDS]:
                        candidates.append({
                            "parcel_id": point["parcel_id"],
                            "source_url": url,
                            "attributes": feature.get("attributes") or {},
                            "source_candidate_only": True,
                            "property_type_bound": False,
                            "uprn_bound": False,
                        })
            except Exception as exc:
                bounded = f"JSON_PARSE_ERROR:{type(exc).__name__}:{exc}"
                record.update({
                    "relevant_record_ids_or_excerpt": bounded[:500],
                    "candidate_count": 0,
                    "proven_fields": record["proven_fields"] + ["raw response SHA-256"],
                })
        evidence.append(record)
        if index + 1 < len(points):
            time.sleep(1.2)

    completed = len(evidence)
    target = len(points)
    blocker = None if candidates else {
        "code": "LAMBETH_NON_ESTATE_PROPERTY_BUILDINGS_NO_USABLE_RESPONSE",
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
        "state": "CANDIDATES_PUBLISHED" if candidates else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": target,
        "previous_percent": 0.0,
        "progress_percent": round((completed / target) * 100, 6) if target else 0.0,
        "percent_increase": round((completed / target) * 100, 6) if target else 0.0,
        "validated_canonical_points": [point["parcel_id"] for point in points],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": evidence,
        "blocker": blocker,
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_NON_ESTATE_PROPERTY_BUILDINGS",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for rel in OUTPUTS:
        write_atomic(root / rel, result)
    return result

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    if args.validate_only:
        print(validate(root))
        return 0
    validate(root)
    print(json.dumps(run(root, args.timeout), ensure_ascii=False, separators=(",", ":")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
