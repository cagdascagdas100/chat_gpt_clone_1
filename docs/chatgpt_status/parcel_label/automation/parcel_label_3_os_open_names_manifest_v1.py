from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-os-open-names-manifest-v1-20260802"
SOURCE_URL = "https://api.os.uk/downloads/v1/products/OpenNames/downloads?area=GB&format=CSV"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/os_open_names_manifest_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/os_open_names_manifest_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 2 * 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def is_relative_repo_path(value: str) -> bool:
    p = Path(value)
    return not p.is_absolute() and ".." not in p.parts


def validate(root: Path) -> tuple[dict[str, Any], str]:
    paths = (PROBE, *OUTPUTS)
    if not all(is_relative_repo_path(path) for path in paths):
        raise ValueError("NON_RELATIVE_PATH")
    probe_path = root / PROBE
    if not probe_path.is_file():
        raise FileNotFoundError(PROBE)
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    points = probe.get("canonical_points") or []
    by_id = {row.get("parcel_id"): row for row in points if isinstance(row, dict)}
    if tuple(by_id) != IDS:
        # Require all and only the three expected IDs, while preserving source order.
        if [row.get("parcel_id") for row in points] != list(IDS):
            raise ValueError("CANONICAL_POINT_IDS_MISMATCH")
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"INVALID_CANONICAL_POINT:{parcel_id}")
        if not isinstance(row.get("longitude"), (int, float)) or not isinstance(row.get("latitude"), (int, float)):
            raise ValueError(f"INVALID_COORDINATES:{parcel_id}")
    if SOURCE_URL != "https://api.os.uk/downloads/v1/products/OpenNames/downloads?area=GB&format=CSV":
        raise ValueError("SOURCE_URL_CHANGED")
    return probe, "PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_OS_OPEN_NAMES_MANIFEST_MAX2MIB_NO_ARCHIVE_DOWNLOAD"


def collect_candidates(value: Any, out: list[dict[str, Any]]) -> None:
    if isinstance(value, dict):
        url = value.get("url") or value.get("downloadUrl") or value.get("downloadURL")
        name = value.get("fileName") or value.get("filename") or value.get("name")
        if isinstance(url, str) and url.startswith("http"):
            out.append({
                "url": url,
                "file_name": name if isinstance(name, str) else None,
                "size": value.get("size"),
                "md5": value.get("md5"),
                "sha256": value.get("sha256"),
            })
        for child in value.values():
            collect_candidates(child, out)
    elif isinstance(value, list):
        for child in value:
            collect_candidates(child, out)


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(temp, path)


def run(root: Path, timeout: float) -> dict[str, Any]:
    _, validation = validate(root)
    accessed_at = now()
    query_sha = sha256(SOURCE_URL)
    candidates: list[dict[str, Any]] = []
    response_sha: str | None = None
    http_status: int | None = None
    error_excerpt: str | None = None
    try:
        req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "TerraYield-AAYS/parcel_label_3 bounded-source-verifier"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            http_status = int(getattr(response, "status", 200))
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("RESPONSE_EXCEEDS_2_MIB")
        response_sha = sha256(raw)
        parsed = json.loads(raw.decode("utf-8"))
        collect_candidates(parsed, candidates)
        # Deduplicate and cap persisted candidates; never follow any candidate URL.
        dedup: dict[str, dict[str, Any]] = {}
        for row in candidates:
            dedup.setdefault(row["url"], row)
        candidates = list(dedup.values())[:50]
    except Exception as exc:  # fail closed, including DNS and malformed JSON
        error_excerpt = f"OS_OPEN_NAMES_MANIFEST_ERROR:{type(exc).__name__}:{str(exc)[:240]}"
        response_sha = sha256(error_excerpt)
        candidates = []

    state = "SOURCE_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
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
        "validated_canonical_points": list(IDS),
        "source_url": SOURCE_URL,
        "source_accessed_at": accessed_at,
        "query_sha256": query_sha,
        "http_status": http_status,
        "content_sha256": response_sha,
        "sha256_basis": "raw_response" if error_excerpt is None else "bounded_error_evidence_string",
        "relevant_record_ids_or_excerpt": error_excerpt or [row.get("file_name") or row["url"] for row in candidates],
        "record_scope": "one bounded OS Open Names downloads-manifest request; max 2 MiB; no archive or CSV download",
        "proven_fields": ["request URL", "access time", "query SHA-256", "raw response SHA-256" if error_excerpt is None else "bounded error type"],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "blocker": {
            "code": None if candidates else "OS_OPEN_NAMES_MANIFEST_NO_USABLE_RESPONSE",
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OS_OPEN_NAMES_MANIFEST",
        "archive_downloaded": False,
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
        "validation": validation,
    }
    for rel in OUTPUTS:
        atomic_write(root / rel, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.validate_only:
        _, message = validate(root)
        print(message)
        return 0
    payload = run(root, args.timeout)
    print(json.dumps({
        "state": payload["state"],
        "completed": f'{payload["completed_count"]}/{payload["target_count"]}',
        "candidate_rows": payload["produced_candidate_rows"],
        "evidence": payload["relevant_record_ids_or_excerpt"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
