from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.db.models import SourceSnapshot
from app.quality.source_confidence_integration import build_source_confidence_metadata
from app.schemas.common import SourceDescriptor, SourceStatus
from app.services.source_catalog import SOURCE_CATALOG, STALE_THRESHOLDS
from app.services.source_manifest_status import inspect_configured_manifest_status


def list_source_descriptors() -> list[SourceDescriptor]:
    return [SourceDescriptor(**payload) for payload in SOURCE_CATALOG.values()]


def _build_source_status_notes(source_name: str, metadata_json: dict[str, Any] | None, settings) -> dict[str, Any]:
    notes = dict(metadata_json or {})
    manifest_status = inspect_configured_manifest_status(source_name, settings)
    if manifest_status:
        notes["manifest_status"] = manifest_status

    source_confidence_record = {
        "source_url": notes.get("source_url")
        or notes.get("listing_url")
        or notes.get("canonical_url")
        or notes.get("provider_url"),
        "parcel_ref": notes.get("parcel_ref") or notes.get("inspire_id"),
        "parcel_specific_spatial_match": bool(
            notes.get("has_parcel_match")
            or notes.get("has_geometry")
            or notes.get("geometry_verified")
        ),
        "ambiguous_match": bool(notes.get("ambiguous_match") or notes.get("needs_review")),
    }
    notes["source_confidence"] = build_source_confidence_metadata(
        source_confidence_record,
        origin="source_status",
    )
    return notes


def list_source_statuses(session) -> list[SourceStatus]:
    settings = get_settings()
    statuses: list[SourceStatus] = []
    threshold_map = {
        'homes_england_landhub': settings.landhub_stale_after_days,
        'government_property_finder': settings.government_property_stale_after_days,
        'planning_data_brownfield': settings.planning_data_stale_after_days,
        'local_authority_brownfield': settings.local_brownfield_stale_after_days,
        'hmlr_inspire': settings.inspire_stale_after_days,
        'hmlr_price_paid': settings.price_paid_stale_after_days,
        'market_listing_adapter': settings.market_stale_after_days,
    }

    latest_rows = session.query(SourceSnapshot).order_by(SourceSnapshot.source_name.asc(), SourceSnapshot.fetched_at.desc()).all()
    latest_by_source = {}
    for row in latest_rows:
        latest_by_source.setdefault(row.source_name, row)

    for name in SOURCE_CATALOG:
        latest = latest_by_source.get(name)
        last_snapshot_at = getattr(latest, 'fetched_at', None)
        last_source_updated_at = getattr(latest, 'source_updated_at', None)
        row_count = getattr(latest, 'row_count', 0) or 0
        stale_days = threshold_map.get(name, STALE_THRESHOLDS.get(name, 30))
        is_stale = True
        if last_source_updated_at:
            delta_days = (settings.now_utc() - last_source_updated_at).days
            is_stale = delta_days > stale_days
        statuses.append(
            SourceStatus(
                name=name,
                last_snapshot_at=last_snapshot_at,
                last_source_updated_at=last_source_updated_at,
                row_count=row_count,
                stale_threshold_days=stale_days,
                is_stale=is_stale,
                notes=_build_source_status_notes(
                    name,
                    latest.metadata_json if latest and latest.metadata_json else {},
                    settings,
                ),
            )
        )
    return statuses
