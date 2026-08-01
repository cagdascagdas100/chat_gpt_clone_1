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
TASK_ID = "parcel-label-3-osm-overpass-building-v1-20260801"
SOURCE_URL = "https://overpass-api.de/api/interpreter"
DOCUMENTATION_URL = "https://wiki.openstreetmap.org/wiki/Overpass_API"
QUERY_LANGUAGE_URL = "https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL"
LICENSE_URL = "https://www.openstreetmap.org/copyright"
PROBE_PATH = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
WRITE_PATHS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/osm_overpass_building_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/osm_overpass_building_latest.json",
)
EXPECTED_IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
TARGET_COUNT = 3
RADIUS_METRES = 30
REQUEST_SPACING_SECONDS = 2.0
TAG_KEYS = (
    "building",
    "building:use",
    "building:levels",
    "amenity",
    "name",
    "addr:housenumber",
    "addr:street",
    "addr:postcode",
)


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
    normalized: list[dict[str, Any]] = []
    for item in points:
        if not isinstance(item, dict):
            raise ValueError("CANONICAL_POINT_NOT_OBJECT")
        parcel_id = str(item.get("parcel_id"))
        if parcel_id not in EXPECTED_IDS:
            raise ValueError("UNEXPECTED_PARCEL_ID")
        if item.get("geometry_type") != "Point" or item.get("point_valid") is not True:
            raise ValueError("CANONICAL_POINT_INVALID")
        normalized.append(
            {
                "parcel_id": parcel_id,
                "latitude": float(item["latitude"]),
                "longitude": float(item["longitude"]),
            }
        )
    normalized.sort(key=lambda row: EXPECTED_IDS.index(row["parcel_id"]))
    if tuple(row["parcel_id"] for row in normalized) != EXPECTED_IDS:
        raise ValueError("CANONICAL_POINT_IDS_MISMATCH")
    return normalized


def build_query(point: dict[str, Any]) -> str:
    lat = f'{point["latitude"]:.7f}'
    lon = f'{point["longitude"]:.7f}'
    return (
        '[out:json][timeout:25];'
        '('
        f'nwr(around:{RADIUS_METRES},{lat},{lon})["building"];'
        f'nwr(around:{RADIUS_METRES},{lat},{lon})["addr:housenumber"];'
        ');'
        'out center tags;'
    )


def fetch(query: str, timeout: int) -> tuple[bytes, int]:
    body = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        SOURCE_URL,
        data=body,
        method="POST",
        headers={
            "User-Agent": "AAYS-parcel-label-3/1.0 (bounded OSM research; https://github.com/cagdascagdas100/chat_gpt_clone_1)",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), int(response.status)


def element_coordinates(element: dict[str, Any]) -> tuple[float, float] | None:
    if element.get("lat") is not None and element.get("lon") is not None:
        return float(element["lat"]), float(element["lon"])
    center = element.get("center")
    if isinstance(center, dict) and center.get("lat") is not None and center.get("lon") is not None:
        return float(center["lat"]), float(center["lon"])
    return None


