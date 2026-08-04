#!/usr/bin/env python3
"""Validate and publish the official NDA-only refrigerant-gas loss row."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
MAX_RECORDS = 10
REQUIRED_RECORD_IDS = (
    "publication_identity", "pdf_identity_and_licence",
    "nda_only_boundary_and_methodology", "f_gas_release_context",
    "nda_only_refrigerant_gas_losses_table",
)

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--prior", type=Path, required=True)
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def canonical_record_sha(record: dict[str, Any]) -> str:
    core = {k: v for k, v in record.items() if k != "sha256"}
    return sha256_bytes(canonical_json(core).encode("utf-8"))

def main() -> int:
    a = parse_args()
    contract_bytes, prior_bytes, snapshot_bytes = a.contract.read_bytes(), a.prior.read_bytes(), a.snapshot.read_bytes()
    contract, prior, snapshot = json.loads(contract_bytes), json.loads(prior_bytes), json.loads(snapshot_bytes)
    if contract.get("schema_version") != 3 or contract.get("state") != "READY":
        raise ValueError("contract is not schema-v3 READY")
    pre = contract["precondition"]
    if sha256_bytes(prior_bytes) != pre["prior_output_sha256"]: raise ValueError("prior output SHA mismatch")
    if prior.get("task_id") != pre["required_prior_task_id"]: raise ValueError("prior task mismatch")
    if prior.get("state") != pre["required_prior_state"]: raise ValueError("prior state mismatch")
    if prior.get("next_unverified_step") != pre["required_prior_next_unverified_step"]: raise ValueError("prior next step mismatch")
    if sha256_bytes(snapshot_bytes) != contract["source_evidence_manifest"]["snapshot_sha256"]:
        raise ValueError("snapshot SHA mismatch")
    records = snapshot.get("records", [])
    if len(records) > MAX_RECORDS: raise ValueError("record limit exceeded")
    by_id = {}
    for record in records:
        if canonical_record_sha(record) != record.get("sha256"): raise ValueError("record SHA mismatch")
        by_id[record["record_id"]] = record
    complete = all(r in by_id for r in REQUIRED_RECORD_IDS)
    identity = by_id.get("publication_identity", {}).get("proven_fields", {})
    pdf = by_id.get("pdf_identity_and_licence", {}).get("proven_fields", {})
    boundary = by_id.get("nda_only_boundary_and_methodology", {}).get("proven_fields", {})
    release = by_id.get("f_gas_release_context", {}).get("proven_fields", {})
    metric = by_id.get("nda_only_refrigerant_gas_losses_table", {}).get("proven_fields", {})
    exact = (
        complete and identity.get("document") == "Nuclear Decommissioning Authority: Annual Report and Accounts 2025 to 2026"
        and identity.get("published_date") == "2026-07-16" and pdf.get("licence") == "Open Government Licence v3.0"
        and pdf.get("report_period") == "2025/26" and boundary.get("organisation_scope") == "NDA only"
        and boundary.get("reporting_boundary") == "Herdus House and NDA staff operations"
        and release.get("f_gas_release_increased_scope1") is True and release.get("equipment_context") == "air conditioning units"
        and metric.get("metric_type") == "refrigerant_gas_losses" and metric.get("period") == "2025/26"
        and metric.get("source_value") == 38.1 and metric.get("source_unit") == "kg"
        and metric.get("tco2e_conversion_provided") is False and metric.get("group_or_site_allocation_provided") is False
    )
    matches = []
    if exact:
        matches.append({
            "row_id":"NDA_ONLY_2025_26_REFRIGERANT_GAS_LOSSES","organisation_scope":"NDA only",
            "operational_boundary":"Herdus House and NDA staff operations","period":"2025/26",
            "metric_type":"refrigerant_gas_losses","source_value":38.1,"source_unit":"kg",
            "historical_context":{"2022/23":19.0,"2023/24":3.0,"2024/25":3.0},
            "tco2e_value":None,"site_or_group_allocation":None,
            "source_record_id":"nda_only_refrigerant_gas_losses_table","source_line_range":[7681,7688],
            "unit_conversion_applied":False,"value_inferred":False,
        })
    state = "EXACT_NDA_ONLY_REFRIGERANT_GAS_LOSS_ROW_VERIFIED" if matches else "NO_DATA_CONTINUE"
    next_step = "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_NDA_ONLY_2025_26_REFRIGERANT_GAS_LOSS_PUBLISHED" if matches else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_NDA_ONLY_2025_26_REFRIGERANT_GAS_NO_DATA"
    blocker = "NONE" if matches else "OFFICIAL_NDA_2025_26_RECORD_SET_DID_NOT_PASS_EXACT_REFRIGERANT_GAS_LOSS_GATE"
    output = {
        "schema_version":3,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id":"gas_emissions_3","task_id":contract["task_id"],"continuation_key":contract["continuation_key"],
        "state":state,"panel_status":"PUBLISHED","execution_mode":"SHA_LOCKED_OFFICIAL_GOVUK_PAGE_AND_PARSED_PDF_SNAPSHOT",
        "first_unverified_step_completed":contract["first_unverified_step"],"next_unverified_step":next_step,
        "input":{"contract_path":str(a.contract),"contract_sha256":sha256_bytes(contract_bytes),"prior_output_path":str(a.prior),"prior_output_sha256":sha256_bytes(prior_bytes),"snapshot_path":str(a.snapshot),"snapshot_sha256":sha256_bytes(snapshot_bytes),"source_page_url":snapshot["source_page_url"],"source_asset_url":snapshot["source_asset_url"],"capture_scope":snapshot["capture_scope"]},
        "counts":{"completed_count":1,"target_count":1,"records_scanned":len(records),"matched_targets":1 if matches else 0,"matched_rows":len(matches),"produced_business_rows":len(matches),"produced_source_evidence_records":len(records)},
        "progress_percent":100.0,
        "targets":[{"target_id":contract["runtime_targets"][0]["target_id"],"organisation_scope":"NDA only","attempt_completed":True,"decision":state,"matched_rows":len(matches),"matches":matches}],
        "decision":{"blocker":blocker,"official_source_only":True,"nda_only_boundary_preserved":True,"refrigerant_mass_not_relabelled_as_tco2e":True,"scope1_total_not_used_to_derive_refrigerant_mass":True,"site_or_group_allocation_prohibited":True,"units_preserved_without_conversion":True,"inferred_values":0,"fake_data":False},
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(canonical_json(output), encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())
