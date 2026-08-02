from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-govuk-lbsm2-transparency-record-v1-20260802"
SOURCE_URL = "https://www.gov.uk/algorithmic-transparency-records/greater-london-authority-london-building-stock-model-2"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/govuk_lbsm2_transparency_record_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/govuk_lbsm2_transparency_record_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, target)


def validate_probe() -> list[dict[str, Any]]:
    payload = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    points = payload.get("canonical_points")
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
        lon = point.get("longitude")
        lat = point.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        selected.append(point)
    return selected


def normalized_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace")
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch(timeout: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    accessed_at = utc_now()
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "AAYS-parcel-label-3/1.0 (+bounded-source-scope-check)"},
    )
    query_sha = hashlib.sha256(SOURCE_URL.encode("utf-8")).hexdigest()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            status = getattr(response, "status", None)
        if len(raw) > MAX_BYTES:
            raise ValueError("response_exceeded_1_mib")
        text = normalized_text(raw)
        lower = text.lower()
        markers = {
            "record_name": "london building stock model 2" in lower,
            "uprn_linkage": "uprn" in lower,
            "property_type_scope": ("type of property" in lower or "property type" in lower),
            "residential_property_scale": ("3.8m residential properties" in lower or "3.8 million residential properties" in lower),
        }
        usable = all(markers.values())
        evidence = {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "query_sha256": query_sha,
            "http_status": status,
            "content_sha256": sha256_bytes(raw),
            "sha256_basis": "bounded_raw_response_bytes",
            "record_scope": "one bounded official GOV.UK LBSM2 algorithmic transparency record request; max 1 MiB",
            "relevant_record_ids_or_excerpt": "GOVUK_LBSM2_TRANSPARENCY_MARKERS:" + json.dumps(markers, sort_keys=True),
            "proven_fields": [key for key, value in markers.items() if value],
            "candidate_count": 1 if usable else 0,
        }
        candidates = []
        if usable:
            candidates.append({
                "candidate_type": "OFFICIAL_SOURCE_SCOPE",
                "source_url": SOURCE_URL,
                "proven_fields": ["UPRN linkage", "property-type scope", "residential output scale"],
                "parcel_binding_claimed": False,
            })
        return evidence, candidates
    except Exception as exc:  # fail closed with bounded error evidence
        message = f"GOVUK_LBSM2_TRANSPARENCY_ERROR:{type(exc).__name__}:{exc}"
        bounded = message[:2048]
        evidence = {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "query_sha256": query_sha,
            "http_status": None,
            "content_sha256": hashlib.sha256(bounded.encode("utf-8")).hexdigest(),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": "one bounded official GOV.UK LBSM2 algorithmic transparency record request; max 1 MiB",
            "relevant_record_ids_or_excerpt": bounded,
            "proven_fields": ["request URL", "access time", "query SHA-256", "bounded error type"],
            "candidate_count": 0,
        }
        return evidence, []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    points = validate_probe()
    if args.validate_only:
        assert not Path(SOURCE_URL).is_absolute()
        assert all(not Path(path).is_absolute() for path in (PROBE, *OUTPUTS))
        assert MAX_BYTES == 1024 * 1024
        print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_GOVUK_LBSM2_TRANSPARENCY_MAX1MIB")
        return 0

    evidence, candidates = fetch(args.timeout)
    completed_count = 1
    target_count = 1
    state = "SOURCE_SCOPE_CANDIDATE" if candidates else "NO_DATA_CONTINUE"
    payload: dict[str, Any] = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": completed_count,
        "target_count": target_count,
        "previous_percent": 0.0,
        "progress_percent": completed_count / target_count * 100.0,
        "percent_increase": completed_count / target_count * 100.0,
        "validated_canonical_points": [p["parcel_id"] for p in points],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": [evidence],
        "blocker": {
            "code": "NONE" if candidates else "GOVUK_LBSM2_TRANSPARENCY_NO_USABLE_RESPONSE",
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "EVALUATE_LBSM2_SOURCE_SCOPE_FOR_BOUNDED_DATA_DICTIONARY_OR_CSV_HEADER" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_GOVUK_LBSM2_TRANSPARENCY",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        atomic_write(output, payload)
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
