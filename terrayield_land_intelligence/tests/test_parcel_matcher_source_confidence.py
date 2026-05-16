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


def test_parcel_matcher_reports_partial_lineage_without_source_url() -> None:
    record = SimpleNamespace(
        parcel_ref="17103798",
        source_name="hmlr_inspire",
        source_record_id="england:east-devon-district-council:17103798",
        source_updated_at="2026-04-30",
        site_geometry=None,
        point_geometry=None,
    )
    config = {"polygon_attr": "site_geometry", "point_attr": "point_geometry"}
    candidate = MatchCandidate(
        parcel_id=477,
        match_method="metadata_inspire_exact",
        match_score=99.8,
        requires_review=False,
    )

    fields = _build_match_source_confidence_fields(record, config, candidate)

    assert fields["source_lineage_status"] == "partial_lineage_no_source_url"
    assert fields["source_lineage_missing_reason"] == "missing_source_url_high_confidence_withheld"
    assert "source_name" in fields["source_lineage_fields_present"]
    assert "source_record_id" in fields["source_lineage_fields_present"]
    assert "parcel_ref" in fields["source_lineage_fields_present"]
    assert fields["source_confidence_needs_review"] is True
