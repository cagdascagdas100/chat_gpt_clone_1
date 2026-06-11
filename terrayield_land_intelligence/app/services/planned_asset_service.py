from __future__ import annotations

import json

import datetime as dt
import re
import uuid
from collections import Counter
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import case, delete, desc, func, or_, select
from sqlalchemy.orm import Session

from app.db.geo import geometry_to_geojson, wkt_to_element
from app.db.models import (
    ParcelInspire,
    ParcelPlannedAssetMatch,
    PlannedAsset,
    PlannedAssetDataQualityIssue,
    PlannedAssetIngestionLog,
    PlannedAssetScoreHistory,
    PlannedAssetSource,
    SourceRegistry,
)
from app.schemas.planned_asset import (
    ParcelFutureGrowthScoreResponse,
    ParcelPlannedFeatureSummary,
    PlannedAssetItem,
    PlannedAssetSourceItem,
    PlannedAssetsIngestRequest,
    PlannedAssetsIngestResponse,
    PlannedAssetsRecalculateRequest,
    PlannedAssetsRecalculateResponse,
)
from app.services.planned_asset_scoring import (
    calculate_delay_risk_score,
    calculate_delivery_probability_score,
    delivery_probability_label,
    estimate_timeline,
    freshness_score_0_100,
    normalize_status,
    source_confidence_score,
    value_impact_score,
)
from app.services.planned_source_registry import PLANNED_ADAPTERS, list_enabled_planned_sources, seed_default_source_registry


TRANSPORT_TYPES = {"new_station", "rail_upgrade", "metro_tram_project", "road_scheme", "highway_improvement", "bridge_tunnel"}
MAJOR_DEVELOPMENT_TYPES = {"residential_development", "commercial_development", "mixed_use_development", "major_employment_zone"}
REGEN_TYPES = {"regeneration_area", "brownfield_site", "local_plan_allocation"}


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def _parse_datetime(value: Any) -> dt.datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt.UTC)
    try:
        normalized = str(value).strip().replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.UTC)
    except Exception:
        return None


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _canonical_key(payload: dict[str, Any]) -> str:
    planning_ref = _clean_text(payload.get("planning_reference"))
    if planning_ref:
        return f"planning_ref::{planning_ref}"
    title = _clean_text(payload.get("title"))
    authority = _clean_text(payload.get("local_authority"))
    postcode = _clean_text(payload.get("postcode"))
    return f"title::{title}::la::{authority}::pc::{postcode}"


def _asset_geom_27700_expr():
    raw_geom = PlannedAsset.geometry
    normalized_geom = case(
        (raw_geom.is_(None), None),
        (func.ST_SRID(raw_geom) == 27700, raw_geom),
        (func.ST_SRID(raw_geom) == 4326, func.ST_Transform(raw_geom, 27700)),
        (func.ST_SRID(raw_geom) == 0, func.ST_SetSRID(raw_geom, 27700)),
        else_=func.ST_Transform(raw_geom, 27700),
    )
    centroid_geom = case(
        (PlannedAsset.centroid_lat.is_(None), None),
        (PlannedAsset.centroid_lon.is_(None), None),
        else_=func.ST_Transform(func.ST_SetSRID(func.ST_MakePoint(PlannedAsset.centroid_lon, PlannedAsset.centroid_lat), 4326), 27700),
    )
    return func.COALESCE(normalized_geom, centroid_geom)


def _asset_geom_4326_geojson_expr():
    geom_27700 = _asset_geom_27700_expr()
    return func.ST_AsGeoJSON(func.ST_Transform(geom_27700, 4326))


