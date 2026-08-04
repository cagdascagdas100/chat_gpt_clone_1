#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, tempfile, urllib.parse, urllib.request
from datetime import datetime, timezone
from typing import Any

INPUT = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json")
MANIFEST = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/lambeth_metropolitan_sinc_point_containment_source_manifest_20260804.json")
OUTPUTS = [
    pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/lambeth_metropolitan_sinc_point_containment_result_latest.json"),
    pathlib.Path("england_map_web/data/aays_21_slots/parcel_label_3/lambeth_metropolitan_sinc_point_containment_latest.json"),
]
SERVICE_ROOTS = [
    "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethSiteOfMetropolitanNatureConservationImportance/FeatureServer/0",
    "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethSiteOfMetropolitanNatureConservationImportance/MapServer/0",
]
ALLOWED_HOST = "gis.lambeth.gov.uk"
HARVEST_GUID = "88f412c44fcb44b298495e9282343807_3"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024

def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

def atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temporary = pathlib.Path(handle.name)
    temporary.replace(path)

def safe_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or (parsed.hostname or "").casefold() != ALLOWED_HOST or parsed.username or parsed.password or parsed.fragment:
        raise RuntimeError(f"UNSAFE_OR_UNTRUSTED_URL:{url}")
    return url

def fetch(url: str, timeout: int, accept: str = "application/json") -> tuple[bytes, str, int]:
    safe_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label-3/1.0", "Accept": accept})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = safe_url(response.geturl())
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise RuntimeError(f"RESPONSE_TOO_LARGE:{len(body)}")
        return body, final_url, int(getattr(response, "status", 200))

def load_manifest() -> dict[str, Any]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("service_roots") != SERVICE_ROOTS or payload.get("harvest_guid") != HARVEST_GUID:
        raise RuntimeError("WRONG_SOURCE_MANIFEST")
    if len(payload.get("target_uprns", [])) != 3 or len(payload.get("sources", [])) < 4:
        raise RuntimeError("INCOMPLETE_SOURCE_MANIFEST")
    for source in payload["sources"]:
        excerpt = source.get("retained_excerpt", "")
        if not excerpt or sha256(excerpt.encode("utf-8")) != source.get("retained_excerpt_sha256"):
            raise RuntimeError("SOURCE_EXCERPT_SHA_MISMATCH")
    return payload

def load_rows() -> list[dict[str, Any]]:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    targets = set(load_manifest()["target_uprns"])
    if len(records) != 3:
        raise RuntimeError(f"EXPECTED_3_INPUT_ROWS:{len(records)}")
    rows: list[dict[str, Any]] = []
    for record in records:
        keys = ("parcel_id", "UPRN", "FULLADDRESS", "POSTCODE", "longitude", "latitude")
        if not record.get("exact_uprn_bound") or any(key not in record for key in keys):
            raise RuntimeError("INVALID_INPUT_ROW")
        row = {key: record[key] for key in keys}
        row["UPRN"] = str(row["UPRN"])
        row["exact_uprn_bound"] = True
        if row["UPRN"] not in targets:
            raise RuntimeError(f"UPRN_NOT_IN_MANIFEST:{row['UPRN']}")
        rows.append(row)
    if len({row["UPRN"] for row in rows}) != 3:
        raise RuntimeError("INPUT_UPRNS_NOT_UNIQUE")
    return rows

def on_segment(point: tuple[float, float], a: list[float], b: list[float], eps: float = 1e-12) -> bool:
    x, y = point
    x1, y1 = a[:2]
    x2, y2 = b[:2]
    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    return abs(cross) <= eps and min(x1, x2) - eps <= x <= max(x1, x2) + eps and min(y1, y2) - eps <= y <= max(y1, y2) + eps

