#!/usr/bin/env python3
"""Semantic gate V4: reject permit/performance mass values from air releases.

V3 already validates official source, facility, reporting year, pollutant, air
medium, finite non-negative value, annual mass unit and C/E/M/U method class.
V4 additionally rejects fuel/reagent consumption, storage, capacity, operating
hours and monitoring/performance records even when their units are tonnes/year.
"""
from __future__ import annotations

import json
from typing import Any

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V3 as v3

BASE_REVIEW = v3.review
CONTEXT_KEYS = (
    "record_type", "record_category", "section", "parameter", "field", "metric",
    "measure", "description", "semantics", "output_semantics",
)
CONTEXT_REJECT_TERMS = (
    "gas oil usage", "fuel usage", "fuel consumption", "adblue", "urea usage",
    "reagent consumption", "operating hours", "hours per sbg", "number of runs",
    "minutes per run", "maintenance operation", "emergency operation",
    "storage capacity", "fuel storage", "permitted storage", "design capacity",
    "permitted capacity", "thermal input", "throughput", "performance parameter",
    "process monitoring", "monitoring frequency", "no limit set", "emission limit",
    "permit limit", "mcpd limit", "abatement efficiency", "design concentration",
)


def context_text(row: dict[str, Any]) -> str:
    selected = {key: row.get(key) for key in CONTEXT_KEYS if row.get(key) not in (None, "")}
    return json.dumps(selected, ensure_ascii=False, sort_keys=True).casefold()


def review(row: dict[str, Any]) -> dict[str, Any]:
    result = BASE_REVIEW(row)
    reasons = list(result.get("reasons") or [])
    text = context_text(row)
    matched = sorted({term for term in CONTEXT_REJECT_TERMS if term in text})
    if matched and "PERMIT_PERFORMANCE_CONSUMPTION_OR_OPERATION_CONTEXT" not in reasons:
        reasons.append("PERMIT_PERFORMANCE_CONSUMPTION_OR_OPERATION_CONTEXT")
    accepted = not reasons
    result.update({
        "accepted_as_facility_air_emission": accepted,
        "reasons": reasons,
        "context_reject_terms_matched": matched,
        "normalized_kg_per_year": result.get("normalized_kg_per_year") if accepted else None,
        "canonical_unit": "kg/year" if accepted else None,
        "output_semantics": "FACILITY_ANNUAL_AIR_MASS_KG_PER_YEAR_NOT_PARCEL_VALUE" if accepted else "REJECTED_PERMIT_PERFORMANCE_NON_AIR_NON_MASS_OR_INCOMPLETE_CANDIDATE",
        "parcel_binding_status": "PENDING_VERIFIED_GEOMETRY",
    })
    return result


if __name__ == "__main__":
    v3.review = review
    raise SystemExit(v3.main())
