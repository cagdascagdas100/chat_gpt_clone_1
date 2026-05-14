from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any
import re

from sqlalchemy import and_, case, cast, delete, desc, exists, func, or_, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import (
    DQIssue,
    ListingParcelLink,
    ListingsGovernmentPropertyFinder,
    ListingsLandHub,
    ListingsMarketAdapter,
    ManualMatchOverride,
    ParcelInspire,
    SitesBrownfieldLocalAuthority,
    SitesBrownfieldPlanningData,
    TransactionsPricePaid,
)
from app.quality.source_confidence_integration import build_source_confidence_fields
from app.services.scoring import compute_confidence_score, freshness_score, should_require_review, source_reliability_score

settings = get_settings()

LONDON_POSTCODE_PREFIXES = {
    'E', 'EC', 'N', 'NW', 'SE', 'SW', 'W', 'WC',
    'BR', 'CR', 'DA', 'EN', 'HA', 'IG', 'KT', 'RM', 'SM', 'TW', 'UB',
}
LONDON_BBOX_WGS84 = (-0.65, 51.25, 0.35, 51.75)

SOURCE_MODEL_CONFIG: dict[str, dict[str, Any]] = {
    'homes_england_landhub': {
        'model': ListingsLandHub,
        'record_id_attr': 'listing_id',
        'listing_id_attr': 'listing_id',
        'polygon_attr': 'geometry',
        'point_attr': None,
        'postcode_attr': 'postcode',
        'name_attrs': ['parcel_name'],
    },
    'government_property_finder': {
        'model': ListingsGovernmentPropertyFinder,
        'record_id_attr': 'listing_id',
        'listing_id_attr': 'listing_id',
        'polygon_attr': 'site_geometry',
        'point_attr': 'point_geometry',
        'postcode_attr': 'postcode',
        'name_attrs': ['title', 'address_text'],
    },
    'planning_data_brownfield': {
        'model': SitesBrownfieldPlanningData,
        'record_id_attr': 'site_id',
        'listing_id_attr': None,
        'polygon_attr': 'site_geometry',
        'point_attr': 'point_geometry',
        'postcode_attr': 'postcode',
        'name_attrs': ['reference', 'notes'],
    },
    'local_authority_brownfield': {
        'model': SitesBrownfieldLocalAuthority,
        'record_id_attr': 'site_id',
        'listing_id_attr': None,
        'polygon_attr': 'site_geometry',
        'point_attr': 'point_geometry',
        'postcode_attr': 'postcode',
        'name_attrs': ['site_reference', 'site_name_address'],
    },
    'hmlr_price_paid': {
        'model': TransactionsPricePaid,
        'record_id_attr': 'transaction_id',
        'listing_id_attr': None,
        'polygon_attr': None,
        'point_attr': None,
        'postcode_attr': 'postcode',
        'name_attrs': ['address_text', 'street', 'town_city'],
    },
    'market_listing_adapter': {
        'model': ListingsMarketAdapter,
        'record_id_attr': 'listing_id',
        'listing_id_attr': 'listing_id',
        'polygon_attr': 'site_geometry',
        'point_attr': 'point_geometry',
        'postcode_attr': 'postcode',
        'name_attrs': ['parcel_name', 'title', 'address_text'],
    },
}


_SOURCE_URL_HINT_ATTRS = (
    "source_url",
    "listing_url",
    "url",
    "canonical_url",
    "verification_source_url",
    "site_plan_url",
)

_SPATIAL_MATCH_METHODS = {
    "polygon_intersect",
    "polygon_contains",
    "polygon_centroid",
    "point_within",
    "point_nearest",
}


def _first_populated_attr(record: Any, attrs: tuple[str, ...]) -> Any:
    for attr in attrs:
        value = getattr(record, attr, None)
        if value is not None and str(value).strip():
            return value
    return None


def _build_match_source_confidence_fields(record: Any, config: dict[str, Any], candidate: "MatchCandidate") -> dict[str, Any]:
    source_url = _first_populated_attr(record, _SOURCE_URL_HINT_ATTRS)
    record_parcel_hint = _first_populated_attr(record, ("parcel_ref", "inspire_id", "matched_parcel_id"))
    has_geometry = False
    polygon_attr = config.get("polygon_attr")
    point_attr = config.get("point_attr")
    if polygon_attr and getattr(record, polygon_attr, None) is not None:
        has_geometry = True
    if point_attr and getattr(record, point_attr, None) is not None:
        has_geometry = True

    payload = {
        "source_url": source_url,
        "matched_parcel_id": candidate.parcel_id,
        "parcel_ref": record_parcel_hint,
        "parcel_specific_spatial_match": (
            candidate.match_method in _SPATIAL_MATCH_METHODS
            or candidate.overlap_ratio is not None
            or candidate.distance_m is not None
            or has_geometry
        ),
        "ambiguous_match": bool(candidate.requires_review),
    }
    return build_source_confidence_fields(payload)


@dataclass
class MatchCandidate:
    parcel_id: int
    match_method: str
    match_score: float
    overlap_ratio: float | None = None
    distance_m: float | None = None
    postcode_match: bool | None = None
    name_similarity: float | None = None
    requires_review: bool = False
    source_scope: str | None = None
    match_tier: str | None = None
    can_publish_history_signal: bool = True
    forced_confidence_score: float | None = None


def _normalize_authority(value: str | None) -> str | None:
    if not value:
        return None
    return " ".join(value.strip().lower().split())


AUTHORITY_CANONICAL_STOPWORDS = {
    'council',
    'borough',
    'district',
    'city',
    'county',
    'metropolitan',
    'unitary',
    'authority',
    'corporation',
    'the',
    'of',
}


