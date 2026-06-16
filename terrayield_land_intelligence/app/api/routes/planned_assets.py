from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.services.planned_asset_response import get_planned_assets_parcel_layer_response

router = APIRouter()
admin_router = APIRouter()


def planned_assets_metadata() -> dict[str, Any]:
    return {
        "layer": "Nearby Planned Developments",
        "data_present": False,
        "data_gap": "No verified planned-assets parcel match dataset is loaded in this runtime.",
        "unmatched_parcels_included": False,
    }


@router.get("/planned-assets/parcel-layer")
def planned_assets_parcel_layer() -> dict[str, Any]:
    data = get_planned_assets_parcel_layer_response([])
    data.setdefault("metadata", {}).update(planned_assets_metadata())
    return data


@router.get("/planned-assets/search")
def planned_assets_search() -> dict[str, Any]:
    return {
        "items": [],
        "count": 0,
        "metadata": planned_assets_metadata(),
    }
