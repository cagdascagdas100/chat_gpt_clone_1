from __future__ import annotations

from fastapi import APIRouter

from app.quality.source_confidence_integration import (
    build_review_route_payload,
    build_source_confidence_fields,
)
from app.services.sale_land_verification import decide_sale_land_verification

router = APIRouter(prefix="/verification/sale-land", tags=["sale-land-verification"])


@router.post("/classify")
def classify_sale_land_record(record: dict):
    decision = decide_sale_land_verification(record)
    source_confidence = build_source_confidence_fields(record)
    review_payload = build_review_route_payload(record, origin="sale_land_verification_route")
    return {
        "verification_level": decision.level.value,
        "confidence": decision.confidence,
        "confidence_breakdown": decision.confidence_breakdown,
        "missing_evidence": decision.missing_evidence,
        "conflict_flags": decision.conflict_flags,
        "display_polygon_warning": decision.display_polygon_warning,
        "verified_sale_boundary": decision.verified_sale_boundary,
        "source_confidence": source_confidence,
        "source_confidence_review_payload": review_payload,
    }