def _canonicalize_authority(value: str | None) -> str | None:
    if not value:
        return None
    tokens = [
        token
        for token in re.sub(r'[^a-z0-9]+', ' ', value.strip().lower()).split()
        if token and token not in AUTHORITY_CANONICAL_STOPWORDS
    ]
    if not tokens:
        return None
    return " ".join(tokens)


def _covered_authorities(session: Session) -> set[str]:
    rows = session.execute(select(ParcelInspire.local_authority).where(ParcelInspire.local_authority.is_not(None)).distinct()).scalars()
    return {normalized for value in rows if (normalized := _normalize_authority(value))}


def _covered_authority_lookup(session: Session) -> dict[str, str | None]:
    rows = session.execute(select(ParcelInspire.local_authority).where(ParcelInspire.local_authority.is_not(None)).distinct()).scalars()
    canonical_to_values: dict[str, set[str]] = {}
    for value in rows:
        canonical = _canonicalize_authority(value)
        if not canonical:
            continue
        canonical_to_values.setdefault(canonical, set()).add(str(value))
    lookup: dict[str, str | None] = {}
    for canonical, values in canonical_to_values.items():
        lookup[canonical] = next(iter(values)) if len(values) == 1 else None
    return lookup


def _resolve_local_authority_filter(record_local_authority: str | None, covered_authorities: set[str], authority_lookup: dict[str, str | None]) -> str | None:
    normalized = _normalize_authority(record_local_authority)
    if normalized and normalized in covered_authorities:
        return record_local_authority
    canonical = _canonicalize_authority(record_local_authority)
    if canonical:
        return authority_lookup.get(canonical)
    return None


def _parcel_extent_subquery():
    return select(func.ST_SetSRID(func.ST_Envelope(func.ST_Extent(ParcelInspire.geometry)), 27700)).scalar_subquery()


def _normalized_postcode_expr(column):
    return func.upper(func.replace(func.coalesce(column, ''), ' ', ''))


def _normalize_postcode_value(value: str | None) -> str:
    if not value:
        return ''
    return ''.join(str(value).upper().split())


def _postcode_prefix(normalized_postcode: str) -> str:
    if not normalized_postcode:
        return ''
    match = re.match(r'^[A-Z]{1,2}', normalized_postcode)
    return match.group(0) if match else ''


def _normalize_address_text(*parts: Any) -> str:
    text_value = ' '.join(str(part or '') for part in parts if part not in (None, ''))
    text_value = re.sub(r'[^A-Z0-9]+', ' ', text_value.upper())
    return ' '.join(text_value.split()).strip()


def _ensure_hmlr_link_columns(session: Session) -> None:
    session.execute(
        text(
            """
            ALTER TABLE public.listing_parcel_link
            ADD COLUMN IF NOT EXISTS source_scope varchar(64),
            ADD COLUMN IF NOT EXISTS match_tier varchar(32),
            ADD COLUMN IF NOT EXISTS can_publish_history_signal boolean NOT NULL DEFAULT true
            """
        )
    )


def _london_market_postcodes(session: Session) -> set[str]:
    west, south, east, north = LONDON_BBOX_WGS84
    bbox = func.ST_MakeEnvelope(west, south, east, north, 4326)
    geom = func.COALESCE(ListingsMarketAdapter.site_geometry, ListingsMarketAdapter.point_geometry)
    rows = (
        session.execute(
            select(_normalized_postcode_expr(ListingsMarketAdapter.postcode))
            .where(
                ListingsMarketAdapter.postcode.is_not(None),
                ListingsMarketAdapter.is_demo.is_(False),
                or_(
                    ListingsMarketAdapter.truth_tier.is_(None),
                    ListingsMarketAdapter.truth_tier != 'demo',
                ),
                geom.is_not(None),
                func.ST_Intersects(
                    case(
                        (func.ST_SRID(geom) == 4326, geom),
                        (func.ST_SRID(geom) == 0, func.ST_SetSRID(geom, 4326)),
                        else_=func.ST_Transform(geom, 4326),
                    ),
                    bbox,
                ),
            )
            .distinct()
        )
        .scalars()
        .all()
    )
    return {str(row) for row in rows if row}


def _classify_hmlr_source_scope(normalized_postcode: str, london_market_postcodes: set[str]) -> str:
    if not normalized_postcode:
        return 'no_postcode'
    if normalized_postcode in london_market_postcodes:
        return 'london_market_postcode'
    if _postcode_prefix(normalized_postcode) in LONDON_POSTCODE_PREFIXES:
        return 'london_prefix_candidate'
    return 'non_london_scope'

def _postcode_exists_expr(postcode_column):
    return exists(
        select(ParcelInspire.parcel_id).where(
            ParcelInspire.postcode.is_not(None),
            _normalized_postcode_expr(ParcelInspire.postcode) == _normalized_postcode_expr(postcode_column),
        )
    )


def _metadata_hint_exists_expr(model: Any):
    metadata_col = getattr(model, 'metadata_json', None)
    if metadata_col is None:
        return None

    metadata_jsonb = cast(metadata_col, JSONB)
    matched_inspire = func.nullif(
        func.jsonb_extract_path_text(metadata_jsonb, 'match_hints', 'matched_inspire_id'),
        '',
    )
    matched_parcel = func.nullif(
        func.jsonb_extract_path_text(metadata_jsonb, 'match_hints', 'matched_parcel_ref'),
        '',
    )
    return or_(matched_inspire.is_not(None), matched_parcel.is_not(None))


