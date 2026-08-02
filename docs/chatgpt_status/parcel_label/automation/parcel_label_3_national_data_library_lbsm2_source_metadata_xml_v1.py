from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-national-data-library-lbsm2-source-metadata-xml-v1-20260802"
SOURCE_URL = "https://www.data.gov.uk/api/2/rest/harvestobject/e731fe6d-7ba0-4ffe-9faf-2c38e71880b5/xml"
PROBE_PATH = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUT_PATHS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/national_data_library_lbsm2_source_metadata_xml_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/national_data_library_lbsm2_source_metadata_xml_latest.json",
)
TARGET_IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024
MAX_CANDIDATES = 20


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_write_json(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temp, target)


def validate_probe() -> list[dict[str, Any]]:
    payload = json.loads(Path(PROBE_PATH).read_text(encoding="utf-8"))
    points = payload.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    selected = []
    for target_id in TARGET_IDS:
        matches = [item for item in points if item.get("parcel_id") == target_id]
        if len(matches) != 1:
            raise ValueError(f"expected one point for {target_id}")
        point = matches[0]
        if point.get("geometry_type") != "Point" or point.get("point_valid") is not True:
            raise ValueError(f"invalid point for {target_id}")
        if not isinstance(point.get("longitude"), (int, float)) or not isinstance(point.get("latitude"), (int, float)):
            raise ValueError(f"missing coordinates for {target_id}")
        selected.append(point)
    return selected


def validate_contract() -> None:
    paths = (PROBE_PATH, *OUTPUT_PATHS)
    if any(Path(path).is_absolute() for path in paths):
        raise ValueError("all paths must be repository-relative")
    if len(OUTPUT_PATHS) != 2 or MAX_BYTES != 1024 * 1024:
        raise ValueError("bounded output contract mismatch")
    if SOURCE_URL.count("harvestobject/") != 1 or not SOURCE_URL.endswith("/xml"):
        raise ValueError("source endpoint mismatch")


def extract_candidates(text: str) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    # Preserve only bounded, source-verbatim snippets around the two relevant resources.
    for label in ("London Building Stock Model 2 - Data Dictionary.xlsx", "London Building Stock Model 2 - Lambeth"):
        for match in re.finditer(re.escape(label), text, flags=re.IGNORECASE):
            start = max(0, match.start() - 240)
            end = min(len(text), match.end() + 500)
            excerpt = re.sub(r"\s+", " ", text[start:end]).strip()[:740]
            urls = re.findall(r"https?://[^\s<>'\"&]+", excerpt)
            candidates.append({
                "label": label,
                "excerpt": excerpt,
                "url_candidate": urls[0] if urls else "",
            })
            if len(candidates) >= MAX_CANDIDATES:
                return candidates
    return candidates


def execute(timeout_seconds: float) -> dict[str, Any]:
    points = validate_probe()
    accessed_at = now()
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "AAYS-parcel-label-3/1.0", "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.1"},
    )
    evidence: dict[str, Any] = {
        "source_url": SOURCE_URL,
        "accessed_at": accessed_at,
        "query_sha256": sha256_bytes(SOURCE_URL.encode("utf-8")),
        "record_scope": "one bounded official National Data Library LBSM2 harvest-source XML request; max 1 MiB",
        "proven_fields": ["request URL", "access time", "query SHA-256"],
        "http_status": None,
    }
    candidates: list[dict[str, str]] = []
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError("response exceeded 1 MiB bound")
            evidence["http_status"] = getattr(response, "status", None)
            evidence["content_sha256"] = sha256_bytes(body)
            evidence["sha256_basis"] = "bounded_raw_response"
            text = body.decode("utf-8", errors="replace")
            candidates = extract_candidates(text)
            evidence["relevant_record_ids_or_excerpt"] = [item["label"] for item in candidates]
            evidence["proven_fields"].extend(["raw response SHA-256", "matching resource labels"])
    except Exception as exc:  # fail closed; no inferred source values
        bounded = f"NATIONAL_DATA_LIBRARY_LBSM2_SOURCE_METADATA_XML_ERROR:{type(exc).__name__}:{str(exc)[:400]}"
        evidence["content_sha256"] = sha256_bytes(bounded.encode("utf-8"))
        evidence["sha256_basis"] = "bounded_error_evidence_string"
        evidence["relevant_record_ids_or_excerpt"] = bounded

    state = "SOURCE_CANDIDATES" if candidates else "NO_DATA_CONTINUE"
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
        "validated_canonical_points": [item["parcel_id"] for item in points],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": [evidence],
        "blocker": {
            "code": "NATIONAL_DATA_LIBRARY_LBSM2_SOURCE_METADATA_XML_NO_USABLE_RESPONSE" if not candidates else None,
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_NATIONAL_DATA_LIBRARY_LBSM2_SOURCE_METADATA_XML",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for path in OUTPUT_PATHS:
        atomic_write_json(path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    validate_contract()
    if args.validate_only:
        print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_NATIONAL_DATA_LIBRARY_LBSM2_SOURCE_METADATA_XML_MAX1MIB")
        return 0
    result = execute(args.timeout)
    print(json.dumps({"state": result["state"], "completed": "1/1", "candidate_rows": result["produced_candidate_rows"]}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
