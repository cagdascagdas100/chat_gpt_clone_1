#!/usr/bin/env python3
"""Fail-closed official geometry pipeline for future_growth_1.

Scope is limited to canonical rows 1..30761. The script can validate the first
three canonical rows, fetch GLA Brownfield polygons, optionally read current HM
Land Registry INSPIRE GML polygons, and publish spatial candidate relations.
It never emits a Future Growth score until the complete future_growth_v1 factor
matrix is independently validated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from pyproj import Transformer
from shapely.geometry import MultiPolygon, Point, Polygon, mapping, shape
from shapely.ops import transform as shapely_transform

SLOT_ID = "future_growth_1"
ROW_START, ROW_END, SHARD_COUNT, CANONICAL_COUNT = 1, 30761, 30761, 92283
CALCULATION_VERSION = "future_growth_v1"
GLA_QUERY = "https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/MapServer/101/query"
HMLR_DOWNLOAD_INDEX = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
SITE_REFS = ("LBBD49/XJ", "LBBD72/ZZ", "LBBD23", "LBBD91/DI")
TARGET_INSPIRE_IDS = ("39729785", "39724273", "60116682")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def finite_float(value: Any, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {field}: {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"non-finite {field}: {value!r}")
    return result


@dataclass(frozen=True)
class Parcel:
    row_no: int
    parcel_id: str
    inspire_id: str
    lon: float
    lat: float
    authority: str


def load_first_three(path: Path) -> tuple[list[Parcel], dict[str, Any]]:
    payload = read_json(path)
    features = payload.get("features") if isinstance(payload, dict) else None
    if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
        raise ValueError("canonical source must be a FeatureCollection")
    if len(features) != CANONICAL_COUNT:
        raise ValueError(f"expected {CANONICAL_COUNT} canonical features, received {len(features)}")

    rows: set[int] = set()
    parcel_ids: set[str] = set()
    inspire_ids: set[str] = set()
    selected: list[Parcel] = []
    for feature in features:
        props = dict(feature.get("properties") or {})
        row_no = int(props.get("row_no"))
        parcel_id = str(props.get("parcel_id") or "").strip()
        inspire_id = str(props.get("hmlr_inspire_id") or "").strip()
        authority = str(props.get("london_authority") or "").strip()
        lon = finite_float(props.get("hmlr_lon"), "hmlr_lon")
        lat = finite_float(props.get("hmlr_lat"), "hmlr_lat")
        if not parcel_id or not inspire_id or not authority:
            raise ValueError(f"row {row_no} has empty canonical identity fields")
        if row_no in rows or parcel_id in parcel_ids or inspire_id in inspire_ids:
            raise ValueError("canonical row, parcel, or INSPIRE identity is duplicated")
        rows.add(row_no)
        parcel_ids.add(parcel_id)
        inspire_ids.add(inspire_id)
        if row_no in (1, 2, 3):
            geom = shape(feature.get("geometry"))
            if geom.geom_type != "Point" or abs(geom.x - lon) > 1e-7 or abs(geom.y - lat) > 1e-7:
                raise ValueError(f"row {row_no} point geometry does not match HMLR coordinates")
            selected.append(Parcel(row_no, parcel_id, inspire_id, lon, lat, authority))

    if rows != set(range(1, CANONICAL_COUNT + 1)):
        raise ValueError("canonical row registry is not exactly 1..92283")
    selected.sort(key=lambda row: row.row_no)
    if [row.inspire_id for row in selected] != list(TARGET_INSPIRE_IDS):
        raise ValueError("first-three canonical HMLR INSPIRE IDs changed")
    return selected, {
        "features_validated": len(features),
        "unique_rows": len(rows),
        "unique_parcel_ids": len(parcel_ids),
        "unique_inspire_ids": len(inspire_ids),
        "source_sha256": sha256(path),
        "sample_rows": [1, 2, 3],
    }


def build_gla_url(refs: Iterable[str]) -> str:
    refs = tuple(refs)
    if not refs:
        raise ValueError("site references are required")
    quoted = ",".join("'" + ref.replace("'", "''") + "'" for ref in refs)
    params = {
        "where": f"sitereference IN ({quoted})",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    return GLA_QUERY + "?" + urllib.parse.urlencode(params)


def validate_gla(payload: dict[str, Any], expected_refs: set[str]) -> None:
    features = payload.get("features") if isinstance(payload, dict) else None
    if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
        raise ValueError("GLA response is not a FeatureCollection")
    seen: set[str] = set()
    for feature in features:
        props = dict(feature.get("properties") or {})
        ref = str(props.get("sitereference") or "").strip()
        if ref not in expected_refs or ref in seen:
            raise ValueError(f"unexpected or duplicate GLA reference: {ref!r}")
        geom = shape(feature.get("geometry"))
        if geom.geom_type not in {"Polygon", "MultiPolygon"} or geom.is_empty or not geom.is_valid:
            raise ValueError(f"invalid official GLA polygon for {ref}")
        seen.add(ref)
    if not seen:
        raise ValueError("GLA response returned no official site polygons")


def fetch_gla(refs: Iterable[str], timeout: float) -> dict[str, Any]:
    url = build_gla_url(refs)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AAYS-TerraYield-future_growth_1/1.0", "Accept": "application/geo+json,application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
        status = getattr(response, "status", 200)
    if status != 200:
        raise RuntimeError(f"official GLA endpoint returned HTTP {status}")
    payload = json.loads(raw)
    validate_gla(payload, set(refs))
    payload["_retrieval"] = {"url": url, "http_status": status, "bytes": len(raw)}
    return payload


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_pos_list(text: str) -> list[tuple[float, float]]:
    values = [float(part) for part in text.replace(",", " ").split()]
    if len(values) < 8 or len(values) % 2:
        raise ValueError("invalid GML posList")
    coords = list(zip(values[0::2], values[1::2]))
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return coords


def extract_hmlr(gml_path: Path, targets: set[str]) -> dict[str, Polygon | MultiPolygon]:
    found: dict[str, Polygon | MultiPolygon] = {}
    for _, elem in ET.iterparse(gml_path, events=("end",)):
        texts = [str(node.text or "").strip() for node in elem.iter()]
        target = next((item for item in targets if item in texts), None)
        if not target:
            continue
        polygons: list[Polygon] = []
        for node in elem.iter():
            if local_name(node.tag) == "posList" and (node.text or "").strip():
                polygon = Polygon(parse_pos_list(node.text or ""))
                if polygon.is_valid and not polygon.is_empty and polygon.area > 0:
                    polygons.append(polygon)
        if polygons:
            found[target] = polygons[0] if len(polygons) == 1 else MultiPolygon(polygons)
        elem.clear()
        if set(found) >= targets:
            break
    missing = targets - set(found)
    if missing:
        raise ValueError(f"HMLR GML is missing target INSPIRE IDs: {sorted(missing)}")
    return found


def relation(parcel_bng, site_wgs84) -> dict[str, Any]:
    to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform
    site_bng = shapely_transform(to_bng, site_wgs84)
    if site_bng.is_empty or not site_bng.is_valid:
        raise ValueError("transformed official site polygon is invalid")
    distance = float(parcel_bng.distance(site_bng))
    intersects = bool(parcel_bng.intersects(site_bng))
    if intersects:
        relation_type, weight, cap = "INTERSECTS_PARCEL", 1.0, "high_if_all_other_requirements_pass"
    elif distance <= 250:
        relation_type, weight, cap = "WITHIN_250M", 0.85, "medium_high"
    elif distance <= 500:
        relation_type, weight, cap = "WITHIN_500M", 0.70, "medium"
    elif distance <= 1000:
        relation_type, weight, cap = "WITHIN_1000M", 0.52, "low_medium"
    elif distance <= 2000:
        relation_type, weight, cap = "WITHIN_2000M", 0.35, "low"
    else:
        relation_type, weight, cap = "OUTSIDE_2000M", 0.0, "none"
    return {
        "relation_type": relation_type,
        "polygon_distance_m": round(distance, 3),
        "intersects": intersects,
        "relation_weight_hint": weight,
        "confidence_cap": cap,
        "site_geometry_bng_area_m2": round(float(site_bng.area), 3),
        "parcel_geometry_bng_area_m2": round(float(parcel_bng.area), 3),
    }


def publish(parcels: list[Parcel], audit: dict[str, Any], gla: dict[str, Any], hmlr, output_dir: Path, hmlr_source: str | None) -> dict[str, Any]:
    by_ref = {str((feature.get("properties") or {}).get("sitereference")): feature for feature in gla.get("features", [])}
    to_bng = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True).transform
    rows: list[dict[str, Any]] = []
    geo_features: list[dict[str, Any]] = []
    for parcel in parcels:
        parcel_polygon = hmlr.get(parcel.inspire_id) if hmlr else None
        parcel_point = shapely_transform(to_bng, Point(parcel.lon, parcel.lat))
        for ref in SITE_REFS:
            feature = by_ref.get(ref)
            if not feature:
                continue
            props = dict(feature.get("properties") or {})
            site_polygon = shape(feature.get("geometry"))
            site_bng = shapely_transform(to_bng, site_polygon)
            spatial = relation(parcel_polygon, site_polygon) if parcel_polygon is not None else {
                "relation_type": "PENDING_HMLR_PARCEL_POLYGON",
                "polygon_distance_m": None,
                "intersects": None,
                "relation_weight_hint": 0.0,
                "confidence_cap": "zero_until_parcel_polygon",
                "site_geometry_bng_area_m2": round(float(site_bng.area), 3),
                "parcel_geometry_bng_area_m2": None,
            }
            end_date = str(props.get("enddate") or "").strip()
            notes = str(props.get("notes") or "").strip()
            stale = bool(end_date) or "complete" in notes.lower()
            row = {
                "row_no": parcel.row_no,
                "parcel_id": parcel.parcel_id,
                "hmlr_inspire_id": parcel.inspire_id,
                "local_authority": parcel.authority,
                "source_key": "planning_brownfield_gla_polygon",
                "source_url": GLA_QUERY,
                "source_reference": ref,
                "site_name": props.get("sitenameaddress") or props.get("sitename"),
                "hectares": props.get("hectares"),
                "planning_status": props.get("planningstatus"),
                "deliverable": props.get("deliverable"),
                "end_date": end_date or None,
                "notes": notes or None,
                "point_to_site_polygon_distance_m": round(float(parcel_point.distance(site_bng)), 3),
                **spatial,
                "site_polygon_verified": True,
                "parcel_polygon_verified": parcel_polygon is not None,
                "active_growth_signal": not stale,
                "future_growth_score": None,
                "scorable": False,
                "score_blocker": "FULL_FUTURE_GROWTH_FACTOR_MATRIX_NOT_VALIDATED",
            }
            rows.append(row)
            geo_features.append({"type": "Feature", "geometry": mapping(site_polygon), "properties": {k: v for k, v in row.items() if k != "source_url"}})

    verified = sum(1 for row in rows if row["parcel_polygon_verified"])
    result = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "calculation_version": CALCULATION_VERSION,
        "canonical_scope": "LONDON_CANONICAL_92283_NOT_ALL_ENGLAND",
        "parcel_partition": {"start": ROW_START, "end": ROW_END, "count": SHARD_COUNT, "canonical_count": CANONICAL_COUNT},
        "canonical_audit": audit,
        "official_sources": {"gla_brownfield_layer": GLA_QUERY, "hmlr_download_index": HMLR_DOWNLOAD_INDEX, "hmlr_gml_source": hmlr_source},
        "counts": {
            "canonical_parcels_sampled": len(parcels),
            "gla_site_polygons": len(gla.get("features", [])),
            "candidate_relations": len(rows),
            "parcel_polygon_relations_verified": verified,
            "active_candidates": sum(1 for row in rows if row["active_growth_signal"]),
            "stale_or_completed_rejections": sum(1 for row in rows if not row["active_growth_signal"]),
            "scored_business_rows": 0,
            "actual_business_data_rows_written": 0,
        },
        "rows": rows,
        "first_unverified_step": "BUILD_30761_ROW_FULL_FACTOR_MATRIX_THEN_SCORE_WITH_CONFIDENCE" if verified else "PROVIDE_CURRENT_HMLR_BARKING_DAGENHAM_GML_THEN_VERIFY_PARCEL_POLYGONS",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    write_json(output_dir / "official_geometry_verification_latest.json", result)
    write_json(output_dir / "official_site_polygons_latest.geojson", {"type": "FeatureCollection", "features": geo_features})
    return result


def self_test() -> dict[str, Any]:
    ox, oy = 540000, 180000
    parcel = Polygon([(ox, oy), (ox + 100, oy), (ox + 100, oy + 100), (ox, oy + 100), (ox, oy)])
    to_wgs = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True).transform
    cases = [
        (Polygon([(ox + 50, oy + 50), (ox + 150, oy + 50), (ox + 150, oy + 150), (ox + 50, oy + 150), (ox + 50, oy + 50)]), "INTERSECTS_PARCEL"),
        (Polygon([(ox + 200, oy), (ox + 250, oy), (ox + 250, oy + 50), (ox + 200, oy + 50), (ox + 200, oy)]), "WITHIN_250M"),
        (Polygon([(ox + 400, oy), (ox + 450, oy), (ox + 450, oy + 50), (ox + 400, oy + 50), (ox + 400, oy)]), "WITHIN_500M"),
        (Polygon([(ox + 1500, oy), (ox + 1550, oy), (ox + 1550, oy + 50), (ox + 1500, oy + 50), (ox + 1500, oy)]), "WITHIN_2000M"),
        (Polygon([(ox + 3000, oy), (ox + 3050, oy), (ox + 3050, oy + 50), (ox + 3000, oy + 50), (ox + 3000, oy)]), "OUTSIDE_2000M"),
    ]
    checks = []
    for index, (site_bng, expected) in enumerate(cases, start=1):
        actual = relation(parcel, shapely_transform(to_wgs, site_bng))["relation_type"]
        checks.append({"check": f"relation_{index}", "expected": expected, "actual": actual, "pass": actual == expected})
    fixture = {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": mapping(shapely_transform(to_wgs, cases[0][0])), "properties": {"sitereference": "LBBD49/XJ"}}]}
    validate_gla(fixture, {"LBBD49/XJ"})
    checks.append({"check": "gla_polygon_validation", "expected": "PASS", "actual": "PASS", "pass": True})
    query_ok = build_gla_url(SITE_REFS).startswith("https://gis.london.gov.uk/")
    checks.append({"check": "official_query_domain", "expected": True, "actual": query_ok, "pass": query_ok})
    return {"slot_id": SLOT_ID, "checks": checks, "passed": sum(1 for check in checks if check["pass"]), "total": len(checks), "ok": all(check["pass"] for check in checks), "network_used": False, "fake_data_written": False}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--canonical-geojson", type=Path)
    parser.add_argument("--gla-geojson", type=Path)
    parser.add_argument("--hmlr-gml", type=Path)
    parser.add_argument("--network", action="store_true")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        result = self_test()
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["ok"] else 2

    root = args.repo_root.resolve()
    canonical = (args.canonical_geojson or root / "england_map_web/data/program_layer_matrix/security.geojson").resolve()
    output = (args.output_dir or root / "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_2").resolve()
    parcels, audit = load_first_three(canonical)
    if args.gla_geojson:
        gla = read_json(args.gla_geojson.resolve())
        validate_gla(gla, set(SITE_REFS))
        gla["_retrieval"] = {"path": str(args.gla_geojson.resolve()), "sha256": sha256(args.gla_geojson.resolve())}
    elif args.network:
        gla = fetch_gla(SITE_REFS, args.timeout)
    else:
        raise ValueError("provide --gla-geojson or enable --network")

    hmlr = None
    hmlr_source = None
    if args.hmlr_gml:
        hmlr_path = args.hmlr_gml.resolve()
        hmlr = extract_hmlr(hmlr_path, set(TARGET_INSPIRE_IDS))
        hmlr_source = f"{hmlr_path} sha256={sha256(hmlr_path)}"
    result = publish(parcels, audit, gla, hmlr, output, hmlr_source)
    print(json.dumps({"ok": True, "slot_id": SLOT_ID, "candidate_relations": result["counts"]["candidate_relations"], "parcel_polygon_relations_verified": result["counts"]["parcel_polygon_relations_verified"], "scored_business_rows": 0, "output_dir": str(output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "slot_id": SLOT_ID, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
