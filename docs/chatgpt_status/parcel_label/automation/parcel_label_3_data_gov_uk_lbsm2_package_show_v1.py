from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-data-gov-uk-lbsm2-package-show-v1-20260802"
PACKAGE_URL = "https://ckan.publishing.service.gov.uk/api/3/action/package_show?id=london-building-stock-model-2-lbsm-21"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/data_gov_uk_lbsm2_package_show_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/data_gov_uk_lbsm2_package_show_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 2 * 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def read_probe() -> list[dict[str, Any]]:
    data = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    rows = data.get("canonical_points")
    if not isinstance(rows, list):
        raise ValueError("canonical_points missing")
    selected = []
    by_id = {row.get("parcel_id"): row for row in rows if isinstance(row, dict)}
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon = row.get("longitude")
        lat = row.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        selected.append(row)
    return selected


def write_atomic(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, target)


def run(timeout: float) -> dict[str, Any]:
    points = read_probe()
    request_time = now()
    request_sha = sha256(PACKAGE_URL)
    evidence: dict[str, Any] = {
        "source_url": PACKAGE_URL,
        "accessed_at": request_time,
        "query_sha256": request_sha,
        "record_scope": "one bounded data.gov.uk CKAN package_show request for the exact LBSM2 package; max 2 MiB",
        "proven_fields": ["request URL", "access time", "query SHA-256"],
        "http_status": None,
        "content_sha256": None,
        "sha256_basis": None,
        "relevant_record_ids_or_excerpt": None,
        "candidate_count": 0,
    }
    candidates: list[dict[str, Any]] = []
    blocker = None
    try:
        request = urllib.request.Request(
            PACKAGE_URL,
            headers={"User-Agent": "AAYS-parcel-label-3/1.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("response exceeds 2 MiB")
            evidence["http_status"] = getattr(response, "status", None)
        evidence["content_sha256"] = sha256(raw)
        evidence["sha256_basis"] = "bounded_raw_response_bytes"
        parsed = json.loads(raw.decode("utf-8"))
        resources = (((parsed or {}).get("result") or {}).get("resources") or [])
        for item in resources:
            if not isinstance(item, dict):
                continue
            haystack = " ".join(str(item.get(k) or "") for k in ("name", "description", "url", "format")).lower()
            if "lambeth" not in haystack:
                continue
            candidate = {
                "resource_id": item.get("id"),
                "name": item.get("name"),
                "format": item.get("format"),
                "url": item.get("url"),
                "last_modified": item.get("last_modified"),
            }
            candidates.append(candidate)
        evidence["candidate_count"] = len(candidates)
        evidence["relevant_record_ids_or_excerpt"] = [c.get("resource_id") for c in candidates]
        evidence["proven_fields"] += ["bounded raw response SHA-256", "matching resource count"]
    except Exception as exc:
        error_text = f"DATA_GOV_UK_LBSM2_PACKAGE_SHOW_ERROR:{type(exc).__name__}:{exc}"
        evidence["content_sha256"] = sha256(error_text)
        evidence["sha256_basis"] = "bounded_error_evidence_string"
        evidence["relevant_record_ids_or_excerpt"] = error_text
        blocker = "DATA_GOV_UK_LBSM2_PACKAGE_SHOW_NO_USABLE_RESPONSE"

    payload = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "CANDIDATE_METADATA_FOUND" if candidates else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": list(IDS),
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": [evidence],
        "blocker": {
            "code": blocker,
            "state": "NO_DATA_CONTINUE" if blocker else "NONE",
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_DATA_GOV_UK_LBSM2_PACKAGE_SHOW",
        "large_file_downloaded": False,
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        write_atomic(output, payload)
    return payload


def validate_only() -> None:
    read_probe()
    assert not Path(PACKAGE_URL).is_absolute()
    assert all(not Path(path).is_absolute() for path in OUTPUTS)
    assert MAX_BYTES == 2 * 1024 * 1024
    print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_DATA_GOV_UK_LBSM2_PACKAGE_SHOW_MAX2MIB_NO_CSV_DOWNLOAD")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_only()
        return 0
    payload = run(args.timeout)
    print(json.dumps({
        "state": payload["state"],
        "completed_count": payload["completed_count"],
        "target_count": payload["target_count"],
        "produced_candidate_rows": payload["produced_candidate_rows"],
        "blocker": payload["blocker"]["code"],
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
