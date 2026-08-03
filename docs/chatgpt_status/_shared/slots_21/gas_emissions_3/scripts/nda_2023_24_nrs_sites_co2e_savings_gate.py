#!/usr/bin/env python3
"""Validate and publish the official NRS Sites organisation-wide CO2e savings row."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_RECORDS = 10
REQUIRED_RECORD_IDS = (
    "document_identity",
    "licence_and_canonical_url",
    "nrs_sites_co2e_savings_2023_24",
    "nrs_sites_portfolio_context",
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

def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def canonical_record_sha(record: dict[str, Any]) -> str:
    core = {key: value for key, value in record.items() if key != "sha256"}
    return sha256_bytes(canonical_json(core).encode("utf-8"))

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

    complete = all(record_id in by_id for record_id in REQUIRED_RECORD_IDS)
    identity = by_id.get("document_identity", {}).get("proven_fields", {})
    licence = by_id.get("licence_and_canonical_url", {}).get("proven_fields", {})
    metric = by_id.get("nrs_sites_co2e_savings_2023_24", {}).get("proven_fields", {})
    portfolio = by_id.get("nrs_sites_portfolio_context", {}).get("proven_fields", {})

    exact_match = (
        complete
        and identity.get("document") == "Nuclear Decommissioning Authority: Annual Report and Accounts 2023 to 2024"
        and identity.get("published_date") == "2024-10-09"
        and licence.get("licence") == "Open Government Licence v3.0"
        and metric.get("organisation") == "NRS Sites"
        and metric.get("period") == "2023/24"
        and metric.get("metric_type") == "energy_improvement_CO2e_savings"
        and metric.get("saved_value") == 800.0
        and metric.get("target_value") == 500.0
        and metric.get("unit") == "tonnes CO2e"
        and metric.get("site_allocation_provided") is False
        and portfolio.get("includes_site") == "Trawsfynydd"
        and portfolio.get("operates_hydroelectric_station") == "Maentwrog"
    )

    matches: list[dict[str, Any]] = []
    if exact_match:
        matches.append({
            "row_id": "NRS_SITES_2023_24_ENERGY_IMPROVEMENT_CO2E_SAVINGS",
            "organisation": "NRS Sites",
            "period": "2023/24",
            "metric_type": "organisation_wide_energy_improvement_CO2e_savings",
            "source_value": 800.0,
            "source_unit": "tonnes CO2e",
            "target_source_value": 500.0,
            "target_source_unit": "tonnes CO2e",
            "portfolio_context_sites": ["Trawsfynydd", "Maentwrog"],
            "site_level_allocation": None,
            "source_record_id": "nrs_sites_co2e_savings_2023_24",
            "source_line_range": [2625, 2639],
            "unit_conversion_applied": False,
            "value_inferred": False,
        })

    state = "EXACT_NRS_SITES_ORGANISATION_CO2E_SAVINGS_ROW_VERIFIED" if matches else "NO_DATA_CONTINUE"
    next_step = (
        "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_NRS_SITES_2023_24_CO2E_SAVINGS_PUBLISHED"
        if matches
        else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_NRS_SITES_2023_24_NO_DATA"
    )
    blocker = "NONE" if matches else "OFFICIAL_NDA_2023_24_RECORD_SET_DID_NOT_PASS_EXACT_NRS_SITES_CO2E_SAVINGS_GATE"

    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_3",
        "task_id": contract["task_id"],
        "continuation_key": contract["continuation_key"],
        "state": state,
        "panel_status": "PUBLISHED",
        "execution_mode": "SHA_LOCKED_OFFICIAL_GOVUK_HTML_SNAPSHOT",
        "first_unverified_step_completed": contract["first_unverified_step"],
        "next_unverified_step": next_step,
        "input": {
            "contract_path": str(args.contract),
            "contract_sha256": sha256_bytes(contract_bytes),
            "prior_output_path": str(args.prior),
            "prior_output_sha256": sha256_bytes(prior_bytes),
            "snapshot_path": str(args.snapshot),
            "snapshot_sha256": sha256_bytes(snapshot_bytes),
            "source_page_url": snapshot["source_page_url"],
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
            "organisation": "NRS Sites",
            "attempt_completed": True,
            "decision": state,
            "matched_rows": len(matches),
            "matches": matches,
        }],
        "decision": {
            "blocker": blocker,
            "official_page_only": True,
            "organisation_wide_scope_preserved": True,
            "site_level_allocation_prohibited": True,
            "Trawsfynydd_or_Maentwrog_value_inferred": False,
            "units_preserved_without_conversion": True,
            "inferred_values": 0,
            "fake_data": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(canonical_json(output), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
