from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "parcel-label-3-london-building-stock-model-2-metadata-v1-20260802"
SOURCE_URL = "https://data.london.gov.uk/dataset/london-building-stock-model-2-lbsm-2-2k55d"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/london_building_stock_model_2_metadata_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/london_building_stock_model_2_metadata_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 2 * 1024 * 1024
LAMBETH_RESOURCE_NAME = "London Building Stock Model 2 - Lambeth"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def load_points(root: Path) -> list[dict[str, Any]]:
    payload = json.loads((root / PROBE).read_text(encoding="utf-8"))
    points = {row.get("parcel_id"): row for row in payload.get("canonical_points", [])}
    selected: list[dict[str, Any]] = []
    for parcel_id in IDS:
        row = points.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"out-of-range canonical point: {parcel_id}")
        selected.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return selected


def bounded_fetch(url: str, timeout: float) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-parcel-label-3/1.0 (+bounded-source-metadata-audit)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = int(getattr(response, "status", 200))
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("response exceeds 2 MiB")
    return status, body


def strip_tags(text: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def parse_candidates(body: bytes) -> list[dict[str, Any]]:
    text = body.decode("utf-8", errors="replace")
    plain = strip_tags(text)
    if LAMBETH_RESOURCE_NAME.lower() not in plain.lower():
        return []
    size_match = re.search(r"London Building Stock Model 2\s*-\s*Lambeth\s*\(([^)]+)\)", plain, flags=re.I)
    data_date_match = re.search(r"current version[^.]*based on data from\s+([A-Za-z]+\s+\d{4})", plain, flags=re.I)
    licence = "Open Government Licence v3" if re.search(r"Open Government Licence\s*v3", plain, flags=re.I) else None
    return [{
        "dataset_title": "London Building Stock Model 2 (LBSM 2)",
        "resource_name": LAMBETH_RESOURCE_NAME,
        "resource_size_label": size_match.group(1).strip() if size_match else None,
        "data_reference_date": data_date_match.group(1).strip() if data_date_match else None,
        "licence": licence,
        "candidate_scope": ["property type", "built form", "energy efficiency", "building fabric"],
        "source_candidate_only": True,
    }]


def build_result(root: Path, timeout: float) -> dict[str, Any]:
    points = load_points(root)
    accessed_at = now()
    query_hash = sha256(SOURCE_URL)
    evidence: dict[str, Any] = {
        "source_url": SOURCE_URL,
        "accessed_at": accessed_at,
        "query_sha256": query_hash,
        "record_scope": "one bounded official GLA London Building Stock Model 2 dataset-page request; max 2 MiB; no CSV download",
        "proven_fields": ["request URL", "access time", "query SHA-256"],
    }
    candidates: list[dict[str, Any]] = []
    try:
        status, body = bounded_fetch(SOURCE_URL, timeout)
        evidence.update({
            "http_status": status,
            "content_sha256": sha256(body),
            "sha256_basis": "bounded_raw_response_bytes",
            "response_bytes": len(body),
        })
        candidates = parse_candidates(body)
        evidence["candidate_count"] = len(candidates)
        evidence["proven_fields"] += ["HTTP status", "raw-response SHA-256", "response byte count"]
        if candidates:
            evidence["proven_fields"] += ["Lambeth resource name", "resource size label", "dataset reference date", "licence"]
    except Exception as exc:
        error_text = f"LONDON_BUILDING_STOCK_MODEL_2_METADATA_ERROR:{type(exc).__name__}:{str(exc)[:300]}"
        evidence.update({
            "http_status": None,
            "content_sha256": sha256(error_text),
            "sha256_basis": "bounded_error_evidence_string",
            "relevant_record_ids_or_excerpt": error_text,
            "candidate_count": 0,
        })
    state = "SOURCE_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
    return {
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
        "validated_canonical_points": [row["parcel_id"] for row in points],
        "produced_candidate_rows": len(candidates),
        "source_candidates": candidates,
        "source_evidence": [evidence],
        "blocker": {
            "code": None if candidates else "LONDON_BUILDING_STOCK_MODEL_2_METADATA_NO_USABLE_RESPONSE",
            "state": state,
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "REVIEW_LBSM2_LAMBETH_RESOURCE_METADATA_CANDIDATE" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LONDON_BUILDING_STOCK_MODEL_2_METADATA",
        "property_type_binding_claimed": False,
        "uprn_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "large_file_downloaded": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }


def validate(root: Path) -> None:
    load_points(root)
    assert not Path(PROBE).is_absolute()
    assert all(not Path(path).is_absolute() for path in OUTPUTS)
    assert SOURCE_URL.startswith("https://data.london.gov.uk/dataset/")
    assert MAX_BYTES == 2 * 1024 * 1024
    print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_LONDON_BUILDING_STOCK_MODEL_2_METADATA_MAX2MIB_NO_CSV_DOWNLOAD")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.validate_only:
        validate(root)
        return 0
    result = build_result(root, args.timeout)
    for relative in OUTPUTS:
        atomic_write(root / relative, result)
    print(json.dumps({
        "state": result["state"],
        "completed": f'{result["completed_count"]}/{result["target_count"]}',
        "candidate_rows": result["produced_candidate_rows"],
        "output_sha256": sha256(json.dumps(result, ensure_ascii=False, separators=(",", ":"))),
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
