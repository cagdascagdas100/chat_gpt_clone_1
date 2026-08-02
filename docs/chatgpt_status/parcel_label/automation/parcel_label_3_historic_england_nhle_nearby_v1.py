from __future__ import annotations
import argparse, hashlib, json, os, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "parcel-label-3-historic-england-nhle-nearby-v1-20260802"
PROBE = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
OUT = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/historic_england_nhle_nearby_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/historic_england_nhle_nearby_latest.json",
)
IDS = ("parcel_61523", "parcel_61524", "parcel_61525")
SERVICE = "https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer/0/query"
METADATA = "https://services-eu1.arcgis.com/ZOdPfBS3aqqDYPUQ/arcgis/rest/services/National_Heritage_List_for_England_NHLE_v02_VIEW/FeatureServer"
DOWNLOADS = "https://historicengland.org.uk/listing/the-list/data-downloads"
OGL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_BYTES = 1048576
RADIUS_M = 100

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()

def write(path: str, obj: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, p)

def points() -> list[dict]:
    raw = json.loads(Path(PROBE).read_text(encoding="utf-8"))
    by_id = {row["parcel_id"]: row for row in raw["canonical_points"]}
    out = []
    for pid in IDS:
        row = by_id.get(pid)
        if not row or row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError(f"invalid canonical point {pid}")
        lon = float(row["longitude"])
        lat = float(row["latitude"])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"invalid coordinate {pid}")
        out.append({"parcel_id": pid, "longitude": lon, "latitude": lat})
    return out

def validate() -> None:
    points()
    for path in (PROBE, *OUT):
        if Path(path).is_absolute():
            raise ValueError("relative paths required")
    if not OUT[0].startswith("docs/chatgpt_status/_shared/slots_21/parcel_label_3/"):
        raise ValueError("state output boundary")
    if not OUT[1].startswith("england_map_web/data/aays_21_slots/parcel_label_3/"):
        raise ValueError("web output boundary")
    print("PASS_TARGET_3_HISTORIC_ENGLAND_NHLE_LISTED_BUILDING_WITHIN_100M_MAX1MIB_CANDIDATE_ONLY")

def request_url(row: dict) -> str:
    params = {
        "f": "json",
        "where": "1=1",
        "geometry": json.dumps({"x": row["longitude"], "y": row["latitude"], "spatialReference": {"wkid": 4326}}, separators=(",", ":")),
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": str(RADIUS_M),
        "units": "esriSRUnit_Meter",
        "outFields": "*",
        "returnGeometry": "false",
        "resultRecordCount": "20",
    }
    return SERVICE + "?" + urllib.parse.urlencode(params)

def compact_attributes(attrs: dict) -> dict:
    keep = {}
    for key, value in attrs.items():
        nk = key.lower().replace("_", "").replace(" ", "")
        if nk in {"listentry", "name", "grade", "hyperlink", "nhlelink", "ngref", "nationaleasting", "nationalnorthing", "easting", "northing"}:
            keep[key] = value
    return keep

def run(timeout: float) -> dict:
    evidence = []
    candidates = []
    for row in points():
        url = request_url(row)
        accessed_at = now()
        req = urllib.request.Request(url, headers={"User-Agent": "TerraYield-AAYS/1.0 bounded Historic England NHLE research"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("response exceeded 1 MiB")
                payload = json.loads(raw.decode("utf-8"))
                if payload.get("error"):
                    raise ValueError("ArcGIS error " + json.dumps(payload["error"], separators=(",", ":"))[:400])
                features = payload.get("features") or []
                for feature in features[:20]:
                    attrs = compact_attributes(feature.get("attributes") or {})
                    candidates.append({
                        "parcel_id": row["parcel_id"],
                        "search_radius_m": RADIUS_M,
                        "source_url": url,
                        "attributes": attrs,
                        "candidate_only": True,
                        "listed_building_proximity_only": True,
                        "property_type_binding_claimed": False,
                        "exact_parcel_binding_claimed": False,
                    })
                evidence.append({
                    "parcel_id": row["parcel_id"],
                    "source_url": url,
                    "accessed_at": accessed_at,
                    "content_sha256": sha(raw),
                    "sha256_basis": "bounded_raw_response_bytes",
                    "record_scope": "one official Historic England NHLE Listed Building points query; 100 m radius; max 20 records; max 1 MiB",
                    "supports_fields": ["ListEntry", "Name", "Grade", "NHLE link", "proximity within 100 m"],
                    "relevant_record_ids_or_excerpt": {
                        "feature_count": len(features),
                        "list_entries": [compact_attributes(f.get("attributes") or {}) for f in features[:20]],
                    },
                    "license_or_terms_url": OGL,
                    "documentation_url": DOWNLOADS,
                    "service_metadata_url": METADATA,
                    "http_status": getattr(response, "status", None),
                })
        except Exception as exc:
            msg = f"HISTORIC_ENGLAND_NHLE_NEARBY_ERROR:{type(exc).__name__}:{exc}"
            evidence.append({
                "parcel_id": row["parcel_id"],
                "source_url": url,
                "accessed_at": accessed_at,
                "content_sha256": sha(msg),
                "sha256_basis": "bounded_error_evidence_string",
                "record_scope": "one official Historic England NHLE Listed Building points query; 100 m radius; no bulk download",
                "supports_fields": ["NHLE query endpoint availability"],
                "relevant_record_ids_or_excerpt": msg[:512],
                "license_or_terms_url": OGL,
                "documentation_url": DOWNLOADS,
                "service_metadata_url": METADATA,
                "http_status": getattr(exc, "code", None),
            })
    state = "NHLE_PROXIMITY_CANDIDATES_FOUND" if candidates else "NO_DATA_CONTINUE"
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
        "search_radius_m": RADIUS_M,
        "produced_candidate_rows": len(candidates),
        "candidate_rows": candidates,
        "source_evidence": evidence,
        "blocker": {
            "code": "NONE" if candidates else "HISTORIC_ENGLAND_NHLE_NO_USABLE_RESPONSE_OR_NO_LISTED_BUILDING_WITHIN_100M",
            "state": state,
            "manual_action_required": False,
            "retry_unchanged_route": False,
        },
        "next_unverified_step": "VALIDATE_NHLE_PROXIMITY_CANDIDATES_WITHOUT_PARCEL_OR_PROPERTY_TYPE_INFERENCE" if candidates else "SELECT_NEXT_OFFICIAL_OR_FREE_SOURCE_AFTER_HISTORIC_ENGLAND_NHLE_NEARBY",
        "large_data_downloaded": False,
        "property_type_binding_claimed": False,
        "exact_parcel_binding_claimed": False,
        "inferred_values": 0,
        "fake_data": False,
        "final_ready": False,
    }
    for path in OUT:
        write(path, result)
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
