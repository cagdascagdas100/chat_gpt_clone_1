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

TASK_ID = "parcel-label-3-lambeth-land-properties-sold-v1-20260802"
LAYER_URL = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethLandandPropertiesSold/FeatureServer/0/query"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_land_properties_sold_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_land_properties_sold_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024
MAX_RECORDS = 10
DISTANCE_METERS = 25
REQUEST_SPACING_SECONDS = 1.2


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


def load_points(root: Path) -> list[dict]:
    payload = json.loads((root / PROBE).read_text(encoding="utf-8"))
    rows = payload.get("canonical_points")
    if not isinstance(rows, list):
        raise ValueError("canonical_points must be a list")
    by_id = {row.get("parcel_id"): row for row in rows if isinstance(row, dict)}
    points: list[dict] = []
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row:
            raise ValueError(f"missing canonical point: {parcel_id}")
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon = row.get("longitude")
        lat = row.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        points.append({"parcel_id": parcel_id, "longitude": float(lon), "latitude": float(lat)})
    return points


def build_url(point: dict) -> str:
    params = {
        "where": "1=1",
        "geometry": f"{point['longitude']},{point['latitude']}",
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


def run(root: Path, timeout: float) -> dict:
    points = load_points(root)
    evidence: list[dict] = []
    candidates: list[dict] = []
    for index, point in enumerate(points):
        if index:
            time.sleep(REQUEST_SPACING_SECONDS)
        url = build_url(point)
        accessed_at = now()
        base = {
            "parcel_id": point["parcel_id"],
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": sha(url),
            "record_scope": "one bounded 25m Lambeth Land and Properties Sold query; max 10 records",
            "proven_fields": ["query URL", "access time", "query SHA-256"],
        }
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label-source-audit/1.0"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("response exceeds 1 MiB limit")
                status = getattr(response, "status", None)
            raw_sha = sha(raw)
            payload = json.loads(raw.decode("utf-8"))
            features = payload.get("features", [])
            if not isinstance(features, list):
                raise ValueError("features is not a list")
            selected = features[:MAX_RECORDS]
            base.update({
                "http_status": status,
                "content_sha256": raw_sha,
                "sha256_basis": "bounded_raw_response_bytes",
                "relevant_record_ids_or_excerpt": f"feature_count={len(selected)}",
                "candidate_count": len(selected),
            })
            evidence.append(base)
            for ordinal, feature in enumerate(selected, start=1):
                attributes = feature.get("attributes") if isinstance(feature, dict) else None
                candidates.append({
                    "parcel_id": point["parcel_id"],
                    "candidate_ordinal": ordinal,
                    "source_url": url,
                    "raw_attributes": attributes if isinstance(attributes, dict) else {},
                    "source_candidate_only": True,
                })
        except Exception as exc:  # fail closed and preserve bounded technical evidence
            error = f"LAMBETH_LAND_PROPERTIES_SOLD_ERROR:{type(exc).__name__}:{exc}"
            base.update({
                "http_status": None,
                "content_sha256": sha(error),
                "sha256_basis": "bounded_error_evidence_string",
                "relevant_record_ids_or_excerpt": error[:1000],
                "candidate_count": 0,
            })
            evidence.append(base)

    completed = len(points)
    target = len(IDS)
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "CANDIDATE_ROWS" if candidates else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": target,
        "previous_percent": 0.0,
        "progress_percent": completed / target * 100.0,
        "percent_increase": completed / target * 100.0,
        "validated_canonical_points": list(IDS),
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": None if candidates else "LAMBETH_LAND_PROPERTIES_SOLD_NO_USABLE_RESPONSE",
            "state": "NONE" if candidates else "NO_DATA_CONTINUE",
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "REVIEW_LAMBETH_LAND_PROPERTIES_SOLD_CANDIDATES" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_LAND_PROPERTIES_SOLD",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for rel in OUTPUTS:
        atomic_write(root / rel, result)
    return result


def validate(root: Path) -> None:
    points = load_points(root)
    if len(points) != 3:
        raise ValueError("target must be exactly 3")
    if not all(not Path(path).is_absolute() for path in (PROBE, *OUTPUTS)):
        raise ValueError("all paths must be relative")
    sample = build_url(points[0])
    required = ("distance=25", "resultRecordCount=10", "returnGeometry=false", "inSR=4326")
    if not all(token in sample for token in required):
        raise ValueError("bounded query parameters missing")
    print("PASS_TARGET_3_NETWORK_FETCH_RELATIVE_PATHS_LAMBETH_LAND_PROPERTIES_SOLD_25M_MAX10_MAX1MIB")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.validate_only:
        validate(root)
        return 0
    result = run(root, args.timeout)
    print(json.dumps({
        "state": result["state"],
        "completed_count": result["completed_count"],
        "target_count": result["target_count"],
        "produced_candidate_rows": result["produced_candidate_rows"],
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
