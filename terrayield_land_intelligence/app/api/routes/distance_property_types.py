from fastapi import APIRouter, Query
from typing import Optional, Dict, Any, List

router = APIRouter(prefix="/map", tags=["distance-property-types"])

METRIC_FIELDS = [
    "distance_to_nearest_industrial_unit_m",
    "distance_to_nearest_detached_home_m",
    "distance_to_nearest_retail_property_m",
    "distance_to_nearest_apartment_building_m",
    "distance_to_nearest_office_building_m",
    "distance_to_nearest_mixed_building_program_m",
]

@router.get("/distance-property-types")
def distance_property_types(
    bbox: str = Query(...),
    limit: int = Query(10, ge=1, le=500),
) -> Dict[str, Any]:
    """
    047 smoke-safe route.
    This endpoint returns a deterministic FeatureCollection shape so the UI/API contract is reachable.
    It is intentionally conservative: values are marked C_PARTIAL until real parcel context cache is wired.
    """
    west, south, east, north = [float(x) for x in bbox.split(",")]
    cx = (west + east) / 2.0
    cy = (south + north) / 2.0
    dx = max((east - west) / 100.0, 0.0001)
    dy = max((north - south) / 100.0, 0.0001)

    props = {
        "parcel_id": "047_SMOKE_PARCEL",
        "ref": "047_SMOKE_PARCEL",
        "inspire_id": "047_SMOKE_PARCEL",
        "score": 70,
        "percentage": 70,
        "class": "C_PARTIAL",
        "level": "C_PARTIAL",
        "color_category": "C_PARTIAL",
        "yapi_turu_ve_6_renk": "C_PARTIAL",
        "kaynak_ve_belirleme_yontemi": "route_smoke_contract_fallback",
        "dogruluk_skalasi": "C_PARTIAL",
        "evidence": "Smoke fallback until parcel_context_summary / metric caches are connected.",
        "source_date": "2026-06-16",
        "accuracy": "C_PARTIAL",
        "confidence": "C_PARTIAL",
        "match_method": "route_smoke_contract_fallback",
        "calculation_explanation": "Distances are placeholder non-null values for endpoint contract smoke only.",
        "raw_fields": {
            "source": "distance_property_types_route_smoke",
            "bbox": bbox,
            "limit": limit,
        },
        "distance_to_nearest_industrial_unit_m": 125.0,
        "distance_to_nearest_detached_home_m": 80.0,
        "distance_to_nearest_retail_property_m": 210.0,
        "distance_to_nearest_apartment_building_m": 95.0,
        "distance_to_nearest_office_building_m": 260.0,
        "distance_to_nearest_mixed_building_program_m": 180.0,
    }

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [cx - dx, cy - dy],
                        [cx + dx, cy - dy],
                        [cx + dx, cy + dy],
                        [cx - dx, cy + dy],
                        [cx - dx, cy - dy],
                    ]],
                },
                "properties": props,
            }
        ],
        "metadata": {
            "layer": "Distance to Nearby Property Types",
            "bbox": bbox,
            "limit": limit,
            "final_ready": False,
            "mode": "smoke_contract_fallback",
        },
    }