def _coverage_filtered_record_stmt(config: dict[str, Any]):
    model = config["model"]
    stmt = select(model)
    parcel_extent = _parcel_extent_subquery()
    coverage_conditions = []

    polygon_attr = config["polygon_attr"]
    point_attr = config["point_attr"]
    postcode_attr = config["postcode_attr"]

    if polygon_attr:
        polygon_column = getattr(model, polygon_attr)
        coverage_conditions.append(and_(polygon_column.is_not(None), func.ST_Intersects(polygon_column, parcel_extent)))
    if point_attr:
        point_column = getattr(model, point_attr)
        coverage_conditions.append(and_(point_column.is_not(None), func.ST_Intersects(point_column, parcel_extent)))
    if postcode_attr:
        postcode_column = getattr(model, postcode_attr)
        coverage_conditions.append(and_(postcode_column.is_not(None), _postcode_exists_expr(postcode_column)))
    hint_expr = _metadata_hint_exists_expr(model)
    if hint_expr is not None:
        coverage_conditions.append(hint_expr)

    if coverage_conditions:
        stmt = stmt.where(or_(*coverage_conditions))
    return stmt



def _completeness_score(record: Any, fields: list[str]) -> float:
    populated = 0
    for field in fields:
        value = getattr(record, field, None)
        if value not in (None, '', []):
            populated += 1
    return populated / max(len(fields), 1)



def _geometry_quality(method: str, overlap_ratio: float | None = None, distance_m: float | None = None) -> float:
    if method == 'polygon_intersect':
        return 0.75 + min(overlap_ratio or 0, 1.0) * 0.25
    if method == 'polygon_centroid_within':
        return 0.82
    if method == 'polygon_centroid_nearest':
        normalized = max(0.0, 1.0 - min((distance_m or 0.0) / max(settings.polygon_centroid_match_radius_m, 1.0), 1.0))
        return 0.58 + normalized * 0.18
    if method == 'point_within':
        return 0.9
    if method == 'point_nearest':
        normalized = max(0.0, 1.0 - min((distance_m or 0.0) / max(settings.point_match_radius_m, 1.0), 1.0))
        return 0.6 + normalized * 0.25
    if method == 'postcode_assisted':
        return 0.55
    if method == 'fuzzy_address':
        return 0.45
    if method == 'manual_override':
        return 1.0
    return 0.4



def _record_dq_issue(session: Session, *, run_id: str, source_name: str, source_record_id: str, message: str, severity: str = 'warning', rule_code: str = 'unmatched_record', payload: dict[str, Any] | None = None) -> None:
    session.add(
        DQIssue(
            run_id=run_id,
            source_name=source_name,
            severity=severity,
            rule_code=rule_code,
            message=message,
            source_record_id=source_record_id,
            payload=payload,
        )
    )



def _manual_override_candidates(session: Session, source_name: str, source_record_id: str) -> list[MatchCandidate]:
    rows = session.execute(
        select(ManualMatchOverride).where(
            ManualMatchOverride.source_name == source_name,
            ManualMatchOverride.source_record_id == source_record_id,
            ManualMatchOverride.override_action == 'force_link',
        )
    ).scalars().all()
    return [MatchCandidate(parcel_id=row.parcel_id, match_method='manual_override', match_score=100.0) for row in rows]

def _extract_match_hints(record: Any) -> dict[str, Any]:
    metadata = getattr(record, 'metadata_json', None)
    if not isinstance(metadata, dict):
        return {}
    hints = metadata.get('match_hints')
    return hints if isinstance(hints, dict) else {}



def _hint_candidates(session: Session, record: Any, local_authority: str | None = None) -> list[MatchCandidate]:
    hints = _extract_match_hints(record)
    matched_inspire_id = str(hints.get('matched_inspire_id') or '').strip()
    matched_parcel_ref = str(hints.get('matched_parcel_ref') or '').strip()

    if matched_inspire_id:
        stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.inspire_id == matched_inspire_id)
        if local_authority:
            stmt = stmt.where(ParcelInspire.local_authority == local_authority)
        parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
        if parcel_id is not None:
            return [MatchCandidate(parcel_id=int(parcel_id), match_method='metadata_inspire_exact', match_score=99.8)]

    if matched_parcel_ref:
        stmt = select(ParcelInspire.parcel_id).where(ParcelInspire.parcel_ref == matched_parcel_ref)
        if local_authority:
            stmt = stmt.where(ParcelInspire.local_authority == local_authority)
        parcel_id = session.execute(stmt.limit(1)).scalar_one_or_none()
        if parcel_id is not None:
            return [MatchCandidate(parcel_id=int(parcel_id), match_method='metadata_parcel_ref_exact', match_score=99.6)]

    return []



def _polygon_candidates(session: Session, geom_value: Any, local_authority: str | None = None) -> list[MatchCandidate]:
    safe_geom = func.ST_CollectionExtract(func.ST_MakeValid(geom_value), 3)
    overlap_ratio = (
        func.ST_Area(func.ST_Intersection(ParcelInspire.geometry, safe_geom))
        / func.nullif(func.ST_Area(ParcelInspire.geometry), 0)
    ).label('overlap_ratio')
    stmt = select(ParcelInspire.parcel_id, overlap_ratio).where(func.ST_Intersects(ParcelInspire.geometry, safe_geom))
    if local_authority:
        stmt = stmt.where(ParcelInspire.local_authority == local_authority)
    rows = session.execute(stmt.order_by(desc(overlap_ratio)).limit(settings.max_polygon_match_candidates)).all()
    candidates = []
    for parcel_id, overlap in rows:
        overlap_value = float(overlap or 0.0)
        if overlap_value < 0.01:
            continue
        candidates.append(MatchCandidate(parcel_id=parcel_id, match_method='polygon_intersect', match_score=min(100.0, 70.0 + overlap_value * 30.0), overlap_ratio=overlap_value))
    return candidates



