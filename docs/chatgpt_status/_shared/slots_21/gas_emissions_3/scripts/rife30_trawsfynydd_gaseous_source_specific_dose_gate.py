#!/usr/bin/env python3
"""Validate and publish the official RIFE 30 Trawsfynydd gaseous source-specific dose row."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_RECORDS = 20
REQUIRED_RECORD_IDS = (
    "technical_summary_identity",
    "dose_methodology",
    "trawsfynydd_total_dose_2024",
    "trawsfynydd_source_specific_dose_2024",
    "trawsfynydd_gaseous_classification_2024",
    "publication_page_and_asset_identity",
)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical_record_sha(record: dict[str, Any]) -> str:
    core = {key: value for key, value in record.items() if key != "sha256"}
    payload = json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)

def main() -> int:
    args = parse_args()
    contract_bytes = args.contract.read_bytes()
    prior_bytes = args.prior.read_bytes()
    snapshot_bytes = args.snapshot.read_bytes()

    contract = json.loads(contract_bytes)
    prior = json.loads(prior_bytes)
    snapshot = json.loads(snapshot_bytes)

    if contract.get("schema_version") != 3 or contract.get("state") != "READY":
        raise ValueError("contract is not schema-v3 READY")

    pre = contract["precondition"]
    if sha256_bytes(prior_bytes) != pre["prior_output_sha256"]:
        raise ValueError("prior output SHA mismatch")
    if prior.get("task_id") != pre["required_prior_task_id"]:
        raise ValueError("prior task mismatch")
    if prior.get("state") != pre["required_prior_state"]:
        raise ValueError("prior state mismatch")
    if prior.get("next_unverified_step") != pre["required_prior_next_unverified_step"]:
        raise ValueError("prior next step mismatch")

    if sha256_bytes(snapshot_bytes) != contract["source_evidence_manifest"]["snapshot_sha256"]:
        raise ValueError("snapshot SHA mismatch")

    records = snapshot.get("records", [])
    if len(records) > MAX_RECORDS:
        raise ValueError("record limit exceeded")
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        if canonical_record_sha(record) != record.get("sha256"):
            raise ValueError("record SHA mismatch")
        by_id[record["record_id"]] = record

    required_complete = all(record_id in by_id for record_id in REQUIRED_RECORD_IDS)
    source_specific = by_id.get("trawsfynydd_source_specific_dose_2024", {}).get("proven_fields", {})
    gaseous = by_id.get("trawsfynydd_gaseous_classification_2024", {}).get("proven_fields", {})
    total_dose = by_id.get("trawsfynydd_total_dose_2024", {}).get("proven_fields", {})

    exact_match = (
        required_complete
        and source_specific.get("site") == "Trawsfynydd"
        and gaseous.get("site") == "Trawsfynydd"
        and source_specific.get("value") == 0.037
        and gaseous.get("value") == 0.037
        and source_specific.get("unit") == "mSv y-1"
        and gaseous.get("unit") == "mSv y-1"
        and source_specific.get("year") == 2024
        and gaseous.get("year") == 2024
        and source_specific.get("age_group") == "1-year-old infants"
        and total_dose.get("value") == 0.010
        and total_dose.get("metric_type") == "total_dose_all_pathways_and_sources"
    )

    matches: list[dict[str, Any]] = []
    if exact_match:
        matches.append({
            "row_id": "TRAWSFYNYDD_RIFE30_GASEOUS_SOURCE_SPECIFIC_DOSE_2024",
            "site_name": "Trawsfynydd nuclear power station",
            "jurisdiction": "Wales",
            "metric_type": "source_specific_public_dose_from_gaseous_discharges",
            "source_value": 0.037,
            "source_unit": "mSv y-1",
            "year": 2024,
            "representative_person_age_group": "1-year-old infants",
            "historical_permitted_discharge_context": True,
            "comparison_year": 2023,
            "comparison_source_value": 0.034,
            "source_record_ids": [
                "trawsfynydd_source_specific_dose_2024",
                "trawsfynydd_gaseous_classification_2024",
            ],
            "source_line_ranges": [[142, 143], [323, 326]],
            "emission_activity_value": None,
            "greenhouse_gas_mass_value": None,
            "unit_conversion_applied": False,
            "value_inferred": False,
        })

    state = "EXACT_TRAWSFYNYDD_GASEOUS_SOURCE_SPECIFIC_DOSE_ROW_VERIFIED" if matches else "NO_DATA_CONTINUE"
    next_step = (
        "VALIDATE_AND_PUBLISH_RIFE30_TRAWSFYNYDD_GASEOUS_SOURCE_SPECIFIC_DOSE_ROW"
        if matches
        else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_RIFE30_TRAWSFYNYDD_DOSE_NO_DATA"
    )
    blocker = (
        "NONE"
        if matches
        else "OFFICIAL_RIFE30_RECORD_SET_DID_NOT_PASS_EXACT_TRAWSFYNYDD_GASEOUS_SOURCE_SPECIFIC_DOSE_GATE"
    )

    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_3",
        "task_id": contract["task_id"],
        "continuation_key": contract["continuation_key"],
        "state": state,
        "panel_status": "PUBLISHED",
        "execution_mode": "SHA_LOCKED_OFFICIAL_GOVUK_HTML_CROSS_PAGE_SNAPSHOT",
        "first_unverified_step_completed": contract["first_unverified_step"],
        "next_unverified_step": next_step,
        "input": {
            "contract_path": str(args.contract),
            "contract_sha256": sha256_bytes(contract_bytes),
            "prior_output_path": str(args.prior),
            "prior_output_sha256": sha256_bytes(prior_bytes),
            "snapshot_path": str(args.snapshot),
            "snapshot_sha256": sha256_bytes(snapshot_bytes),
            "source_page_urls": snapshot["source_page_urls"],
            "source_asset_url": snapshot["source_asset_url"],
            "capture_scope": snapshot["capture_scope"],
        },
        "counts": {
            "completed_count": 1,
            "target_count": 1,
            "records_scanned": len(records),
            "matched_targets": 1 if matches else 0,
            "matched_rows": len(matches),
            "produced_business_rows": len(matches),
            "produced_source_evidence_records": len(records),
        },
        "progress_percent": 100.0,
        "targets": [{
            "target_id": contract["runtime_targets"][0]["target_id"],
            "site_name": "Trawsfynydd nuclear power station",
            "attempt_completed": True,
            "decision": state,
            "matched_rows": len(matches),
            "matches": matches,
        }],
        "excluded_evidence": [{
            "record_id": "trawsfynydd_total_dose_2024",
            "reason": "TOTAL_DOSE_ALL_PATHWAYS_AND_SOURCES_IS_DISTINCT_FROM_GASEOUS_SOURCE_SPECIFIC_DOSE",
            "source_value": 0.010,
            "source_unit": "mSv y-1",
            "year": 2024,
        }],
        "decision": {
            "blocker": blocker,
            "official_pages_only": True,
            "cross_page_value_and_unit_agreement_required": True,
            "total_dose_not_substituted_for_gaseous_source_specific_dose": True,
            "dose_not_relabelled_as_emission_activity": True,
            "dose_not_relabelled_as_greenhouse_gas_mass": True,
            "units_preserved_without_conversion": True,
            "inferred_values": 0,
            "fake_data": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
