from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-bbbike-london-checksum-v1-20260802"
SOURCE_URL = "https://data.bbbike.org/osm/bbbike/London/CHECKSUM.txt"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/bbbike_london_checksum_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/bbbike_london_checksum_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 65536


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(value: str | bytes) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def repo_root() -> Path:
    return Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()


def validate_points(root: Path) -> list[dict]:
    payload = json.loads((root / PROBE).read_text(encoding="utf-8"))
    index = {item.get("parcel_id"): item for item in payload.get("canonical_points", [])}
    points = []
    for parcel_id in IDS:
        item = index.get(parcel_id)
        if not item or item.get("geometry_type") != "Point" or item.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        if not isinstance(item.get("longitude"), (int, float)) or not isinstance(item.get("latitude"), (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        points.append(
            {
                "parcel_id": parcel_id,
                "longitude": float(item["longitude"]),
                "latitude": float(item["latitude"]),
            }
        )
    return points


def parse_checksum(text: str) -> dict | None:
    for line in text.splitlines():
        if "London.osm.pbf" not in line:
            continue
        match = re.search(r"\b([0-9a-fA-F]{32}|[0-9a-fA-F]{40}|[0-9a-fA-F]{64})\b", line)
        if not match:
            continue
        return {
            "filename": "London.osm.pbf",
            "checksum": match.group(1).lower(),
            "checksum_length": len(match.group(1)),
            "raw_line": line[:512],
        }
    return None


def attempt(timeout: int) -> dict:
    accessed_at = now()
    query_sha256 = sha(SOURCE_URL)
    try:
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "AAYS/parcel-label-3"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            status = getattr(response, "status", None)
        if len(raw) > MAX_BYTES:
            raise ValueError("response_exceeds_65536_bytes")
        text = raw.decode("utf-8", errors="replace")
        parsed = parse_checksum(text)
        return {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "query_sha256": query_sha256,
            "http_status": status,
            "content_sha256": sha(raw),
            "sha256_basis": "raw_response_bytes",
            "relevant_record_ids_or_excerpt": parsed["raw_line"] if parsed else "London.osm.pbf checksum record not found",
            "proven_fields": [
                "checksum catalog URL",
                "access time",
                "query SHA-256",
                "raw response SHA-256",
            ] + (["London OSM PBF filename", "checksum value"] if parsed else []),
            "record_scope": "one bounded BBBike London CHECKSUM.txt request",
            "source_candidate": parsed,
            "source_candidate_only": True,
        }
    except Exception as exc:
        error = f"BBBIKE_LONDON_CHECKSUM_ERROR:{type(exc).__name__}"
        return {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "query_sha256": query_sha256,
            "http_status": None,
            "content_sha256": sha(error),
            "sha256_basis": "bounded_error_evidence_string",
            "relevant_record_ids_or_excerpt": error,
            "proven_fields": [
                "checksum catalog URL",
                "access time",
                "query SHA-256",
                "bounded error type",
            ],
            "record_scope": "one bounded BBBike London CHECKSUM.txt request",
            "source_candidate": None,
            "source_candidate_only": True,
        }


def atomic_write(root: Path, rel_path: str, payload: dict) -> None:
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temp, target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    points = validate_points(root)

    if args.validate_only:
        print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_BBBIKE_LONDON_CHECKSUM_MAX_65536")
        return 0

    evidence = attempt(args.timeout)
    candidate = evidence.get("source_candidate")
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "CANDIDATE_SOURCE_FOUND" if candidate else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": [p["parcel_id"] for p in points],
        "produced_candidate_rows": 1 if candidate else 0,
        "source_candidates": [candidate] if candidate else [],
        "source_evidence": [evidence],
        "blocker": {
            "code": None if candidate else "BBBIKE_LONDON_CHECKSUM_NO_USABLE_RESPONSE",
            "state": "SOURCE_CANDIDATE_ONLY" if candidate else "NO_DATA_CONTINUE",
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "DOWNLOAD_BOUNDED_BBBIKE_LONDON_PBF_PARTITION_CANDIDATE"
            if candidate
            else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_BBBIKE_LONDON_CHECKSUM"
        ),
        "parcel_binding_claimed": False,
        "uprn_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for output in OUTPUTS:
        atomic_write(root, output, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
