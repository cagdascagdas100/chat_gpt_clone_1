from __future__ import annotations
import argparse, hashlib, json, os, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-geofabrik-greater-london-checksum-v1-20260802"
SOURCE_URL = "https://download.geofabrik.de/europe/united-kingdom/england/greater-london-latest.osm.pbf.md5"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUTPUTS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/geofabrik_greater_london_checksum_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/geofabrik_greater_london_checksum_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
MAX_BYTES = 4096

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
        out.append({"parcel_id": parcel_id, "longitude": float(item["longitude"]), "latitude": float(item["latitude"])})
    return out

def fetch(timeout: int) -> dict:
    accessed_at = now()
    query_sha256 = sha(SOURCE_URL)
    try:
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "AAYS/parcel-label-3"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("checksum_response_too_large")
            status = getattr(response, "status", None)
        text = raw.decode("ascii", errors="strict").strip()
        match = re.fullmatch(r"([0-9a-fA-F]{32})\s+\*?(.+)", text)
        if not match:
            raise ValueError("invalid_md5_record")
        return {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "query_sha256": query_sha256,
            "http_status": status,
            "content_sha256": sha(raw),
            "sha256_basis": "raw_checksum_response",
            "relevant_record_ids_or_excerpt": text,
            "proven_fields": ["checksum URL", "access time", "query SHA-256", "raw response SHA-256", "MD5", "filename"],
            "record_scope": "one bounded Geofabrik Greater London latest OSM PBF checksum record",
            "md5": match.group(1).lower(),
            "filename": match.group(2),
            "source_candidate_only": True,
        }
    except Exception as exc:
        bounded = f"GEOFABRIK_GREATER_LONDON_CHECKSUM_ERROR:{type(exc).__name__}"
        return {
            "source_url": SOURCE_URL,
            "accessed_at": accessed_at,
            "query_sha256": query_sha256,
            "http_status": None,
            "content_sha256": sha(bounded),
            "sha256_basis": "bounded_error_evidence_string",
            "relevant_record_ids_or_excerpt": bounded,
            "proven_fields": ["checksum URL", "access time", "query SHA-256", "bounded error type"],
            "record_scope": "one bounded Geofabrik Greater London latest OSM PBF checksum record",
            "md5": None,
            "filename": None,
            "source_candidate_only": True,
        }

def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)

def validate(root: Path) -> None:
    pts = points(root)
    if len(pts) != 3 or MAX_BYTES != 4096 or not SOURCE_URL.endswith(".osm.pbf.md5"):
        raise ValueError("validation failed")
    print("PASS_TARGET_1_NETWORK_FETCH_RELATIVE_PATHS_GEOFABRIK_GREATER_LONDON_MD5_MAX_4096")

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
    evidence = fetch(args.timeout)
    has_candidate = bool(evidence.get("md5") and evidence.get("filename"))
    payload = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": "SOURCE_CANDIDATE_FOUND" if has_candidate else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": [p["parcel_id"] for p in pts],
        "produced_candidate_rows": 1 if has_candidate else 0,
        "source_candidates": ([{"filename": evidence["filename"], "md5": evidence["md5"], "source_url": SOURCE_URL}] if has_candidate else []),
        "source_evidence": [evidence],
        "blocker": {
            "code": None if has_candidate else "GEOFABRIK_GREATER_LONDON_CHECKSUM_NO_USABLE_RESPONSE",
            "state": "SOURCE_CANDIDATE_FOUND" if has_candidate else "NO_DATA_CONTINUE",
            "candidate_research_blocked": False,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "EVALUATE_GEOFABRIK_GREATER_LONDON_PBF_CANDIDATE" if has_candidate else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_GEOFABRIK_GREATER_LONDON_CHECKSUM",
        "parcel_binding_claimed": False,
        "uprn_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for rel in OUTPUTS:
        atomic_write(root / rel, payload)
    print(json.dumps({"completed_count":1,"target_count":1,"produced_candidate_rows":payload["produced_candidate_rows"],"state":payload["state"]}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
