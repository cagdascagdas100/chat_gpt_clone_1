from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "parcel_label_3"
TASK_ID = "parcel-label-3-osm-nominatim-reverse-v1-20260801"
SOURCE_BASE = "https://nominatim.openstreetmap.org/reverse"
LICENSE_URL = "https://www.openstreetmap.org/copyright"
USAGE_POLICY_URL = "https://operations.osmfoundation.org/policies/nominatim/"
PROBE_PATH = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
WRITE_PATHS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/osm_nominatim_reverse_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/osm_nominatim_reverse_latest.json",
)
EXPECTED_IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
TARGET_COUNT = 3


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    partial.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(partial, path)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_points(repo: Path) -> list[dict[str, Any]]:
    payload = json.loads((repo / PROBE_PATH).read_text(encoding="utf-8-sig"))
    points = payload.get("canonical_points")
    if not isinstance(points, list) or len(points) != TARGET_COUNT:
        raise ValueError("CANONICAL_POINT_COUNT_NOT_3")
    normalized = []
    for item in points:
        if not isinstance(item, dict):
            raise ValueError("CANONICAL_POINT_NOT_OBJECT")
        parcel_id = str(item.get("parcel_id"))
        if parcel_id not in EXPECTED_IDS:
            raise ValueError("UNEXPECTED_PARCEL_ID")
        if item.get("geometry_type") != "Point" or item.get("point_valid") is not True:
            raise ValueError("CANONICAL_POINT_INVALID")
        normalized.append({
            "parcel_id": parcel_id,
            "latitude": float(item["latitude"]),
            "longitude": float(item["longitude"]),
        })
    normalized.sort(key=lambda row: EXPECTED_IDS.index(row["parcel_id"]))
    if tuple(row["parcel_id"] for row in normalized) != EXPECTED_IDS:
        raise ValueError("CANONICAL_POINT_IDS_MISMATCH")
    return normalized


def build_url(point: dict[str, Any]) -> str:
    params = {
        "format": "jsonv2",
        "lat": f'{point["latitude"]:.7f}',
        "lon": f'{point["longitude"]:.7f}',
        "zoom": "18",
        "addressdetails": "1",
        "extratags": "1",
        "namedetails": "1",
    }
    return SOURCE_BASE + "?" + urllib.parse.urlencode(params)


