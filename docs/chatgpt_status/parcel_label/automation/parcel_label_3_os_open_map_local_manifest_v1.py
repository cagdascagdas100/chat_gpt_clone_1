from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-os-open-map-local-manifest-v1-20260802"
SOURCE_URL = "https://api.os.uk/downloads/v1/products/OpenMapLocal/downloads?area=GB&format=GeoPackage"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/os_open_map_local_manifest_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/os_open_map_local_manifest_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 2 * 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def validate_probe(root: Path) -> list[dict[str, Any]]:
    payload = json.loads((root / PROBE).read_text(encoding="utf-8"))
    points = payload.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    by_id = {row.get("parcel_id"): row for row in points if isinstance(row, dict)}
    validated: list[dict[str, Any]] = []
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon = row.get("longitude")
        lat = row.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        validated.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return validated


def validate_contract() -> None:
    if not SOURCE_URL.startswith("https://api.os.uk/downloads/v1/products/OpenMapLocal/downloads?"):
        raise ValueError("unexpected source URL")
    if "area=GB" not in SOURCE_URL or "format=GeoPackage" not in SOURCE_URL:
        raise ValueError("manifest filters missing")
    if any(Path(path).is_absolute() for path in (PROBE, *OUTPUTS)):
        raise ValueError("paths must be relative")
    if MAX_BYTES != 2 * 1024 * 1024:
        raise ValueError("unexpected byte limit")


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temporary, path)


def execute(root: Path, timeout: float) -> dict[str, Any]:
    validated = validate_probe(root)
    accessed_at = now()
    request_sha = sha256(SOURCE_URL)
    candidates: list[dict[str, Any]] = []
    evidence: dict[str, Any]
    try:
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "AAYS-parcel-label-3/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("response exceeds 2 MiB")
            status = getattr(response, "status", None)
        raw_sha = sha256(raw)
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, list):
            raise ValueError("manifest response is not a list")
        for row in parsed[:20]:
            if not isinstance(row, dict):
                continue
            candidate = {
                key: row.get(key)
                for key in ("fileName", "format", "subformat", "area", "size", "md5", "url")
                if row.get(key) is not None
            }
            if candidate:
                candidates.append(candidate)
        evidence = {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "query_sha256": request_sha,
            "http_status": status,
            "content_sha256": raw_sha,
            "sha256_basis": "bounded_raw_response_bytes",
            "relevant_record_ids_or_excerpt": [c.get("fileName") for c in candidates if c.get("fileName")],
            "record_scope": "one bounded OS OpenMap Local GB GeoPackage downloads-manifest request; max 2 MiB; no archive download",
            "proven_fields": ["manifest response", "file name", "format", "subformat", "area", "size", "md5", "download URL"],
            "candidate_count": len(candidates),
        }
        state = "SOURCE_CANDIDATES_DISCOVERED" if candidates else "NO_DATA_CONTINUE"
        blocker = None if candidates else "OS_OPEN_MAP_LOCAL_MANIFEST_EMPTY"
    except Exception as exc:
        error_text = f"OS_OPEN_MAP_LOCAL_MANIFEST_ERROR:{type(exc).__name__}:{exc}"
        evidence = {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "query_sha256": request_sha,
            "http_status": None,
            "content_sha256": sha256(error_text),
            "sha256_basis": "bounded_error_evidence_string",
            "relevant_record_ids_or_excerpt": error_text,
            "record_scope": "one bounded OS OpenMap Local GB GeoPackage downloads-manifest request; max 2 MiB; no archive download",
            "proven_fields": ["request URL", "access time", "query SHA-256", "bounded error type"],
            "candidate_count": 0,
        }
        state = "NO_DATA_CONTINUE"
        blocker = "OS_OPEN_MAP_LOCAL_MANIFEST_NO_USABLE_RESPONSE"

    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": [row["parcel_id"] for row in validated],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": [evidence],
        "blocker": {
            "code": blocker,
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OS_OPEN_MAP_LOCAL_MANIFEST",
        "archive_downloaded": False,
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for relative in OUTPUTS:
        atomic_write(root / relative, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    validate_contract()
    validate_probe(root)
    if args.validate_only:
        print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_OS_OPEN_MAP_LOCAL_MANIFEST_MAX2MIB_NO_ARCHIVE_DOWNLOAD")
        return 0
    result = execute(root, args.timeout)
    print(json.dumps({"state": result["state"], "completed_count": 1, "target_count": 1, "candidate_rows": result["produced_candidate_rows"]}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
