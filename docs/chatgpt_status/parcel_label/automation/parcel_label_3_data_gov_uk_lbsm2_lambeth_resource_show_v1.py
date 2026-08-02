from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

TASK_ID = "parcel-label-3-data-gov-uk-lbsm2-lambeth-resource-show-v1-20260802"
RESOURCE_ID = "7ed7c78d-82a4-4b28-9ab0-80ef863f0608"
SOURCE_URL = f"https://ckan.publishing.service.gov.uk/api/3/action/resource_show?id={RESOURCE_ID}"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/data_gov_uk_lbsm2_lambeth_resource_show_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/data_gov_uk_lbsm2_lambeth_resource_show_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_points(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    points = data.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    by_id = {row.get("parcel_id"): row for row in points if isinstance(row, dict)}
    selected: list[dict[str, Any]] = []
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon, lat = row.get("longitude"), row.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        selected.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return selected


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def validate_only() -> None:
    for value in (PROBE, *OUTPUTS):
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"path must be tracked relative: {value}")
    parsed = urlparse(SOURCE_URL)
    if parsed.scheme != "https" or parsed.netloc != "ckan.publishing.service.gov.uk":
        raise ValueError("unexpected official source URL")
    if "resource_show" not in parsed.path or RESOURCE_ID not in SOURCE_URL:
        raise ValueError("resource_show route or resource id missing")
    if MAX_BYTES != 1024 * 1024:
        raise ValueError("unexpected response bound")
    if len(IDS) != 3 or len(set(IDS)) != 3:
        raise ValueError(unexpected canonical target count)
    print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_DATA_GOV_UK_LBSM2_LAMBETH_RESOURCE_SHOW_MAX1MIB_NO_CSV_DOWNLOAD")


def run(timeout: int) -> dict[str, Any]:
    points = load_points(Path(PROBE))
    accessed_at = now()
    query_sha = sha256(SOURCE_URL)
    candidates: list[dict[str, Any]] = []
    evidence: dict[str, Any]
    try:
        request = urllib.request.Request(
            SOURCE_URL,
            headers={
                "User-Agent": "TerraYield-AAYS/1.0 (+bounded official resource metadata verification)",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("response exceeded 1 MiB bound")
            payload = json.loads(raw.decode("utf-8"))
            result = payload.get("result") if isinstance(payload, dict) and payload.get("success") is True else None
            if isinstance(result, dict) and result.get("id") == RESOURCE_ID:
                candidate = {
                    "resource_id": result.get("id"),
                    "name": result.get"name"),
                    "format": result.get("format"),
                    "url": result.get("url"),
                    "size": result.get("size"),
                    "created": result.get("created"),
                    "last_modified": result.get("last_modified"),
                    "package_id": result.get("package_id"),
                }
                candidates.append(candidate)
            evidence = {
                "source_url": SOURCE_URL,
                "accessed_at": accessed_at,
                "http_status": getattr(response, "status", None),
                "query_sha256": query_sha,
                "content_sha256": sha256(raw),
                "sha256_basis": "bounded_raw_json",
                "record_scope": "one bounded official data.gov.uk CKAN resource_show request; max 1 MiB; no CSV download",
                "relevant_record_ids_or_excerpt": candidates[:1],
                "proven_fields": ["resource id", "resource name", "format", "download URL", "reported size", "timestamps", "package id"],
                "candidate_count": len(candidates),
            }
    except Exception as exc:
        error_text = f"DATA_GOV_UK_LBSM2_LAMBETH_RESOURCE_SHOW_ERROR:{type(exc).__name__}:{exc}"
        evidence = {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "http_status": None,
            "query_sha256": query_sha,
            "content_sha256": sha256(error_text),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": "one bounded official data.gov.uk CKAN resource_show request; max 1 MiB; no CSV download",
            "relevant_record_ids_or_excerpt": error_text,
            "proven_fields": ["request URL", "resource id", "access time", "query SHA-256", "bounded error type"],
            "candidate_count": 0,
        }

    state = "SOURCE_METADATA_CANDIDATES" if candidates else "NO_DATA_CONTINUE"
    payload = {
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
        "validated_canonical_points": [p["parcel_id"] for p in points],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": [evidence],
        "blocker": {
            "code": None if candidates else "DATA_GOV_UK_LBSM2_LAMBETH_RESOURCE_SHOW_NO_USABLE_RESPONSE",
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VERIFY_BOUNDED_LBSM2_LAMBETH_RESOURCE_URL"
            if candidates
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_DATA_GOV_UK_LBSM2_LAMBETH_RESOURCE_SHOW"
        ),
        "csv_downloaded": False,
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        atomic_write(Path(output), payload)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_only()
        return 0
    run(args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
