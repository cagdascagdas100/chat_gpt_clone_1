from __future__ import annotations

import datetime as dt

from app.core.config import get_settings
from app.services.source_catalog import get_stale_threshold_days

SOURCE_RELIABILITY = {
    'homes_england_landhub': 0.95,
    'government_property_finder': 0.93,
    'hmlr_inspire': 0.95,
    'local_authority_brownfield': 0.9,
    'planning_data_brownfield': 0.8,
    'hmlr_price_paid': 0.7,
    'market_listing_adapter': 0.65,
}


def source_reliability_score(source_name: str) -> float:
    return SOURCE_RELIABILITY.get(source_name, 0.6)


def freshness_score(updated_at: dt.datetime | None, source_name: str, now: dt.datetime | None = None) -> float:
    now = now or dt.datetime.now(dt.UTC)
    if updated_at is None:
        return 0.35
    age_days = max((now - updated_at).days, 0)
    threshold = max(get_stale_threshold_days(source_name), 1)
    ratio = min(age_days / threshold, 1.5)
    return round(max(0.0, 1.0 - (ratio / 1.5)), 4)


def compute_confidence_score(*, source_reliability: float, freshness: float, geometry_quality: float, match_quality: float, completeness: float) -> float:
    s = get_settings()
    weighted = (
        source_reliability * s.confidence_weight_source_reliability
        + freshness * s.confidence_weight_freshness
        + max(0.0, min(1.0, geometry_quality)) * s.confidence_weight_geometry_quality
        + max(0.0, min(1.0, match_quality)) * s.confidence_weight_match_quality
        + max(0.0, min(1.0, completeness)) * s.confidence_weight_completeness
    )
    return round(weighted * 100.0, 2)


def should_require_review(
    *,
    confidence_score: float,
    match_method: str,
    distance_m: float | None = None,
    source_confidence_needs_review: bool = False,
) -> bool:
    if source_confidence_needs_review:
        return True
    if confidence_score < 60:
        return True
    if match_method == 'fuzzy_address':
        return True
    if match_method == 'point_nearest' and distance_m is not None and distance_m > 80:
        return True
    return False
