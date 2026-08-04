#!/usr/bin/env python3
"""Validate and publish the official NDA-only 2025/26 operational GHG table rows."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MAX_RECORDS = 10
REQUIRED_RECORD_IDS = (
    "publication_identity",
    "pdf_identity_and_licence",
    "nda_only_operational_boundary",
    "nda_only_operational_ghg_table_2025_26",
    "scope3_boundary_change_2025_26",
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

    manifest = contract["source_evidence_manifest"]
    if sha256_bytes(snapshot_bytes) != manifest["snapshot_sha256"]:
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
    identity = by_id.get("publication_identity", {}).get("proven_fields", {})
    licence = by_id.get("pdf_identity_and_licence", {}).get("proven_fields", {})
    boundary = by_id.get("nda_only_operational_boundary", {}).get("proven_fields", {})
    table = by_id.get("nda_only_operational_ghg_table_2025_26", {}).get("proven_fields", {})
    scope3 = by_id.get("scope3_boundary_change_2025_26", {}).get("proven_fields", {})

    exact_match = (
        complete
        and identity.get("document") == "Nuclear Decommissioning Authority: Annual Report and Accounts 2025 to 2026"
        and identity.get("published_date") == "2026-07-16"
        and licence.get("licence") == "Open Government Licence v3.0"
        and licence.get("report_period") == "2025/26"
        and boundary.get("organisation_scope") == "NDA only"
        and boundary.get("period") == "2025/26"
        and boundary.get("unit") == "tCO2e"
        and boundary.get("group_or_site_allocation_provided") is False
        and table.get("organisation_scope") == "NDA only"
        and table.get("period") == "2025/26"
        and table.get("scope_1_gross_tco2e") == 73.0
        and table.get("scope_2_gross_tco2e") == 129.0
        and table.get("scope_3_gross_tco2e") == 584.0
        and table.get("reported_total_scope_1_2_3_tco2e") == 787.0
        and table.get("reported_total_recalculated") is False
        and table.get("site_allocation_provided") is False
        and scope3.get("period") == "2025/26"
        and scope3.get("scope_3_components") == [
            "upstream transmission and distribution losses",
            "business travel",
            "employee commuting",
            "homeworking",
        ]
    )

    rows: list[dict[str, Any]] = []
    if exact_match:
        row_specs = [
            ("NDA_ONLY_2025_26_SCOPE1_GROSS_GHG", "gross_scope_1_direct_GHG_emissions", 73.0),
            ("NDA_ONLY_2025_26_SCOPE2_GROSS_GHG", "gross_scope_2_energy_indirect_GHG_emissions", 129.0),
            ("NDA_ONLY_2025_26_SCOPE3_GROSS_GHG", "gross_scope_3_GHG_emissions", 584.0),
            ("NDA_ONLY_2025_26_REPORTED_TOTAL_SCOPE123_GHG", "reported_total_scope_1_2_3_GHG_emissions", 787.0),
        ]
        for row_id, metric_type, value in row_specs:
            rows.append({
                "row_id": row_id,
                "organisation_scope": "NDA only",
                "operational_boundary": "offices under NDA operational control and NDA staff conducting operations",
                "period": "2025/26",
                "metric_type": metric_type,
                "source_value": value,
                "source_unit": "tCO2e",
                "site_or_group_allocation": None,
                "source_record_id": "nda_only_operational_ghg_table_2025_26",
                "source_line_range": [7619, 7630],
                "reported_total_recalculated": False,
                "unit_conversion_applied": False,
                "value_inferred": False,
            })

    state = "EXACT_NDA_ONLY_OPERATIONAL_GHG_TABLE_ROWS_VERIFIED" if rows else "NO_DATA_CONTINUE"
    next_step = (
        "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_NDA_ONLY_2025_26_OPERATIONAL_GHG_TABLE_PUBLISHED"
        if rows
        else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_NDA_ONLY_2025_26_OPERATIONAL_GHG_NO_DATA"
    )
    blocker = (
        "NONE"
        if rows
        else "OFFICIAL_NDA_2025_26_RECORD_SET_DID_NOT_PASS_EXACT_NDA_ONLY_OPERATIONAL_GHG_TABLE_GATE"
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
        "execution_mode": "SHA_LOCKED_OFFICIAL_GOVUK_PAGE_AND_PARSED_PDF_SNAPSHOT",
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
            "source_asset_url": snapshot["source_asset_url"],
            "capture_scope": snapshot["capture_scope"],
        },
        "counts": {
            "completed_count": 1,
            "target_count": 1,
            "records_scanned": len(records),
            "matched_targets": 1 if rows else 0,
            "matched_rows": len(rows),
            "produced_business_rows": len(rows),
            "produced_source_evidence_records": len(records),
        },
        "progress_percent": 100.0,
        "targets": [{
            "target_id": contract["runtime_targets"][0]["target_id"],
            "organisation_scope": "NDA only",
            "attempt_completed": True,
            "decision": state,
            "matched_rows": len(rows),
            "matches": rows,
        }],
        "decision": {
            "blocker": blocker,
            "official_source_only": True,
            "NDA_only_operational_boundary_preserved": True,
            "NDA_group_or_site_allocation_prohibited": True,
            "reported_total_not_recalculated": True,
            "rounded_components_not_forced_to_sum_to_reported_total": True,
            "scope3_boundary_change_preserved": True,
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