def fetch(url: str, timeout: int) -> tuple[bytes, int]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-parcel-label-3/1.0 (bounded research; https://github.com/cagdascagdas100/chat_gpt_clone_1)",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), int(response.status)


def normalize_candidate(point: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any] | None:
    required = ("place_id", "osm_type", "osm_id", "lat", "lon", "display_name")
    if any(payload.get(key) in (None, "") for key in required):
        return None
    result_lat = float(payload["lat"])
    result_lon = float(payload["lon"])
    address = payload.get("address") if isinstance(payload.get("address"), dict) else {}
    extratags = payload.get("extratags") if isinstance(payload.get("extratags"), dict) else {}
    namedetails = payload.get("namedetails") if isinstance(payload.get("namedetails"), dict) else {}
    return {
        "parcel_id": point["parcel_id"],
        "canonical_point": {
            "latitude": point["latitude"],
            "longitude": point["longitude"],
        },
        "nominatim_result": {
            "place_id": payload["place_id"],
            "osm_type": payload["osm_type"],
            "osm_id": payload["osm_id"],
            "latitude": result_lat,
            "longitude": result_lon,
            "category": payload.get("category"),
            "type": payload.get("type"),
            "name": payload.get("name"),
            "display_name": payload["display_name"],
            "address": address,
            "extratags": extratags,
            "namedetails": namedetails,
        },
        "distance_to_canonical_point_m": round(
            haversine_m(point["latitude"], point["longitude"], result_lat, result_lon), 1
        ),
        "candidate_only": True,
        "exact_uprn_bound": False,
        "property_type_bound": False,
        "parcel_binding_claimed": False,
    }


def run(repo: Path, timeout: int) -> dict[str, Any]:
    points = load_points(repo)
    attempts: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for index, point in enumerate(points):
        url = build_url(point)
        evidence: dict[str, Any] = {
            "parcel_id": point["parcel_id"],
            "source_url": url,
            "accessed_at": utc_now(),
            "http_status": None,
            "content_sha256": None,
            "sha256_basis": "raw_response_bytes",
            "relevant_record_ids_or_excerpt": None,
            "proven_fields": [
                "place_id", "osm_type", "osm_id", "lat", "lon", "category",
                "type", "display_name", "address", "extratags", "namedetails",
            ],
            "license_or_terms_url": LICENSE_URL,
            "usage_policy_url": USAGE_POLICY_URL,
        }
        try:
            body, status = fetch(url, timeout)
            evidence["http_status"] = status
            evidence["content_sha256"] = sha256_bytes(body)
            parsed = json.loads(body.decode("utf-8"))
            candidate = normalize_candidate(point, parsed)
            if candidate is None:
                evidence["relevant_record_ids_or_excerpt"] = "INCOMPLETE_NOMINATIM_RESPONSE"
            else:
                candidates.append(candidate)
                evidence["relevant_record_ids_or_excerpt"] = {
                    "place_id": candidate["nominatim_result"]["place_id"],
                    "osm_type": candidate["nominatim_result"]["osm_type"],
                    "osm_id": candidate["nominatim_result"]["osm_id"],
                }
        except Exception as exc:
            error_text = f"NOMINATIM_REVERSE_ERROR:{type(exc).__name__}"
            evidence["content_sha256"] = sha256_bytes(error_text.encode("utf-8"))
            evidence["sha256_basis"] = "bounded_error_evidence_string"
            evidence["relevant_record_ids_or_excerpt"] = error_text
        attempts.append(evidence)
        if index + 1 < len(points):
            time.sleep(1.1)

    completed_count = len(attempts)
    state = "PUBLISHED_CANDIDATE_ONLY" if candidates else "NO_DATA_CONTINUE"
    blocker = None if candidates else {
        "code": "OSM_NOMINATIM_REVERSE_NO_USABLE_RESPONSE",
        "state": "NO_DATA_CONTINUE",
        "candidate_research_blocked": False,
        "manual_action_required": False,
        "retry_unchanged_route": False,
    }
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": completed_count,
        "target_count": TARGET_COUNT,
        "previous_percent": 0.0,
        "progress_percent": round(100.0 * completed_count / TARGET_COUNT, 4),
        "percent_increase": round(100.0 * completed_count / TARGET_COUNT, 4),
        "produced_candidate_rows": len(candidates),
        "candidates": candidates,
        "source_evidence": attempts,
        "blocker": blocker,
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OSM_NOMINATIM",
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate_only() -> dict[str, Any]:
    assert TARGET_COUNT == len(EXPECTED_IDS) == 3
    assert urllib.parse.urlparse(SOURCE_BASE).hostname == "nominatim.openstreetmap.org"
    assert all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in WRITE_PATHS)
    assert not Path(PROBE_PATH).is_absolute() and ".." not in Path(PROBE_PATH).parts
    return {
        "state": "VALIDATED",
        "target_count": TARGET_COUNT,
        "expected_ids": list(EXPECTED_IDS),
        "resource_class": "network_fetch",
        "read_path": PROBE_PATH,
        "write_paths": list(WRITE_PATHS),
        "minimum_request_spacing_seconds": 1.1,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        print(json.dumps(validate_only(), ensure_ascii=False))
        return 0
    repo = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[4]
    result = run(repo, max(1, min(args.timeout, 60)))
    for relative in WRITE_PATHS:
        atomic_json(repo / relative, result)
    print(json.dumps({
        "state": result["state"],
        "completed_count": result["completed_count"],
        "target_count": result["target_count"],
        "produced_candidate_rows": result["produced_candidate_rows"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
