from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class VerificationLevel(str, Enum):
    review_required = "review_required"
    verified = "verified"


@dataclass(frozen=True)
class SaleLandVerificationDecision:
    level: VerificationLevel
    confidence: float
    confidence_breakdown: dict[str, Any] = field(default_factory=dict)
    missing_evidence: list[str] = field(default_factory=list)
    conflict_flags: list[str] = field(default_factory=list)
    display_polygon_warning: bool = False
    verified_sale_boundary: bool = False


def decide_sale_land_verification(record: dict[str, Any]) -> SaleLandVerificationDecision:
    missing: list[str] = []
    if not str(record.get("source_url") or "").strip():
        missing.append("source_url")
    if not record.get("geometry"):
        missing.append("geometry")

    if missing:
        return SaleLandVerificationDecision(
            level=VerificationLevel.review_required,
            confidence=45.0,
            confidence_breakdown={"missing_evidence_penalty": missing},
            missing_evidence=missing,
            display_polygon_warning=True,
            verified_sale_boundary=False,
        )

    return SaleLandVerificationDecision(
        level=VerificationLevel.verified,
        confidence=85.0,
        confidence_breakdown={"source_url": True, "geometry": True},
        verified_sale_boundary=True,
    )
