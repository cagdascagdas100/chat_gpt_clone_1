from __future__ import annotations
import json
import logging
import socket
import time
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from fastapi import APIRouter, Query

from app.api.deps import DBSession
from app.core.config import get_settings
from app.schemas.common import GeoJSONFeatureCollection
from app.services.brownfield_service import list_brownfield_sites
from app.services.listing_service import list_listings
from app.services.parcel_service import list_parcels

router = APIRouter(prefix='/map', tags=['map'])
logger = logging.getLogger(__name__)
_DB_SOCKET_CACHE: dict[str, Any] = {"checked_at": 0.0, "available": None}
_DISTANCE_PROPERTY_TYPES_LOOKUP_CANDIDATES = (
    Path(__file__).resolve().parents[3] / "data" / "exports" / "parcel_use6" / "parcel_use6_lookup.json",
    Path(__file__).resolve().parents[3] / "docs" / "handoff_imports" / "20260523_parcel_label" / "zip_3_2" / "parcel_use6_lookup.json",
)
_DISTANCE_PROPERTY_TYPES_SOURCE_PATH = "terrayield_land_intelligence/data/exports/parcel_use6/parcel_use6_lookup.json"
_DISTANCE_PROPERTY_TYPES_USE6_CATALOG = {
    "industrial": {
        "building_type_label": "Sanayi",
        "land_use_category": "industrial",
        "color_hex": "#F4D03F",
    },
    "detached_residential": {
        "building_type_label": "Mustakil",
        "land_use_category": "residential_detached",
        "color_hex": "#A8E6A3",
    },
    "apartment_residential": {
        "building_type_label": "Apartman",
        "land_use_category": "residential_apartment",
        "color_hex": "#1B7F3A",
    },
    "retail": {
        "building_type_label": "Perakende",
        "land_use_category": "retail",
        "color_hex": "#74C0FC",
    },
    "office": {
        "building_type_label": "Ofis",
        "land_use_category": "office",
        "color_hex": "#1F4E79",
    },
    "mixed_use_vertical": {
        "building_type_label": "Karma",
        "land_use_category": "mixed_use",
        "color_hex": "#8E44AD",
    },
    "unknown": {
        "building_type_label": "Bilinmiyor",
        "land_use_category": "unknown",
        "color_hex": "#9CA3AF",
    },
}


def _parse_bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if not value:
        return None
    west, south, east, north = [float(part.strip()) for part in value.split(',')]
    return west, south, east, north


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return str(value)
    return value


def _empty_feature_collection() -> GeoJSONFeatureCollection:
    return GeoJSONFeatureCollection(features=[])

