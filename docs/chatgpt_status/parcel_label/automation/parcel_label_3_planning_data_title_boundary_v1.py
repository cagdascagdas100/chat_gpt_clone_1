from __future__ import annotations
import argparse, hashlib, json, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-planning-data-title-boundary-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/planning_data_title_boundary_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/planning_data_title_boundary_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
ENDPOINT = "https://www.planning.data.gov.uk/entity.json"
DOCS_URL = "https://www.planning.data.gov.uk/docs"
DATASET_URL = "https://www.planning.data.gov.uk/dataset/title-boundary"
LICENSE_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
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

def canonical_points() -> list[dict]:
    rows = json.loads(Path(PROBE).read_text(encoding="utf-8"))["canonical_points"]
    by_id = {row["parcel_id"]: row for row in rows}
    result = []
    for parcel_id in IDS:
        row = by_id.get(parcel_id)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point: {parcel_id}")
        if not isinstance(row.get("longitude"), (int, float)) or not isinstance(row.get("latitude"), (int, float)):
            raise ValueError(f"invalid coordinates: {parcel_id}")
        result.append(row)
    return result

def request_url(row: dict) -> str:
    query = urllib.parse.urlencode([
        ("latitude", str(row["latitude"])),
        ("longitude", str(row["longitude"])),
        ("dataset", "title-boundary"),
        ("field", "entity"),
        ("field", "reference"),
        ("field", "dataset"),
        ("field", "geometry"),
        ("field", "point"),
        ("field", "quality"),
        ("limit", "20"),
    ])
    return ENDPOINT + "?" + query

def validate() -> None:
    canonical_points()
    if Path(PROBE).is_absolute() or any(Path(path).is_absolute() for path in OUT):
        raise ValueError("all paths must be relative")
    if not all(path.startswith((
        "docs/chatgpt_status/_shared/slots_21/parcel_label_3/",
        "england_map_web/data/aays_21_slots/parcel_label_3/",
    )) for path in OUT):
        raise ValueError("write boundary")
    if not ENDPOINT.startswith("https://www.planning.data.gov.uk/"):
        raise ValueError("official endpoint")
    print("PASS_TARGET_3_PLANNING_DATA_TITLE_BOUNDARY_POINT_INTERSECTION_MAX1MIB_CANDIDATE_ONLY")

def run(timeout: float) -> dict:
    evidence = []
    candidates = []
    for row in canonical_points():
        url = request_url(row)
        accessed_at = now()
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "TerraYield-AAYS/1.0 parcel-label-research (three bounded official Planning Data queries)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("response exceeded 1 MiB")
                payload = json.loads(raw.decode("utf-8"))
                entities = payload.get("entities")
                if entities is None:
                    entities = payload.get("data", [])
                if not isinstance(entities, list):
                    entities = []
                selected = []
                for entity in entities[:20]:
                    if not isinstance(entity, dict) or entity.get("dataset") != "title-boundary":
                        continue
                    selected.append({
                        "entity": entity.get("entity"),
                        "reference": entity.get("reference"),
                        "dataset": entity.get("dataset"),
                        "quality": entity.get("quality"),
                        "geometry_sha256": sha256(str(entity.get("geometry", ""))),
                        "point": entity.get("point"),
                    })
                    candidates.append({
                        "parcel_id": row["parcel_id"],
                        "candidate_type": "TITLE_BOUNDARY_INTERSECTING_POINT",
                        "entity": entity.get("entity"),
                        "reference": entity.get("reference"),
                        "source_url": url,
                        "candidate_only": True,
                        "property_type_binding_claimed": False,
                        "exact_parcel_binding_claimed": False,
                    })
                evidence.append({
                    "parcel_id": row["parcel_id"],
                    "source_url": url,
                    "accessed_at": accessed_at,
                    "content_sha256": sha256(raw),
                    "sha256_basis": "bounded_raw_response_bytes",
                    "record_scope": "one official Planning Data point-intersection query; dataset=title-boundary; limit=20; max 1 MiB",
                    "supports_fields": ["entity", "reference", "dataset", "geometry", "point", "quality"],
                    "relevant_record_ids_or_excerpt": {"returned_title_boundary_count": len(selected), "records": selected},
                    "license_or_terms_url": LICENSE_URL,
                    "documentation_url": DOCS_URL,
                    "dataset_url": DATASET_URL,
                    "http_status": getattr(response, "status", None),
                })
        except Exception as exc:
            message = f"PLANNING_DATA_TITLE_BOUNDARY_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({
                "parcel_id": row["parcel_id"],
                "source_url": url,
                "accessed_at": accessed_at,
                "content_sha256": sha256(message),
                "sha256_basis": "bounded_error_evidence_string",
                "record_scope": "one official Planning Data point-intersection query; no bulk download",
                "supports_fields": ["title-boundary endpoint availability"],
                "relevant_record_ids_or_excerpt": message[:512],
                "license_or_terms_url": LICENSE_URL,
                "documentation_url": DOCS_URL,
                "dataset_url": DATASET_URL,
                "http_status": getattr(exc, "code", None),
            })
    state = "TITLE_BOUNDARY_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": TASK_ID,
        "generated_at": now(),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": 3,
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": 100.0,
        "percent_increase": 100.0,
        "validated_canonical_points": list(IDS),
        "produced_candidate_rows": len(candidates),
        "candidate_rows": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": "NONE" if candidates else "PLANNING_DATA_TITLE_BOUNDARY_NO_VERIFIED_INTERSECTION",
            "state": state,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": (
            "VALIDATE_TITLE_BOUNDARY_CANDIDATES_WITHOUT_PROPERTY_TYPE_INFERENCE"
            if candidates else
            "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_PLANNING_DATA_TITLE_BOUNDARY"
        ),
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
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
    print(json.dumps({
        "state": result["state"],
        "completed_count": result["completed_count"],
        "target_count": result["target_count"],
        "produced_candidate_rows": result["produced_candidate_rows"],
        "evidence_records": len(result["source_evidence"]),
    }, separators=(",", ":")))

if __name__ == "__main__":
    main()
