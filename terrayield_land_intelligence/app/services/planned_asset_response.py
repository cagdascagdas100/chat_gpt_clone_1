from __future__ import annotations

from typing import Any

from terrayield_land_intelligence.app.services.planned_asset_service import build_planned_buildings_feature_collection


def get_planned_assets_parcel_layer_response(features: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    data = build_planned_buildings_feature_collection(features or [])
    data.setdefault("metadata", {})["icon_file"] = "planed_buildings.png"
    return data