def _fast_map_parcels_geojson(
    db,
    *,
    authority: str | None,
    min_confidence: float | None,
    max_confidence: float | None,
    brownfield_signal: bool | None,
    on_market_signal: bool | None,
    portal_listing_signal: bool | None,
    sale_ready_signal: bool | None,
    exclude_demo: bool,
    real_price_only: bool,
    source_tier: str | None,
    bbox_tuple: tuple[float, float, float, float] | None,
    limit: int,
    offset: int,
) -> GeoJSONFeatureCollection:
    """Fast map-only parcel endpoint; avoids expensive per-parcel detail enrichment."""
    params: dict[str, Any] = {
        "authority": authority,
        "min_confidence": min_confidence,
        "max_confidence": max_confidence,
        "limit": int(limit),
        "offset": int(offset),
    }
    filters: list[str] = [
        "p.geometry IS NOT NULL",
        "(:authority IS NULL OR p.local_authority = :authority)",
    ]
    if min_confidence is not None:
        filters.append("coalesce(s.highest_confidence_score, 0) >= :min_confidence")
    if max_confidence is not None:
        filters.append("coalesce(s.highest_confidence_score, 0) <= :max_confidence")
    if brownfield_signal is not None:
        params["brownfield_signal"] = bool(brownfield_signal)
        filters.append("coalesce(s.brownfield_signal, false) = :brownfield_signal")
    if on_market_signal is not None:
        params["on_market_signal"] = bool(on_market_signal)
        filters.append("coalesce(s.official_sale_signal, false) = :on_market_signal")
    if portal_listing_signal is not None:
        params["portal_listing_signal"] = bool(portal_listing_signal)
        filters.append("coalesce(s.portal_listing_signal, false) = :portal_listing_signal")
    if sale_ready_signal is not None:
        params["sale_ready_signal"] = bool(sale_ready_signal)
        filters.append("(coalesce(s.official_sale_signal, false) OR coalesce(s.portal_listing_signal, false)) = :sale_ready_signal")
    if source_tier == "official":
        filters.append("coalesce(s.official_sale_visible_count, 0) > 0")
    elif source_tier == "licensed":
        filters.append("coalesce(s.licensed_sale_visible_count, 0) > 0")
    elif source_tier == "manual":
        filters.append("coalesce(s.manual_sale_visible_count, 0) > 0")
    elif source_tier == "demo" and not exclude_demo:
        filters.append("coalesce(s.demo_sale_count, 0) > 0")
    if real_price_only:
        filters.append("coalesce(s.real_price_count, 0) > 0")
    if bbox_tuple:
        west, south, east, north = bbox_tuple
        params.update({"west": west, "south": south, "east": east, "north": north})
        filters.append(
            """
            p.geometry && ST_Transform(ST_MakeEnvelope(:west, :south, :east, :north, 4326), 27700)
            AND ST_Intersects(
              p.geometry,
              ST_Transform(ST_MakeEnvelope(:west, :south, :east, :north, 4326), 27700)
            )
            """
        )

    where_sql = "\n      AND ".join(filters)
    sql = f"""
    SELECT
      p.parcel_id,
      coalesce(p.inspire_id, 'parcel:' || p.parcel_id::text) AS inspire_id,
      coalesce(p.parcel_ref, p.inspire_id, 'parcel:' || p.parcel_id::text) AS parcel_ref,
      p.local_authority,
      p.area_m2,
      p.perimeter_m,
      coalesce(s.official_sale_signal, false) AS official_sale_signal,
      coalesce(s.brownfield_signal, false) AS brownfield_signal,
      coalesce(s.portal_listing_signal, false) AS portal_listing_signal,
      coalesce(s.highest_confidence_score, NULL) AS highest_confidence_score,
      s.latest_source_updated_at AS last_updated,
      coalesce(s.requires_review, false) AS requires_review,
      coalesce(s.visible_sale_count, 0) AS visible_sale_count,
      coalesce(s.real_price_count, 0) AS real_price_count,
      coalesce(s.history_transaction_count, 0) AS history_transaction_count,
      ST_AsGeoJSON(ST_Transform(p.geometry, 4326)) AS geom
    FROM parcels_inspire p
    LEFT JOIN parcel_signal_summary s ON s.parcel_id = p.parcel_id
    WHERE {where_sql}
    ORDER BY p.parcel_id ASC
    LIMIT :limit OFFSET :offset
    """
    rows = db.connection().exec_driver_sql(sql, params).mappings().all()
    features: list[dict[str, Any]] = []
    for row in rows:
        geom_raw = row.get("geom")
        if not geom_raw:
            continue
        try:
            geometry = json.loads(geom_raw)
        except Exception:
            continue
        properties = {
            "parcel_id": row.get("parcel_id"),
            "inspire_id": row.get("inspire_id"),
            "parcel_ref": row.get("parcel_ref"),
            "local_authority": row.get("local_authority"),
            "area_m2": _serialize_value(row.get("area_m2")),
            "perimeter_m": _serialize_value(row.get("perimeter_m")),
            "sale_ready_signal": bool(row.get("official_sale_signal") or row.get("portal_listing_signal")),
            "official_sale_signal": bool(row.get("official_sale_signal")),
            "brownfield_signal": bool(row.get("brownfield_signal")),
            "portal_listing_signal": bool(row.get("portal_listing_signal")),
            "highest_confidence_score": _serialize_value(row.get("highest_confidence_score")),
            "last_updated": _serialize_value(row.get("last_updated")),
            "requires_review": bool(row.get("requires_review")),
            "visible_sale_count": _serialize_value(row.get("visible_sale_count")),
            "real_price_count": _serialize_value(row.get("real_price_count")),
            "history_transaction_count": _serialize_value(row.get("history_transaction_count")),
            "layer_kind": "fast_parcel_polygon",
        }
        features.append({"type": "Feature", "geometry": geometry, "properties": properties})
    return GeoJSONFeatureCollection(features=features)


def _coerce_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _coerce_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _score_band(score_pct: float | None) -> str:
    if score_pct is None:
        return "unknown"
    if score_pct >= 80:
        return "very_high"
    if score_pct >= 60:
        return "high"
    if score_pct >= 40:
        return "medium"
    if score_pct >= 20:
        return "low"
    return "very_low"


def _weighted_score(*pairs: tuple[float | None, float]) -> float | None:
    weighted_total = 0.0
    total_weight = 0.0
    for value, weight in pairs:
        if value is None:
            continue
        weighted_total += value * weight
        total_weight += weight
    if total_weight <= 0:
        return None
    return round(weighted_total / total_weight, 1)


def _proximity_score_pct(distance_m: float | None, cap_m: float) -> float | None:
    if distance_m is None or cap_m <= 0:
        return None
    return round(_clamp(1.0 - (distance_m / cap_m), 0.0, 1.0) * 100.0, 1)


def _normalize_ratio_pct(value: float | None) -> float | None:
    if value is None:
        return None
    return round(_clamp(value, 0.0, 1.0) * 100.0, 1)


def _normalize_count_pct(value: int | None, divisor: float) -> float | None:
    if value is None or divisor <= 0:
        return None
    return round(_clamp(value / divisor, 0.0, 1.0) * 100.0, 1)


def _first_finite(*values: Any) -> float | None:
    for value in values:
        parsed = _coerce_float(value)
        if parsed is not None:
            return parsed
    return None