def _log_ingestion(
    session: Session,
    *,
    run_id: str,
    source_id: str | None,
    source_name: str | None,
    pipeline_step: str,
    status_value: str = "ok",
    records_in: int = 0,
    records_out: int = 0,
    error_message: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> None:
    session.add(
        PlannedAssetIngestionLog(
            run_id=run_id,
            source_id=source_id,
            source_name=source_name,
            pipeline_step=pipeline_step,
            status=status_value,
            records_in=records_in,
            records_out=records_out,
            error_message=error_message,
            metadata_json=metadata_json or {},
            started_at=_now(),
            ended_at=_now(),
        )
    )


def _create_quality_issue(
    session: Session,
    *,
    source_id: str | None,
    planned_asset_id: int | None,
    issue_type: str,
    message: str,
    severity: str = "medium",
    payload: dict[str, Any] | None = None,
) -> None:
    session.add(
        PlannedAssetDataQualityIssue(
            source_id=source_id,
            planned_asset_id=planned_asset_id,
            issue_type=issue_type,
            severity=severity,
            message=message,
            issue_payload_json=payload or {},
            is_resolved=False,
            detected_at=_now(),
        )
    )


def _geometry_confidence(record: dict[str, Any]) -> float:
    if record.get("geometry_wkt"):
        return 90.0
    if record.get("centroid_lat") is not None and record.get("centroid_lon") is not None:
        return 35.0
    return 8.0


def _impact_radius_for_asset(asset_type: str | None) -> int:
    if asset_type in {"new_station", "rail_upgrade", "metro_tram_project", "road_scheme", "bridge_tunnel"}:
        return 5000
    if asset_type in {"regeneration_area", "major_employment_zone", "commercial_development", "mixed_use_development"}:
        return 3000
    return 2000


def _metadata_float(metadata_json: dict[str, Any] | None, key: str) -> float:
    if not isinstance(metadata_json, dict):
        return 0.0
    value = metadata_json.get(key)
    try:
        return float(value)
    except Exception:
        return 0.0


def _quality_validate(record: dict[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if not str(record.get("source_url") or "").strip():
        issues.append("missing_source_url")
    if not str(record.get("evidence_text") or "").strip():
        issues.append("missing_evidence_text")
    return (not issues), issues


def _upsert_planned_asset(
    session: Session,
    *,
    source: SourceRegistry,
    normalized: dict[str, Any],
) -> tuple[PlannedAsset, bool]:
    canonical_key = _canonical_key(normalized)
    asset = session.execute(
        select(PlannedAsset).where(PlannedAsset.canonical_key == canonical_key)
    ).scalar_one_or_none()
    is_new = asset is None
    if asset is None:
        asset = PlannedAsset(canonical_key=canonical_key)
        session.add(asset)

    timeline = estimate_timeline(
        planned_start_year=normalized.get("planned_start_year"),
        planned_completion_year=normalized.get("planned_completion_year"),
        estimated_window_start=normalized.get("estimated_delivery_window_start"),
        estimated_window_end=normalized.get("estimated_delivery_window_end"),
        evidence_text=normalized.get("evidence_text"),
        status=normalized.get("status"),
    )

    normalized_status = normalize_status(normalized.get("status"))
    funded = "fund" in str(normalized.get("funding_status") or "").lower()
    delivery_score = calculate_delivery_probability_score(
        status=normalized_status,
        funding_status=normalized.get("funding_status"),
        developer_name=normalized.get("developer_name"),
        promoter_name=normalized.get("promoter_name"),
    )
    source_conf = max(
        source_confidence_score(source.source_type),
        source_confidence_score(normalized.get("source_type")),
    )
    source_updated_at = _parse_datetime(normalized.get("last_source_update_at"))
    freshness_score = freshness_score_0_100(last_source_update_at=source_updated_at)
    geometry_conf = _geometry_confidence(normalized)
    stale_flag = freshness_score < 30.0
    delay_score = calculate_delay_risk_score(
        status=normalized_status,
        delivery_probability_score_value=delivery_score,
        timeline_confidence_score=float(timeline["timeline_confidence_score"]),
        funded=funded,
        conflict_flag=bool(asset.conflict_flag),
        stale_flag=stale_flag,
    )
    base_impact_score = value_impact_score(
        asset_type=normalized.get("asset_type"),
        distance_m=0.0,
        delivery_probability_score_value=delivery_score,
        source_confidence_score_value=source_conf,
        freshness_score_value=freshness_score,
    )

    previous_status = str(asset.status or "").strip()
    if previous_status and previous_status != normalized_status and previous_status != "unknown":
        asset.conflict_flag = True

    asset.source_id = source.source_id
    asset.source_name = str(normalized.get("source_name") or source.source_name)
    asset.source_type = str(normalized.get("source_type") or source.source_type)
    asset.source_url = str(normalized.get("source_url") or source.base_url)
    asset.asset_type = str(normalized.get("asset_type") or "local_plan_allocation")
    asset.asset_subtype = normalized.get("asset_subtype")
    asset.title = str(normalized.get("title") or normalized.get("source_record_id") or "Planned Asset")
    asset.description = normalized.get("description")
    asset.planning_reference = normalized.get("planning_reference")
    asset.local_authority = normalized.get("local_authority")
    asset.region = normalized.get("region")
    asset.country = str(normalized.get("country") or "England")
    asset.status = normalized_status
    asset.planning_stage = normalized.get("planning_stage")
    asset.delivery_stage = normalized.get("delivery_stage")
    asset.funding_status = normalized.get("funding_status")
    asset.developer_name = normalized.get("developer_name")
    asset.promoter_name = normalized.get("promoter_name")
    asset.geometry = wkt_to_element(normalized.get("geometry_wkt"), srid=27700)
    asset.centroid_lat = normalized.get("centroid_lat")
    asset.centroid_lon = normalized.get("centroid_lon")
    asset.address_text = normalized.get("address_text")
    asset.postcode = normalized.get("postcode")
    asset.planned_start_year = timeline.get("planned_start_year")
    asset.planned_completion_year = timeline.get("planned_completion_year")
    asset.estimated_delivery_window_start = timeline.get("estimated_delivery_window_start")
    asset.estimated_delivery_window_end = timeline.get("estimated_delivery_window_end")
    asset.timeline_confidence_score = float(timeline["timeline_confidence_score"])
    asset.delivery_probability_score = delivery_score
    asset.delivery_probability_label = delivery_probability_label(delivery_score)
    asset.delay_risk_score = delay_score
    asset.impact_radius_m = _impact_radius_for_asset(asset.asset_type)
    asset.value_impact_score = base_impact_score
    asset.source_confidence_score = source_conf
    asset.geometry_confidence_score = geometry_conf
    asset.freshness_score = freshness_score
    asset.evidence_text = str(normalized.get("evidence_text") or "")
    asset.evidence_for_timeline = str(normalized.get("evidence_for_timeline") or timeline.get("evidence_for_timeline") or "")
    asset.evidence_for_probability = str(normalized.get("evidence_for_probability") or "")
    asset.last_checked_at = _now()
    asset.last_source_update_at = source_updated_at
    asset.stale_flag = stale_flag
    asset.metadata_json = dict(normalized.get("metadata") or {})

    session.flush()

    support_row = session.execute(
        select(PlannedAssetSource)
        .where(PlannedAssetSource.planned_asset_id == asset.id)
        .where(PlannedAssetSource.source_name == asset.source_name)
        .where(PlannedAssetSource.source_url == asset.source_url)
    ).scalar_one_or_none()
    if support_row is None:
        support_row = PlannedAssetSource(
            planned_asset_id=asset.id,
            source_id=asset.source_id,
            source_name=asset.source_name,
            source_type=asset.source_type,
            source_url=asset.source_url,
            evidence_text=asset.evidence_text,
            is_primary=True,
        )
        session.add(support_row)
    support_row.evidence_for_timeline = asset.evidence_for_timeline
    support_row.evidence_for_probability = asset.evidence_for_probability
    support_row.source_confidence_score = asset.source_confidence_score
    support_row.status_snapshot = asset.status
    support_row.planning_stage_snapshot = asset.planning_stage
    support_row.delivery_stage_snapshot = asset.delivery_stage
    support_row.last_source_update_at = asset.last_source_update_at
    support_row.last_checked_at = asset.last_checked_at
    support_row.metadata_json = dict(normalized.get("metadata") or {})

    session.add(
        PlannedAssetScoreHistory(
            planned_asset_id=asset.id,
            computed_at=_now(),
            delivery_probability_score=asset.delivery_probability_score,
            delivery_probability_label=asset.delivery_probability_label,
            delay_risk_score=asset.delay_risk_score,
            value_impact_score=asset.value_impact_score,
            source_confidence_score=asset.source_confidence_score,
            freshness_score=asset.freshness_score,
            timeline_confidence_score=asset.timeline_confidence_score,
            notes_json={"status": asset.status, "source_name": asset.source_name},
        )
    )

    return asset, is_new


def match_to_parcels(session: Session, *, asset_ids: list[int] | None = None) -> tuple[int, set[int]]:
    target_asset_ids = asset_ids or [
        item[0]
        for item in session.execute(select(PlannedAsset.id)).all()
    ]
    updated_rows = 0
    parcel_ids_touched: set[int] = set()
    asset_geom_expr = _asset_geom_27700_expr()

    for asset_id in target_asset_ids:
        asset = session.get(PlannedAsset, asset_id)
        if asset is None:
            continue
        if asset.geometry is None and (asset.centroid_lat is None or asset.centroid_lon is None):
            continue

        rows = session.execute(
            select(
                ParcelInspire.parcel_id,
                func.ST_Distance(ParcelInspire.geometry, asset_geom_expr).label("distance_m"),
                func.ST_Intersects(ParcelInspire.geometry, asset_geom_expr).label("intersects"),
                func.ST_Contains(ParcelInspire.geometry, asset_geom_expr).label("contains"),
            )
            .select_from(ParcelInspire, PlannedAsset)
            .where(PlannedAsset.id == asset_id)
            .where(func.ST_DWithin(ParcelInspire.geometry, asset_geom_expr, 5000))
        ).all()

        for parcel_id, distance_m, intersects, contains in rows:
            distance_val = float(distance_m or 0.0)
            match = session.execute(
                select(ParcelPlannedAssetMatch)
                .where(ParcelPlannedAssetMatch.parcel_id == int(parcel_id))
                .where(ParcelPlannedAssetMatch.planned_asset_id == int(asset_id))
            ).scalar_one_or_none()
            if match is None:
                match = ParcelPlannedAssetMatch(parcel_id=int(parcel_id), planned_asset_id=int(asset_id))
                session.add(match)
            distance_component = max(0.0, 1.0 - min(distance_val, 5000.0) / 5000.0)
            impact_score = value_impact_score(
                asset_type=asset.asset_type,
                distance_m=distance_val,
                delivery_probability_score_value=asset.delivery_probability_score,
                source_confidence_score_value=asset.source_confidence_score,
                freshness_score_value=asset.freshness_score,
            )
            match.distance_m = round(distance_val, 2)
            match.intersects = bool(intersects)
            match.contains = bool(contains)
            match.within_500m = distance_val <= 500
            match.within_1km = distance_val <= 1000
            match.within_2km = distance_val <= 2000
            match.within_5km = distance_val <= 5000
            match.impact_score = impact_score
            match.delivery_probability_score = asset.delivery_probability_score
            match.value_impact_score = asset.value_impact_score
            match.match_confidence_score = round(
                (asset.source_confidence_score * 0.50)
                + (asset.geometry_confidence_score * 0.30)
                + (distance_component * 20.0),
                2,
            )
            parcel_ids_touched.add(int(parcel_id))
            updated_rows += 1

    session.flush()
    return updated_rows, parcel_ids_touched


def ingest_planned_assets(session: Session, payload: PlannedAssetsIngestRequest) -> PlannedAssetsIngestResponse:
    run_id = str(uuid.uuid4())
    seed_default_source_registry(session)
    sources = list_enabled_planned_sources(session)
    if payload.source_ids:
        target = {item.strip() for item in payload.source_ids}
        sources = [src for src in sources if src.source_id in target]

    total_raw = 0
    total_normalized = 0
    total_assets = 0
    total_supporting = 0
    total_skipped = 0
    warnings: list[str] = []
    touched_asset_ids: set[int] = set()
    quality_issue_count = 0

    for src in sources:
        adapter_cls = PLANNED_ADAPTERS.get(src.adapter_type)
        if adapter_cls is None:
            warning = f"Adapter not found for source_id={src.source_id}, adapter_type={src.adapter_type}"
            warnings.append(warning)
            _log_ingestion(
                session,
                run_id=run_id,
                source_id=src.source_id,
                source_name=src.source_name,
                pipeline_step="fetch_sources",
                status_value="error",
                error_message=warning,
            )
            continue

        adapter = adapter_cls()
        try:
            extract = adapter.download_raw(sample_data=payload.sample_data)
            raw_records = adapter.parse_records(extract)
            normalized_rows = adapter.normalize_records(raw_records)
        except Exception as exc:
            _log_ingestion(
                session,
                run_id=run_id,
                source_id=src.source_id,
                source_name=src.source_name,
                pipeline_step="parse_source",
                status_value="error",
                error_message=str(exc),
            )
            warnings.append(f"{src.source_id}: {exc}")
            continue

        if payload.pilot_local_authorities:
            pilot_las = {_clean_text(item) for item in payload.pilot_local_authorities}
            normalized_rows = [
                row for row in normalized_rows
                if _clean_text(row.get("local_authority")) in pilot_las
            ]

        if payload.limit_per_source and payload.limit_per_source > 0:
            normalized_rows = normalized_rows[: payload.limit_per_source]

        total_raw += len(raw_records)
        total_normalized += len(normalized_rows)
        _log_ingestion(
            session,
            run_id=run_id,
            source_id=src.source_id,
            source_name=src.source_name,
            pipeline_step="normalize_asset",
            status_value="ok",
            records_in=len(raw_records),
            records_out=len(normalized_rows),
        )

        for normalized in normalized_rows:
            ok, issues = _quality_validate(normalized)
            if not ok:
                total_skipped += 1
                for issue in issues:
                    quality_issue_count += 1
                    _create_quality_issue(
                        session,
                        source_id=src.source_id,
                        planned_asset_id=None,
                        issue_type=issue,
                        message=f"Record skipped due to {issue}",
                        severity="high" if issue in {"missing_source_url", "missing_evidence_text"} else "medium",
                        payload={"record": normalized},
                    )
                continue

            asset, is_new = _upsert_planned_asset(session, source=src, normalized=normalized)
            touched_asset_ids.add(asset.id)
            if is_new:
                total_assets += 1
            total_supporting += 1

            if asset.geometry is None:
                quality_issue_count += 1
                _create_quality_issue(
                    session,
                    source_id=src.source_id,
                    planned_asset_id=asset.id,
                    issue_type="missing_geometry",
                    message="Planned asset stored without geometry; centroid fallback may reduce accuracy.",
                    severity="medium",
                )
            if asset.timeline_confidence_score < 40:
                quality_issue_count += 1
                _create_quality_issue(
                    session,
                    source_id=src.source_id,
                    planned_asset_id=asset.id,
                    issue_type="low_timeline_confidence",
                    message="Timeline confidence is low due to insufficient explicit dates.",
                    severity="low",
                )
            if asset.source_confidence_score < 50:
                quality_issue_count += 1
                _create_quality_issue(
                    session,
                    source_id=src.source_id,
                    planned_asset_id=asset.id,
                    issue_type="low_source_confidence",
                    message="Source confidence is low for this source type.",
                    severity="low",
                )
            if asset.conflict_flag:
                quality_issue_count += 1
                _create_quality_issue(
                    session,
                    source_id=src.source_id,
                    planned_asset_id=asset.id,
                    issue_type="status_conflict",
                    message="Conflicting status detected for the same canonical planned asset.",
                    severity="medium",
                )

    match_row_count = 0
    if not payload.dry_run and touched_asset_ids:
        match_row_count, _ = match_to_parcels(session, asset_ids=sorted(touched_asset_ids))
        _log_ingestion(
            session,
            run_id=run_id,
            source_id=None,
            source_name="planned_assets",
            pipeline_step="match_to_parcels",
            status_value="ok",
            records_in=len(touched_asset_ids),
            records_out=match_row_count,
        )

    _log_ingestion(
        session,
        run_id=run_id,
        source_id=None,
        source_name="planned_assets",
        pipeline_step="log_quality_metrics",
        status_value="ok",
        records_in=total_normalized,
        records_out=quality_issue_count,
        metadata_json={"warnings": warnings},
    )

    session.flush()

    return PlannedAssetsIngestResponse(
        run_id=run_id,
        source_count=len(sources),
        raw_record_count=total_raw,
        normalized_record_count=total_normalized,
        stored_asset_count=total_assets,
        supporting_source_count=total_supporting,
        match_row_count=match_row_count,
        quality_issue_count=quality_issue_count,
        skipped_record_count=total_skipped,
        warnings=warnings,
        notes={"dry_run": payload.dry_run, "pilot_local_authorities": payload.pilot_local_authorities or []},
    )


def _serialize_planned_asset_row(row: Any) -> PlannedAssetItem:
    if hasattr(row, "_mapping"):
        mapping = row._mapping
        asset = mapping.get("PlannedAsset", row[0])
        geometry_json = mapping.get("geometry_geojson")
        if geometry_json is None and len(row) > 1:
            geometry_json = row[1]
        distance_m = mapping.get("distance_m")
        if distance_m is None and len(row) > 2:
            distance_m = row[2]
        intersects = mapping.get("intersects")
        if intersects is None and len(row) > 3:
            intersects = row[3]
        contains = mapping.get("contains")
        if contains is None and len(row) > 4:
            contains = row[4]
    elif isinstance(row, tuple):
        asset = row[0]
        geometry_json = row[1] if len(row) > 1 else None
        distance_m = row[2] if len(row) > 2 else None
        intersects = row[3] if len(row) > 3 else None
        contains = row[4] if len(row) > 4 else None
    else:
        asset = row
        geometry_json = None
        distance_m = None
        intersects = None
        contains = None

    return PlannedAssetItem(
        id=asset.id,
        source_id=asset.source_id,
        source_name=asset.source_name,
        source_type=asset.source_type,
        source_url=asset.source_url,
        asset_type=asset.asset_type,
        asset_subtype=asset.asset_subtype,
        title=asset.title,
        description=asset.description,
        planning_reference=asset.planning_reference,
        local_authority=asset.local_authority,
        region=asset.region,
        country=asset.country,
        status=asset.status,
        planning_stage=asset.planning_stage,
        delivery_stage=asset.delivery_stage,
        funding_status=asset.funding_status,
        developer_name=asset.developer_name,
        promoter_name=asset.promoter_name,
        geometry=geometry_to_geojson(geometry_json),
        centroid_lat=asset.centroid_lat,
        centroid_lon=asset.centroid_lon,
        address_text=asset.address_text,
        postcode=asset.postcode,
        planned_start_year=asset.planned_start_year,
        planned_completion_year=asset.planned_completion_year,
        estimated_delivery_window_start=asset.estimated_delivery_window_start,
        estimated_delivery_window_end=asset.estimated_delivery_window_end,
        timeline_confidence_score=asset.timeline_confidence_score,
        delivery_probability_score=asset.delivery_probability_score,
        delivery_probability_label=asset.delivery_probability_label,
        delay_risk_score=asset.delay_risk_score,
        impact_radius_m=asset.impact_radius_m,
        value_impact_score=asset.value_impact_score,
        source_confidence_score=asset.source_confidence_score,
        geometry_confidence_score=asset.geometry_confidence_score,
        freshness_score=asset.freshness_score,
        evidence_text=asset.evidence_text,
        evidence_for_timeline=asset.evidence_for_timeline,
        evidence_for_probability=asset.evidence_for_probability,
        last_checked_at=asset.last_checked_at,
        last_source_update_at=asset.last_source_update_at,
        conflict_flag=asset.conflict_flag,
        stale_flag=asset.stale_flag,
        updated_at=asset.updated_at,
        distance_m=float(distance_m) if distance_m is not None else None,
        intersects=bool(intersects) if intersects is not None else None,
        contains=bool(contains) if contains is not None else None,
    )


def get_planned_asset(session: Session, planned_asset_id: int) -> PlannedAssetItem:
    geom_expr = _asset_geom_4326_geojson_expr().label("geometry_geojson")
    row = session.execute(
        select(PlannedAsset, geom_expr)
        .where(PlannedAsset.id == planned_asset_id)
    ).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planned asset not found")
    return _serialize_planned_asset_row(row)


def search_planned_assets(
    session: Session,
    *,
    query_text: str | None = None,
    asset_type: str | None = None,
    status_filter: str | None = None,
    local_authority: str | None = None,
    min_delivery_probability: float | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[PlannedAssetItem]:
    geom_expr = _asset_geom_4326_geojson_expr().label("geometry_geojson")
    stmt = select(PlannedAsset, geom_expr)
    if query_text:
        like = f"%{query_text.strip()}%"
        stmt = stmt.where(
            or_(
                PlannedAsset.title.ilike(like),
                PlannedAsset.description.ilike(like),
                PlannedAsset.planning_reference.ilike(like),
            )
        )
    if asset_type:
        stmt = stmt.where(PlannedAsset.asset_type == asset_type)
    if status_filter:
        stmt = stmt.where(PlannedAsset.status == normalize_status(status_filter))
    if local_authority:
        stmt = stmt.where(PlannedAsset.local_authority == local_authority)
    if min_delivery_probability is not None:
        stmt = stmt.where(PlannedAsset.delivery_probability_score >= float(min_delivery_probability))
    rows = session.execute(
        stmt.order_by(desc(PlannedAsset.value_impact_score), desc(PlannedAsset.updated_at)).limit(limit).offset(offset)
    ).all()
    return [_serialize_planned_asset_row(row) for row in rows]


def nearby_planned_assets(
    session: Session,
    *,
    lat: float,
    lon: float,
    radius_m: int = 2000,
    limit: int = 200,
) -> list[PlannedAssetItem]:
    geom_expr = _asset_geom_27700_expr()
    point_27700 = func.ST_Transform(func.ST_SetSRID(func.ST_MakePoint(float(lon), float(lat)), 4326), 27700)
    geojson_expr = _asset_geom_4326_geojson_expr().label("geometry_geojson")
    distance_expr = func.ST_Distance(geom_expr, point_27700).label("distance_m")
    rows = session.execute(
        select(PlannedAsset, geojson_expr, distance_expr)
        .where(geom_expr.is_not(None))
        .where(func.ST_DWithin(geom_expr, point_27700, radius_m))
        .order_by(distance_expr.asc(), desc(PlannedAsset.delivery_probability_score))
        .limit(limit)
    ).all()
    return [_serialize_planned_asset_row(row) for row in rows]


def list_planned_asset_sources(session: Session) -> list[PlannedAssetSourceItem]:
    rows = session.execute(
        select(SourceRegistry).where(SourceRegistry.country == "England").order_by(SourceRegistry.trust_level.asc(), SourceRegistry.source_name.asc())
    ).scalars().all()
    return [
        PlannedAssetSourceItem(
            source_id=row.source_id,
            source_name=row.source_name,
            source_type=row.source_type,
            country=row.country,
            region=row.region,
            local_authority=row.local_authority,
            base_url=row.base_url,
            api_available=row.api_available,
            scrape_required=row.scrape_required,
            adapter_type=row.adapter_type,
            update_frequency=row.update_frequency,
            trust_level=row.trust_level,
            expected_format=row.expected_format,
            parser_name=row.parser_name,
            enabled=row.enabled,
            last_checked_at=row.last_checked_at,
            last_success_at=row.last_success_at,
            last_error=row.last_error,
        )
        for row in rows
    ]


def get_parcel_planned_assets(session: Session, parcel_id: int, *, limit: int = 200) -> list[PlannedAssetItem]:
    parcel = session.get(ParcelInspire, parcel_id)
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
    geom_expr = _asset_geom_4326_geojson_expr().label("geometry_geojson")
    rows = session.execute(
        select(
            PlannedAsset,
            geom_expr,
            ParcelPlannedAssetMatch.distance_m,
            ParcelPlannedAssetMatch.intersects,
            ParcelPlannedAssetMatch.contains,
        )
        .join(ParcelPlannedAssetMatch, ParcelPlannedAssetMatch.planned_asset_id == PlannedAsset.id)
        .where(ParcelPlannedAssetMatch.parcel_id == parcel_id)
        .order_by(desc(ParcelPlannedAssetMatch.impact_score), ParcelPlannedAssetMatch.distance_m.asc().nulls_last())
        .limit(limit)
    ).all()
    return [_serialize_planned_asset_row(row) for row in rows]


def _build_parcel_summary(session: Session, parcel_id: int) -> ParcelPlannedFeatureSummary:
    rows = session.execute(
        select(ParcelPlannedAssetMatch, PlannedAsset)
        .join(PlannedAsset, PlannedAsset.id == ParcelPlannedAssetMatch.planned_asset_id)
        .where(ParcelPlannedAssetMatch.parcel_id == parcel_id)
    ).all()
    if not rows:
        return ParcelPlannedFeatureSummary(parcel_id=parcel_id, evidence=["insufficient evidence"], risks=["No nearby planned assets found."])

    counts = Counter()
    distances_station: list[float] = []
    distances_road: list[float] = []
    distances_major_dev: list[float] = []
    high_prob_distances: list[float] = []
    low_prob_high_impact_distances: list[float] = []
    evidence_set: set[str] = set()
    risks: list[str] = []
    weighted_prob_numer = 0.0
    weighted_prob_denom = 0.0
    weighted_growth_numer = 0.0
    weighted_growth_denom = 0.0
    transport_uplift_numer = 0.0
    transport_uplift_denom = 0.0
    max_value_impact = 0.0
    highest_source_conf = 0.0
    planned_housing_units = 0.0
    planned_commercial_area = 0.0
    delay_risk_values: list[float] = []
    source_conf_values: list[float] = []
    delivery_values: list[float] = []
    status_counter = Counter()
    asset_type_counter = Counter()

    for match, asset in rows:
        dist = float(match.distance_m) if match.distance_m is not None else None
        status_counter[asset.status] += 1
        asset_type_counter[asset.asset_type] += 1
        delay_risk_values.append(float(asset.delay_risk_score or 0.0))
        source_conf_values.append(float(asset.source_confidence_score or 0.0))
        delivery_values.append(float(asset.delivery_probability_score or 0.0))
        highest_source_conf = max(highest_source_conf, float(asset.source_confidence_score or 0.0))
        max_value_impact = max(max_value_impact, float(asset.value_impact_score or 0.0))
        planned_housing_units += _metadata_float(asset.metadata_json, "housing_units")
        planned_commercial_area += _metadata_float(asset.metadata_json, "commercial_area_m2")
        if asset.evidence_text:
            evidence_set.add(asset.evidence_text[:240])
        if asset.timeline_confidence_score < 45:
            risks.append("Timeline uncertainty medium-high")
        if str(asset.funding_status or "").strip() == "":
            risks.append("Funding status partially confirmed")

        if dist is not None:
            if asset.asset_type == "new_station":
                distances_station.append(dist)
            if asset.asset_type in {"road_scheme", "highway_improvement", "bridge_tunnel"}:
                distances_road.append(dist)
            if asset.asset_type in MAJOR_DEVELOPMENT_TYPES:
                distances_major_dev.append(dist)
            if asset.delivery_probability_score >= 70:
                high_prob_distances.append(dist)
            if asset.delivery_probability_score < 50 and asset.value_impact_score >= 60:
                low_prob_high_impact_distances.append(dist)

        if match.within_500m:
            counts["within_500m"] += 1
        if match.within_1km:
            counts["within_1km"] += 1
            if asset.status == "approved":
                counts["approved_1km"] += 1
            if asset.status == "under_construction":
                counts["under_construction_1km"] += 1
        if match.within_2km:
            counts["within_2km"] += 1
            if asset.status in {"proposed", "consultation", "submitted", "validated"}:
                counts["proposed_2km"] += 1
        if match.within_5km:
            counts["within_5km"] += 1

        distance_weight = 1.0
        if dist is not None:
            if dist > 5000:
                distance_weight = 0.05
            elif dist > 2000:
                distance_weight = 0.3
            elif dist > 1000:
                distance_weight = 0.55
            elif dist > 500:
                distance_weight = 0.8
            else:
                distance_weight = 1.0

        weighted_prob_numer += distance_weight * float(asset.delivery_probability_score or 0.0)
        weighted_prob_denom += distance_weight
        weighted_growth_numer += distance_weight * float(match.impact_score or 0.0)
        weighted_growth_denom += distance_weight

        if asset.asset_type in TRANSPORT_TYPES:
            transport_uplift_numer += distance_weight * float(match.impact_score or 0.0)
            transport_uplift_denom += distance_weight

    weighted_delivery_prob = (weighted_prob_numer / weighted_prob_denom) if weighted_prob_denom else 0.0
    weighted_growth = (weighted_growth_numer / weighted_growth_denom) if weighted_growth_denom else 0.0
    weighted_transport = (transport_uplift_numer / transport_uplift_denom) if transport_uplift_denom else 0.0

    planning_momentum = min(
        100.0,
        (status_counter["approved"] * 8.0)
        + (status_counter["under_construction"] * 10.0)
        + (status_counter["funded"] * 9.0)
        + (status_counter["submitted"] * 3.0)
        + (status_counter["local_plan_allocated"] * 2.5),
    )
    regen_score = min(
        100.0,
        (asset_type_counter["regeneration_area"] * 12.0)
        + (asset_type_counter["local_plan_allocation"] * 6.0)
        + (asset_type_counter["brownfield_site"] * 4.0)
        + (status_counter["approved"] * 2.0),
    )

    return ParcelPlannedFeatureSummary(
        parcel_id=parcel_id,
        nearest_planned_station_distance_m=min(distances_station) if distances_station else None,
        nearest_planned_road_scheme_distance_m=min(distances_road) if distances_road else None,
        nearest_major_development_distance_m=min(distances_major_dev) if distances_major_dev else None,
        planned_assets_within_500m_count=counts["within_500m"],
        planned_assets_within_1km_count=counts["within_1km"],
        planned_assets_within_2km_count=counts["within_2km"],
        planned_assets_within_5km_count=counts["within_5km"],
        approved_projects_within_1km_count=counts["approved_1km"],
        under_construction_projects_within_1km_count=counts["under_construction_1km"],
        proposed_projects_within_2km_count=counts["proposed_2km"],
        planned_housing_units_within_2km=round(planned_housing_units, 2),
        planned_commercial_area_within_2km=round(planned_commercial_area, 2),
        local_plan_allocation_overlap_flag=any(asset.asset_type == "local_plan_allocation" and bool(match.intersects) for match, asset in rows),
        brownfield_register_overlap_flag=any(asset.asset_type == "brownfield_site" and bool(match.intersects) for match, asset in rows),
        regeneration_area_overlap_flag=any(asset.asset_type == "regeneration_area" and bool(match.intersects) for match, asset in rows),
        weighted_delivery_probability_nearby=round(weighted_delivery_prob, 2),
        weighted_future_growth_score=round(weighted_growth, 2),
        weighted_transport_uplift_score=round(weighted_transport, 2),
        max_value_impact_asset_nearby=round(max_value_impact, 2),
        highest_confidence_source_nearby=round(highest_source_conf, 2),
        nearest_high_probability_project_distance_m=min(high_prob_distances) if high_prob_distances else None,
        nearest_low_probability_but_high_impact_project_distance_m=min(low_prob_high_impact_distances) if low_prob_high_impact_distances else None,
        planning_momentum_score=round(planning_momentum, 2),
        regeneration_potential_score=round(regen_score, 2),
        source_confidence_score=round(sum(source_conf_values) / len(source_conf_values), 2) if source_conf_values else 0.0,
        delivery_probability_score=round(sum(delivery_values) / len(delivery_values), 2) if delivery_values else 0.0,
        delay_risk_score=round(sum(delay_risk_values) / len(delay_risk_values), 2) if delay_risk_values else 0.0,
        evidence=sorted(evidence_set)[:8] or ["insufficient evidence"],
        risks=sorted(set(risks))[:8] or ["No material delay risk signal detected."],
        updated_at=_now(),
    )


def get_parcel_future_growth_score(session: Session, parcel_id: int) -> ParcelFutureGrowthScoreResponse:
    parcel = session.get(ParcelInspire, parcel_id)
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
    summary = _build_parcel_summary(session, parcel_id)
    planned_dev_impact = round(
        min(100.0, (summary.max_value_impact_asset_nearby * 0.55) + (summary.weighted_future_growth_score * 0.45)),
        2,
    )
    return ParcelFutureGrowthScoreResponse(
        parcel_id=parcel_id,
        future_growth_score=summary.weighted_future_growth_score,
        planned_development_impact_score=planned_dev_impact,
        planned_transport_uplift_score=summary.weighted_transport_uplift_score,
        planning_momentum_score=summary.planning_momentum_score,
        regeneration_potential_score=summary.regeneration_potential_score,
        delivery_probability_score=summary.delivery_probability_score,
        source_confidence_score=summary.source_confidence_score,
        delay_risk_score=summary.delay_risk_score,
        summary=summary,
    )


def get_parcel_future_intelligence_summary(session: Session, parcel_id: int) -> ParcelPlannedFeatureSummary:
    parcel = session.get(ParcelInspire, parcel_id)
    if not parcel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
    return _build_parcel_summary(session, parcel_id)


def recalculate_planned_assets(
    session: Session,
    payload: PlannedAssetsRecalculateRequest,
) -> PlannedAssetsRecalculateResponse:
    stmt = select(PlannedAsset).distinct()
    if payload.local_authority:
        stmt = stmt.where(PlannedAsset.local_authority == payload.local_authority)
    if payload.parcel_ids:
        stmt = stmt.join(
            ParcelPlannedAssetMatch,
            ParcelPlannedAssetMatch.planned_asset_id == PlannedAsset.id,
        ).where(ParcelPlannedAssetMatch.parcel_id.in_(payload.parcel_ids))
    assets = session.execute(stmt.limit(max(1, int(payload.limit)))).scalars().all()

    touched_asset_ids: list[int] = []
    for asset in assets:
        timeline = estimate_timeline(
            planned_start_year=asset.planned_start_year,
            planned_completion_year=asset.planned_completion_year,
            estimated_window_start=asset.estimated_delivery_window_start,
            estimated_window_end=asset.estimated_delivery_window_end,
            evidence_text=asset.evidence_text,
            status=asset.status,
        )
        delivery_score = calculate_delivery_probability_score(
            status=asset.status,
            funding_status=asset.funding_status,
            developer_name=asset.developer_name,
            promoter_name=asset.promoter_name,
        )
        fresh_score = freshness_score_0_100(last_source_update_at=asset.last_source_update_at)
        asset.timeline_confidence_score = float(timeline["timeline_confidence_score"])
        asset.delivery_probability_score = delivery_score
        asset.delivery_probability_label = delivery_probability_label(delivery_score)
        asset.freshness_score = fresh_score
        asset.delay_risk_score = calculate_delay_risk_score(
            status=asset.status,
            delivery_probability_score_value=asset.delivery_probability_score,
            timeline_confidence_score=asset.timeline_confidence_score,
            funded="fund" in str(asset.funding_status or "").lower(),
            conflict_flag=asset.conflict_flag,
            stale_flag=asset.stale_flag,
        )
        asset.value_impact_score = value_impact_score(
            asset_type=asset.asset_type,
            distance_m=0.0,
            delivery_probability_score_value=asset.delivery_probability_score,
            source_confidence_score_value=asset.source_confidence_score,
            freshness_score_value=asset.freshness_score,
        )
        session.add(
            PlannedAssetScoreHistory(
                planned_asset_id=asset.id,
                computed_at=_now(),
                delivery_probability_score=asset.delivery_probability_score,
                delivery_probability_label=asset.delivery_probability_label,
                delay_risk_score=asset.delay_risk_score,
                value_impact_score=asset.value_impact_score,
                source_confidence_score=asset.source_confidence_score,
                freshness_score=asset.freshness_score,
                timeline_confidence_score=asset.timeline_confidence_score,
                notes_json={"recalculated": True},
            )
        )
        touched_asset_ids.append(asset.id)

    updated_match_count, parcel_ids_touched = match_to_parcels(session, asset_ids=touched_asset_ids) if touched_asset_ids else (0, set())
    session.flush()
    return PlannedAssetsRecalculateResponse(
        updated_asset_count=len(touched_asset_ids),
        updated_match_count=updated_match_count,
        updated_parcel_count=len(parcel_ids_touched),
        notes={"local_authority": payload.local_authority, "parcel_ids": payload.parcel_ids or []},
    )


def delete_all_planned_matches(session: Session) -> int:
    result = session.execute(delete(ParcelPlannedAssetMatch))
    return int(result.rowcount or 0)

def _parse_bbox_4326(bbox: str) -> tuple[float, float, float, float]:
    parts = [part.strip() for part in str(bbox or "").split(",")]
    if len(parts) != 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="bbox must be west,south,east,north in EPSG:4326")
    west, south, east, north = [float(part) for part in parts]
    if west >= east or south >= north:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="bbox must satisfy west < east and south < north")
    return west, south, east, north


def _json_geojson(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _safe_float(value: Any) -> float | None:
    try:
        return round(float(value), 2) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def get_planned_asset_parcel_layer(session: Session, *, bbox: str, limit: int = 2000, min_delivery_probability: float | None = None, asset_type: str | None = None, status_filter: str | None = None) -> dict[str, Any]:
    west, south, east, north = _parse_bbox_4326(bbox)
    safe_limit = max(1, min(int(limit or 2000), 10000))
    bbox_geom_27700 = func.ST_Transform(func.ST_MakeEnvelope(west, south, east, north, 4326), 27700)
    parcel_geometry_geojson = func.ST_AsGeoJSON(func.ST_Transform(ParcelInspire.geometry, 4326)).label("geometry_geojson")
    planned_asset_count = func.count(PlannedAsset.id).over(partition_by=ParcelPlannedAssetMatch.parcel_id).label("planned_asset_count")
    rank_num = func.row_number().over(partition_by=ParcelPlannedAssetMatch.parcel_id, order_by=(desc(ParcelPlannedAssetMatch.impact_score), desc(PlannedAsset.delivery_probability_score), ParcelPlannedAssetMatch.distance_m.asc().nulls_last(), desc(PlannedAsset.updated_at))).label("rank_num")
    stmt = select(ParcelInspire.parcel_id.label("parcel_id"), ParcelInspire.parcel_ref.label("parcel_ref"), ParcelInspire.local_authority.label("local_authority"), ParcelInspire.postcode.label("postcode"), ParcelInspire.address_text.label("address_text"), ParcelInspire.area_m2.label("area_m2"), parcel_geometry_geojson, planned_asset_count, rank_num, PlannedAsset.id.label("top_planned_asset_id"), PlannedAsset.title.label("top_title"), PlannedAsset.asset_type.label("top_asset_type"), PlannedAsset.status.label("top_status"), PlannedAsset.delivery_probability_score.label("top_delivery_probability_score"), PlannedAsset.delivery_probability_label.label("top_delivery_probability_label"), PlannedAsset.value_impact_score.label("top_value_impact_score"), PlannedAsset.source_confidence_score.label("top_source_confidence_score"), PlannedAsset.source_name.label("source_name"), PlannedAsset.source_url.label("source_url"), PlannedAsset.evidence_text.label("evidence_text"), ParcelPlannedAssetMatch.distance_m.label("nearest_distance_m"), ParcelPlannedAssetMatch.impact_score.label("impact_score"), ParcelPlannedAssetMatch.match_confidence_score.label("match_confidence_score")).join(ParcelPlannedAssetMatch, ParcelPlannedAssetMatch.parcel_id == ParcelInspire.parcel_id).join(PlannedAsset, PlannedAsset.id == ParcelPlannedAssetMatch.planned_asset_id).where(ParcelInspire.geometry.is_not(None)).where(func.ST_Intersects(ParcelInspire.geometry, bbox_geom_27700))
    if min_delivery_probability is not None:
        stmt = stmt.where(PlannedAsset.delivery_probability_score >= float(min_delivery_probability))
    if asset_type:
        stmt = stmt.where(PlannedAsset.asset_type == asset_type)
    if status_filter:
        stmt = stmt.where(PlannedAsset.status == normalize_status(status_filter))
    ranked = stmt.subquery()
    rows = session.execute(select(ranked).where(ranked.c.rank_num == 1).order_by(desc(ranked.c.impact_score), desc(ranked.c.top_delivery_probability_score)).limit(safe_limit)).all()
    features: list[dict[str, Any]] = []
    for row in rows:
        data = row._mapping
        geometry = _json_geojson(data.get("geometry_geojson"))
        if not geometry:
            continue
        properties = {"layer_kind": "planned_parcel", "parcel_id": _safe_int(data.get("parcel_id")), "parcel_ref": data.get("parcel_ref"), "local_authority": data.get("local_authority"), "postcode": data.get("postcode"), "address_text": data.get("address_text"), "area_m2": _safe_float(data.get("area_m2")), "planned_asset_count": _safe_int(data.get("planned_asset_count")) or 0, "top_planned_asset_id": _safe_int(data.get("top_planned_asset_id")), "top_title": data.get("top_title"), "top_asset_type": data.get("top_asset_type"), "top_status": data.get("top_status"), "top_delivery_probability_score": _safe_float(data.get("top_delivery_probability_score")), "top_delivery_probability_label": data.get("top_delivery_probability_label"), "top_value_impact_score": _safe_float(data.get("top_value_impact_score")), "top_source_confidence_score": _safe_float(data.get("top_source_confidence_score")), "nearest_distance_m": _safe_float(data.get("nearest_distance_m")), "match_confidence_score": _safe_float(data.get("match_confidence_score")), "impact_score": _safe_float(data.get("impact_score")), "evidence_summary": str(data.get("evidence_text") or "insufficient evidence"), "source_name": data.get("source_name"), "source_url": data.get("source_url"), "color_hex": "#16a34a"}
        features.append({"type": "Feature", "geometry": geometry, "properties": properties})
    return {"type": "FeatureCollection", "features": features, "metadata": {"layer_kind": "planned_parcel", "bbox": [west, south, east, north], "feature_count": len(features), "limit": safe_limit}}
