"""Evidence-first source confidence guard rules.

Safe module:
- no database writes
- no network calls
- no production deployment behavior
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


HIGH = "high"
MEDIUM = "medium"
LOW = "low"


@dataclass(frozen=True)
class ConfidenceDecision:
    level: str
    score: float
    reasons: tuple[str, ...]


def normalize_source_url(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "n/a", "na"}:
        return None
    return text


def normalize_parcel_key(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().upper()
    if not text:
        return None
    return " ".join(text.replace("_", " ").replace("-", " ").split())


def has_parcel_specific_spatial_match(record: Mapping[str, Any]) -> bool:
    for key in (
        "parcel_specific_spatial_match",
        "has_parcel_specific_spatial_match",
        "spatial_match",
        "geometry_match",
    ):
        value = record.get(key)
        if isinstance(value, bool) and value:
            return True
        if isinstance(value, str) and value.strip().lower() in {"true", "yes", "1", "parcel"}:
            return True

    parcel_id = normalize_parcel_key(
        record.get("parcel_id")
        or record.get("matched_parcel_id")
        or record.get("uprn")
        or record.get("cadastre_id")
    )
    geometry = record.get("geometry") or record.get("centroid") or record.get("geom")
    return bool(parcel_id and geometry)


def decide_confidence(record: Mapping[str, Any]) -> ConfidenceDecision:
    reasons: list[str] = []

    if not normalize_source_url(record.get("source_url")):
        reasons.append("missing_source_url")

    if not has_parcel_specific_spatial_match(record):
        reasons.append("missing_parcel_specific_spatial_match")

    ambiguous = record.get("ambiguous_match") or record.get("needs_review")
    if isinstance(ambiguous, str):
        ambiguous = ambiguous.strip().lower() in {"true", "yes", "1"}

    if ambiguous:
        reasons.append("ambiguous_parcel_match")

    if "ambiguous_parcel_match" in reasons:
        return ConfidenceDecision(level=LOW, score=0.25, reasons=tuple(reasons))

    if reasons:
        return ConfidenceDecision(level=MEDIUM, score=0.55, reasons=tuple(reasons))

    return ConfidenceDecision(level=HIGH, score=0.9, reasons=("source_and_parcel_match_verified",))


def should_route_to_review(record: Mapping[str, Any]) -> bool:
    decision = decide_confidence(record)
    return decision.level != HIGH or "ambiguous_parcel_match" in decision.reasons