@lru_cache(maxsize=1)
def _load_distance_property_types_lookup() -> dict[int, dict[str, Any]]:
    for candidate in _DISTANCE_PROPERTY_TYPES_LOOKUP_CANDIDATES:
        if not candidate.exists():
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        rows = payload.get("rows") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            continue
        lookup: dict[int, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            parcel_id = _coerce_int(row.get("parcel_id"))
            if parcel_id is None:
                continue
            lookup[parcel_id] = row
        if lookup:
            return lookup
    return {}


def _lookup_use6_payload(parcel_id: int) -> dict[str, Any]:
    row = _load_distance_property_types_lookup().get(parcel_id) or {}
    use6_code = str(row.get("use6_code") or "unknown").strip().lower()
    catalog = _DISTANCE_PROPERTY_TYPES_USE6_CATALOG.get(use6_code, _DISTANCE_PROPERTY_TYPES_USE6_CATALOG["unknown"])
    return {
        "use6_code": use6_code,
        "building_type_label": str(row.get("use6_label_tr") or catalog["building_type_label"]).strip() or catalog["building_type_label"],
        "land_use_category": catalog["land_use_category"],
        "color_hex": str(row.get("use6_color_hex") or catalog["color_hex"]).strip() or catalog["color_hex"],
        "accuracy_scale": str(row.get("dogruluk_skalasi") or "D_UNKNOWN").strip().upper(),
        "confidence_score": _coerce_float(row.get("confidence")),
        "evidence_summary": str(row.get("kaynak_ve_belirleme_yontemi") or "").strip(),
        "source_name": "parcel_use6_lookup",
        "source_url": _DISTANCE_PROPERTY_TYPES_SOURCE_PATH,
    }


def _fallback_use6_code(row: dict[str, Any]) -> str:
    dominant_context = str(row.get("dominant_context_code") or "").strip().lower()
    residential_ratio = _coerce_float(row.get("residential_ratio_500m")) or 0.0
    commercial_ratio = _coerce_float(row.get("commercial_ratio_500m")) or 0.0
    industrial_ratio = _coerce_float(row.get("industrial_ratio_500m")) or 0.0
    land_use_mix_score = _coerce_float(row.get("land_use_mix_score")) or 0.0
    office_count = _coerce_int(row.get("office_count_500m")) or 0
    retail_count = _coerce_int(row.get("retail_count_500m")) or 0
    if industrial_ratio >= 0.45 or dominant_context == "industrial":
        return "industrial"
    if land_use_mix_score >= 0.55 and residential_ratio >= 0.20 and commercial_ratio >= 0.20:
        return "mixed_use_vertical"
    if commercial_ratio >= 0.35 and office_count >= max(2, retail_count):
        return "office"
    if commercial_ratio >= 0.25 and retail_count >= 2:
        return "retail"
    if residential_ratio >= 0.65 and commercial_ratio <= 0.25 and industrial_ratio <= 0.15:
        return "detached_residential"
    if residential_ratio >= 0.35:
        return "apartment_residential"
    return "unknown"


def _confidence_level_from_accuracy(accuracy_scale: str, score_pct: float | None, metric_count: int) -> str:
    normalized = str(accuracy_scale or "").strip().upper()
    if normalized and normalized != "D_UNKNOWN":
        return normalized
    if score_pct is not None and score_pct >= 80 and metric_count >= 4:
        return "B_HIGH"
    if metric_count >= 2:
        return "C_PARTIAL"
    return "D_UNKNOWN"


def _database_socket_available(ttl_s: float = 15.0, timeout_s: float = 0.25) -> bool:
    now = time.monotonic()
    cached = _DB_SOCKET_CACHE.get("available")
    checked_at = float(_DB_SOCKET_CACHE.get("checked_at") or 0.0)
    if cached is not None and (now - checked_at) < ttl_s:
        return bool(cached)

    raw_url = str(get_settings().database_url or "")
    parsed = urlparse(raw_url.replace("postgresql+psycopg://", "postgresql://", 1))
    host = parsed.hostname or "localhost"
    port = int(parsed.port or 5432)
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            available = True
    except OSError:
        available = False
    _DB_SOCKET_CACHE.update({"checked_at": now, "available": available})
    return available


@router.get('/parcels', response_model=GeoJSONFeatureCollection)
def get_map_parcels(
    db: DBSession,
    sales_history_signal: bool = Query(False, description="Only parcels with verified parcel sales history."),
    external_market_signal: bool = Query(False, description="Only parcels with external market polygon evidence."),
    region: str | None = None,
    local_authority: str | None = None,
    min_confidence: float | None = Query(default=None, ge=0, le=100),
    max_confidence: float | None = Query(default=None, ge=0, le=100),
    brownfield_signal: bool | None = None,
    on_market_signal: bool | None = None,
    portal_listing_signal: bool | None = None,
    sale_ready_signal: bool | None = None,
    history_signal: bool | None = None,
    exclude_demo: bool = True,
    real_price_only: bool = False,
    source_tier: str | None = Query(default=None, pattern='^(official|licensed|manual|demo)$'),
    bbox: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    fast_mode: bool = True,
) -> GeoJSONFeatureCollection:
    authority = local_authority or region
    if not _database_socket_available():
        return _empty_feature_collection()
    if fast_mode and not external_market_signal and not sales_history_signal and history_signal is None:
        try:
            return _fast_map_parcels_geojson(
                db,
                authority=authority,
                min_confidence=min_confidence,
                max_confidence=max_confidence,
                brownfield_signal=brownfield_signal,
                on_market_signal=on_market_signal,
                portal_listing_signal=portal_listing_signal,
                sale_ready_signal=sale_ready_signal,
                exclude_demo=exclude_demo,
                real_price_only=real_price_only,
                source_tier=source_tier,
                bbox_tuple=_parse_bbox(bbox),
                limit=limit,
                offset=offset,
            )
        except Exception as exc:
            logger.warning("Fast map parcels unavailable; falling back to enriched path: %s", exc)
    try:
        items, _ = list_parcels(
            db,
            local_authority=authority,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            brownfield_signal=brownfield_signal,
            on_market_signal=on_market_signal,
            portal_listing_signal=portal_listing_signal,
            sale_ready_signal=sale_ready_signal,
            history_signal=history_signal,
            exclude_demo=exclude_demo,
            real_price_only=real_price_only,
            source_tier=source_tier,
            bbox=_parse_bbox(bbox),
            limit=limit,
            offset=offset,
            include_total=False,
            fast_mode=fast_mode,

            external_market_signal=external_market_signal,
            sales_history_signal=sales_history_signal,)
    except Exception as exc:
        logger.warning("Map parcels unavailable; returning empty FeatureCollection: %s", exc)
        return _empty_feature_collection()
    return GeoJSONFeatureCollection(features=[{'type': 'Feature', 'geometry': item.geometry, 'properties': item.model_dump(exclude={'geometry'})} for item in items])


@router.get('/listings', response_model=GeoJSONFeatureCollection)
def get_map_listings(
    db: DBSession,
    source: str | None = None,
    region: str | None = None,
    local_authority: str | None = None,
    provider_name: str | None = None,
    listing_status: str | None = None,
    min_confidence: float | None = Query(default=None, ge=0, le=100),
    max_confidence: float | None = Query(default=None, ge=0, le=100),
    exclude_demo: bool = True,
    real_price_only: bool = False,
    source_tier: str | None = Query(default=None, pattern='^(official|licensed|manual|demo)$'),
    bbox: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> GeoJSONFeatureCollection:
    authority = local_authority or region
    if not _database_socket_available():
        return _empty_feature_collection()
    items, _ = list_listings(
        db,
        source=source,
        local_authority=authority,
        provider_name=provider_name,
        listing_status=listing_status,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        exclude_demo=exclude_demo,
        real_price_only=real_price_only,
        source_tier=source_tier,
        bbox=_parse_bbox(bbox),
        limit=limit,
        offset=offset,
    )
    return GeoJSONFeatureCollection(features=[{'type': 'Feature', 'geometry': item.geometry, 'properties': item.model_dump(exclude={'geometry'})} for item in items])


@router.get('/brownfield', response_model=GeoJSONFeatureCollection)
def get_map_brownfield(
    db: DBSession,
    source: str | None = None,
    region: str | None = None,
    local_authority: str | None = None,
    planning_status: str | None = None,
    min_confidence: float | None = Query(default=None, ge=0, le=100),
    max_confidence: float | None = Query(default=None, ge=0, le=100),
    bbox: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> GeoJSONFeatureCollection:
    authority = local_authority or region
    if not _database_socket_available():
        return _empty_feature_collection()
    items, _ = list_brownfield_sites(db, source=source, local_authority=authority, planning_status=planning_status, min_confidence=min_confidence, max_confidence=max_confidence, bbox=_parse_bbox(bbox), limit=limit, offset=offset)
    return GeoJSONFeatureCollection(features=[{'type': 'Feature', 'geometry': item.geometry, 'properties': item.model_dump(exclude={'geometry'})} for item in items])


@router.get('/internet-access', response_model=GeoJSONFeatureCollection)
def get_map_internet_access(
    db: DBSession,
    region: str | None = None,
    local_authority: str | None = None,
    bbox: str | None = None,
    min_score: float | None = Query(default=None, ge=0, le=10),
    max_score: float | None = Query(default=None, ge=0, le=10),
    limit: int = Query(default=5000, ge=1, le=20000),
    offset: int = Query(default=0, ge=0),
) -> GeoJSONFeatureCollection:
    authority = local_authority or region
    if not _database_socket_available():
        return _empty_feature_collection()
    bbox_tuple = _parse_bbox(bbox)
    params: dict[str, Any] = {
        "authority": authority,
        "min_score": min_score,
        "max_score": max_score,
        "limit": int(limit),
        "offset": int(offset),
    }
    bbox_filter = ""
    if bbox_tuple:
        params.update({
            "west": bbox_tuple[0],
            "south": bbox_tuple[1],
            "east": bbox_tuple[2],
            "north": bbox_tuple[3],
        })
        bbox_filter = """
          and p.geometry && ST_Transform(ST_MakeEnvelope(:west, :south, :east, :north, 4326), 27700)
          and ST_Intersects(
                p.geometry,
                ST_Transform(ST_MakeEnvelope(:west, :south, :east, :north, 4326), 27700)
              )
        """

    sql = f"""
    select
      p.parcel_id,
      p.parcel_ref,
      p.inspire_id,
      p.local_authority,
      p.postcode,
      p.address_text,
      p.area_m2,
      s.internet_access_score_10,
      s.internet_access_pct,
      s.internet_access_level_5,
      s.confidence_level_4,
      s.confidence_score_pct,
      s.confidence_reason,
      s.factor_name,
      s.factor_level,
      s.raw_value,
      s.normalized_0_100,
      s.weight,
      s.contribution,
      s.source_name,
      s.source_url,
      s.source_date,
      s.last_verified_at,
      s.evidence_ref,
      s.calculation_version,
      ST_AsGeoJSON(ST_Transform(p.geometry, 4326)) as geom
    from parcel_internet_access_scores s
    join parcels_inspire p on p.parcel_id = s.parcel_id
    where (:authority is null or p.local_authority = :authority)
      and (:min_score is null or s.internet_access_score_10 >= :min_score)
      and (:max_score is null or s.internet_access_score_10 <= :max_score)
      {bbox_filter}
    order by s.internet_access_score_10 desc nulls last, p.parcel_id asc
    limit :limit offset :offset
    """
    try:
        rows = db.connection().exec_driver_sql(sql, params).mappings().all()
    except Exception:
        return _empty_feature_collection()

    features = []
    for row in rows:
        geom_raw = row.get("geom")
        if not geom_raw:
            continue
        try:
            geometry = json.loads(geom_raw)
        except Exception:
            continue
        properties = {
            "parcel_id": row.get("parcel_id"),
            "parcel_ref": row.get("parcel_ref"),
            "inspire_id": row.get("inspire_id"),
            "local_authority": row.get("local_authority"),
            "postcode": row.get("postcode"),
            "address_text": row.get("address_text"),
            "area_m2": _serialize_value(row.get("area_m2")),
            "internet_access_score_10": _serialize_value(row.get("internet_access_score_10")),
            "internet_access_pct": _serialize_value(row.get("internet_access_pct")),
            "internet_access_level_5": row.get("internet_access_level_5"),
            "confidence_level_4": row.get("confidence_level_4"),
            "confidence_score_pct": _serialize_value(row.get("confidence_score_pct")),
            "confidence_reason": row.get("confidence_reason"),
            "factor_name": row.get("factor_name"),
            "factor_level": row.get("factor_level"),
            "raw_value": _serialize_value(row.get("raw_value")),
            "normalized_0_100": _serialize_value(row.get("normalized_0_100")),
            "weight": _serialize_value(row.get("weight")),
            "contribution": _serialize_value(row.get("contribution")),
            "source_name": row.get("source_name"),
            "source_url": row.get("source_url"),
            "source_date": _serialize_value(row.get("source_date")),
            "last_verified_at": _serialize_value(row.get("last_verified_at")),
            "evidence_ref": row.get("evidence_ref"),
            "calculation_version": row.get("calculation_version"),
            "layer_kind": "internet_access_score_10",
        }
        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties,
        })

    return GeoJSONFeatureCollection(features=features)


@router.get('/distance-property-types', response_model=GeoJSONFeatureCollection)
def get_map_distance_property_types(
    db: DBSession,
    region: str | None = None,
    local_authority: str | None = None,
    bbox: str | None = None,
    limit: int = Query(default=5000, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
) -> GeoJSONFeatureCollection:
    authority = local_authority or region
    if not _database_socket_available():
        return _empty_feature_collection()

    bbox_tuple = _parse_bbox(bbox)
    params: dict[str, Any] = {
        "authority": authority,
        "limit": int(limit),
        "offset": int(offset),
    }
    bbox_filter = ""
    if bbox_tuple:
        params.update({
            "west": bbox_tuple[0],
            "south": bbox_tuple[1],
            "east": bbox_tuple[2],
            "north": bbox_tuple[3],
        })
        bbox_filter = """
          AND p.geometry && ST_Transform(ST_MakeEnvelope(:west, :south, :east, :north, 4326), 27700)
          and ST_Intersects(
                p.geometry,
                ST_Transform(ST_MakeEnvelope(:west, :south, :east, :north, 4326), 27700)
              )
        """

    sql = f"""
    WITH base AS (
      SELECT
        p.parcel_id,
        p.parcel_ref,
        p.inspire_id,
        p.local_authority,
        p.postcode,
        p.address_text,
        p.area_m2,
        pcs.dominant_context_code,
        pcs.nearest_industrial_m,
        pcs.nearest_office_m,
        pcs.nearest_retail_m,
        pcs.industrial_count_500m,
        pcs.office_count_500m,
        pcs.retail_count_500m,
        pcs.residential_ratio_500m,
        pcs.commercial_ratio_500m,
        pcs.industrial_ratio_500m,
        pcs.land_use_mix_score,
        pcs.nuisance_score,
        pcs.accessibility_score,
        pcs.last_computed_at,
        ST_AsGeoJSON(ST_Transform(p.geometry, 4326)) AS geom
      FROM parcel_context_summary pcs
      JOIN parcels_inspire p ON p.parcel_id = pcs.parcel_id
      WHERE p.geometry IS NOT NULL
        AND (:authority IS NULL OR p.local_authority = :authority)
        {bbox_filter}
      ORDER BY pcs.last_computed_at DESC NULLS LAST, p.parcel_id ASC
      LIMIT :limit OFFSET :offset
    ),
    detail AS (
      SELECT
        d.parcel_id,
        MIN(CASE WHEN d.category_code = 'residential' THEN d.nearest_distance_m END) AS nearest_residential_m,
        MIN(CASE WHEN d.category_code = 'commercial' THEN d.nearest_distance_m END) AS nearest_commercial_m
      FROM parcel_context_metric_details d
      WHERE d.parcel_id IN (SELECT parcel_id FROM base)
      GROUP BY d.parcel_id
    )
    SELECT
      base.*,
      detail.nearest_residential_m,
      detail.nearest_commercial_m
    FROM base
    LEFT JOIN detail ON detail.parcel_id = base.parcel_id
    """

    try:
        rows = db.connection().exec_driver_sql(sql, params).mappings().all()
    except Exception as exc:
        logger.warning("Distance property types layer unavailable; returning empty FeatureCollection: %s", exc)
        return _empty_feature_collection()

    features: list[dict[str, Any]] = []
    for row in rows:
        geom_raw = row.get("geom")
        if not geom_raw:
            continue
        try:
            geometry = json.loads(geom_raw)
        except Exception:
            continue

        parcel_id = _coerce_int(row.get("parcel_id"))
        if parcel_id is None:
            continue

        lookup_payload = _lookup_use6_payload(parcel_id)
        use6_code = lookup_payload["use6_code"]
        if not use6_code or use6_code == "unknown":
            use6_code = _fallback_use6_code(row)
            fallback_catalog = _DISTANCE_PROPERTY_TYPES_USE6_CATALOG.get(use6_code, _DISTANCE_PROPERTY_TYPES_USE6_CATALOG["unknown"])
            lookup_payload.update({
                "use6_code": use6_code,
                "building_type_label": fallback_catalog["building_type_label"],
                "land_use_category": fallback_catalog["land_use_category"],
                "color_hex": fallback_catalog["color_hex"],
            })

        residential_distance_m = _first_finite(row.get("nearest_residential_m"))
        industrial_distance_m = _first_finite(row.get("nearest_industrial_m"))
        office_distance_m = _first_finite(row.get("nearest_office_m"))
        retail_distance_m = _first_finite(row.get("nearest_retail_m"))
        commercial_distance_m = _first_finite(row.get("nearest_commercial_m"))
        mixed_distance_m = _first_finite(commercial_distance_m, office_distance_m, retail_distance_m, residential_distance_m)

        residential_ratio_pct = _normalize_ratio_pct(_coerce_float(row.get("residential_ratio_500m")))
        commercial_ratio_pct = _normalize_ratio_pct(_coerce_float(row.get("commercial_ratio_500m")))
        industrial_ratio_pct = _normalize_ratio_pct(_coerce_float(row.get("industrial_ratio_500m")))
        land_use_mix_pct = _normalize_ratio_pct(_coerce_float(row.get("land_use_mix_score")))
        accessibility_pct = _normalize_ratio_pct(_coerce_float(row.get("accessibility_score")))
        low_nuisance_pct = None
        nuisance_ratio = _coerce_float(row.get("nuisance_score"))
        if nuisance_ratio is not None:
            low_nuisance_pct = round((1.0 - _clamp(nuisance_ratio, 0.0, 1.0)) * 100.0, 1)

        industrial_unit_score_pct = _weighted_score(
            (_proximity_score_pct(industrial_distance_m, 1500.0), 0.55),
            (industrial_ratio_pct, 0.30),
            (_normalize_count_pct(_coerce_int(row.get("industrial_count_500m")), 8.0), 0.15),
        )
        detached_home_score_pct = _weighted_score(
            (_proximity_score_pct(residential_distance_m, 1200.0), 0.45),
            (residential_ratio_pct, 0.35),
            (low_nuisance_pct, 0.10),
            (round(100.0 - (land_use_mix_pct or 0.0), 1) if land_use_mix_pct is not None else None, 0.10),
        )
        apartment_building_score_pct = _weighted_score(
            (_proximity_score_pct(residential_distance_m, 1200.0), 0.40),
            (residential_ratio_pct, 0.30),
            (accessibility_pct, 0.20),
            (land_use_mix_pct, 0.10),
        )
        retail_property_score_pct = _weighted_score(
            (_proximity_score_pct(retail_distance_m, 1400.0), 0.45),
            (commercial_ratio_pct, 0.30),
            (_normalize_count_pct(_coerce_int(row.get("retail_count_500m")), 10.0), 0.15),
            (accessibility_pct, 0.10),
        )
        office_building_score_pct = _weighted_score(
            (_proximity_score_pct(office_distance_m, 1400.0), 0.45),
            (commercial_ratio_pct, 0.30),
            (_normalize_count_pct(_coerce_int(row.get("office_count_500m")), 10.0), 0.15),
            (accessibility_pct, 0.10),
        )
        mixed_building_program_score_pct = _weighted_score(
            (_proximity_score_pct(mixed_distance_m, 1400.0), 0.30),
            (land_use_mix_pct, 0.30),
            (commercial_ratio_pct, 0.20),
            (residential_ratio_pct, 0.20),
        )

        score_by_use6 = {
            "industrial": industrial_unit_score_pct,
            "detached_residential": detached_home_score_pct,
            "apartment_residential": apartment_building_score_pct,
            "retail": retail_property_score_pct,
            "office": office_building_score_pct,
            "mixed_use_vertical": mixed_building_program_score_pct,
        }
        overall_score_pct = score_by_use6.get(use6_code)
        if overall_score_pct is None:
            overall_score_pct = _weighted_score(
                (industrial_unit_score_pct, 1.0),
                (detached_home_score_pct, 1.0),
                (apartment_building_score_pct, 1.0),
                (retail_property_score_pct, 1.0),
                (office_building_score_pct, 1.0),
                (mixed_building_program_score_pct, 1.0),
            )

        if overall_score_pct is None and use6_code == "unknown":
            continue

        accuracy_scale = lookup_payload["accuracy_scale"] or "D_UNKNOWN"
        metric_count = len([
            value for value in (
                industrial_distance_m,
                residential_distance_m,
                retail_distance_m,
                office_distance_m,
                mixed_distance_m,
            )
            if value is not None
        ])
        confidence_level_4 = _confidence_level_from_accuracy(accuracy_scale, overall_score_pct, metric_count)
        computed_at = _serialize_value(row.get("last_computed_at"))
        source_date = None
        if isinstance(computed_at, str) and len(computed_at) >= 10:
            source_date = computed_at[:10]

        distance_source_summary = lookup_payload["evidence_summary"] or (
            "parcel_context_summary metrikleri ve parcel_context_metric_details residential/commercial en yakinlik proxyleri kullanildi."
        )
        calculation_explanation = (
            "Industrial, office ve retail mesafeleri parcel_context_summary tablosundan alindi. "
            "Detached/apartment icin residential nearest proxy parcel_context_metric_details tablosundan turetildi. "
            "Mixed-use mesafesi residential/commercial/office/retail en yakinliklarinin en dusuk proxy degerinden hesaplandi. "
            "Score alanlari mesafe yakinligi, oran/yogunluk ve erisilebilirlik sinyallerinin agirlikli ortalamasidir."
        )

        properties = {
            "parcel_id": parcel_id,
            "parcel_ref": row.get("parcel_ref"),
            "inspire_id": row.get("inspire_id"),
            "local_authority": row.get("local_authority"),
            "postcode": row.get("postcode"),
            "address_text": row.get("address_text"),
            "area_m2": _serialize_value(row.get("area_m2")),
            "layer_name": "Distance to Nearby Property Types",
            "use6_code": use6_code,
            "use6_label": lookup_payload["building_type_label"],
            "building_type_label": lookup_payload["building_type_label"],
            "color_hex": lookup_payload["color_hex"],
            "land_use_category": lookup_payload["land_use_category"],
            "parcel_use_label": lookup_payload["land_use_category"],
            "nearest_industrial_unit_m": _serialize_value(industrial_distance_m),
            "industrial_unit_score_pct": industrial_unit_score_pct,
            "nearest_detached_home_m": _serialize_value(residential_distance_m),
            "detached_home_score_pct": detached_home_score_pct,
            "nearest_retail_property_m": _serialize_value(retail_distance_m),
            "retail_property_score_pct": retail_property_score_pct,
            "nearest_apartment_building_m": _serialize_value(residential_distance_m),
            "apartment_building_score_pct": apartment_building_score_pct,
            "nearest_office_building_m": _serialize_value(office_distance_m),
            "office_building_score_pct": office_building_score_pct,
            "nearest_mixed_building_program_m": _serialize_value(mixed_distance_m),
            "mixed_building_program_score_pct": mixed_building_program_score_pct,
            "overall_distance_property_type_score_pct": overall_score_pct,
            "class_level": f"{_score_band(overall_score_pct)}_{use6_code}",
            "source_name": "parcel_context_summary + parcel_context_metric_details + parcel_use6_lookup",
            "source_url": lookup_payload["source_url"],
            "source_date": source_date,
            "evidence_ref": f"parcel:{parcel_id};lookup:{lookup_payload['source_name']}",
            "evidence_summary": distance_source_summary,
            "confidence_level_4": confidence_level_4,
            "accuracy_scale": accuracy_scale,
            "matching_method": "parcel_id join + parcel polygon spatial bbox filter",
            "calculation_explanation": calculation_explanation,
            "last_verified_at": computed_at,
            "calculation_version": "distance_property_types_v2_real_context",
            "yapi_turu_ve_6_renk": f"{lookup_payload['building_type_label']} | {use6_code} | {lookup_payload['color_hex']}",
            "dogruluk_skalasi": accuracy_scale,
        }
        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties,
        })

    return GeoJSONFeatureCollection(features=features)



