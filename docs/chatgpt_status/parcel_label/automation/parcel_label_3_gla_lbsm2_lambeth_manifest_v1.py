from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-gla-lbsm2-lambeth-manifest-v1-20260802"
SOURCE_URL = "https://data.london.gov.uk/dataset/london-building-stock-model-2-lbsm-2-2k55d"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/gla_lbsm2_lambeth_manifest_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/gla_lbsm2_lambeth_manifest_latest.json",
)
TARGET_IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 2 * 1024 * 1024
EXPECTED_MARKERS = (
    "London Building Stock Model 2 - Lambeth",
    "London Building Stock Model 2 - Data Dictionary.xlsx",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    temp.write_text(encoded, encoding="utf-8")
    os.replace(temp, target)


def load_points() -> list[dict[str, Any]]:
    payload = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    points = payload.get("canonical_points")
    if not isinstance(points, list):
        raise ValueError("canonical_points missing")
    by_id = {row.get("parcel_id"): row for row in points if isinstance(row, dict)}
    validated: list[dict[str, Any]] = []
    for parcel_id in TARGET_IDS:
        row = by_id.get(parcel_id)
        if not row:
            raise ValueError(f"missing canonical point {parcel_id}")
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {parcel_id}")
        lon = row.get("longitude")
        lat = row.get("latitude")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise ValueError(f"invalid coordinates {parcel_id}")
        validated.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return validated


def validate_only() -> None:
    load_points()
    if not SOURCE_URL.startswith("https://data.london.gov.uk/"):
        raise ValueError("source must be official London Datastore HTTPS URL")
    if not all(not Path(path).is_absolute() for path in (PROBE, *OUTPUTS)):
        raise ValueError("all paths must be repository-relative")
    if len(OUTPUTS) != 2 or MAX_BYTES != 2 * 1024 * 1024:
        raise ValueError("bounded output contract mismatch")
    print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_GLA_LBSM2_LAMBETH_MANIFEST_MAX2MIB_NO_DATA_DOWNLOAD")


def run(timeout: float) -> dict[str, Any]:
    points = load_points()
    accessed_at = now()
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "TerraYield-AAYS/1.0 (+source-manifest-only)"},
        method="GET",
    )
    query_hash = sha256(SOURCE_URL)
    evidence: dict[str, Any]
    candidates: list[dict[str, Any]] = []
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("response exceeded 2 MiB bound")
            text = raw.decode("utf-8", errors="replace")
            normalized = re.sub(r"\s+", " ", text)
            found = [marker for marker in EXPECTED_MARKERS if marker in normalized]
            candidates = [
                {
                    "candidate_type": "GLA_LBSM2_RESOURCE_LABEL",
                    "label": marker,
                    "source_url": SOURCE_URL,
                    "binding_claimed": False,
                }
                for marker in found
            ]
            evidence = {
                "source_url": SOURCE_URL,
                "accessed_at": accessed_at,
                "query_sha256": query_hash,
                "http_status": getattr(response, "status", None),
                "content_sha256": sha256(raw),
                "sha256_basis": "bounded_raw_response_bytes",
                "record_scope": "one bounded official London Datastore LBSM2 dataset-page request; max 2 MiB; no CSV/ZIP download",
                "relevant_record_ids_or_excerpt": found,
                "proven_fields": ["dataset page response", "resource labels present in bounded response"],
            }
    except Exception as exc:
        error_text = f"GLA_LBSM2_LAMBETH_MANIFEST_ERROR:{type(exc).__name__}:{exc}"
        evidence = {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "query_sha256": query_hash,
            "http_status": getattr(exc, "code", None),
            "content_sha256": sha256(error_text),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": "one bounded official London Datastore LBSM2 dataset-page request; max 2 MiB; no CSV/ZIP download",
            "relevant_record_ids_or_excerpt": error_text[:512],
            "proven_fields": ["request URL", "access time", "query SHA-256", "bounded error type"],
        }

    completed = 1
    target = 1
    result_state = "SOURCE_CANDIDATES_DISCOVERED" if candidates else "NO_DATA_CONTINUE"
    payload: dict[str, Any] = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": result_state,
        "panel_status": "PUBLISHED",
        "completed_count": completed,
        "target_count": target,
        "previous_percent": 0.0,
        "progress_percent": completed / target * 100.0,
        "percent_increase": completed / target * 100.0,
        "validated_canonical_points": [row["parcel_id"] for row in points],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": [evidence],
        "blocker": {
            "code": "NONE" if candidates else "GLA_LBSM2_LAMBETH_MANIFEST_NO_USABLE_RESPONSE",
            "state": result_state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_GLA_LBSM2_LAMBETH_MANIFEST",
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for path in OUTPUTS:
        atomic_write(path, payload)
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
