from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.schemas.contractor import (
    ContractorExportRowsResponse,
    ContractorParcelContactsResponse,
    ContractorStatusResponse,
)
from app.services.estate_agent_service import (
    load_estate_dataset,
    lookup_agents_by_parcel,
)
from app.services.runtime_ops_service import get_runtime_storage_registry

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


_PREFLIGHT_AUDIT_ALLOWED_KEYS = {
    "status",
    "db_credentials_present",
    "database_url_present",
    "connection_ok",
    "db_query_ok",
    "tcp_connect_ok",
    "env_local_present",
    "pgdatabase_present",
    "pghost_present",
    "pgpassword_present",
    "pgport_present",
    "pguser_present",
}


def _sanitize_preflight_audit(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key in _PREFLIGHT_AUDIT_ALLOWED_KEYS:
        value = payload.get(key)
        if isinstance(value, bool):
            sanitized[key] = value
        elif key == "status" and isinstance(value, str):
            sanitized[key] = value
    return sanitized


def _build_manifests(
    *,
    preflight: dict[str, Any],
    load_manifest: dict[str, Any],
    match_manifest: dict[str, Any],
    export_manifest: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        "preflight": preflight,
        "postgres_load": load_manifest,
        "parcel_match": match_manifest,
        "export": export_manifest,
    }


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


def _safe_float(value: Any) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return 0.0


def _safe_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


_STRUCTURE_TYPE_ALIASES: dict[str, tuple[str, ...]] = {
    "mustakil": ("mustakil", "detached", "single_family", "residential_detached"),
    "apartman": ("apartman", "apartment", "multi_family", "residential_block"),
    "site": ("site", "estate", "housing_estate", "masterplan"),
    "perakende": ("perakende", "retail", "shop", "mall"),
    "ofis": ("ofis", "office", "workspace"),
    "karma": ("karma", "mixed_use", "mixed-use", "mixed use"),
    "endustriyel": ("endustriyel", "industrial", "warehouse", "logistics"),
    "prefab": ("prefab", "prefabricated", "modular"),
    "tarimsal": ("tarimsal", "agricultural", "farm", "rural"),
}

_STRUCTURE_HINT_FIELDS: tuple[str, ...] = (
    "structure_type",
    "structure_types",
    "target_structure_type",
    "coverage_structure_types",
    "preferred_structure_types",
    "project_type",
    "project_types",
    "specialization",
    "specializations",
    "service_types",
    "segment",
    "segments",
    "reason",
    "note",
)

_SEPARATOR_PATTERN = re.compile(r"[|,;/]+")


def _normalize_structure_token(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    normalized = (
        normalized.replace("ı", "i")
        .replace("ş", "s")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ö", "o")
        .replace("ç", "c")
    )
    return normalized.replace("-", "_").replace(" ", "_")


def _structure_alias_set(structure_type: str | None) -> set[str]:
    if not structure_type:
        return set()
    key = _normalize_structure_token(structure_type)
    aliases = _STRUCTURE_TYPE_ALIASES.get(key)
    if aliases:
        return {_normalize_structure_token(item) for item in aliases}
    if key:
        return {key}
    return set()


def _row_matches_structure_type(
    *,
    contractor_row: dict[str, Any],
    match_row: dict[str, Any],
    structure_aliases: set[str],
) -> bool:
    if not structure_aliases:
        return True
    candidate_values: list[str] = []
    for field in _STRUCTURE_HINT_FIELDS:
        raw_value = contractor_row.get(field)
        if raw_value is not None and str(raw_value).strip():
            candidate_values.append(str(raw_value))
        raw_match_value = match_row.get(field)
        if raw_match_value is not None and str(raw_match_value).strip():
            candidate_values.append(str(raw_match_value))
    if not candidate_values:
        return True

    normalized_tokens: set[str] = set()
    for raw_value in candidate_values:
        for piece in _SEPARATOR_PATTERN.split(raw_value):
            token = _normalize_structure_token(piece)
            if token:
                normalized_tokens.add(token)
    if not normalized_tokens:
        return True

    if normalized_tokens.intersection(structure_aliases):
        return True
    return any(alias in token for alias in structure_aliases for token in normalized_tokens)


def _build_parcel_contact_rows(
    *,
    parcel_id: str,
    limit: int,
    include_blocked: bool,
    structure_type: str | None = None,
) -> tuple[list[dict[str, Any]], int, int, int, Path, Path, dict[str, Any]]:
    settings = get_settings()
    estate_dataset = load_estate_dataset(settings)
    estate_lookup_payload: dict[str, Any] = {}
    estate_join_count = 0
    strict_mode = bool(getattr(settings, "estate_agent_strict_mode", False))
    if estate_dataset.available:
        lookup_payload = lookup_agents_by_parcel(estate_dataset, parcel_id, limit=100000)
        estate_lookup_payload = lookup_payload if isinstance(lookup_payload, dict) else {}
        estate_join_count = int(estate_lookup_payload.get("join_rows_count") or 0)
        if estate_join_count > 0 or strict_mode:
            estate_rows = lookup_payload.get("agents") if isinstance(lookup_payload, dict) else []
            converted_rows: list[dict[str, Any]] = []
            ready_rows = 0
            blocked_rows = 0
            for agent_row in estate_rows if isinstance(estate_rows, list) else []:
                contact_allowed = bool(agent_row.get("contact_allowed", True))
                if contact_allowed:
                    ready_rows += 1
                else:
                    blocked_rows += 1
                if not include_blocked and not contact_allowed:
                    continue
                evidence = agent_row.get("evidence")
                evidence_url = ""
                if isinstance(evidence, list):
                    first_evidence = evidence[0] if evidence else {}
                    if isinstance(first_evidence, dict):
                        evidence_url = str(first_evidence.get("source_url") or "").strip()
                converted_rows.append(
                    {
                        "parcel_id": parcel_id,
                        "contractor_id": agent_row.get("agent_id"),
                        "company_number": None,
                        "company_name": agent_row.get("company_name"),
                        "registered_office_address": agent_row.get("office_address"),
                        "postal_code": agent_row.get("postcode"),
                        "locality": agent_row.get("locality"),
                        "region": agent_row.get("region"),
                        "country": "UK",
                        "company_source_url": agent_row.get("company_source_url") or evidence_url,
                        "project_count": None,
                        "reliability_score": agent_row.get("trust_score_10"),
                        "data_confidence_score": agent_row.get("overall_data_truth_score_4"),
                        "legal_contact_score": agent_row.get("overall_data_truth_score_4"),
                        "quality_band": None,
                        "activity_density_label": None,
                        "structure_type": structure_type,
                        "structure_types": None,
                        "coverage_structure_types": None,
                        "specialization": None,
                        "match_method": agent_row.get("coverage_method"),
                        "match_score": agent_row.get("coverage_truth_score_4"),
                        "region_activity_label": None,
                        "reason": f"parcel_group_id={agent_row.get('parcel_group_id')}",
                        "matched_at": None,
                        "phone": agent_row.get("phone"),
                        "email": agent_row.get("email"),
                        "website_url": agent_row.get("website_url"),
                        "contact_allowed": contact_allowed,
                        "do_not_contact": not contact_allowed,
                        "contact_status": agent_row.get("contact_status") or ("READY" if contact_allowed else "DO_NOT_CONTACT"),
                    }
                )
            converted_rows.sort(
                key=lambda row: (
                    0 if row.get("contact_allowed") else 1,
                    -_safe_float(row.get("reliability_score")),
                    -_safe_float(row.get("data_confidence_score")),
                    str(row.get("company_name") or ""),
                )
            )
            return (
                converted_rows[:limit],
                int(lookup_payload.get("total_agents") or len(estate_rows)),
                ready_rows,
                blocked_rows,
                Path(str(lookup_payload.get("source_files", {}).get("join", ""))),
                Path(str(lookup_payload.get("source_files", {}).get("agents", ""))),
                {
                    "integration_mode": "estate_agent_read_only",
                    "parcel_group_ids": lookup_payload.get("parcel_group_ids", []),
                    "source_files": lookup_payload.get("source_files", {}),
                    "final_audit": lookup_payload.get("audit", {}),
                },
            )

    export_root = _resolve_export_root()
    matches_file = (export_root / "contractor_parcel_matches_for_app.csv").resolve()
    contractors_file = (export_root / "contractors_for_app.csv").resolve()
    if estate_dataset.available and estate_join_count == 0 and not strict_mode:
        if not matches_file.exists() or not contractors_file.exists():
            return (
                [],
                0,
                0,
                0,
                Path(str(estate_lookup_payload.get("source_files", {}).get("join", ""))),
                Path(str(estate_lookup_payload.get("source_files", {}).get("agents", ""))),
                {
                    "integration_mode": "estate_agent_read_only",
                    "parcel_group_ids": [],
                    "source_files": estate_lookup_payload.get("source_files", {}),
                    "final_audit": estate_lookup_payload.get("audit", {}),
                },
            )
    if not matches_file.exists():
        raise HTTPException(status_code=404, detail=f"CSV export not found: {matches_file}")
    if not contractors_file.exists():
        raise HTTPException(status_code=404, detail=f"CSV export not found: {contractors_file}")

    contractor_map: dict[str, dict[str, Any]] = {}
    try:
        with contractors_file.open("r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                key = str(row.get("contractor_id") or "").strip()
                if key:
                    contractor_map[key] = dict(row)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read CSV export: {exc}") from exc

    merged_rows: list[dict[str, Any]] = []
    total_rows = 0
    ready_rows = 0
    blocked_rows = 0
    structure_aliases = _structure_alias_set(structure_type)
    try:
        with matches_file.open("r", encoding="utf-8-sig", newline="") as fh:
            for match_row in csv.DictReader(fh):
                match_parcel_id = str(match_row.get("parcel_id") or "").strip()
                if match_parcel_id != parcel_id:
                    continue
                contractor_id = str(match_row.get("contractor_id") or "").strip()
                contractor = contractor_map.get(contractor_id, {})
                if not _row_matches_structure_type(
                    contractor_row=contractor,
                    match_row=match_row,
                    structure_aliases=structure_aliases,
                ):
                    continue
                total_rows += 1
                legal_score = _safe_float(contractor.get("legal_contact_score"))
                contractor_do_not_contact = _safe_bool(contractor.get("do_not_contact"))
                match_contact_readiness = str(match_row.get("contact_readiness") or "").strip().upper()
                contact_status = str(
                    contractor.get("contact_status")
                    or match_contact_readiness
                    or ("DO_NOT_CONTACT" if contractor_do_not_contact else "READY")
                ).strip().upper()
                do_not_contact = contractor_do_not_contact or legal_score < 50.0 or contact_status == "DO_NOT_CONTACT"
                contact_allowed = not do_not_contact
                if contact_allowed:
                    ready_rows += 1
                else:
                    blocked_rows += 1
                if not include_blocked and not contact_allowed:
                    continue

                merged_rows.append(
                    {
                        "parcel_id": match_parcel_id,
                        "contractor_id": contractor_id or None,
                        "company_number": contractor.get("company_number"),
                        "company_name": contractor.get("company_name"),
                        "registered_office_address": contractor.get("registered_office_address"),
                        "postal_code": contractor.get("postal_code"),
                        "locality": contractor.get("locality"),
                        "region": contractor.get("region"),
                        "country": contractor.get("country"),
                        "company_source_url": contractor.get("company_source_url"),
                        "project_count": contractor.get("project_count"),
                        "reliability_score": contractor.get("reliability_score"),
                        "data_confidence_score": contractor.get("data_confidence_score"),
                        "legal_contact_score": contractor.get("legal_contact_score"),
                        "quality_band": contractor.get("quality_band"),
                        "activity_density_label": contractor.get("activity_density_label"),
                        "structure_type": contractor.get("structure_type") or match_row.get("structure_type"),
                        "structure_types": contractor.get("structure_types") or match_row.get("structure_types"),
                        "coverage_structure_types": contractor.get("coverage_structure_types")
                        or match_row.get("coverage_structure_types"),
                        "specialization": contractor.get("specialization") or contractor.get("specializations"),
                        "match_method": match_row.get("match_method"),
                        "match_score": match_row.get("match_score"),
                        "region_activity_label": match_row.get("region_activity_label"),
                        "reason": match_row.get("reason"),
                        "matched_at": match_row.get("matched_at"),
                        "contact_allowed": contact_allowed,
                        "do_not_contact": do_not_contact,
                        "contact_status": "DO_NOT_CONTACT" if do_not_contact else "READY",
                    }
                )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read CSV export: {exc}") from exc

    merged_rows.sort(
        key=lambda row: (
            0 if row.get("contact_allowed") else 1,
            -_safe_float(row.get("match_score")),
            -_safe_float(row.get("reliability_score")),
            -_safe_float(row.get("data_confidence_score")),
            -_safe_float(row.get("legal_contact_score")),
            str(row.get("company_name") or ""),
        )
    )
    return (
        merged_rows[:limit],
        total_rows,
        ready_rows,
        blocked_rows,
        matches_file,
        contractors_file,
        {
            "integration_mode": "contractor_export_csv",
            "parcel_group_ids": [],
            "source_files": {
                "matches": str(matches_file),
                "contractors": str(contractors_file),
            },
            "final_audit": {
                "DB_WRITE": False,
                "PRODUCTION_DEPLOY": False,
                "FAKE_DATA": False,
            },
        },
    )


@router.get("/status", response_model=ContractorStatusResponse)
def get_contractor_status() -> ContractorStatusResponse:
    settings = get_settings()
    storage_registry = get_runtime_storage_registry()
    export_root = _resolve_export_root()
    manifest_root = _resolve_manifest_root()
    preflight_path = Path(storage_registry.contractor_preflight_path).expanduser()
    preflight_audit = _sanitize_preflight_audit(_safe_read_json(preflight_path))
    load_manifest = _safe_read_json(manifest_root / "postgres_load_manifest.json")
    parcel_match_manifest = _safe_read_json(manifest_root / "parcel_match_manifest.json")
    export_manifest = _safe_read_json(export_root / "export_manifest.json")
    status, warnings = _compute_status(
        preflight=preflight_audit,
        load_manifest=load_manifest,
        match_manifest=parcel_match_manifest,
        export_manifest=export_manifest,
    )
    manifests = _build_manifests(
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
        manifests=manifests,
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


@router.get("/exports/parcel-matches/preview", response_model=ContractorExportRowsResponse)
def get_contractor_parcel_match_preview(
    limit: int = Query(default=20, ge=1, le=100),
) -> ContractorExportRowsResponse:
    source_file = (_resolve_export_root() / "contractor_parcel_matches_for_app.csv").resolve()
    total_rows, rows = _read_csv_window(source_file, offset=0, limit=limit)
    return ContractorExportRowsResponse(
        source_file=str(source_file),
        total_rows=total_rows,
        offset=0,
        limit=limit,
        rows=rows,
    )


@router.get("/parcel/{parcel_id}/contacts", response_model=ContractorParcelContactsResponse)
def get_parcel_contractor_contacts(
    parcel_id: int,
    limit: int = Query(default=10, ge=1, le=100),
    include_blocked: bool = Query(default=False),
    structure_type: str | None = Query(default=None, max_length=64),
) -> ContractorParcelContactsResponse:
    if parcel_id <= 0:
        raise HTTPException(status_code=422, detail="parcel_id must be a positive integer")
    rows, total_rows, ready_rows, blocked_rows, matches_file, contractors_file, integration_meta = _build_parcel_contact_rows(
        parcel_id=str(parcel_id),
        limit=limit,
        include_blocked=include_blocked,
        structure_type=structure_type,
    )
    return ContractorParcelContactsResponse(
        parcel_id=str(parcel_id),
        source_matches_file=str(matches_file),
        source_contractors_file=str(contractors_file),
        total_rows=total_rows,
        ready_rows=ready_rows,
        blocked_rows=blocked_rows,
        limit=limit,
        include_blocked=include_blocked,
        structure_type=structure_type,
        rows=rows,
        integration_mode=str(integration_meta.get("integration_mode") or "unknown"),
        parcel_group_ids=list(integration_meta.get("parcel_group_ids") or []),
        source_files=dict(integration_meta.get("source_files") or {}),
        final_audit=dict(integration_meta.get("final_audit") or {}),
    )
