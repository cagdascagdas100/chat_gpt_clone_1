#!/usr/bin/env python3
"""Exact official GIS point-query runner for AAYS future_growth_2.

Uses only official ArcGIS REST services. It never invents a spatial match and
never emits a future-growth score. A successful zero-feature response means
only "no intersection in this specific queried layer at query time".
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTINUATION_KEY = "5c59c5cee91d859c9e09480645ef8b17efe264568f2a4e312dd49d70e2958462"
USER_AGENT = "AAYS-future-growth-2-official-gis/1.0"

ROWS = [
    {"row_no": 30762, "parcel_id": "parcel_30762", "lpa": "Enfield", "lon": -0.0407406, "lat": 51.6769078},
    {"row_no": 46142, "parcel_id": "parcel_46142", "lpa": "Havering", "lon": 0.1928191, "lat": 51.5931140},
    {"row_no": 61522, "parcel_id": "parcel_61522", "lpa": "Lambeth", "lon": -0.1392630, "lat": 51.4153374},
]

SERVICES: dict[str, dict[str, Any]] = {
    "Enfield": {
        "service": "https://services.arcgis.com/drifeOPKLpgnJ8Qa/arcgis/rest/services/planning_local_plan_data_10/FeatureServer",
        "layers": {
            17: "Medium Growth Housing",
            15: "Medium Growth Mixed Use",
            26: "Indicative Location for Housing GB",
            28: "Green Belt",
            31: "Conservation Areas",
            30: "Crossrail 2 Safeguarding",
            6: "Strategic Industrial Location",
            29: "Future SIL Extensions",
            11: "Metropolitan Open Land",
            9: "Place Making Area Urban Area",
        },
    },
    "Havering": {
        "service": "https://services.arcgis.com/drifeOPKLpgnJ8Qa/arcgis/rest/services/planning_local_plan_data_16/FeatureServer",
        "layers": {
            20: "Retained Site Specific Allocations",
            22: "Romford Site Allocations",
            14: "Metropolitan Green Belt",
            6: "Flood Zone 2",
            7: "Flood Zone 3",
            19: "Proposed Beam Park Station",
            2: "Crossrail Safeguarding",
            1: "Conservation Areas",
            17: "Parks Open Spaces Playing Fields and Allotments",
            15: "Minerals Safeguarding",
        },
    },
    "Lambeth": {
        "service": "https://services.arcgis.com/drifeOPKLpgnJ8Qa/arcgis/rest/services/planning_local_plan_data_22/FeatureServer",
        "layers": {
            33: "Site Allocations",
            27: "Opportunity Areas",
            11: "Flood Risk Zone 2",
            12: "Flood Risk Zone 3",
            6: "Conservation Areas",
            18: "Key Industrial and Business Area Land with Potential",
            26: "Metropolitan Open Land",
            13: "Gypsy and Traveller Site",
            19: "Key Industrial and Business Areas",
            34: "Special Policy Area",
        },
        "additional_layers": [
            {
                "service": "https://gis.lambeth.gov.uk/arcgis/rest/services/LambethBrownfieldLandRegister/MapServer",
                "layer_id": 2,
                "name": "Brownfield Land Register",
            }
        ],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch_json(url: str, timeout: int, retries: int) -> tuple[dict[str, Any] | None, str | None, int | None]:
    last_error: str | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = getattr(response, "status", 200)
                payload = json.loads(response.read().decode("utf-8"))
                return payload, None, status
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < retries:
                time.sleep(min(2 ** (attempt - 1), 4))
    return None, last_error, None


def build_query_url(service: str, layer_id: int, lon: float, lat: float) -> str:
    geometry = json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}, separators=(",", ":"))
    params = {
        "where": "1=1",
        "geometry": geometry,
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "false",
        "resultRecordCount": "50",
        "f": "json",
    }
    return f"{service}/{layer_id}/query?{urllib.parse.urlencode(params)}"


def run(output: Path, timeout: int, retries: int) -> int:
    operations: list[dict[str, Any]] = []
    operation_no = 0
    successful_queries = 0
    failed_queries = 0
    intersections = 0

    for row in ROWS:
        spec = SERVICES[row["lpa"]]
        targets = [
            {"service": spec["service"], "layer_id": layer_id, "name": name}
            for layer_id, name in spec["layers"].items()
        ] + list(spec.get("additional_layers", []))
        for target in targets:
            operation_no += 1
            query_url = build_query_url(target["service"], target["layer_id"], row["lon"], row["lat"])
            payload, error, http_status = fetch_json(query_url, timeout=timeout, retries=retries)
            features = payload.get("features", []) if isinstance(payload, dict) else []
            arcgis_error = payload.get("error") if isinstance(payload, dict) else None
            if error or arcgis_error:
                failed_queries += 1
                result = "QUERY_FAILED"
            else:
                successful_queries += 1
                result = "INTERSECTS" if features else "NO_INTERSECTION_IN_THIS_LAYER"
                intersections += int(bool(features))
            operations.append({
                "operation_no": operation_no,
                "row_no": row["row_no"],
                "parcel_id": row["parcel_id"],
                "lpa": row["lpa"],
                "lon": row["lon"],
                "lat": row["lat"],
                "layer_id": target["layer_id"],
                "layer_name": target["name"],
                "service_url": target["service"],
                "query_url_sha256": stable_hash(query_url),
                "http_status": http_status,
                "result": result,
                "feature_count": len(features),
                "features": [{"attributes": feature.get("attributes", {})} for feature in features],
                "error": error or arcgis_error,
                "source_authority_pct": 100,
                "parcel_binding_pct": 100 if features else 0,
                "future_growth_score": None,
                "confidence_pct": 0,
                "data_status": "SOURCE_VERIFIED_BINDING_FOUND_SCORE_PENDING" if features else "NO_DATA",
                "caution": "A zero result applies only to this queried layer and is not proof that the parcel has no planning constraints.",
            })

    document = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_2",
        "continuation_key": CONTINUATION_KEY,
        "generated_at": utc_now(),
        "execution_state": "COMPLETE" if failed_queries == 0 else "PARTIAL_QUERY_FAILURE",
        "official_gis_queries_total": len(operations),
        "official_gis_queries_succeeded": successful_queries,
        "official_gis_queries_failed": failed_queries,
        "exact_layer_intersections_found": intersections,
        "scored_business_rows": 0,
        "operations": operations,
        "quality_policy": {
            "official_sources_only": True,
            "exact_arcgis_point_intersection": True,
            "zero_result_is_layer_specific_only": True,
            "score_generation_enabled": False,
            "fake_data": False,
        },
        "final_ready": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: document[k] for k in (
        "execution_state", "official_gis_queries_total", "official_gis_queries_succeeded",
        "official_gis_queries_failed", "exact_layer_intersections_found")}, ensure_ascii=False))
    return 0 if failed_queries == 0 else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    return run(args.output, max(5, args.timeout), max(1, args.retries))


if __name__ == "__main__":
    sys.exit(main())
