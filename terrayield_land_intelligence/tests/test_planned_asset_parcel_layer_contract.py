from __future__ import annotations

from app.services.planned_asset_service import (
    PLANNED_BUILDINGS_REQUIRED_PROPERTIES,
    build_planned_buildings_feature,
    build_planned_buildings_feature_collection,
)


def test_planned_buildings_feature_contract_fields() -> None:
    feature = build_planned_buildings_feature(
        "parcel-1",
        {"type": "Polygon", "coordinates": []},
        [
            {
                "title": "School extension",
                "probability": 0.82,
                "completion_month": "2027-03",
                "source_name": "planning_portal",
                "source_url": "https://example.invalid/planning",
                "source_date": "2026-01-15",
                "confidence_score": 0.74,
                "relation_type": "intersects",
                "matching_method": "parcel_overlay",
            }
        ],
    )
    assert feature["type"] == "Feature"
    props = feature["properties"]
    assert PLANNED_BUILDINGS_REQUIRED_PROPERTIES.issubset(props.keys())
    assert props["layer_kind"] == "planned_buildings_v1"
    assert props["parcel_id"] == "parcel-1"
    assert props["planned_asset_count"] == 1
    assert props["planned_building_1_value"] == "School extension"
    assert props["planned_building_1_probability"] == 0.82
    assert props["planned_building_1_completion_month"] == "2027-03"
    assert props["color_category"] == "planned-buildings"


def test_planned_buildings_collection_excludes_unmatched_parcels_flag() -> None:
    collection = build_planned_buildings_feature_collection([])
    assert collection["type"] == "FeatureCollection"
    assert collection["metadata"]["layer_kind"] == "planned_buildings_v1"
    assert collection["metadata"]["unmatched_parcels_included"] is False
