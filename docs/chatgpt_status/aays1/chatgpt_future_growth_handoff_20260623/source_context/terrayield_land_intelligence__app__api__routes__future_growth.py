from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DBSession, require_admin_token
from app.core.config import get_settings
from app.future_growth.evidence_service import FutureGrowthEvidenceService
from app.future_growth.jobs import (
    run_future_growth_all,
    run_future_growth_ingest,
    run_future_growth_score,
    run_future_growth_vectors,
)
from app.future_growth.tile_service import FutureGrowthTileService
from app.schemas.future_growth import (
    FutureGrowthEvidenceItem,
    FutureGrowthJobRequest,
    FutureGrowthJobResponse,
    FutureGrowthLayerResponse,
    FutureGrowthMethodologyResponse,
    FutureGrowthParcelDetailResponse,
    FutureGrowthVectorResponse,
)

router = APIRouter(prefix="/api/future-growth", tags=["future-growth"])


def _parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if not value:
        return None
    west, south, east, north = [float(part.strip()) for part in value.split(",")]
    return west, south, east, north


@router.get("/layer", response_model=FutureGrowthLayerResponse)
def get_future_growth_layer(
    db: DBSession,
    bbox: str | None = Query(default=None),
    zoom: float | None = Query(default=None),
    local_authority_code: str | None = Query(default=None),
    min_score: float | None = Query(default=None, ge=0, le=100),
    max_score: float | None = Query(default=None, ge=0, le=100),
    limit: int = Query(default=5000, ge=1, le=20000),
) -> FutureGrowthLayerResponse:
    service = FutureGrowthTileService(db)
    payload = service.get_layer_geojson(
        bbox=_parse_bbox(bbox),
        zoom=zoom,
        local_authority_code=local_authority_code,
        min_score=min_score,
        max_score=max_score,
        limit=limit,
    )
    return FutureGrowthLayerResponse(**payload)


@router.get("/parcels/{parcel_id}", response_model=FutureGrowthParcelDetailResponse)
def get_future_growth_parcel_detail(db: DBSession, parcel_id: int) -> FutureGrowthParcelDetailResponse:
    service = FutureGrowthEvidenceService(db)
    payload = service.get_parcel_detail(parcel_id)
    return FutureGrowthParcelDetailResponse(**payload)


@router.get("/parcels/{parcel_id}/evidence", response_model=list[FutureGrowthEvidenceItem])
def get_future_growth_parcel_evidence(db: DBSession, parcel_id: int) -> list[FutureGrowthEvidenceItem]:
    service = FutureGrowthEvidenceService(db)
    score = service.get_latest_score(parcel_id)
    payload = service.get_parcel_evidence(parcel_id, score_id=int(score["id"]))
    return [FutureGrowthEvidenceItem(**row) for row in payload]


@router.get("/cities/{city_id}/vector", response_model=FutureGrowthVectorResponse)
def get_future_growth_city_vector(db: DBSession, city_id: str) -> FutureGrowthVectorResponse:
    service = FutureGrowthTileService(db)
    payload = service.get_city_vector(city_id=city_id)
    return FutureGrowthVectorResponse(**payload)


@router.get("/local-authorities/{code}/vector", response_model=FutureGrowthVectorResponse)
def get_future_growth_local_authority_vector(db: DBSession, code: str) -> FutureGrowthVectorResponse:
    service = FutureGrowthTileService(db)
    payload = service.get_city_vector(local_authority_code=code)
    return FutureGrowthVectorResponse(**payload)


@router.get("/methodology", response_model=FutureGrowthMethodologyResponse)
def get_future_growth_methodology() -> FutureGrowthMethodologyResponse:
    settings = get_settings()
    methodology_path = settings.future_growth_methodology_path
    if not methodology_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="future growth methodology dokumani bulunamadi",
        )
    try:
        content = methodology_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = methodology_path.read_text(encoding="utf-8", errors="replace")
    return FutureGrowthMethodologyResponse(
        layer_name="Future Urban Growth & Value Shift Layer",
        methodology_markdown=content,
        source_config_path=str(settings.future_growth_source_config_path),
        generated_at=dt.datetime.now(dt.UTC),
    )


@router.post("/jobs", response_model=FutureGrowthJobResponse)
def run_future_growth_job(
    db: DBSession,
    payload: FutureGrowthJobRequest,
    _auth: None = Depends(require_admin_token),
) -> FutureGrowthJobResponse:
    if payload.action == "future-growth:ingest":
        result = run_future_growth_ingest(
            db,
            source_keys=payload.sources,
            mode=payload.mode,
        )
    elif payload.action == "future-growth:score":
        result = run_future_growth_score(
            db,
            parcel_ids=payload.parcel_ids,
            local_authority_code=payload.local_authority_code,
            calculation_version=payload.calculation_version,
            horizon_years=payload.horizon_years,
            limit=payload.limit,
        )
    elif payload.action == "future-growth:vectors":
        result = run_future_growth_vectors(
            db,
            calculation_version=payload.calculation_version,
            horizon_years=payload.horizon_years,
            local_authority_code=payload.local_authority_code,
        )
    else:
        result = run_future_growth_all(
            db,
            source_keys=payload.sources,
            mode=payload.mode,
            local_authority_code=payload.local_authority_code,
            calculation_version=payload.calculation_version,
            horizon_years=payload.horizon_years,
            limit=payload.limit,
        )
    return FutureGrowthJobResponse(action=payload.action, result=result)