def normalize_elements(point: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
    elements = payload.get("elements")
    if not isinstance(elements, list):
        return []
    rows: list[dict[str, Any]] = []
    for element in elements:
        if not isinstance(element, dict):
            continue
        element_type = element.get("type")
        element_id = element.get("id")
        if element_type not in {"node", "way", "relation"} or not isinstance(element_id, int):
            continue
        tags = element.get("tags") if isinstance(element.get("tags"), dict) else {}
        selected_tags = {key: tags[key] for key in TAG_KEYS if key in tags}
        coordinates = element_coordinates(element)
        if not selected_tags and coordinates is None:
            continue
        result: dict[str, Any] = {
            "parcel_id": point["parcel_id"],
            "canonical_point": {
                "latitude": point["latitude"],
                "longitude": point["longitude"],
            },
            "osm_element": {
                "osm_type": element_type,
                "osm_id": element_id,
                "raw_selected_tags": selected_tags,
            },
            "candidate_only": True,
            "exact_parcel_bound": False,
            "uprn_bound": False,
            "property_type_bound": False,
        }
        if coordinates is not None:
            lat, lon = coordinates
            result["osm_element"]["latitude"] = lat
            result["osm_element"]["longitude"] = lon
            result["distance_to_canonical_point_m"] = round(
                haversine_m(point["latitude"], point["longitude"], lat, lon), 1
            )
        rows.append(result)
    rows.sort(key=lambda row: (row["osm_element"]["osm_type"], row["osm_element"]["osm_id"]))
    return rows


def run(repo: Path, timeout: int) -> dict[str, Any]:
    points = load_points(repo)
    attempts: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for index, point in enumerate(points):
        query = build_query(point)
        evidence: dict[str, Any] = {
            "parcel_id": point["parcel_id"],
            "source_url": SOURCE_URL,
            "accessed_at": utc_now(),
            "query_sha256": sha256_bytes(query.encode("utf-8")),
            "query_scope": {
                "radius_metres": RADIUS_METRES,
                "selectors": ["building", "addr:housenumber"],
                "output": "center tags",
            },
            "http_status": None,
            "content_sha256": None,
            "sha256_basis": "raw_response_bytes",
            "relevant_record_ids_or_excerpt": None,
            "proven_fields": [
                "osm_type",
                "osm_id",
                "lat/lon or center",
                "raw selected OSM tags",
            ],
            "documentation_url": DOCUMENTATION_URL,
            "query_language_url": QUERY_LANGUAGE_URL,
            "license_or_terms_url": LICENSE_URL,
        }
        try:
            body, status = fetch(query, timeout)
            evidence["http_status"] = status
            evidence["content_sha256"] = sha256_bytes(body)
            parsed = json.loads(body.decode("utf-8"))
            rows = normalize_elements(point, parsed)
            candidates.extend(rows)
            evidence["relevant_record_ids_or_excerpt"] = [
                {
                    "osm_type": row["osm_element"]["osm_type"],
                    "osm_id": row["osm_element"]["osm_id"],
                }
                for row in rows
            ]
        except Exception as exc:
            error_text = f"OVERPASS_BUILDING_ERROR:{type(exc).__name__}"
            evidence["content_sha256"] = sha256_bytes(error_text.encode("utf-8"))
            evidence["sha256_basis"] = "bounded_error_evidence_string"
            evidence["relevant_record_ids_or_excerpt"] = error_text
        attempts.append(evidence)
        if index + 1 < len(points):
            time.sleep(REQUEST_SPACING_SECONDS)

    completed_count = len(attempts)
    state = "PUBLISHED_CANDIDATE_ONLY" if candidates else "NO_DATA_CONTINUE"
    blocker = None if candidates else {
        "code": "OSM_OVERPASS_BUILDING_NO_USABLE_RESPONSE",
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
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OSM_OVERPASS",
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate_only() -> dict[str, Any]:
    assert TARGET_COUNT == len(EXPECTED_IDS) == 3
    assert RADIUS_METRES == 30
    assert REQUEST_SPACING_SECONDS >= 2.0
    assert urllib.parse.urlparse(SOURCE_URL).hostname == "overpass-api.de"
    assert all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in WRITE_PATHS)
    assert not Path(PROBE_PATH).is_absolute() and ".." not in Path(PROBE_PATH).parts
    sample = build_query({"latitude": 51.0, "longitude": -0.1})
    assert '[out:json]' in sample and '["building"]' in sample and '["addr:housenumber"]' in sample
    return {
        "state": "VALIDATED",
        "target_count": TARGET_COUNT,
        "expected_ids": list(EXPECTED_IDS),
        "resource_class": "network_fetch",
        "read_path": PROBE_PATH,
        "write_paths": list(WRITE_PATHS),
        "radius_metres": RADIUS_METRES,
        "request_spacing_seconds": REQUEST_SPACING_SECONDS,
        "candidate_only": True,
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
    print(
        json.dumps(
            {
                "state": result["state"],
                "completed_count": result["completed_count"],
                "target_count": result["target_count"],
                "produced_candidate_rows": result["produced_candidate_rows"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
