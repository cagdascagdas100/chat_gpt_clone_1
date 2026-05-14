from app.api.routes.aays_sale_land_verification import classify_sale_land_record


def test_classify_sale_land_record_includes_source_confidence_metadata() -> None:
    payload = {
        "source_url": "",
        "parcel_ref": "abc-123",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
    }

    result = classify_sale_land_record(payload)

    assert "source_confidence" in result
    assert result["source_confidence"]["needs_review"] is True
    assert result["source_confidence"]["review_route"] == "source_confidence_review"
    assert result["source_confidence"]["origin"] == "sale_land_verification_route"
    assert result["source_confidence_review_payload"] is not None
    assert result["source_confidence_review_payload"]["origin"] == "sale_land_verification_route"
    assert result["source_confidence_review_payload"]["source_confidence"]["needs_review"] is True

