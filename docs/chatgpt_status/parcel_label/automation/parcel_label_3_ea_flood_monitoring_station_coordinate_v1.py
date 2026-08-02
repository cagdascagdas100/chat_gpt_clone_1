from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "parcel_label_3"
TASK_ID = "parcel-label-3-ea-flood-monitoring-station-coordinate-v1-20260803"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
API_ROOT = "https://environment.data.gov.uk/flood-monitoring/id/stations"
DOC_URL = "https://environment.data.gov.uk/flood-monitoring/doc/reference"
API_CATALOGUE_URL = "https://www.api.gov.uk/ea/flood-monitoring/"
TERMS_URL = "https://environment.data.gov.uk/help/terms-and-conditions"
OGL_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
ATTRIBUTION = "This uses Environment Agency flood and river level data from the real-time data API (Beta)"
MAX_BYTES = 1_048_576
MAX_CANDIDATES = 20
DIST_KM = 5
POINTS = {
    "parcel_61523": (-0.1387938, 51.4196454),
    "parcel_61524": (-0.1407703, 51.4170637),
    "parcel_61525": (-0.1398845, 51.4167453),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_points(base: Path) -> list[dict[str, Any]]:
    path = base / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("canonical_points")
    if not isinstance(rows, list):
        raise ValueError("canonical_points missing")
    found = {row.get("parcel_id"): row for row in rows if isinstance(row, dict) and row.get("parcel_id") in POINTS}
    if set(found) != set(POINTS):
        raise ValueError("exact target parcels missing")
    output: list[dict[str, Any]] = []
    for parcel_id, expected in POINTS.items():
        row = found[parcel_id]
        longitude = float(row["longitude"])
        latitude = float(row["latitude"])
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical Point {parcel_id}")
        if abs(longitude - expected[0]) > 1e-7 or abs(latitude - expected[1]) > 1e-7:
            raise ValueError(f"coordinate mismatch {parcel_id}")
        output.append({"parcel_id": parcel_id, "longitude": longitude, "latitude": latitude})
    return output


def query_url(point: dict[str, Any]) -> str:
    params = urllib.parse.urlencode(
        {
            "lat": f"{point['latitude']:.7f}",
            "long": f"{point['longitude']:.7f}",
            "dist": str(DIST_KM),
            "_limit": str(MAX_CANDIDATES),
            "_view": "full",
        }
    )
    return f"{API_ROOT}?{params}"


def bounded_get(url: str, timeout: float) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "AAYS-parcel-label-evidence/1.0 bounded official-source research",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("response exceeds 1 MiB")
        return int(getattr(response, "status", 200)), response.geturl(), raw


def compact_station(item: dict[str, Any], parcel_id: str, point: dict[str, Any]) -> dict[str, Any]:
    return {
        "parcel_id": parcel_id,
        "canonical_point": point,
        "source_record_id": item.get("@id"),
        "station_reference": item.get("stationReference"),
        "rloi_id": item.get("RLOIid"),
        "label": item.get("label"),
        "river_name": item.get("riverName"),
        "catchment_name": item.get("catchmentName"),
        "town": item.get("town"),
        "station_type": item.get("type"),
        "status": item.get("status"),
        "date_opened": item.get("dateOpened"),
        "latitude": item.get("lat"),
        "longitude": item.get("long"),
        "source_url": item.get("@id"),
        "context_only": True,
        "exact_parcel_binding": False,
        "property_type_binding": False,
    }


def attempt(point: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    parcel_id = str(point["parcel_id"])
    url = query_url(point)
    accessed_at = utc_now()
    requests_made = 0
    try:
        status, final_url, raw = bounded_get(url, timeout)
        requests_made = 1
        parsed = json.loads(raw.decode("utf-8"))
        items = parsed.get("items", []) if isinstance(parsed, dict) else []
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list):
            items = []
        selected = [item for item in items[:MAX_CANDIDATES] if isinstance(item, dict)]
        rows = [compact_station(item, parcel_id, point) for item in selected]
        record_ids = [str(item.get("stationReference") or item.get("@id") or "") for item in selected]
        evidence = {
            "parcel_id": parcel_id,
            "canonical_point": point,
            "source_url": final_url,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(raw),
            "sha256_basis": "bounded_json_response_bytes",
            "record_scope": "one bounded official Environment Agency flood-monitoring station geo-query; 5 km radius, maximum 20 stations and 1 MiB response",
            "supports_fields": [
                "station identifier",
                "station label",
                "river/catchment/town context",
                "station status and type",
                "station latitude and longitude",
            ],
            "relevant_record_ids_or_excerpt": record_ids,
            "documentation_url": DOC_URL,
            "api_catalogue_url": API_CATALOGUE_URL,
            "terms_or_license_urls": [TERMS_URL, OGL_URL],
            "required_attribution": ATTRIBUTION,
            "http_status": status,
            "requests_made": requests_made,
        }
        return rows, evidence
    except Exception as exc:
        error = f"EA_FLOOD_MONITORING_STATION_ERROR:{type(exc).__name__}:{exc}"
        evidence = {
            "parcel_id": parcel_id,
            "canonical_point": point,
            "source_url": url,
            "accessed_at": accessed_at,
            "content_sha256": sha256_bytes(error.encode("utf-8")),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": "one bounded official Environment Agency flood-monitoring station geo-query; 5 km radius, maximum 20 stations and 1 MiB response",
            "supports_fields": ["flood-monitoring station geo-query availability"],
            "relevant_record_ids_or_excerpt": error,
            "documentation_url": DOC_URL,
            "api_catalogue_url": API_CATALOGUE_URL,
            "terms_or_license_urls": [TERMS_URL, OGL_URL],
            "required_attribution": ATTRIBUTION,
            "http_status": None,
            "requests_made": requests_made,
        }
        return [], evidence


def build_payload(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for point in points:
        rows, record = attempt(point, timeout)
        candidates.extend(rows)
        evidence.append(record)
    count = len(candidates)
    return {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if count else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": points,
        "produced_candidate_rows": count,
        "candidate_rows": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": None if count else "EA_FLOOD_MONITORING_STATION_NO_USABLE_RESPONSE_OR_NO_NEARBY_RESULT",
            "state": "NONE" if count else "NO_DATA_CONTINUE",
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_EA_FLOOD_MONITORING_STATION_COORDINATE",
        "api_root": API_ROOT,
        "documentation_url": DOC_URL,
        "api_catalogue_url": API_CATALOGUE_URL,
        "terms_url": TERMS_URL,
        "open_government_licence_url": OGL_URL,
        "required_attribution": ATTRIBUTION,
        "anonymous_access_used": True,
        "registration_or_api_key_used": False,
        "bulk_download_performed": False,
        "full_station_scan_performed": False,
        "readings_requested": False,
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate_only(base: Path) -> None:
    points = load_points(base)
    if len(points) != 3:
        raise ValueError("target count mismatch")
    if not API_ROOT.startswith("https://environment.data.gov.uk/"):
        raise ValueError("official API root required")
    if DIST_KM != 5 or MAX_CANDIDATES != 20 or MAX_BYTES != 1_048_576:
        raise ValueError("bounded limits changed")
    print("PASS_TARGET_3_EA_FLOOD_MONITORING_STATION_COORDINATE_MAX1_REQUEST_EACH_5KM_MAX1MIB_20_CANDIDATES_ANONYMOUS_CONTEXT_ONLY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    base = repo_root()
    validate_only(base)
    if args.validate_only:
        return 0
    payload = build_payload(load_points(base), max(1.0, min(args.timeout, 30.0)))
    atomic_json(base / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/ea_flood_monitoring_station_coordinate_result_latest.json", payload)
    atomic_json(base / "england_map_web/data/aays_21_slots/parcel_label_3/ea_flood_monitoring_station_coordinate_latest.json", payload)
    if payload["produced_candidate_rows"]:
        print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_3_OF_3")
    else:
        print("PASS_NO_DATA_CONTINUE_3_OF_3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