def _point_candidates(session: Session, point_value: Any, local_authority: str | None = None) -> list[MatchCandidate]:
    within_expr = func.ST_Within(point_value, ParcelInspire.geometry).label('is_within')
    distance_expr = func.ST_Distance(ParcelInspire.centroid, point_value).label('distance_m')
    knn_distance_expr = ParcelInspire.centroid.op('<->')(point_value)
    stmt = (
        select(ParcelInspire.parcel_id, within_expr, distance_expr)
        .where(or_(func.ST_Within(point_value, ParcelInspire.geometry), func.ST_DWithin(ParcelInspire.centroid, point_value, settings.point_match_radius_m)))
    )
    if local_authority:
        stmt = stmt.where(ParcelInspire.local_authority == local_authority)
    rows = session.execute(stmt.order_by(within_expr.desc(), knn_distance_expr.asc()).limit(3)).all()
    candidates = []
    for parcel_id, is_within, distance_m in rows:
        distance_value = float(distance_m or 0.0)
        method = 'point_within' if is_within else 'point_nearest'
        score = 88.0 if is_within else max(55.0, 80.0 - min(distance_value / max(settings.point_match_radius_m, 1.0), 1.0) * 25.0)
        candidates.append(MatchCandidate(parcel_id=parcel_id, match_method=method, match_score=score, distance_m=distance_value))
    if candidates:
        return [candidates[0]]
    return []


def _polygon_centroid_candidates(session: Session, geom_value: Any, local_authority: str | None = None) -> list[MatchCandidate]:
    safe_geom = func.ST_CollectionExtract(func.ST_MakeValid(geom_value), 3)
    centroid_value = func.ST_Centroid(safe_geom)
    within_expr = func.ST_Within(centroid_value, ParcelInspire.geometry).label('is_within')
    distance_expr = func.ST_Distance(ParcelInspire.centroid, centroid_value).label('distance_m')
    knn_distance_expr = ParcelInspire.centroid.op('<->')(centroid_value)
    stmt = (
        select(ParcelInspire.parcel_id, within_expr, distance_expr)
        .where(
            or_(
                func.ST_Within(centroid_value, ParcelInspire.geometry),
                func.ST_DWithin(ParcelInspire.centroid, centroid_value, settings.polygon_centroid_match_radius_m),
            )
        )
    )
    if local_authority:
        stmt = stmt.where(ParcelInspire.local_authority == local_authority)
    rows = session.execute(stmt.order_by(within_expr.desc(), knn_distance_expr.asc()).limit(3)).all()
    candidates: list[MatchCandidate] = []
    for parcel_id, is_within, distance_m in rows:
        distance_value = float(distance_m or 0.0)
        method = 'polygon_centroid_within' if is_within else 'polygon_centroid_nearest'
        score = 84.0 if is_within else max(
            58.0,
            82.0 - min(distance_value / max(settings.polygon_centroid_match_radius_m, 1.0), 1.0) * 24.0,
        )
        candidates.append(
            MatchCandidate(
                parcel_id=parcel_id,
                match_method=method,
                match_score=score,
                distance_m=distance_value,
                requires_review=not bool(is_within),
            )
        )
    if candidates:
        return [candidates[0]]
    return []



def _postcode_candidates(session: Session, postcode: str | None, local_authority: str | None) -> list[MatchCandidate]:
    if not postcode:
        return []
    normalized_postcode = str(postcode).replace(' ', '').upper()
    if not normalized_postcode:
        return []
    stmt = select(ParcelInspire.parcel_id).where(
        ParcelInspire.postcode.is_not(None),
        _normalized_postcode_expr(ParcelInspire.postcode) == normalized_postcode,
    )
    if local_authority:
        stmt = stmt.where(ParcelInspire.local_authority == local_authority)
    parcel_ids = session.execute(stmt.limit(5)).scalars().all()
    return [MatchCandidate(parcel_id=parcel_id, match_method='postcode_assisted', match_score=65.0, postcode_match=True, requires_review=True) for parcel_id in parcel_ids[:1]]



def _market_postcode_bridge_candidates(session: Session, postcode: str | None) -> list[MatchCandidate]:
    if not postcode:
        return []
    normalized_postcode = str(postcode).replace(' ', '').upper()
    if not normalized_postcode:
        return []

    rows = (
        session.execute(
            select(
                ListingParcelLink.parcel_id.label('parcel_id'),
                ListingParcelLink.confidence_score.label('confidence_score'),
                ListingParcelLink.match_score.label('match_score'),
            )
            .join(
                ListingsMarketAdapter,
                and_(
                    ListingParcelLink.source_name == 'market_listing_adapter',
                    or_(
                        ListingParcelLink.listing_id == ListingsMarketAdapter.listing_id,
                        ListingParcelLink.source_record_id == ListingsMarketAdapter.listing_id,
                    ),
                ),
            )
            .where(
                ListingsMarketAdapter.postcode.is_not(None),
                _normalized_postcode_expr(ListingsMarketAdapter.postcode) == normalized_postcode,
                ListingsMarketAdapter.is_demo.is_(False),
                or_(
                    ListingsMarketAdapter.truth_tier.is_(None),
                    ListingsMarketAdapter.truth_tier != 'demo',
                ),
            )
            .order_by(
                ListingParcelLink.confidence_score.desc(),
                ListingParcelLink.match_score.desc(),
                ListingParcelLink.parcel_id.asc(),
            )
            .limit(10)
        )
        .mappings()
        .all()
    )
    if not rows:
        return []

    seen: set[int] = set()
    candidates: list[MatchCandidate] = []
    for row in rows:
        parcel_id = row.get('parcel_id')
        if parcel_id is None:
            continue
        parcel_id_int = int(parcel_id)
        if parcel_id_int in seen:
            continue
        seen.add(parcel_id_int)
        bridge_conf = float(row.get('confidence_score') or 0.0)
        bridge_match = float(row.get('match_score') or 0.0)
        candidates.append(
            MatchCandidate(
                parcel_id=parcel_id_int,
                match_method='market_postcode_bridge',
                match_score=max(58.0, min(82.0, 55.0 + bridge_conf * 0.35 + bridge_match * 0.20)),
                postcode_match=True,
                requires_review=False,
                source_scope='non_london_scope',
                match_tier='tier_b',
                can_publish_history_signal=True,
                forced_confidence_score=0.78,
            )
        )
        if len(candidates) >= 1:
            break
    return candidates


