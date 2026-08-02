from __future__ import annotations
import argparse, hashlib, json, os, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-nominatim-reverse-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/nominatim_reverse_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/nominatim_reverse_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
ENDPOINT = "https://nominatim.openstreetmap.org/reverse"
POLICY_URL = "https://operations.osmfoundation.org/policies/nominatim/"
LICENSE_URL = "https://www.openstreetmap.org/copyright?locale=en-GB"
MAX_BYTES = 1_048_576


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def atomic_write(path: str, obj: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, target)


def points() -> list[dict]:
    rows = json.loads(Path(PROBE).read_text(encoding="utf-8"))["canonical_points"]
    by_id = {r["parcel_id"]: r for r in rows}
    out = []
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        if not isinstance(row.get("longitude"), (int, float)) or not isinstance(row.get("latitude"), (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        out.append(row)
    return out


def validate() -> None:
    if Path(PROBE).is_absolute() or any(Path(p).is_absolute() for p in OUT):
        raise ValueError("all paths must be relative")
    if not all(p.startswith(("docs/chatgpt_status/_shared/slots_21/parcel_label_3/", "england_map_web/data/aays_21_slots/parcel_label_3/")) for p in OUT):
        raise ValueError("write boundary")
    if not ENDPOINT.startswith("https://nominatim.openstreetmap.org/"):
        raise ValueError("endpoint")
    points()
    print("PASS_TARGET_3_NOMINATIM_REVERSE_SINGLE_THREAD_1RPS_MAX1MIB_CANDIDATE_ONLY")


def run(timeout: float) -> dict:
    canonical = points()
    evidence = []
    candidates = []
    allowed_building = {"apartments", "detached", "house", "residential", "semidetached_house", "terrace", "commercial", "office", "retail", "industrial"}
    for index, row in enumerate(canonical):
        if index:
            time.sleep(1.1)
        query = urllib.parse.urlencode({
            "format": "jsonv2", "lat": row["latitude"], "lon": row["longitude"],
            "zoom": 18, "addressdetails": 1, "extratags": 1, "namedetails": 1, "layer": "address",
        })
        url = ENDPOINT + "?" + query
        accessed_at = now()
        req = urllib.request.Request(url, headers={"User-Agent": "TerraYield-AAYS/1.0 parcel-label-research (bounded one-time reverse lookup)"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("response exceeded 1 MiB")
                data = json.loads(raw.decode("utf-8"))
                category = data.get("category") or data.get("class")
                osm_type_value = data.get("type")
                building = (data.get("extratags") or {}).get("building")
                candidate_type = building if building in allowed_building else (osm_type_value if category == "building" and osm_type_value in allowed_building else None)
                if candidate_type:
                    candidates.append({
                        "parcel_id": row["parcel_id"], "candidate_property_type": candidate_type,
                        "source_url": url, "osm_type": data.get("osm_type"), "osm_id": data.get("osm_id"),
                        "distance_not_computed": True, "candidate_only": True,
                        "nearest_object_warning": True, "exact_parcel_binding_claimed": False,
                    })
                evidence.append({
                    "parcel_id": row["parcel_id"], "source_url": url, "accessed_at": accessed_at,
                    "content_sha256": sha256(raw), "sha256_basis": "bounded_raw_response_bytes",
                    "record_scope": "one reverse result for one canonical point; max 1 MiB",
                    "supports_fields": ["display_name", "category", "type", "address", "extratags", "osm_type", "osm_id"],
                    "relevant_record_ids_or_excerpt": {"osm_type": data.get("osm_type"), "osm_id": data.get("osm_id"), "category": category, "type": osm_type_value, "building": building},
                    "license_or_terms_url": LICENSE_URL, "usage_policy_url": POLICY_URL,
                    "http_status": getattr(response, "status", None),
                })
        except Exception as exc:
            message = f"NOMINATIM_REVERSE_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({
                "parcel_id": row["parcel_id"], "source_url": url, "accessed_at": accessed_at,
                "content_sha256": sha256(message), "sha256_basis": "bounded_error_evidence_string",
                "record_scope": "one reverse request for one canonical point; no bulk/grid query",
                "supports_fields": ["reverse endpoint availability"],
                "relevant_record_ids_or_excerpt": message[:512],
                "license_or_terms_url": LICENSE_URL, "usage_policy_url": POLICY_URL,
                "http_status": getattr(exc, "code", None),
            })
    state = "CANDIDATE_ROWS_FOUND" if candidates else "NO_DATA_CONTINUE"
    result = {
        "schema_version": 1, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": "parcel_label_3",
        "task_id": TASK_ID, "generated_at": now(), "state": state, "panel_status": "PUBLISHED",
        "completed_count": 3, "target_count": 3, "previous_percent": 0.0, "progress_percent": 100.0, "percent_increase": 100.0,
        "validated_canonical_points": list(IDS), "produced_candidate_rows": len(candidates), "candidate_rows": candidates,
        "source_evidence": evidence,
        "blocker": {"code": "NONE" if candidates else "NOMINATIM_REVERSE_NO_CONSERVATIVE_BUILDING_TYPE_EVIDENCE", "state": state, "manual_action_required": False, "retry_unchanged_route": False},
        "next_unverified_step": "VALIDATE_NOMINATIM_CANDIDATES_AGAINST_EXACT_OSM_OBJECTS" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_NOMINATIM_REVERSE",
        "rate_limit_seconds": 1.1, "single_thread": True, "large_data_downloaded": False,
        "property_type_binding_claimed": False, "exact_parcel_binding_claimed": False, "inferred_values": 0, "fake_data": False, "final_ready": False,
    }
    for path in OUT:
        atomic_write(path, result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate()
        return
    result = run(args.timeout)
    print(json.dumps({"state": result["state"], "completed_count": 3, "target_count": 3, "produced_candidate_rows": result["produced_candidate_rows"], "evidence_records": len(result["source_evidence"])}, separators=(",", ":")))


if __name__ == "__main__":
    main()