# ============================================================
# AAYS direct sales-layer endpoints
# These bypass generic /map/parcels filtering and return layer-ready GeoJSON.
# ============================================================

@router.get("/map/sales-layers/external-market")
def get_aays_external_market_sales_layer(
    db: DBSession,
    limit: int = 5000,
    offset: int = 0,
):
    sql = """
    with src as (
      select
        p.parcel_id,
        p.parcel_ref,
        p.inspire_id,
        p.local_authority,
        p.postcode,
        p.address_text,
        p.area_m2,
        e.external_market_evidence_count,
        e.external_market_l2_count,
        e.external_market_l3_count,
        e.external_market_polygon_match_count,
        e.external_market_best_overlap_ratio,
        e.external_market_avg_overlap_ratio,
        e.external_market_best_confidence_score,
        e.external_market_evidence_samples,
        ST_AsGeoJSON(ST_Transform(p.geometry, 4326))::jsonb as geom
      from parcel_external_market_evidence_summary e
      join parcels_inspire p on p.parcel_id = e.parcel_id
      order by e.external_market_best_confidence_score desc nulls last,
               e.external_market_best_overlap_ratio desc nulls last,
               p.parcel_id asc
      limit :limit offset :offset
    )
    select jsonb_build_object(
      'type', 'FeatureCollection',
      'features', coalesce(jsonb_agg(
        jsonb_build_object(
          'type', 'Feature',
          'geometry', geom,
          'properties', jsonb_build_object(
            'parcel_id', parcel_id,
            'parcel_ref', parcel_ref,
            'inspire_id', inspire_id,
            'local_authority', local_authority,
            'postcode', postcode,
            'address_text', address_text,
            'area_m2', area_m2,
            'external_market_evidence_available', true,
            'external_market_evidence_count', external_market_evidence_count,
            'external_market_l2_count', external_market_l2_count,
            'external_market_l3_count', external_market_l3_count,
            'external_market_polygon_match_count', external_market_polygon_match_count,
            'external_market_best_overlap_ratio', external_market_best_overlap_ratio,
            'external_market_avg_overlap_ratio', external_market_avg_overlap_ratio,
            'external_market_best_confidence_score', external_market_best_confidence_score,
            'external_market_evidence_samples', coalesce(external_market_evidence_samples, '[]'::jsonb),
            'sales_history_available', false,
            'layer_kind', 'external_market_polygon_evidence'
          )
        )
      ), '[]'::jsonb)
    )::text as geojson
    from src;
    """
    raw = db.connection().exec_driver_sql(sql, {"limit": int(limit), "offset": int(offset)}).scalar()
    return json.loads(raw or '{"type":"FeatureCollection","features":[]}')


