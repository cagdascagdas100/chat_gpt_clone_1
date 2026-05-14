"""Side-effect free integration helpers for source confidence decisions.

This module adapts app.quality.source_confidence_rules into pipeline-friendly
payloads without performing database writes, network calls, queue mutation,
secret changes, migrations, or deployment actions.
"""

from __future__ import annotations

from typing import Any, Mapping

from app.quality.source_confidence_rules import (
    HIGH,
    decide_confidence,
    normalize_parcel_key,
    normalize_source_url,
    should_route_to_review,
)


SOURCE_CONFIDENCE_REVIEW_ROUTE = "source_confidence_review"


_PARCEL_KEYS = (
    "parcel_id",
    "matched_parcel_id",
    "parcel_ref",
    "uprn",
    "cadastre_id",
)


def _first_present(record: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def _canonical_confidence_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copied record with adapter-only aliases mapped safely.

    source_confidence_rules.has_parcel_specific_spatial_match currently treats
    parcel_id, matched_parcel_id, uprn and cadastre_id as parcel identifiers.
    Real pipeline payloads may expose parcel_ref instead, so the adapter maps
    parcel_ref to parcel_id only in the copied evaluation view.
    """

    canonical = dict(record)

    if not _first_present(canonical, ("parcel_id", "matched_parcel_id", "uprn", "cadastre_id")):
        parcel_ref = _first_present(canonical, ("parcel_ref",))
        if parcel_ref is not None:
            canonical["parcel_id"] = parcel_ref

    return canonical


def build_source_confidence_fields(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return normalized confidence fields for downstream pipelines.

    Contract:
    - does not mutate input record
    - does not write to storage
    - does not call network
    - does not enqueue review jobs
    """

    canonical = _canonical_confidence_record(record)
    decision = decide_confidence(canonical)
    needs_review = should_route_to_review(canonical)

    parcel_key = normalize_parcel_key(_first_present(canonical, _PARCEL_KEYS))

    return {
        "source_confidence_level": decision.level,
        "source_confidence_score": decision.score,
        "source_confidence_reasons": list(decision.reasons),
        "source_confidence_needs_review": needs_review,
        "source_confidence_review_route": (
            SOURCE_CONFIDENCE_REVIEW_ROUTE if needs_review else None
        ),
        "source_confidence_source_url": normalize_source_url(canonical.get("source_url")),
        "source_confidence_normalized_parcel_key": parcel_key,
        "source_confidence_publishable_without_review": decision.level == HIGH
        and not needs_review,
    }


def with_source_confidence_fields(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copied record enriched with source confidence metadata."""

    enriched = dict(record)
    enriched.update(build_source_confidence_fields(record))
    return enriched


def build_review_route_payload(
    record: Mapping[str, Any],
    *,
    origin: str,
) -> dict[str, Any] | None:
    """Return review-route payload if confidence rules require review.

    The function only returns data. The caller may pass this payload to an
    existing review service, but this helper intentionally performs no queue
    mutation.
    """

    fields = build_source_confidence_fields(record)
    if not fields["source_confidence_needs_review"]:
        return None

    return {
        "origin": origin,
        "review_route": fields["source_confidence_review_route"],
        "source_confidence_level": fields["source_confidence_level"],
        "source_confidence_score": fields["source_confidence_score"],
        "source_confidence_reasons": fields["source_confidence_reasons"],
        "source_url": fields["source_confidence_source_url"],
        "normalized_parcel_key": fields["source_confidence_normalized_parcel_key"],
    }
