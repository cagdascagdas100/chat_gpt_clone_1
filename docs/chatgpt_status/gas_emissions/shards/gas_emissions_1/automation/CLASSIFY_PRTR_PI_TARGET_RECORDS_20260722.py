#!/usr/bin/env python3
"""Classify gas_emissions_1 PRTR/PI target candidates without parcel attribution.

Input is the read-only binary hydration result. A facility-emission candidate is
published only when an official PRTR/PI record contains an identity match plus
explicit year, pollutant, value and unit fields. Permit limits and missing values
are never promoted. HMLR geometry is not inferred.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "gas_emissions_1"
INPUT_REL = "england_map_web/data/aays_21_slots/gas_emissions_1/binary_target_parse_result_latest.json"
REPORT_REL = "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_facility_emission_review_latest.json"
STATUS_REL = "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_facility_emission_review_latest.json"
WEB_REL = "england_map_web/data/aays_21_slots/gas_emissions_1/facility_emission_review_latest.json"

KEY_ALIASES = {
    "facility": ("facilityname", "installationname", "sitename", "reportingfacility", "facility"),
    "operator": ("operatorname", "parentcompanyname", "companyname", "operator"),
    "permit": ("permitnumber", "permitreference", "permit", "authorisationnumber"),
    "year": ("reportingyear", "year", "calendar_year"),
    "pollutant": ("pollutantname", "pollutant", "substance", "parameter"),
    "medium": ("mediumname", "medium", "environmentalmedium", "release_to"),
    "value": ("totalpollutantquantitykg", "quantitykg", "releasequantity", "pollutantquantity", "totalquantity", "value", "amount"),
    "unit": ("unitcode", "unit", "quantityunit", "reportedunit"),
    "method": ("methodcode", "method", "determinationmethod", "measurementmethod"),
    "easting": ("easting", "xcoordinate", "x_coord"),
    "northing": ("northing", "ycoordinate", "y_coord"),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lon", "lng"),
}
TARGETS = (
    "thames gateway", "07933078", "hp3504ma", "cp3737cv", "rm9 6lf", "tgl419520",
    "cory barking", "01600851", "mcgrath bros", "tp3697np", "fb3306hg", "ig11 0ds",
    "gb3003mb", "kb3006sw", "jb3102ca", "gb3438rl",
)
LIMIT_MARKERS = ("limit", "elv", "permit condition", "maximum permitted")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).casefold())


def scalar_text(value: Any) -> str:
    if isinstance(value, list):
        return " | ".join(scalar_text(v) for v in value)
    if isinstance(value, dict):
        return " | ".join(f"{k}:{scalar_text(v)}" for k, v in value.items())
    return "" if value is None else str(value).strip()


def flatten_dict(value: Any, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten_dict(child, child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            out.update(flatten_dict(child, f"{prefix}[{index}]"))
    else:
        out[prefix] = scalar_text(value)
    return out


def candidate_records(document: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    extracts = document.get("extracts") or {}
    if isinstance(extracts, dict):
        for source_id, block in extracts.items():
            for record in (block or {}).get("candidates") or []:
                if isinstance(record, dict):
                    yield str(source_id), record
    hmlr = document.get("hmlr") or {}
    for record in hmlr.get("candidates") or []:
        if isinstance(record, dict):
            yield "hmlr_inspire_barking_dagenham", record


def field(flat: dict[str, str], semantic: str) -> str | None:
    aliases = KEY_ALIASES[semantic]
    for path, value in flat.items():
        key = norm_key(path.split(".")[-1].split("[")[0])
        if any(key == alias or key.endswith(alias) for alias in aliases) and value:
            return value
    return None


def numeric(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.replace(",", "").strip()
    match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID", SLOT_ID) != SLOT_ID:
        raise RuntimeError("WRONG_SLOT_CONTEXT")
    root = Path.cwd()
    input_path = root / INPUT_REL
    if not input_path.exists():
        raise FileNotFoundError(INPUT_REL)
    document = json.loads(input_path.read_text(encoding="utf-8"))
    reviewed: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for source_id, record in candidate_records(document):
        flat = flatten_dict(record)
        joined = " ".join(flat.values()).casefold()
        matched_targets = sorted({token for token in TARGETS if token in joined})
        values = {name: field(flat, name) for name in KEY_ALIASES}
        explicit_value = numeric(values["value"])
        limit_like = any(marker in joined for marker in LIMIT_MARKERS)
        is_prtr_pi = source_id in {"uk_prtr_2024_xml", "uk_prtr_registry_zip", "ea_pi_2024_zip"}
        requirements = {
            "official_prtr_or_pi_source": is_prtr_pi,
            "target_identity_present": bool(matched_targets),
            "year_present": bool(values["year"]),
            "pollutant_present": bool(values["pollutant"]),
            "numeric_value_present": explicit_value is not None,
            "unit_present": bool(values["unit"]),
            "not_permit_limit_text": not limit_like,
        }
        row = {
            "source_id": source_id,
            "matched_targets": matched_targets,
            "facility": values["facility"],
            "operator": values["operator"],
            "permit": values["permit"],
            "reporting_year": values["year"],
            "pollutant": values["pollutant"],
            "medium": values["medium"],
            "reported_value": explicit_value,
            "reported_value_raw": values["value"],
            "unit": values["unit"],
            "method": values["method"],
            "easting": values["easting"],
            "northing": values["northing"],
            "latitude": values["latitude"],
            "longitude": values["longitude"],
            "requirements": requirements,
            "parcel_binding_status": "PENDING_HMLR_GEOMETRY",
            "semantics": "FACILITY_EMISSION_ROW_NOT_PARCEL_VALUE",
        }
        if all(requirements.values()):
            row["confidence"] = 99
            reviewed.append(row)
        else:
            row["rejection_reasons"] = [name for name, passed in requirements.items() if not passed]
            rejected.append(row)
    payload = {
        "schema_version": 1,
        "architecture_version": 3,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "status": "PASS_EXPLICIT_FACILITY_EMISSION_ROWS_CLASSIFIED" if reviewed else "NO_EXPLICIT_FACILITY_EMISSION_ROW_YET",
        "input_path": INPUT_REL,
        "facility_emission_rows": reviewed,
        "rejected_candidate_rows": rejected,
        "counts": {
            "input_target_candidates": len(reviewed) + len(rejected),
            "explicit_facility_emission_rows": len(reviewed),
            "rejected_or_incomplete_rows": len(rejected),
            "measured_parcel_emission_rows": 0,
            "verified_parcel_bindings": 0,
        },
        "quality_gate": "Explicit official PRTR/PI year, pollutant, numeric value and unit are mandatory. Permit limits are excluded. HMLR geometry is mandatory for parcel attribution.",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    for rel in (REPORT_REL, STATUS_REL, WEB_REL):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
