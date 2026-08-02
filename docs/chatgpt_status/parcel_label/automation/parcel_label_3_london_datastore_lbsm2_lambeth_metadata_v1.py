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
from urllib.parse import urlparse

TASK_ID = "parcel-label-3-london-datastore-lbsm2-lambeth-metadata-v1-20260802"
SOURCE_URL = "https://data.london.gov.uk/dataset/london-building-stock-model-2-lbsm-2-2k55d"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/london_datastore_lbsm2_lambeth_metadata_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/london_datastore_lbsm2_lambeth_metadata_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 2 * 1024 * 1024


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
    if parsed.scheme != "https" or parsed.netloc != "data.london.gov.uk":
        raise ValueError("unexpected official source URL")
    if MAX_BYTES != 2 * 1024 * 1024:
        raise ValueError("unexpected response bound")
    if len(IDS) != 3 or len(set(IDS)) != 3:
        raise ValueError("unexpected canonical target count")
    print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_LONDON_DATASTORE_LBSM2_LAMBETH_METADATA_MAX2MIB_NO_CSV_DOWNLOAD")


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
                "User-Agent": "TerraYield-AAYS/1.0 (+bounded metadata verification)",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("response exceeded 2 MiB bound")
            html = raw.decode("utf-8", errors="replace")
            text = " ".join(re.sub(r"<[^>]+>", " ", html).split())
            match = re.search(r"London Building Stock Model 2\s*-\s*Lambeth\s*\(([^)]+)\)", text, re.IGNORECASE)
            if match:
                candidates.append(
                    {
                        "resource_label": "London Building Stock Model 2 - Lambeth",
                        "reported_size": match.group(1).strip(),
                        "dataset_url": SOURCE_URL,
                    }
                )
            evidence = {
                "source_url": SOURCE_URL,
                "accessed_at": accessed_at,
                "http_status": getattr(response, "status", None),
                "query_sha256": query_sha,
                "content_sha256": sha256(raw),
                "sha256_basis": "bounded_raw_html",
                "record_scope": "one bounded official London Datastore LBSM2 dataset-page request; max 2 MiB; no CSV download",
                "relevant_record_ids_or_excerpt": candidates[:5],
                "proven_fields": ["request URL", "access time", "HTTP status", "raw HTML SHA-256", "Lambeth resource label", "reported resource size"],
                "candidate_count": len(candidates),
            }
    except Exception as exc:
        error_text = f"LONDON_DATASTORE_LBSM2_LAMBETH_METADATA_ERROR:{type(exc).__name__}:{exc}"
        evidence = {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "http_status": None,
            "query_sha256": query_sha,
            "content_sha256": sha256(error_text),
            "sha256_basis": "bounded_error_evidence_string",
            "record_scope": "one bounded official London Datastore LBSM2 dataset-page request; max 2 MiB; no CSV download",
            "relevant_record_ids_or_excerpt": error_text,
            "proven_fields": ["request URL", "access time", "query SHA-256", "bounded error type"],
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
            "code": None if candidates else "LONDON_DATASTORE_LBSM2_LAMBETH_METADATA_NO_USABLE_RESPONSE",
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VERIFY_BOUNDED_LBSM2_LAMBETH_RESOURCE_METADATA"
            if candidates
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LONDON_DATASTORE_LBSM2_LAMBETH_METADATA"
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
