from app.quality.source_confidence_rules import (
    HIGH,
    LOW,
    MEDIUM,
    decide_confidence,
    normalize_parcel_key,
    should_route_to_review,
)


def test_missing_source_url_cannot_be_high_confidence():
    decision = decide_confidence({
        "source_url": "",
        "parcel_id": "abc-123",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
    })
    assert decision.level == MEDIUM
    assert "missing_source_url" in decision.reasons


def test_missing_parcel_specific_match_caps_confidence():
    decision = decide_confidence({"source_url": "https://example.test/source"})
    assert decision.level == MEDIUM
    assert "missing_parcel_specific_spatial_match" in decision.reasons


def test_verified_source_and_parcel_match_can_be_high_confidence():
    decision = decide_confidence({
        "source_url": "https://example.test/source",
        "parcel_id": "abc-123",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
    })
    assert decision.level == HIGH
    assert decision.score >= 0.9


def test_ambiguous_match_routes_to_review_and_low_confidence():
    record = {
        "source_url": "https://example.test/source",
        "parcel_id": "abc-123",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "ambiguous_match": True,
    }
    decision = decide_confidence(record)
    assert decision.level == LOW
    assert should_route_to_review(record) is True


def test_parcel_key_normalization_is_deterministic():
    assert normalize_parcel_key(" abC-123_def ") == "ABC 123 DEF"