def _hmlr_london_tiered_candidate(
    session: Session,
    record: Any,
    normalized_postcode: str,
    source_scope: str,
) -> tuple[MatchCandidate | None, dict[str, Any]]:
    diagnostics: dict[str, Any] = {
        'source_scope': source_scope,
        'normalized_postcode': normalized_postcode,
    }
    if not normalized_postcode:
        diagnostics.update({'match_tier': 'tier_d', 'reason': 'missing_postcode'})
        return None, diagnostics

    rows = (
        session.execute(
            select(
                ListingParcelLink.parcel_id.label('parcel_id'),
                ListingParcelLink.confidence_score.label('confidence_score'),
                ListingParcelLink.match_score.label('match_score'),
                ListingsMarketAdapter.address_text.label('listing_address'),
                ListingsMarketAdapter.title.label('listing_title'),
                ListingsMarketAdapter.parcel_name.label('listing_parcel_name'),
            )
            .join(
                ListingsMarketAdapter,
                and_(
                    ListingParcelLink.source_name == 'market_listing_adapter',
                    or_(
                        ListingParcelLink.listing_id == ListingsMarketAdapter.listing_id,
                        ListingParcelLink.source_record_id == ListingsMarketAdapter.listing_id,
                    ),
                ),
            )
            .where(
                ListingsMarketAdapter.postcode.is_not(None),
                _normalized_postcode_expr(ListingsMarketAdapter.postcode) == normalized_postcode,
                ListingsMarketAdapter.is_demo.is_(False),
                or_(
                    ListingsMarketAdapter.truth_tier.is_(None),
                    ListingsMarketAdapter.truth_tier != 'demo',
                ),
            )
            .order_by(
                ListingParcelLink.confidence_score.desc(),
                ListingParcelLink.match_score.desc(),
            )
            .limit(30)
        )
        .mappings()
        .all()
    )
    if not rows:
        diagnostics.update({'match_tier': 'tier_d', 'reason': 'no_market_bridge_row'})
        return None, diagnostics

    parcel_scores: dict[int, dict[str, float]] = {}
    ppd_address = _normalize_address_text(
        getattr(record, 'address_text', None),
        getattr(record, 'paon', None),
        getattr(record, 'saon', None),
        getattr(record, 'street', None),
        getattr(record, 'town_city', None),
    )
    diagnostics['ppd_address_nonempty'] = bool(ppd_address)

    for row in rows:
        parcel_id_raw = row.get('parcel_id')
        if parcel_id_raw is None:
            continue
        parcel_id = int(parcel_id_raw)
        item = parcel_scores.setdefault(parcel_id, {'bridge': 0.0, 'address': 0.0})
        bridge_conf = float(row.get('confidence_score') or 0.0)
        bridge_match = float(row.get('match_score') or 0.0)
        bridge_score = bridge_conf * 0.65 + bridge_match * 0.35
        if bridge_score > item['bridge']:
            item['bridge'] = bridge_score

        listing_text = _normalize_address_text(
            row.get('listing_address'),
            row.get('listing_title'),
            row.get('listing_parcel_name'),
        )
        if ppd_address and listing_text:
            sim = SequenceMatcher(None, ppd_address, listing_text).ratio()
            if sim > item['address']:
                item['address'] = sim

    if not parcel_scores:
        diagnostics.update({'match_tier': 'tier_d', 'reason': 'no_parcel_candidate'})
        return None, diagnostics

    ranked = sorted(
        parcel_scores.items(),
        key=lambda kv: (kv[1]['address'], kv[1]['bridge'], -kv[0]),
        reverse=True,
    )
    top_parcel_id, top_metrics = ranked[0]
    top_address_sim = float(top_metrics.get('address') or 0.0)
    unique_parcel_count = len(parcel_scores)
    diagnostics['unique_parcel_count'] = unique_parcel_count
    diagnostics['top_address_similarity'] = round(top_address_sim, 4)

    if source_scope == 'london_prefix_candidate':
        diagnostics.update({'match_tier': 'tier_d', 'reason': 'prefix_only_not_publishable'})
        return None, diagnostics

    if unique_parcel_count == 1 and (not ppd_address or top_address_sim >= 0.90):
        tier = 'tier_a' if not ppd_address else 'tier_b'
        confidence = 0.90 if tier == 'tier_a' else 0.82
        candidate = MatchCandidate(
            parcel_id=top_parcel_id,
            match_method='market_postcode_bridge' if tier == 'tier_a' else 'market_postcode_address_bridge',
            match_score=88.0 if tier == 'tier_a' else 79.0,
            postcode_match=True,
            name_similarity=top_address_sim if ppd_address else None,
            requires_review=False,
            source_scope=source_scope,
            match_tier=tier,
            can_publish_history_signal=True,
            forced_confidence_score=confidence,
        )
        diagnostics.update({'match_tier': tier, 'reason': 'accepted_unique'})
        return candidate, diagnostics

    if ppd_address and top_address_sim >= 0.90:
        second_best = ranked[1][1] if len(ranked) > 1 else None
        second_address_sim = float((second_best or {}).get('address') or 0.0)
        if unique_parcel_count <= 2 and (top_address_sim - second_address_sim) >= 0.10:
            candidate = MatchCandidate(
                parcel_id=top_parcel_id,
                match_method='market_postcode_address_bridge',
                match_score=76.0,
                postcode_match=True,
                name_similarity=top_address_sim,
                requires_review=False,
                source_scope=source_scope,
                match_tier='tier_b',
                can_publish_history_signal=True,
                forced_confidence_score=0.78,
            )
            diagnostics.update({'match_tier': 'tier_b', 'reason': 'accepted_strong_address'})
            return candidate, diagnostics

    if ppd_address and 0.80 <= top_address_sim < 0.90:
        diagnostics.update({'match_tier': 'tier_c', 'reason': 'review_address_mid_similarity'})
        return None, diagnostics

    diagnostics.update({'match_tier': 'tier_d', 'reason': 'low_similarity_or_ambiguous'})
    return None, diagnostics


