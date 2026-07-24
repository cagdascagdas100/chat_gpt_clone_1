#!/usr/bin/env python3
"""Semantic gate V3: validate official annual air releases and normalize mass units.

Accepted rows preserve raw value/unit and add normalized_kg_per_year. Missing or
below-threshold data is never converted to zero. Parcel binding remains pending
verified geometry.
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V2 as v2

SLOT_ID = "gas_emissions_1"
INPUT = Path("england_map_web/data/aays_21_slots/gas_emissions_1/facility_emission_review_latest.json")
REPORT = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_facility_emission_semantic_gate_latest.json")
STATUS = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_facility_emission_semantic_gate_latest.json")
WEB = Path("england_map_web/data/aays_21_slots/gas_emissions_1/facility_emission_semantic_gate_latest.json")

KG_UNITS = {"kg", "kilogram", "kilograms", "kg/year", "kg/yr", "kg per year", "kg/a"}
TONNE_UNITS = {"t", "tonne", "tonnes", "metric tonne", "metric tonnes", "t/year", "t/yr", "t per year", "tonne/year", "tonnes/year"}
GRAM_UNITS = {"g", "gram", "grams", "g/year", "g/yr", "g per year"}
BASE_REVIEW = v2.review


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_unit(value: Any, unit: Any) -> tuple[float | None, str | None]:
    numeric = v2.numeric_value(value)
    if numeric is None or not math.isfinite(numeric):
        return None, "NON_FINITE_OR_NON_NUMERIC_RELEASE_VALUE"
    text = " ".join(str(unit or "").strip().casefold().replace("per annum", "per year").split())
    if text in KG_UNITS:
        return numeric, None
    if text in TONNE_UNITS:
        return numeric * 1000.0, None
    if text in GRAM_UNITS:
        return numeric * 0.001, None
    return None, "UNIT_NOT_RECOGNISED_AS_ANNUAL_MASS"


def review(row: dict[str, Any]) -> dict[str, Any]:
    result = BASE_REVIEW(row)
    raw_value = v2.first(row, "value", "release_value", "amount", "quantity")
    raw_unit = v2.first(row, "unit", "release_unit", "quantity_unit")
    normalized, unit_error = normalize_unit(raw_value, raw_unit)
    reasons = list(result.get("reasons") or [])
    if unit_error and unit_error not in reasons:
        reasons.append(unit_error)
    accepted = not reasons
    result.update({
        "accepted_as_facility_air_emission": accepted,
        "reasons": reasons,
        "raw_release_value": raw_value,
        "raw_release_unit": raw_unit,
        "normalized_kg_per_year": normalized if accepted else None,
        "canonical_unit": "kg/year" if accepted else None,
        "output_semantics": "FACILITY_ANNUAL_AIR_MASS_KG_PER_YEAR_NOT_PARCEL_VALUE" if accepted else "REJECTED_NON_AIR_NON_MASS_OR_INCOMPLETE_CANDIDATE",
        "parcel_binding_status": "PENDING_VERIFIED_GEOMETRY",
    })
    return result


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID", SLOT_ID) != SLOT_ID:
        raise RuntimeError("WRONG_SLOT_CONTEXT")
    if not INPUT.exists():
        payload = {
            "schema_version": 3,
            "architecture_version": 3,
            "slot_id": SLOT_ID,
            "generated_at": utc_now(),
            "status": "BLOCKED_INPUT_FACILITY_REVIEW_NOT_AVAILABLE",
            "input_path": str(INPUT),
            "reviewed_candidates": 0,
            "accepted_facility_air_emission_rows": 0,
            "measured_parcel_emission_rows": 0,
            "blocker": "FACILITY_EMISSION_REVIEW_INPUT_MISSING",
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        for path in (REPORT, STATUS, WEB):
            write(path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    doc = json.loads(INPUT.read_text(encoding="utf-8-sig"))
    rows = v2.extract_rows(doc)
    reviews = [review(row) for row in rows]
    accepted = [item for item in reviews if item["accepted_as_facility_air_emission"]]
    payload = {
        "schema_version": 3,
        "architecture_version": 3,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "status": "PASS_ANNUAL_AIR_MASS_SEMANTIC_GATE_V3" if rows else "BLOCKED_NO_CANDIDATE_ROWS_TO_REVIEW",
        "input_path": str(INPUT),
        "reviewed_candidates": len(reviews),
        "accepted_facility_air_emission_rows": len(accepted),
        "rejected_candidates": len(reviews) - len(accepted),
        "reviews": reviews,
        "accepted_mass_unit_families": ["kilogram", "tonne", "gram"],
        "canonical_unit": "kg/year",
        "valid_determination_method_classes": ["CALCULATED", "ESTIMATED", "MEASURED", "UNSPECIFIED"],
        "absence_policy": "MISSING_OR_BELOW_THRESHOLD_DATA_IS_NO_DATA_AND_IS_NEVER_INFERRED_AS_ZERO",
        "measured_parcel_emission_rows": 0,
        "verified_parcel_bindings": 0,
        "parcel_binding_gate_passed": False,
        "quality_contract": "Official UK PRTR or EA Pollution Inventory annual release to air plus facility, year, pollutant, non-negative finite mass and recognised annual mass unit. Raw value/unit are preserved and accepted rows are normalized to kg/year.",
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    for path in (REPORT, STATUS, WEB):
        write(path, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
