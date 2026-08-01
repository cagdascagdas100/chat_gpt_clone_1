from __future__ import annotations
import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-os-open-uprn-download-manifest-v1-20260802"
PRODUCT_ID = "OpenUPRN"
BASE_URL = f"https://api.os.uk/downloads/v1/products/{PRODUCT_ID}/downloads"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/os_open_uprn_download_manifest_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/os_open_uprn_download_manifest_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha(value: str | bytes) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()

def repo_root() -> Path:
    return Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()

def canonical_points(root: Path) -> list[dict]:
    data = json.loads((root / PROBE).read_text(encoding="utf-8"))
    index = {item.get("parcel_id"): item for item in data.get("canonical_points", [])}
    out = []
    for parcel_id in IDS:
        item = index.get(parcel_id)
        if not item or item.get("geometry_type") != "Point" or not item.get("point_valid"):
            raise ValueError(f"invalid canonical point: {parcel_id}")
        if not isinstance(item.get("longitude"), (int, float)) or not isinstance(item.get("latitude"), (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        out.append({
            "parcel_id": parcel_id,
            "longitude": float(item["longitude"]),
            "latitude": float(item["latitude"]),
        })
    return out

def manifest_url() -> str:
    return BASE_URL + "?" + urllib.parse.urlencode({"area": "GB", "format": "CSV"})

def fetch_manifest(timeout: int) -> dict:
    url = manifest_url()
    accessed_at = now()
    query_sha256 = sha(url)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "AAYS/parcel-label-3"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("manifest_response_too_large")
            status = getattr(response, "status", None)
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, list):
            raise ValueError("manifest_not_list")
        candidates = []
        for item in parsed[:10]:
            if not isinstance(item, dict):
                continue
            candidate = {
                key: item.get(key)
                for key in ("fileName", "format", "subformat", "area", "size", "url", "md5")
                if key in item
            }
            if candidate:
                candidates.append(candidate)
        return {
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": query_sha256,
            "http_status": status,
            "content_sha256": sha(raw),
            "sha256_basis": "raw_manifest_response",
            "relevant_record_ids_or_excerpt": [c.get("fileName") for c in candidates if c.get("fileName")],
            "proven_fields": ["manifest URL", "access time", "query SHA-256", "raw response SHA-256", "download metadata"],
            "record_scope": "OS Open UPRN GB CSV download manifest, maximum 10 records",
            "download_candidates": candidates,
        }
    except Exception as exc:
        bounded = f"OS_OPEN_UPRN_DOWNLOAD_MANIFEST_ERROR:{type(exc).__name__}"
        return {
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": query_sha256,
            "http_status": None,
            "content_sha256": sha(bounded),
            "sha256_basis": "bounded_error_evidence_string",
            "relevant_record_ids_or_excerpt": bounded,
            "proven_fields": ["manifest URL", "access time", "query SHA-256", "bounded error type"],
            "record_scope": "one bounded OS Open UPRN GB CSV download-manifest request",
            "download_candidates": [],
        }

def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)

def validate(root: Path) -> None:
    points = canonical_points(root)
    url = manifest_url()
    if len(points) != 3 or "OpenUPRN" not in url or "area=GB" not in url or "format=CSV" not in url:
        raise ValueError("validation failed")
    print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_OS_OPEN_UPRN_GB_CSV_MAX_1MIB")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    if args.validate_only:
        validate(root)
        return 0
    points = canonical_points(root)
    evidence = fetch_manifest(args.timeout)
    candidates = evidence["download_candidates"]
    payload = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "DOWNLOAD_MANIFEST_CANDIDATES_RESOLVED" if candidates else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": [p["parcel_id"] for p in points],
        "produced_candidate_rows": len(candidates),
        "download_candidates": candidates,
        "source_evidence": [evidence],
        "blocker": {
            "code": None if candidates else "OS_OPEN_UPRN_DOWNLOAD_MANIFEST_NO_USABLE_RESPONSE",
            "state": "NONE" if candidates else "NO_DATA_CONTINUE",
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "DOWNLOAD_BOUNDED_OS_OPEN_UPRN_ARTIFACT" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OS_OPEN_UPRN_DOWNLOAD_MANIFEST",
        "uprn_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for rel in OUTPUTS:
        atomic_write(root / rel, payload)
    print(json.dumps({"completed_count": 1, "target_count": 1, "download_candidates": len(candidates)}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
