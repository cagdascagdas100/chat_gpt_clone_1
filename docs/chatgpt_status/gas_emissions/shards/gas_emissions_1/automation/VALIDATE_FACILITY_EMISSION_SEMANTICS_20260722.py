#!/usr/bin/env python3
"""Final read-only semantic gate for gas_emissions_1 facility-emission candidates.

Only an official UK PRTR or Environment Agency Pollution Inventory record with
explicit year, pollutant, environmental medium, numeric value and unit may be
published as a facility-emission row. Permit limits, design values, estimates,
avoided emissions and BAT appraisal values are rejected. Parcel binding always
remains pending until verified HMLR geometry exists.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_1"
INPUT = Path("england_map_web/data/aays_21_slots/gas_emissions_1/facility_emission_review_latest.json")
REPORT = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_facility_emission_semantic_gate_latest.json")
STATUS = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_facility_emission_semantic_gate_latest.json")
WEB = Path("england_map_web/data/aays_21_slots/gas_emissions_1/facility_emission_semantic_gate_latest.json")

REJECT_TERMS = (
    "permit limit", "emission limit", "elv", "design capacity", "permitted capacity",
    "operator estimate", "estimated", "modelled", "modeled", "avoided emission",
    "avoided co2", "co2 reduced", "net figure", "surrogate level", "bat appraisal",
    "application design", "monitoring required", "not measured", "not metered",
    "gwp credit", "gwp debit", "installation configuration", "planning limit",
)
OFFICIAL_SOURCE_TERMS = ("uk prtr", "pollutant release and transfer register", "pollution inventory")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def text_of(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True).casefold()


def first(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def numeric(value: Any) -> bool:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        return bool(re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", cleaned))
    return False


def extract_rows(doc: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("accepted_rows", "facility_emission_rows", "rows", "candidates", "reviewed_candidates"):
        value = doc.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def review(row: dict[str, Any]) -> dict[str, Any]:
    text = text_of(row)
    source = str(first(row, "source_name", "source", "dataset", "official_source") or "").casefold()
    year = first(row, "reporting_year", "year", "calendar_year")
    pollutant = first(row, "pollutant", "pollutant_name", "substance")
    medium = first(row, "medium", "environmental_medium", "release_medium")
    value = first(row, "value", "release_value", "amount", "quantity")
    unit = first(row, "unit", "release_unit", "quantity_unit")
    reasons: list[str] = []
    if not any(term in source or term in text for term in OFFICIAL_SOURCE_TERMS):
        reasons.append("SOURCE_NOT_EXPLICITLY_UK_PRTR_OR_EA_POLLUTION_INVENTORY")
    if any(term in text for term in REJECT_TERMS):
        reasons.append("ESTIMATE_LIMIT_DESIGN_AVOIDED_OR_BAT_VALUE")
    if not (isinstance(year, int) and 2007 <= year <= 2100 or isinstance(year, str) and re.fullmatch(r"20\d{2}", year.strip())):
        reasons.append("REPORTING_YEAR_MISSING_OR_INVALID")
    if not pollutant:
        reasons.append("POLLUTANT_MISSING")
    if not medium:
        reasons.append("ENVIRONMENTAL_MEDIUM_MISSING")
    if not numeric(value):
        reasons.append("NUMERIC_RELEASE_VALUE_MISSING")
    if not unit:
        reasons.append("RELEASE_UNIT_MISSING")
    accepted = not reasons
    return {
        "candidate": row,
        "accepted_as_facility_emission": accepted,
        "reasons": reasons,
        "output_semantics": "FACILITY_EMISSION_ROW_NOT_PARCEL_VALUE" if accepted else "REJECTED_NON_MEASURED_OR_INCOMPLETE_CANDIDATE",
        "parcel_binding_status": "PENDING_HMLR_GEOMETRY",
    }


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID", SLOT_ID) != SLOT_ID:
        raise RuntimeError("WRONG_SLOT_CONTEXT")
    if not INPUT.exists():
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "generated_at": utc_now(),
            "status": "BLOCKED_INPUT_FACILITY_REVIEW_NOT_AVAILABLE",
            "input_path": str(INPUT),
            "reviewed_candidates": 0,
            "accepted_facility_emission_rows": 0,
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
    rows = extract_rows(doc)
    reviews = [review(row) for row in rows]
    accepted = [item for item in reviews if item["accepted_as_facility_emission"]]
    payload = {
        "schema_version": 1,
        "architecture_version": 3,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "status": "PASS_SEMANTIC_GATE" if rows else "BLOCKED_NO_CANDIDATE_ROWS_TO_REVIEW",
        "input_path": str(INPUT),
        "reviewed_candidates": len(reviews),
        "accepted_facility_emission_rows": len(accepted),
        "rejected_candidates": len(reviews) - len(accepted),
        "reviews": reviews,
        "measured_parcel_emission_rows": 0,
        "verified_parcel_bindings": 0,
        "parcel_binding_gate_passed": False,
        "quality_contract": "Official UK PRTR or EA Pollution Inventory plus explicit year, pollutant, medium, numeric value and unit. Limits, estimates, modelled or avoided emissions and design values are rejected.",
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
