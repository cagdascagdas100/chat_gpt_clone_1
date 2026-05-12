from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.schemas.contractor import ContractorExportRowsResponse, ContractorStatusResponse

router = APIRouter(prefix="/api/contractor", tags=["contractor"])


def _resolve_export_root() -> Path:
    settings = get_settings()
    return (settings.contractor_export_root or (settings.contractor_storage_root / "exports")).resolve()


def _resolve_manifest_root() -> Path:
    settings = get_settings()
    return (settings.contractor_manifest_root or (settings.contractor_storage_root / "manifests")).resolve()


def _safe_read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        raw_bytes = path.read_bytes()
        return json.loads(raw_bytes.decode("utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def _read_csv_window(
    path: Path,
    *,
    offset: int,
    limit: int,
    parcel_id: str | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"CSV export not found: {path}")

    total_rows = 0
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                if parcel_id is not None and str(row.get("parcel_id") or "").strip() != parcel_id:
                    continue
                if total_rows >= offset and len(rows) < limit:
                    rows.append(dict(row))
                total_rows += 1
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read CSV export: {exc}") from exc
    return total_rows, rows


def _compute_status(
    *,
    preflight: dict[str, Any],
    load_manifest: dict[str, Any],
    match_manifest: dict[str, Any],
    export_manifest: dict[str, Any],
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    preflight_ok = (
        str(preflight.get("status", "")).lower() == "completed"
        and bool(preflight.get("db_credentials_present"))
        and bool(preflight.get("connection_ok"))
        and bool(preflight.get("db_query_ok"))
    )
    if not preflight_ok:
        warnings.append("Preflight gate not completed.")

    pipeline_ok = bool(load_manifest) and bool(match_manifest) and bool(export_manifest)
    if not pipeline_ok:
        warnings.append("One or more pipeline manifests are missing.")

    if preflight_ok and pipeline_ok:
        return "completed", warnings
    if not preflight_ok:
        return "blocked_preflight", warnings
    return "partial", warnings


@router.get("/status", response_model=ContractorStatusResponse)
def get_contractor_status() -> ContractorStatusResponse:
    settings = get_settings()
    export_root = _resolve_export_root()
    manifest_root = _resolve_manifest_root()
    preflight_audit = _safe_read_json(settings.contractor_preflight_audit_path)
    load_manifest = _safe_read_json(manifest_root / "postgres_load_manifest.json")
    parcel_match_manifest = _safe_read_json(manifest_root / "parcel_match_manifest.json")
    export_manifest = _safe_read_json(export_root / "export_manifest.json")
    status, warnings = _compute_status(
        preflight=preflight_audit,
        load_manifest=load_manifest,
        match_manifest=parcel_match_manifest,
        export_manifest=export_manifest,
    )
    return ContractorStatusResponse(
        status=status,
        storage_root=str(settings.contractor_storage_root),
        export_root=str(export_root),
        warnings=warnings,
        preflight_audit=preflight_audit,
        postgres_load_manifest=load_manifest,
        parcel_match_manifest=parcel_match_manifest,
        export_manifest=export_manifest,
    )


@router.get("/exports/contractors", response_model=ContractorExportRowsResponse)
def get_contractor_exports(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=5000),
) -> ContractorExportRowsResponse:
    source_file = (_resolve_export_root() / "contractors_for_app.csv").resolve()
    total_rows, rows = _read_csv_window(source_file, offset=offset, limit=limit)
    return ContractorExportRowsResponse(
        source_file=str(source_file),
        total_rows=total_rows,
        offset=offset,
        limit=limit,
        rows=rows,
    )


@router.get("/exports/parcel-matches", response_model=ContractorExportRowsResponse)
def get_contractor_parcel_matches(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=5000),
    parcel_id: str | None = Query(default=None),
) -> ContractorExportRowsResponse:
    source_file = (_resolve_export_root() / "contractor_parcel_matches_for_app.csv").resolve()
    total_rows, rows = _read_csv_window(
        source_file,
        offset=offset,
        limit=limit,
        parcel_id=str(parcel_id) if parcel_id is not None else None,
    )
    return ContractorExportRowsResponse(
        source_file=str(source_file),
        total_rows=total_rows,
        offset=offset,
        limit=limit,
        rows=rows,
    )
