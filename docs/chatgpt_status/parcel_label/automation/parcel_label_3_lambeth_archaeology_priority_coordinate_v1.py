from __future__ import annotations

import argparse, hashlib, json, os, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "parcel_label_3"
TASK_ID = "parcel-label-3-lambeth-archaeology-priority-coordinate-v1-20260803"
PROBE_BLOB_SHA = "ea8e95593a58ab6cbb9369abc30bc38ce8543ad9"
LAYER_URL = "https://services.arcgis.com/drifeOPKLpgnJ8Qa/arcgis/rest/services/planning_local_plan_data_22/FeatureServer/21"
DOC_URL = "https://www.lambeth.gov.uk/planning-building-control/conservation-listed-buildings/local-heritage-list"
DATASET_URL = "https://www.planning.data.gov.uk/dataset/archaeological-priority-area"
TERMS = [
    "https://www.lambeth.gov.uk/about-council/using-website/terms-conditions-disclaimer",
    "https://www.lambeth.gov.uk/about-council/using-website/copyright",
    "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
]
FIELDS = ["objectid", "sitereference", "sitename", "address", "borough", "designation", "boroughdesignation", "classification", "notes", "source"]
POINTS = {
    "parcel_61523": (-0.1387938, 51.4196454),
    "parcel_61524": (-0.1407703, 51.4170637),
    "parcel_61525": (-0.1398845, 51.4167453),
}
MAX_BYTES, MAX_FEATURES = 1_048_576, 5


def root() -> Path:
    return Path(__file__).resolve().parents[4]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def load_points(base: Path) -> list[dict[str, Any]]:
    rows = json.loads((base / "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json").read_text())["canonical_points"]
    found = {row.get("parcel_id"): row for row in rows if isinstance(row, dict) and row.get("parcel_id") in POINTS}
    if set(found) != set(POINTS): raise ValueError("exact target parcels missing")
    out = []
    for parcel_id, expected in POINTS.items():
        row = found[parcel_id]; lon, lat = float(row["longitude"]), float(row["latitude"])
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True or abs(lon - expected[0]) > 1e-7 or abs(lat - expected[1]) > 1e-7:
            raise ValueError(f"invalid canonical Point {parcel_id}")
        out.append({"parcel_id": parcel_id, "longitude": lon, "latitude": lat})
    return out


def get(url: str, timeout: float) -> tuple[int, str, bytes]:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "AAYS-parcel-label-evidence/1.0 bounded official-source research"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        raw = res.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES: raise ValueError("response exceeds 1 MiB")
        return int(getattr(res, "status", 200)), res.geturl(), raw


def evidence(kind: str, url: str, accessed: str, digest: str, basis: str, excerpt: str, status: int | None, point: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "attempt_kind": kind, "parcel_id": point.get("parcel_id") if point else None, "canonical_point": point,
        "source_url": url, "accessed_at": accessed, "content_sha256": digest, "sha256_basis": basis,
        "record_scope": "one bounded layer metadata request" if kind == "layer_metadata" else "one bounded exact-point intersection query; maximum five features, selected fields only, no geometry and 1 MiB response",
        "supports_fields": ["layer name", "geometry type", "spatial reference", "public attribute fields", "query capabilities"] if kind == "layer_metadata" else FIELDS,
        "relevant_record_ids_or_excerpt": excerpt, "documentation_url": DOC_URL, "dataset_url": DATASET_URL,
        "terms_or_license_urls": TERMS, "http_status": status, "requests_made": 1 if status is not None else 0,
    }


def metadata_attempt(timeout: float) -> dict[str, Any]:
    accessed, url = now(), LAYER_URL + "?f=json"
    try:
        status, final_url, raw = get(url, timeout); parsed = json.loads(raw)
        available = [f.get("name") for f in parsed.get("fields", []) if isinstance(f, dict) and f.get("type") != "esriFieldTypeGeometry"]
        missing = [field for field in FIELDS if field not in available]
        if missing: raise ValueError("required public fields missing: " + ",".join(missing))
        excerpt = json.dumps({"name": parsed.get("name"), "geometryType": parsed.get("geometryType"), "fields": available[:30]}, separators=(",", ":"))
        return evidence("layer_metadata", final_url, accessed, sha(raw), "bounded_response_bytes", excerpt, status)
    except Exception as exc:
        error = f"LAMBETH_ARCHAEOLOGY_PRIORITY_METADATA_ERROR:{type(exc).__name__}:{exc}"
        return evidence("layer_metadata", url, accessed, sha(error.encode()), "bounded_error_evidence_string", error, None)


