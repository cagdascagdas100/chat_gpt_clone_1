from app.quality.source_confidence_integration import (
    SOURCE_CONFIDENCE_REVIEW_ROUTE,
    build_review_route_payload,
    build_source_confidence_fields,
    with_source_confidence_fields,
)


def test_integration_fields_do_not_mutate_input_record():
    record = {
        "source_url": "https://example.test/source",
        "parcel_id": "abc-123",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
    }
    original = dict(record)

    enriched = with_source_confidence_fields(record)

    assert record == original
    assert enriched is not record
    assert enriched["source_confidence_level"] == "high"
    assert enriched["source_confidence_publishable_without_review"] is True


def test_missing_source_url_is_not_publishable_without_review():
    fields = build_source_confidence_fields(
        {
            "source_url": "",
            "parcel_id": "abc-123",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
        }
    )

    assert fields["source_confidence_level"] == "medium"
    assert fields["source_confidence_needs_review"] is True
    assert fields["source_confidence_review_route"] == SOURCE_CONFIDENCE_REVIEW_ROUTE
    assert fields["source_confidence_publishable_without_review"] is False
    assert "missing_source_url" in fields["source_confidence_reasons"]


def test_missing_parcel_specific_spatial_match_routes_to_review():
    payload = build_review_route_payload(
        {"source_url": "https://example.test/source"},
        origin="parcel_matching_pipeline",
    )

    assert payload is not None
    assert payload["origin"] == "parcel_matching_pipeline"
    assert payload["review_route"] == SOURCE_CONFIDENCE_REVIEW_ROUTE
    assert "missing_parcel_specific_spatial_match" in payload["source_confidence_reasons"]


def test_ambiguous_match_is_low_confidence_and_review_route():
    fields = build_source_confidence_fields(
        {
            "source_url": "https://example.test/source",
            "parcel_id": "abc-123",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "ambiguous_match": "yes",
        }
    )

    assert fields["source_confidence_level"] == "low"
    assert fields["source_confidence_needs_review"] is True
    assert fields["source_confidence_review_route"] == SOURCE_CONFIDENCE_REVIEW_ROUTE
    assert fields["source_confidence_publishable_without_review"] is False
    assert "ambiguous_parcel_match" in fields["source_confidence_reasons"]


def test_verified_source_and_parcel_match_has_no_review_payload():
    record = {
        "source_url": "https://example.test/source",
        "parcel_ref": " abC-123_def ",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
    }

    fields = build_source_confidence_fields(record)
    payload = build_review_route_payload(record, origin="source_ingestion_pipeline")

    assert fields["source_confidence_level"] == "high"
    assert fields["source_confidence_needs_review"] is False
    assert fields["source_confidence_review_route"] is None
    assert fields["source_confidence_normalized_parcel_key"] == "ABC 123 DEF"
    assert payload is None
