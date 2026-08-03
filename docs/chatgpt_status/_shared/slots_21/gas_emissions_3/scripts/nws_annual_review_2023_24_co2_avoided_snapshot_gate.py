#!/usr/bin/env python3
"""Validate an SHA-locked official NWS annual-review CO2-avoidance record."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_IDS = (
    "document_identity",
    "reporting_scope",
    "repository_identity",
    "waste_diversion_context",
    "co2_avoided_metric",
)
MAX_RECORDS = 20

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--prior", type=Path, required=True)
    p.add_argument("--snapshot", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    return p.parse_args()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def norm(value: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).split())

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
        raise ValueError("snapshot record limit exceeded")
    by_id = {}
    for record in records:
        text = record["text"]
        if sha256_bytes(text.encode("utf-8")) != record["sha256"]:
            raise ValueError("record SHA mismatch")
        by_id[record["record_id"]] = record

    complete = all(record_id in by_id for record_id in REQUIRED_IDS)
    document_ok = (
        "nuclear waste services annual review 2023 to 2024"
        in norm(by_id.get("document_identity", {}).get("text", ""))
    )
    scope_text = norm(by_id.get("reporting_scope", {}).get("text", ""))
    scope_ok = (
        "1 april 2023 to 31 march 2024" in scope_text
        and "nuclear waste services" in scope_text
    )
    repository_text = norm(by_id.get("repository_identity", {}).get("text", ""))
    repository_ok = (
        "low level waste repository" in repository_text
        and "cumbria" in repository_text
        and "environmental protection" in repository_text
    )
    diversion_text = norm(by_id.get("waste_diversion_context", {}).get("text", ""))
    diversion_ok = (
        "2 per cent of waste that we assessed and managed was classified for disposal at the repository" in diversion_text
        and "re used or recycled" in diversion_text
    )
    metric_text = norm(by_id.get("co2_avoided_metric", {}).get("text", ""))
    metric_ok = (
        "avoid around 20 000 tonnes of co2 this year" in metric_text
        and "diverting 98 per cent of waste from disposal at the repository site in cumbria" in metric_text
    )

    matches = []
    if complete and document_ok and scope_ok and repository_ok and diversion_ok and metric_ok:
        matches.append({
            "row_id": "NWS_REPOSITORY_DIVERSION_CO2_AVOIDED_2023_24",
            "metric_type": "avoided_carbon_emissions_from_waste_diversion",
            "value_source": "20,000",
            "unit_source": "tonnes CO2",
            "qualifier_source": "around",
            "period_source": "2023 to 2024",
            "scope_source": "NWS waste diversion from disposal at the Repository site in Cumbria",
            "direct_site_emissions": False,
            "source_record": by_id["co2_avoided_metric"],
        })

    state = "ORGANISATION_REPOSITORY_LINKED_CO2_AVOIDED_ROW_VERIFIED" if len(matches) == 1 else "NO_DATA_CONTINUE"
    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_3",
        "task_id": contract["task_id"],
        "continuation_key": contract["continuation_key"],
        "state": state,
        "panel_status": "PUBLISHED",
        "execution_mode": "SHA_LOCKED_OFFICIAL_SOURCE_SNAPSHOT",
        "first_unverified_step_completed": contract["first_unverified_step"],
        "next_unverified_step": (
            "VALIDATE_AND_PUBLISH_NWS_2023_24_REPOSITORY_LINKED_CO2_AVOIDED_ROW"
            if matches else
            "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_NWS_2023_24_NO_DATA"
        ),
        "input": {
            "contract_path": str(args.contract),
            "contract_sha256": sha256_bytes(contract_bytes),
            "prior_output_path": str(args.prior),
            "prior_output_sha256": sha256_bytes(prior_bytes),
            "snapshot_path": str(args.snapshot),
            "snapshot_sha256": sha256_bytes(snapshot_bytes),
            "source_url": snapshot.get("source_url"),
            "capture_scope": snapshot.get("capture_scope"),
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
            "site_name": contract["runtime_targets"][0]["site_name"],
            "organisation": "Nuclear Waste Services",
            "attempt_completed": True,
            "decision": state,
            "matched_rows": len(matches),
            "matches": matches,
        }],
        "decision": {
            "official_report_identity_required": True,
            "reporting_period_required": True,
            "repository_link_required": True,
            "exact_avoided_wording_required": True,
            "direct_site_emissions_not_claimed": True,
            "metric_not_added_to_batch277_project_savings": True,
            "units_preserved_without_conversion": True,
            "partial_candidates_discarded": 0 if matches else int(metric_ok),
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
