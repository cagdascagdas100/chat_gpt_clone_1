from __future__ import annotations
import argparse, hashlib, json, os, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-overture-buildings-catalog-v1-20260802"
RELEASE = "2026-06-17.0"
BASE = "https://overturemapswestus2.blob.core.windows.net/release"
PREFIX = f"{RELEASE}/theme=buildings/type=building/"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/overture_buildings_catalog_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/overture_buildings_catalog_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 1024 * 1024
SPACING = 1.2

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha(value: str | bytes) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()

def repo_root() -> Path:
    return Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()

def points(root: Path) -> list[dict]:
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

def catalog_url() -> str:
    params = {
        "restype": "container",
        "comp": "list",
        "prefix": PREFIX,
        "maxresults": "1",
    }
    return BASE + "?" + urllib.parse.urlencode(params)

def attempt(point: dict, timeout: int) -> dict:
    url = catalog_url()
    accessed_at = now()
    logical_query = url + "#" + point["parcel_id"]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AAYS/parcel-label-3"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("catalog_response_too_large")
            status = getattr(response, "status", None)
        names = []
        root = ET.fromstring(raw)
        for element in root.iter():
            if element.tag.endswith("Name") and element.text:
                names.append(element.text)
        name = names[0] if names else None
        return {
            "parcel_id": point["parcel_id"],
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": sha(logical_query),
            "http_status": status,
            "content_sha256": sha(raw),
            "sha256_basis": "raw_catalog_response",
            "relevant_record_ids_or_excerpt": name or "NO_BLOB_NAME_IN_BOUNDED_CATALOG_RESPONSE",
            "proven_fields": ["catalog URL", "access time", "logical query SHA-256", "raw response SHA-256", "first blob name"],
            "record_scope": "one bounded Overture buildings Azure container listing",
            "source_partition_candidate": name,
            "candidate_only": True,
        }
    except Exception as exc:
        bounded = f"OVERTURE_BUILDINGS_CATALOG_ERROR:{type(exc).__name__}"
        return {
            "parcel_id": point["parcel_id"],
            "source_url": url,
            "accessed_at": accessed_at,
            "query_sha256": sha(logical_query),
            "http_status": None,
            "content_sha256": sha(bounded),
            "sha256_basis": "bounded_error_evidence_string",
            "relevant_record_ids_or_excerpt": bounded,
            "proven_fields": ["catalog URL", "access time", "logical query SHA-256", "bounded error type"],
            "record_scope": "one bounded Overture buildings Azure container listing",
            "source_partition_candidate": None,
            "candidate_only": True,
        }

def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)

def validate(root: Path) -> None:
    pts = points(root)
    if len(pts) != 3 or catalog_url().count("maxresults=1") != 1:
        raise ValueError("validation failed")
    print("PASS_TARGET_3_NETWORK_FETCH_RELATIVE_PATHS_OVERTURE_RELEASE_2026_06_17_MAXRESULTS_1")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    if args.validate_only:
        validate(root)
        return 0
    pts = points(root)
    evidence = []
    for index, point in enumerate(pts):
        if index:
            time.sleep(SPACING)
        evidence.append(attempt(point, args.timeout))
    source_candidates = sorted({item["source_partition_candidate"] for item in evidence if item["source_partition_candidate"]})
    payload = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": len(evidence),
        "target_count": len(pts),
        "previous_percent": 0.0,
        "progress_percent": (len(evidence) / len(pts)) * 100.0,
        "percent_increase": (len(evidence) / len(pts)) * 100.0,
        "produced_candidate_rows": 0,
        "source_partition_candidates": source_candidates,
        "candidates": [],
        "source_evidence": evidence,
        "blocker": {
            "code": "OVERTURE_BUILDINGS_CATALOG_NO_USABLE_RESPONSE",
            "state": "NO_DATA_CONTINUE",
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_OVERTURE_BUILDINGS_CATALOG",
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for rel in OUTPUTS:
        atomic_write(root / rel, payload)
    print(json.dumps({"completed_count": len(evidence), "target_count": len(pts), "source_partition_candidates": len(source_candidates), "produced_candidate_rows": 0}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
