
from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.contractor_export_service import export_status, read_csv_rows, read_manifest

router = APIRouter(prefix="/api/contractors", tags=["contractors"])


@router.get("/status")
def contractor_export_status():
    return export_status()


@router.get("/companies")
def contractor_companies(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    return read_csv_rows("companies", limit=limit, offset=offset)


@router.get("/projects")
def contractor_projects(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    return read_csv_rows("projects", limit=limit, offset=offset)


@router.get("/parcel-matches")
def contractor_parcel_matches(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    return read_csv_rows("parcel_matches", limit=limit, offset=offset)


@router.get("/manifest")
def contractor_manifest():
    return read_manifest()
