#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from pyproj import Transformer
from shapely.geometry import Point, mapping, shape

INPUT = pathlib.Path(
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json"
)
MANIFEST = pathlib.Path(
    "docs/chatgpt_status/_shared/slots_21/parcel_label_3/evidence/"
    "lambeth_conservation_areas_point_containment_source_manifest_20260804.json"
)
OUTPUTS = [
    pathlib.Path(
        "docs/chatgpt_status/_shared/slots_21/parcel_label_3/"
        "lambeth_conservation_areas_point_containment_result_latest.json"
    ),
    pathlib.Path(
        "england_map_web/data/aays_21_slots/parcel_label_3/"
        "lambeth_conservation_areas_point_containment_latest.json"
    ),
]
LAYER_URL = (
    "https://gis.lambeth.gov.uk/arcgis/rest/services/"
    "LambethConservationAreas/MapServer/0"
)
QUERY_ENDPOINT = LAYER_URL + "/query"
ALLOWED_HOST = "gis.lambeth.gov.uk"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_QUERY_REQUESTS = 3
TRANSFORMER = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
NAME_FIELDS = ("NAME", "CONSERVATION_AREA", "AREA_NAME", "CA_NAME")
REFERENCE_FIELDS = ("REF", "REFERENCE", "CA_REF", "CAREF", "CA_NO", "CODE")


def now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(text)
        temporary = pathlib.Path(handle.name)
    temporary.replace(path)


def safe_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").casefold() != ALLOWED_HOST
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise RuntimeError(f"UNSAFE_OR_UNTRUSTED_URL:{url}")
    return url


def fetch(url: str, timeout: int) -> tuple[bytes, str, int]:
    safe_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-parcel-label-3/1.0",
            "Accept": "application/geo+json,application/json;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        safe_url(final_url)
        body = bytearray()
        while True:
            remaining = MAX_RESPONSE_BYTES - len(body) + 1
            chunk = response.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            body.extend(chunk)
            if len(body) > MAX_RESPONSE_BYTES:
                raise RuntimeError(
                    f"RESPONSE_TOO_LARGE:{len(body)}:{MAX_RESPONSE_BYTES}"
                )
        return bytes(body), final_url, int(getattr(response, "status", 200))


def load_manifest() -> dict[str, Any]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if payload.get("layer_url") != LAYER_URL:
        raise RuntimeError("WRONG_MANIFEST_LAYER_URL")
    if payload.get("query_endpoint") != QUERY_ENDPOINT:
        raise RuntimeError("WRONG_MANIFEST_QUERY_ENDPOINT")
    if payload.get("harvest_guid") != "e304f6fb73574e00ae1d2493092f0d61_2":
        raise RuntimeError("WRONG_MANIFEST_HARVEST_GUID")
    if len(payload.get("target_uprns", [])) != 3:
        raise RuntimeError("SOURCE_MANIFEST_TARGET_COUNT")
    sources = payload.get("sources", [])
    if len(sources) < 5:
        raise RuntimeError("SOURCE_MANIFEST_INCOMPLETE")
    for source in sources:
        excerpt = source.get("retained_excerpt", "")
        if (
            not excerpt
            or sha256_bytes(excerpt.encode("utf-8"))
            != source.get("retained_excerpt_sha256")
        ):
            raise RuntimeError("MANIFEST_EXCERPT_SHA_MISMATCH")
    return payload


def load_rows() -> list[dict[str, Any]]:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    manifest = load_manifest()
    target_uprns = set(manifest["target_uprns"])
    if len(records) != 3:
        raise RuntimeError(f"EXPECTED_3_INPUT_ROWS:{len(records)}")
    output: list[dict[str, Any]] = []
    for record in records:
        required = (
            "parcel_id",
            "UPRN",
            "FULLADDRESS",
            "POSTCODE",
            "longitude",
            "latitude",
        )
        if not record.get("exact_uprn_bound") or any(
            field not in record for field in required
        ):
            raise RuntimeError("INVALID_INPUT_ROW")
        row = {field: record[field] for field in required}
        row["UPRN"] = str(row["UPRN"])
        row["exact_uprn_bound"] = True
        if row["UPRN"] not in target_uprns:
            raise RuntimeError(f"UPRN_NOT_IN_MANIFEST:{row['UPRN']}")
        easting, northing = TRANSFORMER.transform(
            float(row["longitude"]), float(row["latitude"])
        )
        row["easting"] = float(easting)
        row["northing"] = float(northing)
        output.append(row)
    if len({row["UPRN"] for row in output}) != 3:
        raise RuntimeError("INPUT_UPRNS_NOT_UNIQUE")
    return output


