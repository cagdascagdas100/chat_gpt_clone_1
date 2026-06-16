from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from app.services.planned_asset_response import get_planned_assets_parcel_layer_response

router = APIRouter()
admin_router = APIRouter()

_DATA_ENV_VARS = (
    "TYLI_PLANNED_ASSETS_GEOJSON",
    "AAYS_PLANNED_ASSETS_GEOJSON",
    "PLANNED_ASSETS_PARCEL_LAYER_GEOJSON",
)
_DATA_FILE_NAMES = (
    "planned_assets_parcel_layer.geojson",
    "parcel_planned_assets.geojson",
    "planned_buildings_parcel_layer.geojson",
    "nearby_planned_developments.geojson",
    "parcel_planned_buildings.geojson",
    "planned_assets_parcel_layer.json",
    "parcel_planned_assets.json",
    "planned_buildings_parcel_layer.json",
    "nearby_planned_developments.json",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _candidate_dirs() -> list[Path]:
    root = _repo_root()
    dirs = [
        root / "england_map_web" / "data",
        root / "terrayield_land_intelligence" / "data",
        root / "data",
        root / "runtime" / "planned_buildings",
    ]
    for name in ("TYLI_SOURCE_DATA_DIR", "TYLI_RAW_STORAGE_DIR", "AAYS_RUNTIME_DATA_DIR"):
        value = os.getenv(name)
        if value:
            dirs.append(Path(value))
    return dirs


def _candidate_files() -> list[Path]:
    files: list[Path] = []
    for env_name in _DATA_ENV_VARS:
        value = os.getenv(env_name)
        if value:
            files.append(Path(value))
    for directory in _candidate_dirs():
        for filename in _DATA_FILE_NAMES:
            files.append(directory / filename)
    return files


def _as_feature_collection(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("features"), list):
        return {"type": "FeatureCollection", "features": payload["features"], "metadata": payload.get("metadata", {})}
    if isinstance(payload, list):
        return {"type": "FeatureCollection", "features": payload, "metadata": {}}
    return {"type": "FeatureCollection", "features": [], "metadata": {}}


@lru_cache(maxsize=1)
def _load_planned_feature_collection() -> tuple[dict[str, Any], str | None]:
    for path in _candidate_files():
        try:
            if not path.exists() or not path.is_file():
                continue
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            fc = _as_feature_collection(payload)
            features = [f for f in fc.get("features", []) if isinstance(f, dict) and f.get("type") == "Feature"]
            fc["features"] = features
            return fc, str(path)
        except Exception:
            continue
    return {"type": "FeatureCollection", "features": [], "metadata": {}}, None


def _parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
    if not bbox:
        return None
    try:
        vals = [float(x.strip()) for x in bbox.split(",")]
        if len(vals) == 4:
            return vals[0], vals[1], vals[2], vals[3]
    except Exception:
        return None
    return None


def _coords_in_bbox(coords: Any, bounds: tuple[float, float, float, float]) -> bool:
    west, south, east, north = bounds
    if isinstance(coords, list) and len(coords) >= 2 and all(isinstance(coords[i], (int, float)) for i in (0, 1)):
        lon = float(coords[0]); lat = float(coords[1])
        return west <= lon <= east and south <= lat <= north
    if isinstance(coords, list):
        return any(_coords_in_bbox(item, bounds) for item in coords)
    return False


def _filter_features(features: list[dict[str, Any]], bbox: str | None, limit: int) -> list[dict[str, Any]]:
    bounds = _parse_bbox(bbox)
    selected: list[dict[str, Any]] = []
    for feature in features:
        if bounds is not None:
            geometry = feature.get("geometry") or {}
            if not _coords_in_bbox(geometry.get("coordinates"), bounds):
                continue
        selected.append(feature)
        if len(selected) >= limit:
            break
    return selected


def planned_assets_metadata(data_path: str | None, total: int, returned: int) -> dict[str, Any]:
    data_present = bool(data_path and total > 0)
    meta = {
        "layer": "Nearby Planned Developments",
        "data_present": data_present,
        "data_path": data_path,
        "feature_count_total": total,
        "feature_count_returned": returned,
        "unmatched_parcels_included": False,
    }
    if not data_present:
        meta["data_gap"] = "No verified planned-assets parcel match dataset is loaded in this runtime."
    return meta


@router.get("/planned-assets/parcel-layer")
def planned_assets_parcel_layer(
    bbox: str | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
) -> dict[str, Any]:
    source_fc, data_path = _load_planned_feature_collection()
    source_features = source_fc.get("features", [])
    features = _filter_features(source_features, bbox, limit)
    data = get_planned_assets_parcel_layer_response(features)
    data.setdefault("metadata", {}).update(planned_assets_metadata(data_path, len(source_features), len(features)))
    return data


@router.get("/planned-assets/search")
def planned_assets_search(limit: int = Query(default=10, ge=1, le=100)) -> dict[str, Any]:
    source_fc, data_path = _load_planned_feature_collection()
    source_features = source_fc.get("features", [])
    features = source_features[:limit]
    items = []
    for feature in features:
        props = feature.get("properties") or {}
        items.append({
            "parcel_id": props.get("parcel_id"),
            "planned_asset_count": props.get("planned_asset_count"),
            "planned_building_1_value": props.get("planned_building_1_value"),
            "source_name": props.get("source_name"),
            "source_date": props.get("source_date"),
            "relation_type": props.get("relation_type"),
            "match_confidence_score": props.get("match_confidence_score"),
        })
    return {
        "items": items,
        "count": len(items),
        "metadata": planned_assets_metadata(data_path, len(source_features), len(items)),
    }