def ring_covers(ring: list[list[float]], point: tuple[float, float]) -> bool:
    if len(ring) < 4:
        return False
    inside = False
    x, y = point
    for a, b in zip(ring, ring[1:]):
        if on_segment(point, a, b):
            return True
        x1, y1 = a[:2]
        x2, y2 = b[:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside

def geometry_covers(geometry: dict[str, Any], point: tuple[float, float]) -> bool:
    coordinates = geometry.get("coordinates")
    def polygon_covers(polygon: list[list[list[float]]]) -> bool:
        return bool(polygon and ring_covers(polygon[0], point) and not any(ring_covers(hole, point) for hole in polygon[1:]))
    if geometry.get("type") == "Polygon" and isinstance(coordinates, list):
        return polygon_covers(coordinates)
    if geometry.get("type") == "MultiPolygon" and isinstance(coordinates, list):
        return any(polygon_covers(polygon) for polygon in coordinates)
    return False

def discover_layer(timeout: int, evidence: dict[str, Any]) -> str:
    errors: list[str] = []
    for root in SERVICE_ROOTS:
        url = root + "?f=json"
        evidence["metadata_request_count"] += 1
        try:
            body, final_url, status = fetch(url, timeout)
            payload = json.loads(body)
            if payload.get("type") != "Feature Layer" or payload.get("geometryType") != "esriGeometryPolygon":
                raise RuntimeError("NOT_POLYGON_FEATURE_LAYER")
            evidence["metadata_response_count"] += 1
            evidence["metadata_requests"].append({
                "layer_root": root, "request_url": url, "final_url": final_url, "http_status": status,
                "bytes": len(body), "response_sha256": sha256(body), "geometry_type": payload.get("geometryType"), "state": "RESPONSE"
            })
            return root
        except Exception as exc:
            error = f"{type(exc).__name__}:{exc}"
            errors.append(error)
            evidence["metadata_requests"].append({"layer_root": root, "request_url": url, "state": "ERROR", "error": error})
    raise RuntimeError("ALL_LAYER_METADATA_ENDPOINTS_FAILED:" + "|".join(errors))

def query_url(root: str, row: dict[str, Any]) -> str:
    params = {
        "where": "1=1",
        "geometry": f"{float(row['longitude']):.15f},{float(row['latitude']):.15f}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    return root + "/query?" + urllib.parse.urlencode(params)

def parse_candidates(body: bytes, row: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    payload = json.loads(body)
    features = payload.get("features")
    if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
        raise RuntimeError("NOT_GEOJSON_FEATURE_COLLECTION")
    point = (float(row["longitude"]), float(row["latitude"]))
    candidates: list[dict[str, Any]] = []
    for index, feature in enumerate(features, 1):
        if not isinstance(feature, dict) or not isinstance(feature.get("geometry"), dict):
            continue
        geometry = feature["geometry"]
        if not geometry_covers(geometry, point):
            continue
        properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
        candidates.append({
            "feature_id": feature.get("id"),
            "feature_index": index,
            "official_sinc_tier": "Metropolitan",
            "official_metropolitan_sinc_designation": True,
            "raw_attributes_sha256": sha256(canonical_json(properties).encode("utf-8")),
            "geometry_sha256": sha256(canonical_json(geometry).encode("utf-8")),
            "geometry": geometry,
        })
    return candidates, len(features)

def synthetic_feature(row: dict[str, Any], feature_id: int, offset: float = 0.0) -> dict[str, Any]:
    lon = float(row["longitude"]) + offset
    lat = float(row["latitude"]) + offset
    delta = 0.00008
    ring = [[lon-delta,lat-delta],[lon+delta,lat-delta],[lon+delta,lat+delta],[lon-delta,lat+delta],[lon-delta,lat-delta]]
    return {"type":"Feature","id":feature_id,"properties":{"OBJECTID":feature_id,"SITE_NAME":f"Synthetic Metropolitan SINC {feature_id}"},"geometry":{"type":"Polygon","coordinates":[ring]}}

def run(rows: list[dict[str, Any]], timeout: int, synthetic: bool = False, ambiguous: bool = False) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    evidence = {"accessed_at": now(), "layer_roots": SERVICE_ROOTS, "metadata_request_count": 0, "metadata_response_count": 0, "metadata_requests": [], "point_query_count": 0, "point_queries": []}
    if synthetic:
        selected_root = SERVICE_ROOTS[0]
    else:
        try:
            selected_root = discover_layer(timeout, evidence)
        except Exception as exc:
            error = f"{type(exc).__name__}:{exc}"
            evidence["discovery_error"] = error
            return evidence, [{**row, "source_url": SERVICE_ROOTS[0], "candidate_count": 0, "state": "NO_DATA", "reason": error, "inferred": False} for row in rows], 0
    evidence["selected_layer_root"] = selected_root
    records: list[dict[str, Any]] = []
    matched = 0
    for index, row in enumerate(rows, 1):
        url = query_url(selected_root, row)
        evidence["point_query_count"] += 1
        try:
            if synthetic:
                features = [synthetic_feature(row, index)]
                if ambiguous and index == 2:
                    features.append(synthetic_feature(row, 100 + index, 0.00001))
                body = canonical_json({"type":"FeatureCollection","features":features}).encode("utf-8")
                final_url, status = url, 200
            else:
                body, final_url, status = fetch(url, timeout, "application/geo+json,application/json;q=0.9")
            candidates, returned_count = parse_candidates(body, row)
            evidence["point_queries"].append({
                "UPRN": row["UPRN"], "request_url": url, "final_url": final_url, "http_status": status,
                "bytes": len(body), "response_sha256": sha256(body), "returned_feature_count": returned_count,
                "point_covering_candidate_count": len(candidates), "state": "RESPONSE"
            })
            output = {**row, "source_url": final_url, "layer_root": selected_root, "candidate_count": len(candidates), "inferred": False}
            if len(candidates) == 1:
                output.update({"state":"MATCHED_UNIQUE_LAMBETH_METROPOLITAN_SINC_POLYGON", **candidates[0]})
                matched += 1
            elif len(candidates) > 1:
                output.update({"state":"NO_DATA","reason":"AMBIGUOUS_MULTIPLE_POINT_CONTAINING_LAMBETH_METROPOLITAN_SINC_POLYGONS","candidate_geometry_sha256":[candidate["geometry_sha256"] for candidate in candidates]})
            else:
                output.update({"state":"NO_DATA","reason":"NO_POINT_CONTAINING_LAMBETH_METROPOLITAN_SINC_POLYGON"})
        except Exception as exc:
            error = f"{type(exc).__name__}:{exc}"
            evidence["point_queries"].append({"UPRN": row["UPRN"], "request_url": url, "state": "ERROR", "error": error})
            output = {**row, "source_url": selected_root + "/query", "layer_root": selected_root, "candidate_count": 0, "state": "NO_DATA", "reason": error, "inferred": False}
        records.append(output)
    return evidence, records, matched

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--synthetic-test", action="store_true")
    parser.add_argument("--synthetic-ambiguous-test", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.timeout <= 300:
        raise RuntimeError("INVALID_TIMEOUT")
    rows = load_rows()
    if args.validate_only:
        print(json.dumps({"valid":True,"input_count":3,"target_uprns":[row["UPRN"] for row in rows],"layer_roots":SERVICE_ROOTS,"resource_class":"network","metadata_request_limit":2,"point_query_limit":3,"max_response_bytes":MAX_RESPONSE_BYTES,"write_paths":[str(path) for path in OUTPUTS]},sort_keys=True))
        return 0
    synthetic = args.synthetic_test or args.synthetic_ambiguous_test
    evidence, records, matched = run(rows, args.timeout, synthetic, args.synthetic_ambiguous_test)
    if args.synthetic_test:
        if matched != 3 or [record["candidate_count"] for record in records] != [1,1,1]:
            raise RuntimeError("SYNTHETIC_UNIQUE_FAILED")
        print(json.dumps({"valid":True,"matched_rows":matched,"point_query_count":evidence["point_query_count"]},sort_keys=True))
        return 0
    if args.synthetic_ambiguous_test:
        if matched != 2 or records[1].get("reason") != "AMBIGUOUS_MULTIPLE_POINT_CONTAINING_LAMBETH_METROPOLITAN_SINC_POLYGONS":
            raise RuntimeError("SYNTHETIC_AMBIGUOUS_FAILED")
        print(json.dumps({"valid":True,"matched_rows":matched,"ambiguous_state":records[1]["state"]},sort_keys=True))
        return 0
    state = "PUBLISHED" if matched else "NO_DATA_CONTINUE"
    result = {
        "schema_version":1,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"parcel_label_3",
        "task_id":"parcel-label-3-lambeth-metropolitan-sinc-point-containment-v1-20260804","state":state,
        "panel_status":"PUBLISHED","completed_count":len(records),"target_count":3,"previous_percent":0.0,
        "progress_percent":round(len(records)/3*100,6),"percent_increase":round(len(records)/3*100,6),
        "matched_unique_metropolitan_sinc_rows":matched,"evidence_records":len(records),"source_evidence":evidence,
        "records":records,"unknown_attributes_promoted_to_label":False,"fake_data":False,"large_raw_files_committed":False,
        "generated_at":now()
    }
    text = canonical_json(result) + "\n"
    for output in OUTPUTS:
        atomic_write(output, text)
    print(json.dumps({"completed_count":len(records),"target_count":3,"matched_unique_metropolitan_sinc_rows":matched,"state":state,"output_sha256":sha256(text.encode("utf-8"))},sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