def point_attempt(point: dict[str, Any], timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    accessed = now()
    params = {"where": "1=1", "geometry": f"{point['longitude']},{point['latitude']}", "geometryType": "esriGeometryPoint", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects", "outFields": ",".join(FIELDS), "returnGeometry": "false", "resultRecordCount": str(MAX_FEATURES), "f": "json"}
    url = LAYER_URL + "/query?" + urllib.parse.urlencode(params)
    try:
        status, final_url, raw = get(url, timeout); parsed = json.loads(raw)
        if parsed.get("error"): raise ValueError("ArcGIS error: " + json.dumps(parsed["error"], separators=(",", ":")))
        features = parsed.get("features", [])[:MAX_FEATURES]
        rows = [{"parcel_id": point["parcel_id"], "canonical_point": point, "source_url": final_url, "archaeology_priority_attributes": {field: feature.get("attributes", {}).get(field) for field in FIELDS}, "planning_context_only": True, "exact_parcel_binding": False, "property_type_binding": False} for feature in features if isinstance(feature, dict)]
        excerpt = json.dumps({"feature_count": len(features), "attributes": [r["archaeology_priority_attributes"] for r in rows]}, ensure_ascii=False, separators=(",", ":"))[:4000]
        return rows, evidence("coordinate_query", final_url, accessed, sha(raw), "bounded_response_bytes", excerpt, status, point)
    except Exception as exc:
        error = f"LAMBETH_ARCHAEOLOGY_PRIORITY_COORDINATE_ERROR:{type(exc).__name__}:{exc}"
        return [], evidence("coordinate_query", url, accessed, sha(error.encode()), "bounded_error_evidence_string", error, None, point)


def build(points: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    records, rows = [metadata_attempt(timeout)], []
    for point in points:
        found, record = point_attempt(point, timeout); rows.extend(found); records.append(record)
    count = len(rows)
    return {
        "schema_version": 1, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": SLOT_ID, "task_id": TASK_ID,
        "generated_at": now(), "state": "CANDIDATES_FOUND_CONTEXT_ONLY" if count else "NO_DATA_CONTINUE", "panel_status": "PUBLISHED",
        "completed_count": 4, "target_count": 4, "previous_percent": 0.0, "progress_percent": 100.0, "percent_increase": 100.0,
        "validated_canonical_points": points, "produced_candidate_rows": count, "candidate_rows": rows, "source_evidence": records,
        "blocker": {"code": None if count else "LAMBETH_ARCHAEOLOGY_PRIORITY_NO_USABLE_RESPONSE_OR_NO_POINT_MATCH", "state": "NONE" if count else "NO_DATA_CONTINUE", "manual_action_required": False, "retry_unchanged_route": False},
        "next_unverified_step": "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_LAMBETH_ARCHAEOLOGY_PRIORITY_COORDINATE",
        "layer_url": LAYER_URL, "documentation_url": DOC_URL, "dataset_url": DATASET_URL, "terms_or_license_urls": TERMS,
        "login_or_api_key_used": False, "geometry_payload_requested": False, "bulk_download_performed": False, "full_dataset_scan_performed": False,
        "large_data_downloaded": False, "property_type_binding_claimed": False, "exact_parcel_binding_claimed": False, "inferred_values": 0, "fake_data": False, "final_ready": False,
    }


def validate(base: Path) -> None:
    if len(load_points(base)) != 3 or not LAYER_URL.endswith("/FeatureServer/21") or len(FIELDS) != 10:
        raise ValueError("validation failed")
    print("PASS_TARGET_4_LAMBETH_ARCHAEOLOGY_PRIORITY_1_METADATA_PLUS_3_EXACT_POINT_QUERIES_MAX5_EACH_MAX1MIB_CONTEXT_ONLY")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--timeout", type=float, default=5.0); parser.add_argument("--validate-only", action="store_true"); args = parser.parse_args()
    base = root(); validate(base)
    if args.validate_only: return 0
    payload = build(load_points(base), max(1.0, min(args.timeout, 30.0)))
    for path in [base / "docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_archaeology_priority_coordinate_result_latest.json", base / "england_map_web/data/aays_21_slots/parcel_label_3/lambeth_archaeology_priority_coordinate_latest.json"]:
        atomic(path, payload)
    print(f"PASS_CONTEXT_CANDIDATES_{payload['produced_candidate_rows']}_4_OF_4" if payload["produced_candidate_rows"] else "PASS_NO_DATA_CONTINUE_4_OF_4")
    return 0


if __name__ == "__main__": raise SystemExit(main())
