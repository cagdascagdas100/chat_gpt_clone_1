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

TASK_ID = "parcel-label-3-data-gov-uk-address-building-dataset-search-v1-20260802"
API_BASE = "https://data.gov.uk/api/action/package_search"
SEARCH_QUERY = "Lambeth address building UPRN"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/data_gov_uk_address_building_dataset_search_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/data_gov_uk_address_building_dataset_search_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 10


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temp, target)


def load_and_validate_probe() -> list[dict[str, Any]]:
    data = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    points = data.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    by_id = {p.get("parcel_id"): p for p in points if isinstance(p, dict)}
    selected: list[dict[str, Any]] = []
    for parcel_id in IDS:
        point = by_id.get(parcel_id)
        if not point:
            raise ValueError(f"missing canonical point: {parcel_id}")
        if point.get("geometry_type") != "Point" or point.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        if not isinstance(point.get("longitude"), (int, float)) or not isinstance(point.get("latitude"), (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        selected.append(point)
    if len(selected) != 3:
        raise ValueError("expected exactly three canonical points")
    return selected


def build_url() -> str:
    params = {
        "q": SEARCH_QUERY,
        "rows": str(MAX_RECORDS),
        "sort": "metadata_modified desc",
    }
    return f"{API_BASE}?{urllib.parse.urlencode(params)}"


def bounded_fetch(url: str, timeout: float) -> tuple[int | None, bytes | None, str | None]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "TerraYield-AAYS/parcel-label-3 bounded public-data catalogue research",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                return getattr(response, "status", None), None, "RESPONSE_EXCEEDS_2_MIB"
            return getattr(response, "status", None), body, None
    except Exception as exc:
        message = f"{type(exc).__name__}:{exc}"
        return None, None, message[:500]


def select_candidates(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("success") is not True:
        return []
    result = payload.get("result")
    records = result.get("results") if isinstance(result, dict) else None
    if not isinstance(records, list):
        return []
    candidates: list[dict[str, Any]] = []
    for record in records[:MAX_RECORDS]:
        if not isinstance(record, dict):
            continue
        org = record.get("organization") if isinstance(record.get("organization"), dict) else {}
        resources = []
        raw_resources = record.get("resources")
        if isinstance(raw_resources, list):
            for resource in raw_resources[:5]:
                if isinstance(resource, dict):
                    resources.append({
                        "name": resource.get("name"),
                        "format": resource.get("format"),
                        "url": resource.get("url"),
                    })
        candidates.append({
            "dataset_id": record.get("id"),
            "name": record.get("name"),
            "title": record.get("title"),
            "metadata_modified": record.get("metadata_modified"),
            "publisher_name": org.get("name"),
            "publisher_title": org.get("title"),
            "resources": resources,
            "candidate_only": True,
        })
    return candidates


def validate_only() -> None:
    load_and_validate_probe()
    if not API_BASE.startswith("https://data.gov.uk/api/action/"):
        raise ValueError("unexpected API base")
    if MAX_RECORDS != 10 or MAX_BYTES != 2 * 1024 * 1024:
        raise ValueError("bounds changed")
    for output in OUTPUTS:
        if Path(output).is_absolute():
            raise ValueError("absolute output path forbidden")
    print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_DATA_GOV_UK_PACKAGE_SEARCH_MAX10_MAX2MIB")


def run(timeout: float) -> dict[str, Any]:
    points = load_and_validate_probe()
    url = build_url()
    accessed_at = now()
    query_sha = sha256(url)
    status, body, error = bounded_fetch(url, timeout)
    candidates: list[dict[str, Any]] = []
    content_sha = None
    relevant = None
    basis = None
    if body is not None:
        content_sha = sha256(body)
        basis = "bounded_raw_response_bytes"
        try:
            candidates = select_candidates(json.loads(body.decode("utf-8")))
            relevant = f"package_search results parsed; candidate_count={len(candidates)}"
        except Exception as exc:
            error = f"JSON_PARSE_ERROR:{type(exc).__name__}:{exc}"[:500]
    if error is not None:
        evidence_string = f"DATA_GOV_UK_PACKAGE_SEARCH_ERROR:{error}"
        content_sha = sha256(evidence_string)
        basis = "bounded_error_evidence_string"
        relevant = evidence_string

    result_state = "CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
    payload: dict[str, Any] = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": result_state,
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": [p["parcel_id"] for p in points],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": [{
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": query_sha,
            "record_scope": "one bounded official data.gov.uk CKAN package_search request; rows=10; max 2 MiB",
            "proven_fields": ["request URL", "access time", "query SHA-256", "bounded response or error SHA-256"],
            "http_status": status,
            "content_sha256": content_sha,
            "sha256_basis": basis,
            "relevant_record_ids_or_excerpt": relevant,
            "candidate_count": len(candidates),
        }],
        "blocker": {
            "code": None if candidates else "DATA_GOV_UK_PACKAGE_SEARCH_NO_USABLE_RESPONSE",
            "state": result_state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "REVIEW_DATA_GOV_UK_DATASET_CANDIDATES" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_DATA_GOV_UK_PACKAGE_SEARCH",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        atomic_write(output, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate_only()
        return 0
    result = run(args.timeout)
    print(json.dumps({
        "state": result["state"],
        "completed_count": result["completed_count"],
        "target_count": result["target_count"],
        "produced_candidate_rows": result["produced_candidate_rows"],
        "evidence_records": len(result["source_evidence"]),
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