def _fuzzy_candidates(session: Session, search_text: str | None) -> list[MatchCandidate]:
    if not search_text:
        return []
    similarity_expr = func.similarity(
        func.lower(func.coalesce(ParcelInspire.address_text, ParcelInspire.parcel_ref, ParcelInspire.inspire_id)),
        search_text.lower(),
    ).label('name_similarity')
    rows = session.execute(
        select(ParcelInspire.parcel_id, similarity_expr)
        .where(similarity_expr >= settings.fuzzy_similarity_threshold)
        .order_by(desc(similarity_expr))
        .limit(5)
    ).all()
    candidates = [MatchCandidate(parcel_id=parcel_id, match_method='fuzzy_address', match_score=float(similarity * 100.0), name_similarity=float(similarity), requires_review=True) for parcel_id, similarity in rows]
    if candidates:
        return [candidates[0]]
    return []



def _score_candidate(
    source_name: str,
    candidate: MatchCandidate,
    source_updated_at,
    completeness: float,
    *,
    source_confidence_needs_review: bool = False,
) -> tuple[float, bool]:
    confidence = compute_confidence_score(
        source_reliability=source_reliability_score(source_name),
        freshness=freshness_score(source_updated_at, source_name),
        geometry_quality=_geometry_quality(candidate.match_method, candidate.overlap_ratio, candidate.distance_m),
        match_quality=candidate.match_score / 100.0,
        completeness=completeness,
    )
    requires_review = candidate.requires_review or should_require_review(
        confidence_score=confidence,
        match_method=candidate.match_method,
        distance_m=candidate.distance_m,
        source_confidence_needs_review=source_confidence_needs_review,
    )
    return confidence, requires_review



def _match_planning_data_brownfield_records(session: Session, run_id: str) -> int:
    config = SOURCE_MODEL_CONFIG['planning_data_brownfield']
    # Planning Data brownfield matching already relies on geometry-first candidate SQL.
    # Distinct local_authority scans on very large parcel tables can hit statement timeout,
    # so we skip authority pre-filtering for this source and keep matching resilient.
    covered_authorities: set[str] = set()
    authority_lookup: dict[str, str | None] = {}
    session.execute(delete(ListingParcelLink).where(ListingParcelLink.source_name == 'planning_data_brownfield'))
    session.flush()

    candidate_sql = text(
        '''
        WITH parcel_extent AS (
          SELECT ST_SetSRID(ST_Envelope(ST_Extent(geometry)), 27700) AS geom
          FROM parcels_inspire
        ),
        source_rows AS (
          SELECT s.site_id, s.point_geometry
          FROM sites_brownfield_planning_data s
          WHERE s.point_geometry IS NOT NULL
            AND ST_Intersects(s.point_geometry, (SELECT geom FROM parcel_extent))
        )
        SELECT
          s.site_id AS source_record_id,
          p.parcel_id,
          CASE WHEN ST_Within(s.point_geometry, p.geometry) THEN 'point_within' ELSE 'point_nearest' END AS match_method,
          CASE WHEN ST_Within(s.point_geometry, p.geometry) THEN 88.0
               ELSE GREATEST(55.0, 80.0 - LEAST(ST_Distance(p.centroid, s.point_geometry) / :radius, 1.0) * 25.0)
          END AS match_score,
          ST_Distance(p.centroid, s.point_geometry) AS distance_m
        FROM source_rows s
        JOIN LATERAL (
          SELECT parcel_id, geometry, centroid
          FROM parcels_inspire
          WHERE ST_Within(s.point_geometry, geometry)
             OR ST_DWithin(centroid, s.point_geometry, :radius)
          ORDER BY ST_Within(s.point_geometry, geometry) DESC, centroid <-> s.point_geometry
          LIMIT 1
        ) p ON TRUE
        '''
    )
    candidate_rows = session.execute(candidate_sql, {'radius': settings.point_match_radius_m}).mappings().all()
    candidate_map = {str(row['source_record_id']): row for row in candidate_rows}

    rows = session.execute(_coverage_filtered_record_stmt(config).execution_options(yield_per=250)).scalars()
    matched_count = 0
    unmatched_issue_count = 0
    suppressed_unmatched_count = 0

    for record in rows:
        source_record_id = getattr(record, config['record_id_attr'])
        completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
        record_local_authority = getattr(record, 'local_authority', None)
        local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
        candidates = _manual_override_candidates(session, 'planning_data_brownfield', source_record_id)
        if not candidates:
            candidates = _hint_candidates(session, record, local_authority_filter)

        if not candidates:
            matched_row = candidate_map.get(str(source_record_id))
            if matched_row is not None:
                candidates = [
                    MatchCandidate(
                        parcel_id=int(matched_row['parcel_id']),
                        match_method=str(matched_row['match_method']),
                        match_score=float(matched_row['match_score']),
                        distance_m=float(matched_row['distance_m']) if matched_row['distance_m'] is not None else None,
                    )
                ]

        # Bulk point matching is the fast path for the common case, but some planning-data
        # rows only have polygon geometry or postcode/name fallback signals. Keep the generic
        # matching ladder for those records so coverage grows instead of shrinking.
        if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
            candidates = _polygon_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
        if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
            candidates = _polygon_centroid_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
        if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
            candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
        if not candidates:
            candidates = _postcode_candidates(session, getattr(record, config['postcode_attr'], None), local_authority_filter)
        if not candidates:
            search_text = ' '.join(str(getattr(record, field, '') or '') for field in config['name_attrs']).strip()
            candidates = _fuzzy_candidates(session, search_text)

        if not candidates:
            record.match_method = None
            record.match_score = None
            record.confidence_score = 0.0
            record.requires_review = True
            if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
                _record_dq_issue(
                    session,
                    run_id=run_id,
                    source_name='planning_data_brownfield',
                    source_record_id=source_record_id,
                    message='No parcel match could be inferred for this source record.',
                    payload={'record_id': source_record_id},
                )
                unmatched_issue_count += 1
            else:
                suppressed_unmatched_count += 1
            continue

        candidate = candidates[0]
        source_confidence_fields = _build_match_source_confidence_fields(record, config, candidate)
        confidence, requires_review = _score_candidate(
            'planning_data_brownfield',
            candidate,
            getattr(record, 'source_updated_at', None),
            completeness,
            source_confidence_needs_review=bool(source_confidence_fields["source_confidence_needs_review"]),
        )
        requires_review = requires_review or bool(source_confidence_fields["source_confidence_needs_review"])
        session.add(
            ListingParcelLink(
                parcel_id=candidate.parcel_id,
                source_name='planning_data_brownfield',
                source_record_id=source_record_id,
                listing_id=None,
                match_method=candidate.match_method,
                overlap_ratio=candidate.overlap_ratio,
                distance_m=candidate.distance_m,
                postcode_match=candidate.postcode_match,
                name_similarity=candidate.name_similarity,
                match_score=candidate.match_score,
                confidence_score=confidence,
                requires_review=requires_review,
            )
        )
        matched_count += 1
        record.match_method = candidate.match_method
        record.match_score = candidate.match_score
        record.confidence_score = confidence
        record.requires_review = requires_review
        record.is_stale = freshness_score(getattr(record, 'source_updated_at', None), 'planning_data_brownfield') < 0.5

    if suppressed_unmatched_count:
        _record_dq_issue(
            session,
            run_id=run_id,
            source_name='planning_data_brownfield',
            source_record_id='__summary__',
            message=f'Suppressed {suppressed_unmatched_count} additional unmatched record issues after the per-run cap was reached.',
            rule_code='unmatched_record_summary',
            payload={'suppressed_unmatched_count': suppressed_unmatched_count},
        )
    session.flush()
    return matched_count


