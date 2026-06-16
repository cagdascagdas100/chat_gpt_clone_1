from fastapi import APIRouter
from terrayield_land_intelligence.app.services.planned_asset_response import get_empty_planned_assets_layer_response

router = APIRouter()

@router.get('/planned-assets/parcel-layer')
def planned_assets_parcel_layer():
    return get_empty_planned_assets_layer_response()