@router.get("/map/sales-layers/verified-history")
def get_aays_verified_sales_history_layer(
    db: DBSession,
    limit: int = 5000,
    offset: int = 0,
):
    sql = """
    with src as (
      select
        p.parcel_id,
        p.parcel_ref,
        p.inspire_id,
        p.local_authority,
        p.postcode,
        p.address_text,
        p.area_m2,
        h.sales_history_count,
        h.latest_sale_year,
        h.latest_sale_date,
        h.latest_sale_price_gbp,
        h.latest_sale_area_m2,
        h.latest_sale_price_per_m2_gbp,
        h.latest_sale_property_type,
        h.best_sales_history_confidence_score,
        h.sales_history_records,
        ST_AsGeoJSON(ST_Transform(p.geometry, 4326))::jsonb as geom
      from parcel_verified_sales_history_summary h
      join parcels_inspire p on p.parcel_id = h.parcel_id
      order by h.latest_sale_date desc nulls last,
               h.best_sales_history_confidence_score desc nulls last,
               p.parcel_id asc
      limit :limit offset :offset
    )
    select jsonb_build_object(
      'type', 'FeatureCollection',
      'features', coalesce(jsonb_agg(
        jsonb_build_object(
          'type', 'Feature',
          'geometry', geom,
          'properties', jsonb_build_object(
            'parcel_id', parcel_id,
            'parcel_ref', parcel_ref,
            'inspire_id', inspire_id,
            'local_authority', local_authority,
            'postcode', postcode,
            'address_text', address_text,
            'area_m2', area_m2,
            'sales_history_available', true,
            'sales_history_count', sales_history_count,
            'latest_sale_year', latest_sale_year,
            'latest_sale_date', latest_sale_date,
            'latest_sale_price_gbp', latest_sale_price_gbp,
            'latest_sale_area_m2', latest_sale_area_m2,
            'latest_sale_price_per_m2_gbp', latest_sale_price_per_m2_gbp,
            'latest_sale_property_type', latest_sale_property_type,
            'sales_history_confidence_score', best_sales_history_confidence_score,
            'sales_history_records', coalesce(sales_history_records, '[]'::jsonb),
            'layer_kind', 'verified_parcel_sales_history'
          )
        )
      ), '[]'::jsonb)
    )::text as geojson
    from src;
    """
    raw = db.connection().exec_driver_sql(sql, {"limit": int(limit), "offset": int(offset)}).scalar()
    return json.loads(raw or '{"type":"FeatureCollection","features":[]}')



