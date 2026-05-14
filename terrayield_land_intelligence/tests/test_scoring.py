from __future__ import annotations

import datetime as dt

from app.services.scoring import compute_confidence_score, freshness_score, should_require_review, source_reliability_score


def test_source_reliability_score_prefers_official_sources() -> None:
    assert source_reliability_score('homes_england_landhub') > source_reliability_score('market_listing_adapter')



def test_freshness_score_decreases_with_age() -> None:
    now = dt.datetime(2026, 3, 30, tzinfo=dt.UTC)
    recent = freshness_score(now - dt.timedelta(days=5), 'homes_england_landhub', now=now)
    stale = freshness_score(now - dt.timedelta(days=120), 'homes_england_landhub', now=now)
    assert recent > stale



def test_confidence_score_respects_weighting() -> None:
    score = compute_confidence_score(
        source_reliability=0.95,
        freshness=0.9,
        geometry_quality=0.85,
        match_quality=0.8,
        completeness=0.7,
    )
    assert 0 < score <= 100
    assert round(score, 2) == score



def test_should_require_review_for_fuzzy_and_low_confidence() -> None:
    assert should_require_review(confidence_score=55, match_method='polygon_intersect') is True
    assert should_require_review(confidence_score=85, match_method='fuzzy_address') is True
    assert should_require_review(confidence_score=85, match_method='point_nearest', distance_m=120) is True
    assert should_require_review(confidence_score=85, match_method='polygon_intersect') is False
    assert should_require_review(
        confidence_score=95,
        match_method='polygon_intersect',
        source_confidence_needs_review=True,
    ) is True