def query_url(row: dict[str, Any]) -> str:
    params = {
        "where": "1=1",
        "geometry": f"{row['easting']:.3f},{row['northing']:.3f}",
        "geometryType": "esriGeometryPoint",
        "inSR": "27700",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    return QUERY_ENDPOINT + "?" + urllib.parse.urlencode(params)


def first_attribute(properties: dict[str, Any], names: tuple[str, ...]) -> Any:
    folded = {str(key).casefold(): value for key, value in properties.items()}
    for name in names:
        value = folded.get(name.casefold())
        if value not in (None, ""):
            return value
    return None


def parse_geojson(
    body: bytes,
    row: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    payload = json.loads(body)
    features = payload.get("features")
    if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
        raise RuntimeError("NOT_GEOJSON_FEATURE_COLLECTION")
    point = Point(float(row["longitude"]), float(row["latitude"]))
    candidates: list[dict[str, Any]] = []
    for index, feature in enumerate(features, 1):
        if not isinstance(feature, dict) or not feature.get("geometry"):
            continue
        geometry = shape(feature["geometry"])
        if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            continue
        if not geometry.is_valid:
            geometry = geometry.buffer(0)
        if geometry.is_empty or not geometry.covers(point):
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        name = first_attribute(properties, NAME_FIELDS)
        reference = first_attribute(properties, REFERENCE_FIELDS)
        geometry_value = mapping(geometry)
        geometry_text = canonical_json(geometry_value)
        raw_attributes_text = canonical_json(properties)
        candidates.append(
            {
                "feature_id": feature.get("id"),
                "feature_index": index,
                "official_conservation_area_name": name,
                "official_conservation_area_reference": reference,
                "geometry": geometry_value,
                "geometry_sha256": sha256_bytes(geometry_text.encode("utf-8")),
                "raw_attributes_sha256": sha256_bytes(
                    raw_attributes_text.encode("utf-8")
                ),
            }
        )
    return candidates, len(features)


def synthetic_feature(
    row: dict[str, Any],
    feature_id: int,
    name: str,
    offset: float = 0.0,
) -> dict[str, Any]:
    longitude = float(row["longitude"]) + offset
    latitude = float(row["latitude"]) + offset
    delta = 0.00008
    ring = [
        [longitude - delta, latitude - delta],
        [longitude + delta, latitude - delta],
        [longitude + delta, latitude + delta],
        [longitude - delta, latitude + delta],
        [longitude - delta, latitude - delta],
    ]
    return {
        "type": "Feature",
        "id": feature_id,
        "properties": {
            "OBJECTID": feature_id,
            "NAME": name,
            "CA_REF": f"CA{feature_id:02d}",
            "UNPROVEN_FIELD": "retained only by hash",
        },
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


def run(
    rows: list[dict[str, Any]],
    timeout: int,
    synthetic: bool = False,
    ambiguous: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
    evidence: dict[str, Any] = {
        "accessed_at": now(),
        "layer_url": LAYER_URL,
        "query_endpoint": QUERY_ENDPOINT,
        "query_count": 0,
        "queries": [],
    }
    records: list[dict[str, Any]] = []
    matched = 0
    for index, row in enumerate(rows, 1):
        url = query_url(row)
        evidence["query_count"] += 1
        try:
            if synthetic:
                features = [
                    synthetic_feature(
                        row,
                        index,
                        f"Synthetic Conservation Area {index}",
                    )
                ]
                if ambiguous and index == 2:
                    features.append(
                        synthetic_feature(
                            row,
                            100 + index,
                            "Second Synthetic Conservation Area",
                            offset=0.00001,
                        )
                    )
                body = canonical_json(
                    {"type": "FeatureCollection", "features": features}
                ).encode("utf-8")
                final_url = url
                status = 200
            else:
                body, final_url, status = fetch(url, timeout)
            candidates, returned_count = parse_geojson(body, row)
            evidence["queries"].append(
                {
                    "UPRN": row["UPRN"],
                    "request_url": url,
                    "final_url": final_url,
                    "http_status": status,
                    "bytes": len(body),
                    "response_sha256": sha256_bytes(body),
                    "returned_feature_count": returned_count,
                    "point_covering_candidate_count": len(candidates),
                    "state": "RESPONSE",
                }
            )
            output = {
                **row,
                "source_url": final_url,
                "layer_url": LAYER_URL,
                "candidate_count": len(candidates),
                "inferred": False,
            }
            if len(candidates) == 1 and candidates[0].get(
                "official_conservation_area_name"
            ):
                output.update(
                    {
                        "state": "MATCHED_UNIQUE_LAMBETH_CONSERVATION_AREA_POLYGON",
                        "official_conservation_area_designation": True,
                        **candidates[0],
                    }
                )
                matched += 1
            elif len(candidates) > 1:
                output.update(
                    {
                        "state": "NO_DATA",
                        "reason": (
                            "AMBIGUOUS_MULTIPLE_POINT_CONTAINING_"
                            "LAMBETH_CONSERVATION_AREA_POLYGONS"
                        ),
                        "candidate_geometry_sha256": [
                            candidate["geometry_sha256"] for candidate in candidates
                        ],
                    }
                )
            elif len(candidates) == 1:
                output.update(
                    {
                        "state": "NO_DATA",
                        "reason": "UNIQUE_POLYGON_MISSING_OFFICIAL_NAME",
                        "candidate_geometry_sha256": [
                            candidates[0]["geometry_sha256"]
                        ],
                    }
                )
            else:
                output.update(
                    {
                        "state": "NO_DATA",
                        "reason": "NO_POINT_CONTAINING_LAMBETH_CONSERVATION_AREA_POLYGON",
                    }
                )
        except Exception as exc:
            error = f"{type(exc).__name__}:{exc}"
            evidence["queries"].append(
                {
                    "UPRN": row["UPRN"],
                    "request_url": url,
                    "state": "ERROR",
                    "error": error,
                }
            )
            output = {
                **row,
                "source_url": QUERY_ENDPOINT,
                "layer_url": LAYER_URL,
                "candidate_count": 0,
                "state": "NO_DATA",
                "reason": error,
                "inferred": False,
            }
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
        print(
            json.dumps(
                {
                    "valid": True,
                    "input_count": 3,
                    "target_uprns": [row["UPRN"] for row in rows],
                    "layer_url": LAYER_URL,
                    "query_endpoint": QUERY_ENDPOINT,
                    "resource_class": "network",
                    "query_request_limit": MAX_QUERY_REQUESTS,
                    "max_response_bytes": MAX_RESPONSE_BYTES,
                    "write_paths": [str(path) for path in OUTPUTS],
                },
                sort_keys=True,
            )
        )
        return 0

    synthetic = args.synthetic_test or args.synthetic_ambiguous_test
    evidence, records, matched = run(
        rows,
        args.timeout,
        synthetic=synthetic,
        ambiguous=args.synthetic_ambiguous_test,
    )
    if args.synthetic_test:
        names = [record.get("official_conservation_area_name") for record in records]
        if matched != 3 or any(not name for name in names):
            raise RuntimeError(f"SYNTHETIC_UNIQUE_FAILED:{matched}:{names}")
        print(
            json.dumps(
                {
                    "valid": True,
                    "matched_rows": matched,
                    "candidate_counts": [record["candidate_count"] for record in records],
                    "names": names,
                },
                sort_keys=True,
            )
        )
        return 0
    if args.synthetic_ambiguous_test:
        states = [record["state"] for record in records]
        if (
            matched != 2
            or states[1] != "NO_DATA"
            or records[1].get("reason")
            != (
                "AMBIGUOUS_MULTIPLE_POINT_CONTAINING_"
                "LAMBETH_CONSERVATION_AREA_POLYGONS"
            )
        ):
            raise RuntimeError(
                f"SYNTHETIC_AMBIGUOUS_FAILED:{matched}:{states}"
            )
        print(
            json.dumps(
                {
                    "valid": True,
                    "matched_rows": matched,
                    "ambiguous_state": states[1],
                    "ambiguous_reason": records[1]["reason"],
                },
                sort_keys=True,
            )
        )
        return 0

    state = "PUBLISHED" if matched else "NO_DATA_CONTINUE"
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": (
            "parcel-label-3-lambeth-conservation-areas-"
            "point-containment-v1-20260804"
        ),
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": len(records),
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": round(len(records) / 3 * 100, 6),
        "percent_increase": round(len(records) / 3 * 100, 6),
        "matched_unique_conservation_area_rows": matched,
        "evidence_records": len(records),
        "source_evidence": evidence,
        "records": records,
        "unknown_attributes_promoted_to_label": False,
        "fake_data": False,
        "large_raw_files_committed": False,
        "generated_at": now(),
    }
    text = canonical_json(result) + "\n"
    for output in OUTPUTS:
        atomic_write(output, text)
    print(
        json.dumps(
            {
                "completed_count": len(records),
                "target_count": 3,
                "matched_unique_conservation_area_rows": matched,
                "state": state,
                "output_sha256": sha256_bytes(text.encode("utf-8")),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
