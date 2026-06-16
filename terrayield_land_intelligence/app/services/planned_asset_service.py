from __future__ import annotations

from typing import Any

PLANNED_BUILDINGS_LAYER_KIND = "planned_buildings_v1"
PLANNED_BUILDINGS_SOURCE_CONTRACT_VERSION = "planned_buildings_v1"

PLANNED_BUILDINGS_REQUIRED_PROPERTIES = {
    "layer_kind",
    "parcel_id",
    "planned_asset_count",
    "planned_buildings",
    "planned_building_1_value",
    "planned_building_1_probability",
    "planned_building_1_completion_month",
    "planned_building_2_value",
    "planned_building_2_probability",
    "planned_building_2_completion_month",
    "planned_building_3_value",
    "planned_building_3_probability",
    "planned_building_3_completion_month",
    "source_name",
    "source_url",
    "source_date",
    "evidence_summary",
    "confidence_accuracy_label",
    "match_confidence_score",
    "relation_type",
    "matching_method",
    "calculation_explanation",
    "color_hex",
    "color_category",
    "source_contract_version",
}


def _compact_asset(asset: dict[str, Any], idx: int) -> dict[str, Any]:
    return {
        "rank": idx,
        "value": asset.get("value") or asset.get("title") or asset.get("project_name"),
        "probability": asset.get("probability"),
        "completion_month": asset.get("completion_month"),
        "type": asset.get("asset_type") or asset.get("planned_asset_type"),
        "title": asset.get("title") or asset.get("project_name"),
        "planning_status": asset.get("planning_status") or asset.get("status"),
        "source_name": asset.get("source_name"),
        "source_url": asset.get("source_url"),
        "source_date": asset.get("source_date") or asset.get("last_source_update_at"),
        "confidence_score": asset.get("confidence_score") or asset.get("match_confidence_score"),
        "relation_type": asset.get("relation_type"),
        "matching_method": asset.get("matching_method"),
        "distance_m": asset.get("distance_m"),
    }


def build_planned_buildings_feature(
    parcel_id: str,
    geometry: dict[str, Any],
    planned_assets: list[dict[str, Any]],
    *,
    color_hex: str = "#7c3aed",
    color_category: str = "planned-buildings",
) -> dict[str, Any]:
    """Build a GeoJSON feature for a matched parcel planned-buildings layer.

    The helper intentionally returns no feature for unmatched parcels; callers
    should pass only parcels with one or more planned assets/buildings.
    """
    top_three = [_compact_asset(asset, i + 1) for i, asset in enumerate(planned_assets[:3])]

    def ranked_value(rank: int, field: str) -> Any:
        return top_three[rank - 1].get(field) if len(top_three) >= rank else None

    first = top_three[0] if top_three else {}
    props: dict[str, Any] = {
        "layer_kind": PLANNED_BUILDINGS_LAYER_KIND,
        "parcel_id": parcel_id,
        "planned_asset_count": len(planned_assets),
        "planned_buildings": top_three,
        "planned_building_1_value": ranked_value(1, "value"),
        "planned_building_1_probability": ranked_value(1, "probability"),
        "planned_building_1_completion_month": ranked_value(1, "completion_month"),
        "planned_building_2_value": ranked_value(2, "value"),
        "planned_building_2_probability": ranked_value(2, "probability"),
        "planned_building_2_completion_month": ranked_value(2, "completion_month"),
        "planned_building_3_value": ranked_value(3, "value"),
        "planned_building_3_probability": ranked_value(3, "probability"),
        "planned_building_3_completion_month": ranked_value(3, "completion_month"),
        "source_name": first.get("source_name"),
        "source_url": first.get("source_url"),
        "source_date": first.get("source_date"),
        "evidence_summary": "Top three planned buildings/assets matched to this parcel.",
        "confidence_accuracy_label": "modelled_match",
        "match_confidence_score": first.get("confidence_score"),
        "relation_type": first.get("relation_type"),
        "matching_method": first.get("matching_method"),
        "calculation_explanation": "Parcel shown because at least one planned building/asset is matched.",
        "color_hex": color_hex,
        "color_category": color_category,
        "source_contract_version": PLANNED_BUILDINGS_SOURCE_CONTRACT_VERSION,
    }
    missing = sorted(PLANNED_BUILDINGS_REQUIRED_PROPERTIES - props.keys())
    if missing:
        raise ValueError(f"planned buildings contract missing properties: {missing}")
    return {"type": "Feature", "geometry": geometry, "properties": props}


def build_planned_buildings_feature_collection(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "metadata": {
            "layer_kind": PLANNED_BUILDINGS_LAYER_KIND,
            "source_contract_version": PLANNED_BUILDINGS_SOURCE_CONTRACT_VERSION,
            "unmatched_parcels_included": False,
        },
        "features": features,
    }
