from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-ckan-lbsm2-lambeth-download-head-v1-20260802"
RESOURCE_ID = "7ed7c78d-82a4-4b28-9ab0-80ef863f0608"
DATASET_URL = "https://ckan.publishing.service.gov.uk/dataset/london-building-stock-model-2-lbsm-21"
RESOURCE_PAGE_URL = f"{DATASET_URL}/resource/{RESOURCE_ID}"
HEAD_URL = f"{RESOURCE_PAGE_URL}/download"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/ckan_lbsm2_lambeth_download_head_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/ckan_lbsm2_lambeth_download_head_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
ALLOWED_HEADERS = (
    "content-length",
    "content-type",
    "etag",
    "last-modified",
    "location",
    "content-disposition",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_points() -> list[dict[str, Any]]:
    data = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    points = data.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    by_id = {p.get("parcel_id"): p for p in points if isinstance(p, dict)}
    selected = []
    for parcel_id in IDS:
        point = by_id.get(parcel_id)
        if not point:
            raise ValueError(f"missing canonical point {parcel_id}")
        if point.get("geometry_type") != "Point" or point.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        lon = point.get("longitude")
        lat = point.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates {parcel_id}")
        selected.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return selected


def atomic_write(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=target.parent) as handle:
        handle.write(raw)
        temp_name = handle.name
    os.replace(temp_name, target)


def validate_only() -> None:
    assert not Path(PROBE).is_absolute()
    assert all(not Path(path).is_absolute() for path in OUTPUTS)
    assert RESOURCE_ID in HEAD_URL
    assert HEAD_URL.endswith("/download")
    assert len(load_points()) == 3
    print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_CKAN_LBSM2_LAMBETH_DOWNLOAD_HEAD_NO_BODY")


def run(timeout: float) -> dict[str, Any]:
    points = load_points()
    accessed_at = now()
    request = urllib.request.Request(
        HEAD_URL,
        method="HEAD",
        headers={"User-Agent": "TerraYield-AAYS/parcel-label-3-evidence"},
    )
    query_sha = sha256(f"HEAD {HEAD_URL}")
    status = None
    final_url = None
    headers: dict[str, str] = {}
    error = None
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", None)
            final_url = response.geturl()
            for key in ALLOWED_HEADERS:
                value = response.headers.get(key)
                if value is not None:
                    headers[key] = value
    except Exception as exc:
        error = f"CKAN_LBSM2_LAMBETH_DOWNLOAD_HEAD_ERROR:{type(exc).__name__}:{exc}"

    evidence_basis = json.dumps(
        {"status": status, "final_url": final_url, "headers": headers, "error": error},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    usable = status is not None and error is None
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "SOURCE_CANDIDATE" if usable else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": [point["parcel_id"] for point in points],
        "produced_candidate_rows": 1 if usable else 0,
        "source_candidates": [{
            "resource_id": RESOURCE_ID,
            "head_url": HEAD_URL,
            "http_status": status,
            "final_url": final_url,
            "headers": headers,
        }] if usable else [],
        "source_evidence": [{
            "source_url": HEAD_URL,
            "resource_page_url": RESOURCE_PAGE_URL,
            "accessed_at": accessed_at,
            "query_sha256": query_sha,
            "record_scope": "one official CKAN LBSM2 Lambeth resource download HEAD request; no response body read",
            "proven_fields": ["request URL", "access time", "query SHA-256"] + (
                ["HTTP status", "redirect/final URL", "selected response headers"] if usable else ["bounded error type"]
            ),
            "http_status": status,
            "final_url": final_url,
            "headers": headers,
            "content_sha256": sha256(evidence_basis),
            "sha256_basis": "canonicalized_head_metadata_or_bounded_error",
            "relevant_record_ids_or_excerpt": (
                f"RESOURCE_ID:{RESOURCE_ID};STATUS:{status};FINAL_URL:{final_url}"
                if usable else error
            ),
            "candidate_count": 1 if usable else 0,
        }],
        "blocker": {
            "code": None if usable else "CKAN_LBSM2_LAMBETH_DOWNLOAD_HEAD_NO_USABLE_RESPONSE",
            "state": "SOURCE_CANDIDATE" if usable else "NO_DATA_CONTINUE",
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VERIFY_CKAN_LBSM2_LAMBETH_RESOURCE_SCHEMA_WITH_BOUNDED_RANGE"
            if usable else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_CKAN_LBSM2_LAMBETH_DOWNLOAD_HEAD"
        ),
        "resource_body_downloaded": False,
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        atomic_write(output, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_only()
        return 0
    result = run(args.timeout)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
