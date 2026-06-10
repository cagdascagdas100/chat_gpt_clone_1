from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import DBSession, require_admin_token
from app.schemas.planned_asset import (
    ParcelFutureGrowthScoreResponse,
    PlannedAssetItem,
    PlannedAssetSourceItem,
    PlannedAssetsIngestRequest,
    PlannedAssetsIngestResponse,
    PlannedAssetsRecalculateRequest,
    PlannedAssetsRecalculateResponse,
)
from app.services.planned_asset_service import (
    get_parcel_future_growth_score,
    get_parcel_planned_assets,
    get_planned_asset,
    ingest_planned_assets,
    list_planned_asset_sources,
    nearby_planned_assets,
    recalculate_planned_assets,
    search_planned_assets,
)

router = APIRouter(tags=["planned-assets"])
admin_router = APIRouter(prefix="/admin/planned-assets", tags=["planned-assets-admin"])


@router.get("/parcels/{parcel_id}/planned-assets", response_model=list[PlannedAssetItem])
def get_parcel_planned_assets_payload(
    db: DBSession,
    parcel_id: int,
    limit: int = Query(default=200, ge=1, le=2000),
) -> list[PlannedAssetItem]:
    return get_parcel_planned_assets(db, parcel_id, limit=limit)


@router.get("/parcels/{parcel_id}/future-growth-score", response_model=ParcelFutureGrowthScoreResponse)
def get_parcel_future_growth_score_payload(
    db: DBSession,
    parcel_id: int,
) -> ParcelFutureGrowthScoreResponse:
    return get_parcel_future_growth_score(db, parcel_id)


@router.get("/planned-assets/search", response_model=list[PlannedAssetItem])
def search_planned_assets_payload(
    db: DBSession,
    q: str | None = Query(default=None, alias="query"),
    asset_type: str | None = None,
    status: str | None = None,
    local_authority: str | None = None,
    min_delivery_probability: float | None = Query(default=None, ge=0, le=100),
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
) -> list[PlannedAssetItem]:
    return search_planned_assets(
        db,
        query_text=q,
        asset_type=asset_type,
        status_filter=status,
        local_authority=local_authority,
        min_delivery_probability=min_delivery_probability,
        limit=limit,
        offset=offset,
    )


@router.get("/planned-assets/nearby", response_model=list[PlannedAssetItem])
def nearby_planned_assets_payload(
    db: DBSession,
    lat: float,
    lon: float,
    radius: int = Query(default=2000, ge=100, le=50000),
    limit: int = Query(default=200, ge=1, le=2000),
) -> list[PlannedAssetItem]:
    return nearby_planned_assets(db, lat=lat, lon=lon, radius_m=radius, limit=limit)


@router.get("/planned-assets/sources", response_model=list[PlannedAssetSourceItem])
def get_planned_asset_sources_payload(db: DBSession) -> list[PlannedAssetSourceItem]:
    return list_planned_asset_sources(db)


@router.get("/planned-assets/{planned_asset_id}", response_model=PlannedAssetItem)
def get_planned_asset_payload(db: DBSession, planned_asset_id: int) -> PlannedAssetItem:
    return get_planned_asset(db, planned_asset_id)


@admin_router.post("/ingest", response_model=PlannedAssetsIngestResponse)
def post_admin_planned_assets_ingest(
    payload: PlannedAssetsIngestRequest,
    db: DBSession,
    _auth: None = Depends(require_admin_token),
) -> PlannedAssetsIngestResponse:
    return ingest_planned_assets(db, payload)


@admin_router.post("/recalculate-scores", response_model=PlannedAssetsRecalculateResponse)
def post_admin_planned_assets_recalculate_scores(
    payload: PlannedAssetsRecalculateRequest,
    db: DBSession,
    _auth: None = Depends(require_admin_token),
) -> PlannedAssetsRecalculateResponse:
    return recalculate_planned_assets(db, payload)
