from fastapi import APIRouter

from app.services.planned_asset_response import get_planned_assets_parcel_layer_response

router = APIRouter()
admin_router = APIRouter()


@router.get('/planned-assets/parcel-layer')
def planned_assets_parcel_layer():
    return get_planned_assets_parcel_layer_response()
