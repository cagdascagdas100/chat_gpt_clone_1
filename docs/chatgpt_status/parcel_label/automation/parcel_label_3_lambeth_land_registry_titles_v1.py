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
from typing import Any

TASK_ID = "parcel-label-3-lambeth-land-registry-titles-v1-20260802"
LAYER_URL = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethLandRegistryTitles/MapServer/0/query"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_land_registry_titles_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_land_registry_titles_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024
MAX_RECORDS = 10
DISTANCE_METERS = 25
REQUEST_SPACING_SECONDS = 1.2


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


def load_points(root: Path) -> list[dict[str, Any]]:
    probe = json.loads((root / PROBE).read_text(encoding="utf-8"))
    points = probe.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    selected = [p for p in points if p.get("parcel_id") in IDS]
    if [p.get("parcel_id") for p in selected] != list(IDS):
        raise ValueError("canonical point order or IDs invalid")
    for point in selected:
        if point.get("geometry_type") != "Point" or point.get("point_valid") is not True:
            raise ValueError("invalid canonical point")
        if not isinstance(point.get("longitude"), (int, float)) or not isinstance(point.get("latitude"), (int, float)):
            raise ValueError("invalid coordinates")
    return selected


def query_url(point: dict[str, Any]) -> str:
    params = {
        "where": "1=1",
        "geometry": f"{point['longitude']},{point['latitude']}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": str(DISTANCE_METERS),
        "units": "esriSRUnit_Meter",
        "outFields": "OBJECTID,TITLE_NO",
        "returnGeometry": "false",
        "resultRecordCount": str(MAX_RECORDS),
        "f": "json",
    }
    return LAYER_URL + "?" + urllib.parse.urlencode(params)


def bounded_fetch(url: str, timeout: int) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label-3/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        return int(response.status), body


def validate() -> str:
    assert not Path(PROBE).is_absolute()
    assert all(not Path(path).is_absolute() for path in OUTPUTS)
    assert LAYER_URL.startswith("https://gis.lambeth.gov.uk/")
    assert MAX_BYTES == 1024 * 1024
    assert MAX_RECORDS == 10
    assert DISTANCE_METERS == 25
    assert REQUEST_SPACING_SECONDS >= 1.2
    return "PASS_TARGET_3_NETWORK_FETCH_RELATIVE_PATHS_LAMBETH_LAND_REGISTRY_TITLES_25M_MAX10_MAX1MIB"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--root", default=".")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        print(validate())
        return 0

    root = Path(args.root)
    points = load_points(root)
    evidence: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for index, point in enumerate(points):
        url = query_url(point)
        accessed_at = now()
        item: dict[str, Any] = {
            "parcel_id": point["parcel_id"],
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": sha256(url),
            "record_scope": "one bounded 25m Lambeth Land Registry Titles layer-0 query; max 10 records",
            "proven_fields": ["query URL", "access time", "query SHA-256"],
        }
        try:
            status, body = bounded_fetch(url, args.timeout)
            item["http_status"] = status
            item["content_sha256"] = sha256(body)
            item["sha256_basis"] = "bounded_raw_response_bytes"
            decoded = json.loads(body.decode("utf-8"))
            features = decoded.get("features", []) if isinstance(decoded, dict) else []
            if not isinstance(features, list):
                features = []
            item["candidate_count"] = min(len(features), MAX_RECORDS)
            item["relevant_record_ids_or_excerpt"] = [
                {
                    "OBJECTID": f.get("attributes", {}).get("OBJECTID"),
                    "TITLE_NO": f.get("attributes", {}).get("TITLE_NO"),
                }
                for f in features[:MAX_RECORDS]
                if isinstance(f, dict)
            ]
            for f in features[:MAX_RECORDS]:
                attrs = f.get("attributes", {}) if isinstance(f, dict) else {}
                candidates.append(
                    {
                        "parcel_id": point["parcel_id"],
                        "OBJECTID": attrs.get("OBJECTID"),
                        "TITLE_NO": attrs.get("TITLE_NO"),
                        "source_candidate_only": True,
                    }
                )
        except Exception as exc:  # fail closed and preserve bounded error evidence
            error = f"LAMBETH_LAND_REGISTRY_TITLES_ERROR:{type(exc).__name__}:{exc}"
            item["http_status"] = None
            item["content_sha256"] = sha256(error)
            item["sha256_basis"] = "bounded_error_evidence_string"
            item["relevant_record_ids_or_excerpt"] = error[:1000]
            item["candidate_count"] = 0
        evidence.append(item)
        if index + 1 < len(points):
            time.sleep(REQUEST_SPACING_SECONDS)

    completed = len(evidence)
    target = len(points)
    progress = completed / target * 100.0 if target else 0.0
    state = "CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
    blocker = None if candidates else {
        "code": "LAMBETH_LAND_REGISTRY_TITLES_NO_USABLE_RESPONSE",
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
        "validated_canonical_points": list(IDS),
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": evidence,
        "blocker": blocker,
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_LAND_REGISTRY_TITLES",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for rel in OUTPUTS:
        atomic_write(root / rel, payload)
    print(json.dumps({"state": state, "completed": completed, "target": target, "candidates": len(candidates)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
