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

TASK_ID = "parcel-label-3-postcodes-io-reverse-v1-20260802"
API_URL = "https://api.postcodes.io/postcodes"
DOC_URL = "https://postcodes.io/docs/postcode/reverse-geocode/"
OVERVIEW_URL = "https://postcodes.io/docs/overview/"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/postcodes_io_reverse_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/postcodes_io_reverse_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024
MAX_RECORDS = 3
RADIUS_METERS = 100
REQUEST_SPACING_SECONDS = 1.2


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def validate_paths() -> None:
    for value in (PROBE, *OUTPUTS):
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"non-relative path: {value}")
    if len(IDS) != 3 or MAX_RECORDS != 3 or RADIUS_METERS != 100 or MAX_BYTES != 1024 * 1024:
        raise ValueError("bounded-task constants changed")


def load_points() -> list[dict[str, Any]]:
    payload = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    points = payload.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    by_id = {row.get("parcel_id"): row for row in points if isinstance(row, dict)}
    selected: list[dict[str, Any]] = []
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row:
            raise ValueError(f"missing canonical point {parcel_id}")
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        lon = row.get("longitude")
        lat = row.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates {parcel_id}")
        selected.append({"parcel_id": parcel_id, "longitude": float(lon), "latitude": float(lat)})
    return selected


def request_point(point: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    query = urllib.parse.urlencode({
        "lon": f"{point['longitude']:.7f}",
        "lat": f"{point['latitude']:.7f}",
        "limit": str(MAX_RECORDS),
        "radius": str(RADIUS_METERS),
    })
    url = f"{API_URL}?{query}"
    evidence: dict[str, Any] = {
        "parcel_id": point["parcel_id"],
        "source_url": url,
        "accessed_at": now(),
        "query_sha256": sha256(url),
        "record_scope": "one bounded 100m nearest-postcode query; maximum 3 results",
        "proven_fields": ["query URL", "access time", "query SHA-256"],
        "http_status": None,
        "content_sha256": None,
        "sha256_basis": None,
        "relevant_record_ids_or_excerpt": None,
        "candidate_count": 0,
    }
    candidates: list[dict[str, Any]] = []
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "TerraYield-AAYS/1.0 bounded-open-source-research"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("response exceeds 1 MiB")
            evidence["http_status"] = getattr(response, "status", None)
            evidence["content_sha256"] = sha256(raw)
            evidence["sha256_basis"] = "bounded_raw_response"
            payload = json.loads(raw.decode("utf-8"))
        rows = payload.get("result")
        if isinstance(rows, list):
            for row in rows[:MAX_RECORDS]:
                if not isinstance(row, dict):
                    continue
                postcode = row.get("postcode")
                distance = row.get("distance")
                if not isinstance(postcode, str) or not isinstance(distance, (int, float)):
                    continue
                candidates.append({
                    "parcel_id": point["parcel_id"],
                    "postcode_candidate": postcode,
                    "distance_m": float(distance),
                    "quality": row.get("quality"),
                    "admin_district": row.get("admin_district"),
                    "region": row.get("region"),
                    "source_url": url,
                    "source_candidate_only": True,
                    "exact_parcel_binding": False,
                    "property_type_binding": False,
                    "uprn_binding": False,
                })
        evidence["candidate_count"] = len(candidates)
        evidence["relevant_record_ids_or_excerpt"] = ",".join(
            row["postcode_candidate"] for row in candidates
        ) or "NO_POSTCODE_CANDIDATES"
        evidence["proven_fields"] += ["HTTP status", "raw response SHA-256", "postcode candidates", "distance meters"]
    except Exception as exc:
        error = f"POSTCODES_IO_REVERSE_ERROR:{type(exc).__name__}:{exc}"
        evidence["content_sha256"] = sha256(error)
        evidence["sha256_basis"] = "bounded_error_evidence_string"
        evidence["relevant_record_ids_or_excerpt"] = error[:512]
        evidence["proven_fields"].append("bounded error type")
    return candidates, evidence


def atomic_write(path_value: str, payload: dict[str, Any]) -> None:
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    tmp.write_text(data, encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    validate_paths()
    if args.validate_only:
        print("PASS_TARGET_3_NETWORK_FETCH_RELATIVE_PATHS_POSTCODES_IO_REVERSE_100M_MAX3_MAX1MIB")
        return 0

    points = load_points()
    all_candidates: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for index, point in enumerate(points):
        candidates, record = request_point(point, args.timeout)
        all_candidates.extend(candidates)
        evidence.append(record)
        if index + 1 < len(points):
            time.sleep(REQUEST_SPACING_SECONDS)

    state = "DATA_CANDIDATES" if all_candidates else "NO_DATA_CONTINUE"
    blocker = None if all_candidates else {
        "code": "POSTCODES_IO_REVERSE_NO_USABLE_RESPONSE",
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
        "completed_count": len(points),
        "target_count": len(IDS),
        "previous_percent": 0.0,
        "progress_percent": len(points) / len(IDS) * 100.0,
        "percent_increase": len(points) / len(IDS) * 100.0,
        "validated_canonical_points": [row["parcel_id"] for row in points],
        "produced_candidate_rows": len(all_candidates),
        "source_candidates": all_candidates,
        "source_evidence": evidence,
        "blocker": blocker,
        "next_unverified_step": "VALIDATE_POSTCODE_CANDIDATES_WITH_DISTINCT_OFFICIAL_PROPERTY_SOURCE" if all_candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_POSTCODES_IO_REVERSE",
        "postcode_binding_claimed": False,
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        atomic_write(output, result)
    print(json.dumps({
        "state": state,
        "completed_count": len(points),
        "target_count": len(IDS),
        "produced_candidate_rows": len(all_candidates),
        "output_sha256": sha256(json.dumps(result, ensure_ascii=False, separators=(",", ":"))),
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
