#!/usr/bin/env python3
"""Fetch official Planning Data GeoJSON and exact-crosswalk it to current HMLR INSPIRE.

A match is promoted only when:
1. the official Planning Data geometry intersects exactly one current HMLR polygon;
2. that polygon exposes a unique Land Registry INSPIRE ID; and
3. the same INSPIRE ID exists in the explicit future_growth_2 canonical shard.

Nearest-point matching is forbidden. Product scores remain null; this script only
produces geometry/identity evidence and confidence caps.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

OFFICIAL_PLANNING_HOST = "www.planning.data.gov.uk"

def official_geojson_url(source_url: str) -> str:
    parsed = urlparse(source_url)
    if parsed.netloc.lower() != OFFICIAL_PLANNING_HOST:
        raise ValueError(f"non-official Planning Data host: {parsed.netloc}")
    path = parsed.path.rstrip("/")
    if not re.fullmatch(r"/entity/\d+", path):
        raise ValueError(f"source URL is not an entity URL: {source_url}")
    return f"{parsed.scheme or 'https'}://{OFFICIAL_PLANNING_HOST}{path}.geojson"

def load_canonical_map(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            inspire_id = str(row.get("hmlr_inspire_id") or "").strip()
            if not inspire_id:
                raise ValueError(f"canonical line {line_no} lacks hmlr_inspire_id")
            if inspire_id in out:
                raise ValueError(f"duplicate canonical hmlr_inspire_id {inspire_id}")
            out[inspire_id] = row
    if not out:
        raise ValueError("canonical shard is empty")
    return out

def detect_inspire_id_column(columns: list[str]) -> str:
    exact = [c for c in columns if norm_col(c) in {"inspireid", "inspire_id", "landregistryinspireid"}]
    if len(exact) == 1:
        return exact[0]
    fuzzy = [c for c in columns if "inspire" in norm_col(c) and "id" in norm_col(c)]
    if len(fuzzy) != 1:
        raise ValueError(f"could not identify one INSPIRE ID column: {columns}")
    return fuzzy[0]

def norm_col(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "", value.lower())

def fetch_json(url: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AAYS-future-growth-2/1.0 official-source-verifier"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("GeoJSON response is not an object")
    return payload

def geojson_geometry(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("type") == "Feature":
        geometry = payload.get("geometry")
    elif payload.get("type") == "FeatureCollection":
        features = payload.get("features")
        if not isinstance(features, list) or len(features) != 1:
            raise ValueError("entity GeoJSON must contain exactly one feature")
        geometry = features[0].get("geometry")
    else:
        raise ValueError("unsupported GeoJSON root type")
    if not isinstance(geometry, dict) or not geometry.get("type"):
        raise ValueError("official entity GeoJSON lacks geometry")
    return geometry

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-json", type=Path, required=True)
    parser.add_argument("--canonical-shard-jsonl", type=Path, required=True)
    parser.add_argument("--hmlr-manifest-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    try:
        import geopandas as gpd
        from shapely.geometry import shape
    except ImportError as exc:
        raise RuntimeError(f"required geospatial dependency missing: {exc}") from exc

    candidates_payload = json.loads(args.candidate_json.read_text(encoding="utf-8"))
    candidates = candidates_payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidate payload lacks candidates array")
    canonical = load_canonical_map(args.canonical_shard_jsonl)
    hmlr_manifest = json.loads(args.hmlr_manifest_json.read_text(encoding="utf-8"))
    downloads = hmlr_manifest.get("downloads")
    if not isinstance(downloads, list) or not downloads:
        raise ValueError("HMLR manifest lacks downloads")

    hmlr_by_authority: dict[str, tuple[Any, str]] = {}
    for item in downloads:
        authority = str(item.get("authority") or "").strip()
        path = Path(str(item.get("path") or ""))
        if not authority or not path.is_file():
            raise ValueError(f"invalid HMLR manifest row: {item}")
        frame = gpd.read_file(path)
        if frame.empty or frame.crs is None:
            raise ValueError(f"HMLR GML is empty or lacks CRS: {path}")
        id_col = detect_inspire_id_column(list(frame.columns))
        hmlr_by_authority[authority] = (frame, id_col)

    results: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        eligibility = str(candidate.get("eligibility") or candidate.get("candidate_eligibility") or "")
        base = {
            "candidate_id": candidate_id,
            "canonical_row_no": None,
            "canonical_parcel_id": None,
            "future_growth_score": None,
            "future_growth_confidence": 0,
            "nearest_point_promotion_used": False,
        }
        if not eligibility.startswith("eligible"):
            results.append({**base, "state": "SKIPPED_NOT_ELIGIBLE"})
            continue
        authority = str(candidate.get("local_authority") or "")
        if authority not in hmlr_by_authority:
            results.append({**base, "state": "BLOCKED_HMLR_AUTHORITY_GML_MISSING"})
            continue
        source_url = str(candidate.get("source_url") or "")
        try:
            geo_url = official_geojson_url(source_url)
            official_payload = fetch_json(geo_url, args.timeout)
            geometry_mapping = geojson_geometry(official_payload)
            geom = shape(geometry_mapping)
        except Exception as exc:
            results.append({**base, "state": "BLOCKED_OFFICIAL_GEOJSON", "error": f"{type(exc).__name__}: {exc}"})
            continue

        frame, id_col = hmlr_by_authority[authority]
        source = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs(frame.crs).iloc[0]
        hit_frame = frame[frame.geometry.intersects(source)]
        unique_ids = sorted({str(v).strip() for v in hit_frame[id_col].tolist() if str(v).strip()})
        if not unique_ids:
            results.append({**base, "state": "NO_EXACT_HMLR_INTERSECTION", "official_geojson_url": geo_url})
            continue
        if len(unique_ids) != 1:
            results.append({
                **base,
                "state": "AMBIGUOUS_MULTIPLE_HMLR_INSPIRE_IDS",
                "official_geojson_url": geo_url,
                "intersecting_hmlr_inspire_ids": unique_ids,
            })
            continue
        inspire_id = unique_ids[0]
        canonical_row = canonical.get(inspire_id)
        if canonical_row is None:
            results.append({
                **base,
                "state": "EXACT_HMLR_INTERSECTION_OUTSIDE_CANONICAL_SHARD",
                "official_geojson_url": geo_url,
                "hmlr_inspire_id": inspire_id,
            })
            continue
        relation = "OFFICIAL_POINT_IN_CURRENT_HMLR_POLYGON" if geom.geom_type == "Point" else "OFFICIAL_GEOMETRY_INTERSECTS_CURRENT_HMLR_POLYGON"
        confidence_cap = 65 if geom.geom_type == "Point" else 90
        results.append({
            **base,
            "state": "EXACT_IDENTITY_CROSSWALK_READY_FOR_EVIDENCE_MATRIX",
            "official_geojson_url": geo_url,
            "source_geometry_type": geom.geom_type,
            "relation_type": relation,
            "hmlr_inspire_id": inspire_id,
            "canonical_row_no": canonical_row.get("row_no"),
            "canonical_parcel_id": canonical_row.get("parcel_id"),
            "parcel_match_confidence_cap": confidence_cap,
            "future_growth_confidence": 0,
        })

    matched = [r for r in results if r["state"] == "EXACT_IDENTITY_CROSSWALK_READY_FOR_EVIDENCE_MATRIX"]
    output = {
        "schema_version": 1,
        "slot_id": "future_growth_2",
        "semantics": "EXACT_CURRENT_HMLR_INTERSECTION_AND_EXPLICIT_INSPIRE_ID_ONLY",
        "candidate_count": len(candidates),
        "results": results,
        "exact_crosswalk_count": len(matched),
        "future_growth_scores_written": 0,
        "actual_business_data_rows_written": 0,
        "nearest_point_promotion_used": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "exact_crosswalks": len(matched), "output": str(args.output_json)}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