def match_source_records(session: Session, source_name: str, run_id: str) -> int:
    if source_name == 'planning_data_brownfield':
        return _match_planning_data_brownfield_records(session, run_id)

    config = SOURCE_MODEL_CONFIG[source_name]
    model = config['model']
    # History transactions (hmlr_price_paid) are high-volume.
    # Distinct authority scans on large parcel tables can hit statement timeout
    # before matching even starts, so skip authority pre-filtering for this source.
    if source_name == 'hmlr_price_paid':
        covered_authorities = set()
        authority_lookup: dict[str, str | None] = {}
    else:
        covered_authorities = _covered_authorities(session)
        authority_lookup = _covered_authority_lookup(session)
    if source_name == 'hmlr_price_paid':
        _ensure_hmlr_link_columns(session)
    session.execute(delete(ListingParcelLink).where(ListingParcelLink.source_name == source_name))
    session.flush()

    london_market_postcodes: set[str] = set()
    if source_name == 'hmlr_price_paid':
        london_market_postcodes = _london_market_postcodes(session)
        postcode_column = getattr(model, config['postcode_attr'])
        market_postcode_exists = exists(
            select(ListingsMarketAdapter.id).where(
                ListingsMarketAdapter.postcode.is_not(None),
                _normalized_postcode_expr(ListingsMarketAdapter.postcode) == _normalized_postcode_expr(postcode_column),
            )
        )
        rows = session.execute(
            select(model)
            .where(
                postcode_column.is_not(None),
                or_(
                    _postcode_exists_expr(postcode_column),
                    market_postcode_exists,
                ),
            )
            .execution_options(yield_per=500)
        ).scalars()
    else:
        rows = session.execute(_coverage_filtered_record_stmt(config).execution_options(yield_per=250)).scalars()
    matched_count = 0
    unmatched_issue_count = 0
    suppressed_unmatched_count = 0
    for record in rows:
        source_record_id = getattr(record, config['record_id_attr'])
        listing_id = getattr(record, config['listing_id_attr']) if config['listing_id_attr'] else None
        completeness = _completeness_score(record, [config['postcode_attr'], *config['name_attrs']])
        record_local_authority = getattr(record, 'local_authority', None)
        local_authority_filter = _resolve_local_authority_filter(record_local_authority, covered_authorities, authority_lookup)
        candidates = _manual_override_candidates(session, source_name, source_record_id)
        if not candidates:
            candidates = _hint_candidates(session, record, local_authority_filter)

        hmlr_scope: str | None = None
        if source_name == 'hmlr_price_paid':
            normalized_postcode = _normalize_postcode_value(getattr(record, config['postcode_attr'], None))
            hmlr_scope = _classify_hmlr_source_scope(normalized_postcode, london_market_postcodes)
            if hmlr_scope in {'london_market_postcode', 'london_prefix_candidate'}:
                hmlr_candidate, diagnostics = _hmlr_london_tiered_candidate(
                    session=session,
                    record=record,
                    normalized_postcode=normalized_postcode,
                    source_scope=hmlr_scope,
                )
                if hmlr_candidate is not None and hmlr_candidate.can_publish_history_signal:
                    candidates = [hmlr_candidate]
                else:
                    record.match_method = diagnostics.get('reason')
                    record.match_score = None
                    record.confidence_score = 0.0
                    record.requires_review = True
                    if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
                        _record_dq_issue(
                            session,
                            run_id=run_id,
                            source_name=source_name,
                            source_record_id=source_record_id,
                            message='HMLR London candidate matched review/reject thresholds and was not published.',
                            rule_code=f"hmlr_history_{diagnostics.get('match_tier', 'tier_d')}",
                            payload=diagnostics,
                        )
                        unmatched_issue_count += 1
                    else:
                        suppressed_unmatched_count += 1
                    continue

        if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
            candidates = _polygon_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
        if not candidates and config['polygon_attr'] and getattr(record, config['polygon_attr']) is not None:
            candidates = _polygon_centroid_candidates(session, getattr(record, config['polygon_attr']), local_authority_filter)
        if not candidates and config['point_attr'] and getattr(record, config['point_attr']) is not None:
            candidates = _point_candidates(session, getattr(record, config['point_attr']), local_authority_filter)
        if not candidates:
            candidates = _postcode_candidates(session, getattr(record, config['postcode_attr'], None), local_authority_filter)
        if not candidates and source_name == 'hmlr_price_paid':
            candidates = _market_postcode_bridge_candidates(session, getattr(record, config['postcode_attr'], None))
        if not candidates and source_name != 'hmlr_price_paid':
            search_text = ' '.join(str(getattr(record, field, '') or '') for field in config['name_attrs']).strip()
            candidates = _fuzzy_candidates(session, search_text)

        if not candidates:
            record.match_method = None
            record.match_score = None
            record.confidence_score = 0.0
            record.requires_review = True
            if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
                _record_dq_issue(session, run_id=run_id, source_name=source_name, source_record_id=source_record_id, message='No parcel match could be inferred for this source record.', payload={'record_id': source_record_id})
                unmatched_issue_count += 1
            else:
                suppressed_unmatched_count += 1
            continue

        if source_name == 'hmlr_price_paid' and hmlr_scope in {'london_market_postcode', 'london_prefix_candidate'}:
            publishable_candidates = [candidate for candidate in candidates if candidate.can_publish_history_signal]
            if not publishable_candidates:
                record.match_method = 'non_publishable_candidate'
                record.match_score = None
                record.confidence_score = 0.0
                record.requires_review = True
                if unmatched_issue_count < settings.max_unmatched_dq_issues_per_run:
                    _record_dq_issue(
                        session,
                        run_id=run_id,
                        source_name=source_name,
                        source_record_id=source_record_id,
                        message='HMLR candidate exists but is not publishable under current tier thresholds.',
                        rule_code='hmlr_history_tier_c',
                        payload={
                            'source_scope': hmlr_scope or 'unknown',
                            'candidate_count': len(candidates),
                        },
                    )
                    unmatched_issue_count += 1
                else:
                    suppressed_unmatched_count += 1
                continue
            candidates = publishable_candidates

        if len(candidates) > 1:
            top = candidates[0].match_score
            for candidate in candidates:
                if abs(top - candidate.match_score) <= 5.0:
                    candidate.requires_review = True

        best_confidence = 0.0
        best_candidate = candidates[0]
        for candidate in candidates:
            source_confidence_fields = _build_match_source_confidence_fields(record, config, candidate)
            if candidate.forced_confidence_score is not None:
                confidence = float(candidate.forced_confidence_score)
                requires_review = bool(candidate.requires_review) or bool(
                    source_confidence_fields["source_confidence_needs_review"]
                )
            else:
                confidence, requires_review = _score_candidate(
                    source_name,
                    candidate,
                    getattr(record, 'source_updated_at', None),
                    completeness,
                    source_confidence_needs_review=bool(source_confidence_fields["source_confidence_needs_review"]),
                )
                requires_review = requires_review or bool(source_confidence_fields["source_confidence_needs_review"])
            session.add(
                ListingParcelLink(
                    parcel_id=candidate.parcel_id,
                    source_name=source_name,
                    source_record_id=source_record_id,
                    listing_id=listing_id,
                    match_method=candidate.match_method,
                    overlap_ratio=candidate.overlap_ratio,
                    distance_m=candidate.distance_m,
                    postcode_match=candidate.postcode_match,
                    name_similarity=candidate.name_similarity,
                    match_score=candidate.match_score,
                    confidence_score=confidence,
                    requires_review=requires_review,
                    source_scope=candidate.source_scope or hmlr_scope,
                    match_tier=candidate.match_tier,
                    can_publish_history_signal=bool(candidate.can_publish_history_signal),
                )
            )
            matched_count += 1
            if confidence >= best_confidence:
                best_confidence = confidence
                best_candidate = candidate
                record.match_method = candidate.match_method
                record.match_score = candidate.match_score
                record.confidence_score = confidence
                record.requires_review = requires_review
        record.is_stale = freshness_score(getattr(record, 'source_updated_at', None), source_name) < 0.5
    if suppressed_unmatched_count:
        _record_dq_issue(
            session,
            run_id=run_id,
            source_name=source_name,
            source_record_id='__summary__',
            message=f'Suppressed {suppressed_unmatched_count} additional unmatched record issues after the per-run cap was reached.',
            rule_code='unmatched_record_summary',
            payload={'suppressed_unmatched_count': suppressed_unmatched_count},
        )
    session.flush()
    return matched_count
