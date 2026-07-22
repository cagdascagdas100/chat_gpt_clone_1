#!/usr/bin/env python3
"""Resolve official EA survey provenance for height_difference_1 sample points.

Primary binding uses the Environment Agency OGC Features collection that describes
which survey extent was used in the 2022 Composite 1m DTM. The time-stamped DTM
ArcGIS layer is queried only as secondary QA; it cannot replace the composite index.
All joins are fail-closed and exact point-in-polygon is required locally.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

SLOT_ID = "height_difference_1"
SCRIPT_VERSION = "1.0-official-ea-composite-metadata"
EXPECTED_SOURCE_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EXPECTED_PARCELS = [f"parcel_{i}" for i in range(1, 12)]
OGC_ITEMS_ENDPOINT = (
    "https://environment.data.gov.uk/geoservices/datasets/"
    "9f0fa3fc-a860-4729-adc9-47fe53f658d0/ogc/features/v1/collections/"
    "LIDAR_Composite_1m_DTM_2022_extents/items"
)
ARCGIS_TIME_STAMPED_ENDPOINT = (
    "https://environment.data.gov.uk/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/"
    "LIDAR_Tiles_Catalogues/FeatureServer/0/query"
)
USER_AGENT = "AAYS-height-difference-survey-metadata/1.0"
MAX_JSON_BYTES = 25_000_000


class EvidenceError(RuntimeError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    return sha256_bytes(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def fetch_json(url: str, *, timeout: int = 120, retries: int = 3) -> tuple[dict[str, Any], bytes]:
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with contextlib.closing(urlopen(request, timeout=timeout)) as response:
                status = getattr(response, "status", 200)
                if status != 200:
                    raise EvidenceError(f"HTTP_{status}:{url}")
                declared = response.headers.get("Content-Length")
                if declared and int(declared) > MAX_JSON_BYTES:
                    raise EvidenceError(f"DECLARED_JSON_TOO_LARGE:{declared}")
                data = response.read(MAX_JSON_BYTES + 1)
            if not data or len(data) > MAX_JSON_BYTES:
                raise EvidenceError(f"INVALID_JSON_RESPONSE_SIZE:{len(data)}")
            payload = json.loads(data)
            if not isinstance(payload, dict):
                raise EvidenceError("JSON_RESPONSE_NOT_OBJECT")
            return payload, data
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(attempt * 2)
    raise EvidenceError(f"JSON_DOWNLOAD_FAILED:{url}:{last}")


def validate_examples(path: Path) -> list[dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("slot_id") != SLOT_ID:
        raise EvidenceError("EXAMPLES_SLOT_ID_MISMATCH")
    if document.get("source_feature_collection_blob_sha") != EXPECTED_SOURCE_BLOB_SHA:
        raise EvidenceError("EXAMPLES_CANONICAL_BLOB_MISMATCH")
    rows = document.get("examples")
    if not isinstance(rows, list) or [row.get("parcel_id") for row in rows] != EXPECTED_PARCELS:
        raise EvidenceError("EXPECTED_ORDERED_PARCEL_1_TO_11")
    for row in rows:
        for field in ("longitude", "latitude", "bng_easting_m", "bng_northing_m"):
            value = float(row[field])
            if not math.isfinite(value):
                raise EvidenceError(f"NON_FINITE_{field}:{row['parcel_id']}")
    return rows


def require_geo_modules() -> tuple[Any, Any]:
    try:
        from shapely.geometry import Point, shape  # type: ignore
    except Exception as exc:
        raise EvidenceError(f"SHAPELY_REQUIRED:{exc}") from exc
    return Point, shape


def normalize_date(value: Any) -> str:
    if value is None or value == "":
        raise EvidenceError("DATE_VALUE_MISSING")
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000.0
        return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc).date().isoformat()
    text = str(value).strip()
    if text.isdigit():
        return normalize_date(int(text))
    text = text.replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(text).date().isoformat()
    except ValueError:
        try:
            return dt.date.fromisoformat(text[:10]).isoformat()
        except ValueError as exc:
            raise EvidenceError(f"DATE_NOT_PARSEABLE:{value}") from exc


def ogc_query_url(longitude: float, latitude: float) -> str:
    delta = 0.00005
    bbox = [longitude - delta, latitude - delta, longitude + delta, latitude + delta]
    params = {
        "f": "json",
        "bbox": ",".join(f"{value:.7f}" for value in bbox),
        "limit": "100",
    }
    return OGC_ITEMS_ENDPOINT + "?" + urlencode(params)


def arcgis_query_url(easting: float, northing: float) -> str:
    params = {
        "where": "1=1",
        "geometry": f"{easting:.3f},{northing:.3f}",
        "geometryType": "esriGeometryPoint",
        "inSR": "27700",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "filename,os_ref,sd_flown,ed_flown,year,polygon_id,pt_spacing,transform,geoid,latest",
        "returnGeometry": "false",
        "f": "json",
    }
    return ARCGIS_TIME_STAMPED_ENDPOINT + "?" + urlencode(params)


def exact_composite_match(
    payload: dict[str, Any], longitude: float, latitude: float, Point: Any, shape: Any
) -> tuple[dict[str, Any], int]:
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise EvidenceError("OGC_RESPONSE_NOT_FEATURE_COLLECTION")
    if payload.get("numberReturned", len(payload["features"])) > 100:
        raise EvidenceError("OGC_RESPONSE_LIMIT_EXCEEDED")
    point = Point(longitude, latitude)
    exact: list[dict[str, Any]] = []
    for feature in payload["features"]:
        geometry = feature.get("geometry")
        properties = feature.get("properties")
        if not geometry or not isinstance(properties, dict):
            continue
        candidate = shape(geometry)
        if candidate.is_valid and not candidate.is_empty and candidate.intersects(point):
            exact.append(feature)
    if len(exact) != 1:
        raise EvidenceError(f"COMPOSITE_METADATA_EXACT_MATCH_NOT_UNIQUE:found={len(exact)}")
    return exact[0], len(payload["features"])


def validate_composite_properties(properties: dict[str, Any]) -> dict[str, Any]:
    required = ["filename", "tilename", "polygon_id", "resolution", "year", "sd_flown", "ed_flown"]
    missing = [name for name in required if properties.get(name) in (None, "")]
    if missing:
        raise EvidenceError("COMPOSITE_METADATA_FIELDS_MISSING:" + ",".join(missing))
    resolution = float(properties["resolution"])
    if not (0.25 <= resolution <= 2.0):
        raise EvidenceError(f"COMPOSITE_RESOLUTION_OUT_OF_RANGE:{resolution}")
    start_date = normalize_date(properties["sd_flown"])
    end_date = normalize_date(properties["ed_flown"])
    if end_date < start_date:
        raise EvidenceError("COMPOSITE_SURVEY_DATE_ORDER_INVALID")
    year = int(str(properties["year"])[:4])
    if not (2000 <= year <= 2022):
        raise EvidenceError(f"COMPOSITE_SURVEY_YEAR_OUT_OF_RANGE:{year}")
    return {
        "filename": str(properties["filename"]),
        "tilename": str(properties["tilename"]),
        "polygon_id": str(properties["polygon_id"]),
        "resolution_m": resolution,
        "survey_date": start_date,
        "survey_end_date": end_date,
        "survey_year": year,
        "od_dtm_fn": properties.get("od_dtm_fn"),
    }


def summarize_time_stamped(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("error"):
        raise EvidenceError(f"ARCGIS_QUERY_ERROR:{payload['error']}")
    features = payload.get("features")
    if not isinstance(features, list):
        raise EvidenceError("ARCGIS_FEATURES_MISSING")
    candidates: list[dict[str, Any]] = []
    for feature in features:
        attrs = feature.get("attributes") if isinstance(feature, dict) else None
        if not isinstance(attrs, dict):
            continue
        try:
            candidates.append({
                "filename": attrs.get("filename"),
                "os_ref": attrs.get("os_ref"),
                "survey_date": normalize_date(attrs.get("sd_flown")),
                "survey_end_date": normalize_date(attrs.get("ed_flown")),
                "year": normalize_date(attrs.get("year"))[:4] if attrs.get("year") else None,
                "polygon_id": attrs.get("polygon_id"),
                "point_spacing_m": attrs.get("pt_spacing"),
                "transform": attrs.get("transform"),
                "geoid": attrs.get("geoid"),
                "latest": attrs.get("latest"),
            })
        except EvidenceError:
            continue
    candidates.sort(key=lambda row: (row.get("survey_date") or "", str(row.get("filename") or "")), reverse=True)
    return {
        "candidate_count": len(candidates),
        "newest_candidate": candidates[0] if candidates else None,
        "candidate_properties_sha256": sha256_json(candidates),
    }


def run_self_test() -> dict[str, Any]:
    Point, shape = require_geo_modules()
    sample = {
        "type": "FeatureCollection",
        "numberReturned": 1,
        "features": [{
            "type": "Feature",
            "properties": {
                "filename": "V1", "tilename": "TQ5083", "polygon_id": "P1",
                "resolution": 1.0, "year": "2020",
                "sd_flown": "2020-01-02T00:00:00Z", "ed_flown": "2020-01-03T00:00:00Z"
            },
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
        }]
    }
    feature, returned = exact_composite_match(sample, 0.5, 0.5, Point, shape)
    validated = validate_composite_properties(feature["properties"])
    if returned != 1 or validated["survey_date"] != "2020-01-02":
        raise EvidenceError("SELF_TEST_FAILED")
    return {"state": "PASS", "checks": 3, "script_version": SCRIPT_VERSION}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(os.environ.get("AAYS_REPO_ROOT", Path.cwd())))
    parser.add_argument("--examples-json", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(run_self_test(), sort_keys=True))
        return 0

    repo = args.repo_root.resolve()
    examples_path = args.examples_json or repo / "england_map_web/data/aays_18_slots/height_difference_1/examples_latest.json"
    output_path = args.output or repo / "docs/chatgpt_status/height_difference/shards/height_difference_1/runner_outputs/official_survey_metadata_latest.json"
    result: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
        "started_at": utc_now(),
        "state": "STARTED_FAIL_CLOSED",
        "primary_collection": "LIDAR_Composite_1m_DTM_2022_extents",
        "secondary_qa_layer": "LIDAR DTM Time Stamped Extents",
        "metadata": {},
        "rows": [],
        "errors": [],
        "fake_data": False,
        "business_rows_written": 0,
        "final_ready": False,
    }
    try:
        examples = validate_examples(examples_path)
        Point, shape = require_geo_modules()

        def resolve(row: dict[str, Any]) -> dict[str, Any]:
            parcel_id = row["parcel_id"]
            record: dict[str, Any] = {
                "parcel_id": parcel_id,
                "state": "BLOCKED_FAIL_CLOSED",
                "ogc_query_url": ogc_query_url(float(row["longitude"]), float(row["latitude"])),
                "arcgis_qa_query_url": arcgis_query_url(float(row["bng_easting_m"]), float(row["bng_northing_m"])),
                "errors": [],
            }
            try:
                ogc_payload, ogc_bytes = fetch_json(record["ogc_query_url"])
                feature, bbox_candidate_count = exact_composite_match(
                    ogc_payload, float(row["longitude"]), float(row["latitude"]), Point, shape
                )
                properties = validate_composite_properties(feature["properties"])
                arcgis_payload, arcgis_bytes = fetch_json(record["arcgis_qa_query_url"])
                qa = summarize_time_stamped(arcgis_payload)
                metadata = {
                    "source_url": record["ogc_query_url"],
                    "source_collection": "LIDAR_Composite_1m_DTM_2022_extents",
                    "resolution_state": "OFFICIAL_METADATA_RESOLVED",
                    "retrieved_at": utc_now(),
                    **properties,
                    "bbox_candidate_count": bbox_candidate_count,
                    "ogc_response_sha256": sha256_bytes(ogc_bytes),
                    "feature_properties_sha256": sha256_json(feature["properties"]),
                    "time_stamped_qa_source_url": record["arcgis_qa_query_url"],
                    "time_stamped_qa_response_sha256": sha256_bytes(arcgis_bytes),
                    "time_stamped_qa": qa,
                }
                record.update({"state": "OFFICIAL_METADATA_RESOLVED", "metadata": metadata})
            except Exception as exc:
                record["errors"].append(str(exc))
            return record

        workers = max(1, min(args.max_workers, 4))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(resolve, examples))
        result["rows"] = rows
        for row in rows:
            if row["state"] == "OFFICIAL_METADATA_RESOLVED":
                result["metadata"][row["parcel_id"]] = row["metadata"]
        resolved = len(result["metadata"])
        if resolved == 11:
            result["state"] = "COMPLETED_ALL_METADATA_RESOLVED"
        elif resolved > 0:
            result["state"] = "COMPLETED_PARTIAL_METADATA_RESOLVED"
        else:
            result["state"] = "COMPLETED_NO_METADATA_RESOLVED"
    except Exception as exc:
        result["state"] = "BLOCKED_FAIL_CLOSED"
        result["errors"].append(str(exc))
    finally:
        result["finished_at"] = utc_now()
        result["counts"] = {
            "prepared_points": 11,
            "primary_ogc_queries": len(result["rows"]),
            "secondary_arcgis_queries": len(result["rows"]),
            "resolved_metadata_rows": len(result["metadata"]),
        }
        atomic_json(output_path, result)

    print(f"SLOT_ID={SLOT_ID}")
    print(f"STATE={result['state']}")
    print(f"RESOLVED_METADATA_ROWS={len(result['metadata'])}")
    print("FINAL_READY=false")
    return 2 if result["state"] == "BLOCKED_FAIL_CLOSED" else 0


if __name__ == "__main__":
    sys.exit(main())
