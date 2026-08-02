from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-police-neighbourhood-coordinate-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/police_neighbourhood_coordinate_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/police_neighbourhood_coordinate_latest.json",
)
LOCATE_BASE = "https://data.police.uk/api/locate-neighbourhood"
DOC_LOCATE = "https://data.police.uk/docs/method/neighbourhood-locate/"
DOC_DETAIL = "https://data.police.uk/docs/method/neighbourhood/"
ABOUT = "https://data.police.uk/about/"
OGL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
TARGET_IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1_048_576
MAX_REQUESTS_PER_POINT = 2


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(value: bytes | str) -> str:
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()


def atomic_write(path: str, obj: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, target)


def canonical_points() -> list[dict[str, Any]]:
    payload = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    rows = {row["parcel_id"]: row for row in payload["canonical_points"]}
    points: list[dict[str, Any]] = []
    for parcel_id in TARGET_IDS:
        row = rows.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        longitude = float(row["longitude"])
        latitude = float(row["latitude"])
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            raise ValueError(f"invalid coordinate {parcel_id}")
        points.append({"parcel_id": parcel_id, "longitude": longitude, "latitude": latitude})
    return points


def fetch_json(url: str, timeout: float) -> tuple[bytes, Any, int | None, str]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "TerraYield-AAYS/1.0 bounded Police.uk neighbourhood coordinate research",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeded 1 MiB")
        payload = json.loads(raw.decode("utf-8"))
        return raw, payload, getattr(response, "status", None), response.geturl()


def run(timeout: float) -> dict[str, Any]:
    points = canonical_points()
    evidence: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []

    for point in points:
        accessed_at = now()
        requests_made = 0
        lat = point["latitude"]
        lon = point["longitude"]
        locate_url = LOCATE_BASE + "?" + urllib.parse.urlencode({"q": f"{lat},{lon}"})
        try:
            locate_raw, locate_payload, locate_status, locate_final_url = fetch_json(locate_url, timeout)
            requests_made = 1
            force = locate_payload.get("force") if isinstance(locate_payload, dict) else None
            neighbourhood_id = locate_payload.get("neighbourhood") if isinstance(locate_payload, dict) else None
            if not isinstance(force, str) or not force or not isinstance(neighbourhood_id, str) or not neighbourhood_id:
                raise ValueError("locate response missing force or neighbourhood")
            detail_url = f"https://data.police.uk/api/{urllib.parse.quote(force)}/{urllib.parse.quote(neighbourhood_id)}"
            detail_raw, detail_payload, detail_status, detail_final_url = fetch_json(detail_url, timeout)
            requests_made = 2
            if not isinstance(detail_payload, dict):
                raise ValueError("neighbourhood detail response was not an object")
            name = detail_payload.get("name")
            centre = detail_payload.get("centre")
            candidate = {
                "parcel_id": point["parcel_id"],
                "canonical_point": point,
                "force": force,
                "neighbourhood_id": neighbourhood_id,
                "neighbourhood_name": name if isinstance(name, str) and name.strip() else None,
                "neighbourhood_centre": centre if isinstance(centre, dict) else None,
                "force_neighbourhood_url": detail_payload.get("url_force") if isinstance(detail_payload.get("url_force"), str) else None,
                "candidate_context_only": True,
                "exact_parcel_binding_claimed": False,
                "property_type_binding_claimed": False,
            }
            candidates.append(candidate)
            evidence.append({
                "parcel_id": point["parcel_id"],
                "canonical_point": point,
                "source_url": detail_final_url,
                "locate_url": locate_final_url,
                "accessed_at": accessed_at,
                "content_sha256": digest(detail_raw),
                "locate_content_sha256": digest(locate_raw),
                "sha256_basis": "bounded_raw_json_response_bytes",
                "record_scope": "one official Police.uk locate-neighbourhood response plus one specific-neighbourhood response; maximum 1 MiB per response",
                "supports_fields": ["force identifier", "neighbourhood identifier", "neighbourhood name", "neighbourhood centre", "force neighbourhood URL"],
                "relevant_record_ids_or_excerpt": {
                    "force": force,
                    "neighbourhood": neighbourhood_id,
                    "name": candidate["neighbourhood_name"],
                },
                "documentation_urls": [DOC_LOCATE, DOC_DETAIL],
                "license_or_terms_url": ABOUT,
                "open_government_licence_url": OGL,
                "locate_http_status": locate_status,
                "detail_http_status": detail_status,
                "requests_made": requests_made,
            })
        except Exception as exc:
            message = f"POLICE_NEIGHBOURHOOD_COORDINATE_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({
                "parcel_id": point["parcel_id"],
                "canonical_point": point,
                "source_url": locate_url,
                "accessed_at": accessed_at,
                "content_sha256": digest(message),
                "sha256_basis": "bounded_error_evidence_string",
                "record_scope": "one bounded official Police.uk coordinate-to-neighbourhood attempt; maximum one locate and one detail response",
                "supports_fields": ["Police.uk coordinate neighbourhood lookup availability"],
                "relevant_record_ids_or_excerpt": message[:512],
                "documentation_urls": [DOC_LOCATE, DOC_DETAIL],
                "license_or_terms_url": ABOUT,
                "open_government_licence_url": OGL,
                "http_status": getattr(exc, "code", None),
                "requests_made": requests_made,
            })

    state = "POLICE_NEIGHBOURHOOD_CONTEXT_FOUND" if candidates else "NO_DATA_CONTINUE"
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": len(candidates),
        "candidate_rows": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": "NONE" if candidates else "POLICE_NEIGHBOURHOOD_NO_USABLE_RESPONSE_OR_NO_COORDINATE_RESULT",
            "state": state,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VALIDATE_POLICE_NEIGHBOURHOOD_CONTEXT_WITHOUT_EXACT_PARCEL_OR_PROPERTY_TYPE_INFERENCE"
            if candidates
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_POLICE_NEIGHBOURHOOD_COORDINATE"
        ),
        "login_or_api_key_used": False,
        "bulk_download_performed": False,
        "neighbourhood_boundary_or_crime_data_requested": False,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output_path in OUT:
        atomic_write(output_path, result)
    return result


def validate() -> None:
    points = canonical_points()
    if len(points) != 3:
        raise ValueError("target count")
    if any(Path(path).is_absolute() for path in (PROBE, *OUT)):
        raise ValueError("relative paths required")
    if not LOCATE_BASE.startswith("https://data.police.uk/api/"):
        raise ValueError("official Police.uk API required")
    if MAX_BYTES != 1_048_576 or MAX_REQUESTS_PER_POINT != 2:
        raise ValueError("bounds changed")
    if len(TARGET_IDS) != 3:
        raise ValueError("exactly three targets required")
    print("PASS_TARGET_3_POLICE_NEIGHBOURHOOD_COORDINATE_MAX2_REQUESTS_EACH_MAX1MIB_CONTEXT_ONLY")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0 or args.timeout > 30:
        raise ValueError("timeout must be >0 and <=30 seconds per request")
    if args.validate_only:
        validate()
        return
    result = run(args.timeout)
    print(f"PASS_{result['state']}_{result['completed_count']}_OF_{result['target_count']}")


if __name__ == "__main__":
    main()
