from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SLOT_ID = "parcel_label_3"
BASE_URL = "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethLLPGAllPostalAddresses/MapServer/0"
LICENSE_URL = "https://www.lambeth.gov.uk/about-council/transparency-open-data/open-mapping-data"
READ_PATH = "england_map_web/data/distance_property_types/parcel_label_3_canonical_probe_latest.json"
WRITE_PATHS = (
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/llpg_exact_binding_result_latest.json",
    "england_map_web/data/aays_21_slots/parcel_label_3/llpg_exact_binding_latest.json",
)
REQUIRED_FIELDS = ("UPRN", "FULLADDRESS", "POSTCODE", "BLPUCLASS")
TARGET_COUNT = 3

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_suffix(path.suffix + ".part")
    part.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(part, path)

def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2-lat1)
    dlambda = math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlambda/2)**2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def fetch(url: str, timeout: int) -> tuple[bytes, int]:
    req = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label-3/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(), int(response.status)

def query_url(lon: float, lat: float) -> str:
    params = {
        "where": "1=1", "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint", "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects", "distance": "30",
        "units": "esriSRUnit_Meter",
        "outFields": "OBJECTID,UPRN,FULLADDRESS,STREET,POSTCODE,BLPUCLASS",
        "returnGeometry": "true", "outSR": "4326", "f": "json",
    }
    return BASE_URL + "/query?" + urllib.parse.urlencode(params)

def load_points(repo: Path) -> list[dict]:
    payload = json.loads((repo / READ_PATH).read_text(encoding="utf-8-sig"))
    rows = payload.get("canonical_points")
    if not isinstance(rows, list) or len(rows) != TARGET_COUNT:
        raise ValueError("CANONICAL_POINT_COUNT_NOT_3")
    result = []
    for row in rows:
        if row.get("geometry_type") != "Point" or row.get("point_valid") is not True:
            raise ValueError("INVALID_CANONICAL_POINT")
        result.append({
            "parcel_id": str(row["parcel_id"]),
            "longitude": float(row["longitude"]),
            "latitude": float(row["latitude"]),
        })
    return result

def run(repo: Path, timeout: int) -> dict:
    points = load_points(repo)
    metadata_url = BASE_URL + "?f=pjson"
    evidence = []
    accepted = []
    completed = 0
    metadata_ok = False
    try:
        body, status = fetch(metadata_url, timeout)
        metadata = json.loads(body.decode("utf-8"))
        fields = {f.get("name") for f in metadata.get("fields", [])}
        metadata_ok = status == 200 and set(REQUIRED_FIELDS).issubset(fields)
        evidence.append({
            "source_url": metadata_url, "accessed_at": utc_now(),
            "http_status": status, "content_sha256": sha256_bytes(body),
            "supports_fields": list(REQUIRED_FIELDS),
            "relevant_record_ids_or_excerpt": sorted(fields.intersection(REQUIRED_FIELDS)),
            "license_or_terms_url": LICENSE_URL,
        })
    except Exception as exc:
        evidence.append({
            "source_url": metadata_url, "accessed_at": utc_now(),
            "http_status": None, "content_sha256": None,
            "supports_fields": list(REQUIRED_FIELDS),
            "relevant_record_ids_or_excerpt": f"METADATA_FETCH_ERROR:{type(exc).__name__}",
            "license_or_terms_url": LICENSE_URL,
        })

    for point in points:
        url = query_url(point["longitude"], point["latitude"])
        item = {
            "parcel_id": point["parcel_id"], "source_url": url,
            "accessed_at": utc_now(), "http_status": None,
            "content_sha256": None, "supports_fields": list(REQUIRED_FIELDS),
            "relevant_record_ids_or_excerpt": [], "license_or_terms_url": LICENSE_URL,
        }
        try:
            body, status = fetch(url, timeout)
            completed += 1
            item["http_status"] = status
            item["content_sha256"] = sha256_bytes(body)
            payload = json.loads(body.decode("utf-8"))
            candidates = []
            for feature in payload.get("features", []):
                attrs = feature.get("attributes") or {}
                geom = feature.get("geometry") or {}
                if not all(str(attrs.get(k) or "").strip() for k in REQUIRED_FIELDS):
                    continue
                if not isinstance(geom.get("x"), (int, float)) or not isinstance(geom.get("y"), (int, float)):
                    continue
                distance = haversine_m(point["longitude"], point["latitude"], float(geom["x"]), float(geom["y"]))
                if distance <= 30.0:
                    candidates.append((distance, attrs, geom))
            candidates.sort(key=lambda x: x[0])
            if candidates:
                distance, attrs, geom = candidates[0]
                record = {
                    "parcel_id": point["parcel_id"], "distance_m": round(distance, 3),
                    "OBJECTID": attrs.get("OBJECTID"), "UPRN": str(attrs.get("UPRN")),
                    "FULLADDRESS": attrs.get("FULLADDRESS"), "STREET": attrs.get("STREET"),
                    "POSTCODE": attrs.get("POSTCODE"), "BLPUCLASS": attrs.get("BLPUCLASS"),
                    "longitude": geom.get("x"), "latitude": geom.get("y"),
                    "exact_uprn_bound": True,
                }
                accepted.append(record)
                item["relevant_record_ids_or_excerpt"] = [attrs.get("OBJECTID"), str(attrs.get("UPRN"))]
            else:
                item["relevant_record_ids_or_excerpt"] = "NO_COMPLETE_FEATURE_WITHIN_30M"
        except Exception as exc:
            completed += 1
            item["relevant_record_ids_or_excerpt"] = f"QUERY_FETCH_ERROR:{type(exc).__name__}"
        evidence.append(item)

    state = "PUBLISHED" if metadata_ok and len(accepted) == TARGET_COUNT else "NO_DATA_CONTINUE"
    return {
        "schema_version": 1, "slot_id": SLOT_ID, "generated_at": utc_now(),
        "state": state, "completed_count": completed, "target_count": TARGET_COUNT,
        "progress_percent": round(100.0 * completed / TARGET_COUNT, 4),
        "exact_verified_rows": len(accepted), "canonical_exact_geometry_rows": TARGET_COUNT,
        "records": accepted, "source_evidence": evidence,
        "fake_data": False, "final_ready": len(accepted) == TARGET_COUNT,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[4]
    points = load_points(repo)
    if args.validate_only:
        print(json.dumps({"state": "VALIDATED", "point_count": len(points), "write_paths": WRITE_PATHS}))
        return 0
    result = run(repo, args.timeout)
    for rel in WRITE_PATHS:
        atomic_json(repo / rel, result)
    print(json.dumps({"state": result["state"], "completed_count": result["completed_count"], "exact_verified_rows": result["exact_verified_rows"]}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
