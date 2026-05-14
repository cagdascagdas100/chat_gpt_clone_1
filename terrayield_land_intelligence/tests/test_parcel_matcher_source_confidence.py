from types import SimpleNamespace

from app.etl.match.parcel_matcher import MatchCandidate, _build_match_source_confidence_fields


def test_parcel_matcher_source_confidence_requires_review_without_source_url() -> None:
    record = SimpleNamespace(parcel_ref="abc-123", site_geometry=None, point_geometry=None)
    config = {"polygon_attr": "site_geometry", "point_attr": "point_geometry"}
    candidate = MatchCandidate(parcel_id=101, match_method="fuzzy_address", match_score=70.0)

    fields = _build_match_source_confidence_fields(record, config, candidate)

    assert fields["source_confidence_needs_review"] is True
    assert "missing_source_url" in fields["source_confidence_reasons"]


def test_parcel_matcher_source_confidence_publishable_when_spatial_and_source_url_present() -> None:
    record = SimpleNamespace(source_url="https://example.test/source", parcel_ref="abc-123", site_geometry="geom", point_geometry=None)
    config = {"polygon_attr": "site_geometry", "point_attr": "point_geometry"}
    candidate = MatchCandidate(parcel_id=202, match_method="point_within", match_score=88.0)

    fields = _build_match_source_confidence_fields(record, config, candidate)

    assert fields["source_confidence_level"] == "high"
    assert fields["source_confidence_needs_review"] is False
    assert fields["source_confidence_publishable_without_review"] is True
