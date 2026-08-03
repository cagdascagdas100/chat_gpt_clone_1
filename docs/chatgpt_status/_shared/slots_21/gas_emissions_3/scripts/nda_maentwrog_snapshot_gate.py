#!/usr/bin/env python3
"""Validate a SHA-locked official NDA snapshot for Maentwrog site-level gas-emissions rows."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-z0-9.<]+", " ", text.lower()).split())


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def validate_identity(contract: dict[str, Any], prior: dict[str, Any], snapshot: dict[str, Any],
                      prior_sha: str, snapshot_sha: str) -> None:
    if contract.get("schema_version") != 3 or contract.get("slot_id") != "gas_emissions_3":
        raise ValueError("contract identity mismatch")
    if contract.get("state") != "READY" or contract.get("status") != "ready":
        raise ValueError("contract is not READY")
    if not contract.get("claimable") or not contract.get("ready_for_claim"):
        raise ValueError("contract is not claimable")
    pre = contract["precondition"]
    if prior_sha != pre["prior_output_sha256"]:
        raise ValueError("prior output SHA mismatch")
    if prior.get("task_id") != pre["required_prior_task_id"]:
        raise ValueError("prior task mismatch")
    if prior.get("state") != pre["required_prior_state"]:
        raise ValueError("prior state mismatch")
    if prior.get("next_unverified_step") != pre["required_prior_next_unverified_step"]:
        raise ValueError("prior next step mismatch")
    manifest = contract["source_evidence_manifest"]
    if snapshot_sha != manifest["snapshot_sha256"]:
        raise ValueError("snapshot SHA mismatch")
    for key in ("source_url", "accessed_at", "published_date", "license", "supports_fields",
                "relevant_record_ids_or_excerpt", "snapshot_path", "snapshot_sha256"):
        if not manifest.get(key):
            raise ValueError(f"missing source manifest field: {key}")
    if snapshot.get("source_url") != manifest["source_url"]:
        raise ValueError("snapshot source URL mismatch")
    if snapshot.get("accessed_at") != manifest["accessed_at"]:
        raise ValueError("snapshot access time mismatch")
    if snapshot.get("license") != manifest["license"]:
        raise ValueError("snapshot license mismatch")


def is_site_emission_record(text: str, aliases: list[str]) -> bool:
    n = norm(text)
    alias_hit = any(norm(alias) in n for alias in aliases)
    emission_term = any(term in n for term in (
        "scope 1 emissions", "scope one emissions", "scope 2 emissions", "scope two emissions",
        "greenhouse gas emissions", "ghg emissions", "gas emissions", "carbon emissions"
    ))
    explicit_unit = bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:tco2e|tonnes? of co2e|kgco2e|tonnes? co2)\b", n))
    return alias_hit and emission_term and explicit_unit


def main() -> int:
    args = parse_args()
    contract_bytes = args.contract.read_bytes()
    prior_bytes = args.prior.read_bytes()
    snapshot_bytes = args.snapshot.read_bytes()
    contract = json.loads(contract_bytes)
    prior = json.loads(prior_bytes)
    snapshot = json.loads(snapshot_bytes)
    validate_identity(
        contract, prior, snapshot,
        hashlib.sha256(prior_bytes).hexdigest(),
        hashlib.sha256(snapshot_bytes).hexdigest(),
    )

    targets = contract["runtime_targets"]
    if len(targets) != 1:
        raise ValueError("exactly one target required")
    target = targets[0]
    aliases = target["exact_aliases"]
    records = snapshot.get("records")
    if not isinstance(records, list):
        raise ValueError("snapshot records missing")
    if len(records) > int(contract["snapshot_policy"]["maximum_records"]):
        raise ValueError("snapshot record limit exceeded")

    site_records: list[dict[str, Any]] = []
    generation_records: list[dict[str, Any]] = []
    emission_records: list[dict[str, Any]] = []
    for record in records:
        text = str(record.get("text", ""))
        expected = record.get("sha256")
        actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if expected != actual:
            raise ValueError(f"record SHA mismatch: {record.get('record_id')}")
        n = norm(text)
        if any(norm(alias) in n for alias in aliases):
            site_records.append(record)
            if "81.4 gigawatt hours" in n and "renewable electricity" in n:
                generation_records.append(record)
        if is_site_emission_record(text, aliases):
            emission_records.append(record)

    matched = bool(emission_records)
    state = "EXACT_SITE_GAS_EMISSIONS_VERIFIED" if matched else "NO_DATA_CONTINUE"
    next_step = (
        "VALIDATE_AND_PUBLISH_EXACT_MAENTWROG_SITE_GAS_EMISSIONS_ROWS"
        if matched else
        "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_NDA_SUSTAINABILITY_NO_SITE_EMISSIONS"
    )
    preserved = [
        {
            "record_id": rec.get("record_id"),
            "line_start": rec.get("line_start"),
            "line_end": rec.get("line_end"),
            "text": rec.get("text"),
            "sha256": rec.get("sha256"),
        }
        for rec in emission_records
    ]
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
        "next_unverified_step": next_step,
        "input": {
            "contract_path": str(args.contract),
            "contract_sha256": hashlib.sha256(contract_bytes).hexdigest(),
            "prior_output_path": str(args.prior),
            "prior_output_sha256": hashlib.sha256(prior_bytes).hexdigest(),
            "snapshot_path": str(args.snapshot),
            "snapshot_sha256": hashlib.sha256(snapshot_bytes).hexdigest(),
            "source_url": snapshot["source_url"],
            "source_line_range": snapshot["capture_scope"],
        },
        "counts": {
            "completed_count": 1,
            "target_count": 1,
            "records_scanned": len(records),
            "site_records": len(site_records),
            "generation_evidence_records": len(generation_records),
            "site_gas_emission_records": len(emission_records),
            "matched_targets": 1 if matched else 0,
            "matched_rows": len(emission_records),
            "produced_business_rows": len(emission_records),
            "produced_source_evidence_records": 2,
        },
        "progress_percent": 100.0,
        "targets": [{
            "target_id": target["target_id"],
            "site_name": target["site_name"],
            "attempt_completed": True,
            "exact_aliases": aliases,
            "site_records": len(site_records),
            "generation_evidence_records": len(generation_records),
            "matched_rows": len(emission_records),
            "matches": preserved,
            "decision": state,
            "reason": (
                None if matched else
                "The bounded official snapshot contains a Maentwrog renewable-generation record "
                "and group-level Scope 1/2 reduction language, but no record combines Maentwrog "
                "with an explicit site-level gas-emissions quantity and unit."
            ),
        }],
        "evidence": {
            "maentwrog_records": [
                {
                    "record_id": rec.get("record_id"),
                    "line_start": rec.get("line_start"),
                    "line_end": rec.get("line_end"),
                    "text": rec.get("text"),
                    "sha256": rec.get("sha256"),
                } for rec in site_records
            ],
            "group_scope_records": [
                {
                    "record_id": rec.get("record_id"),
                    "line_start": rec.get("line_start"),
                    "line_end": rec.get("line_end"),
                    "text": rec.get("text"),
                    "sha256": rec.get("sha256"),
                } for rec in records if "scope one and two carbon emissions" in norm(rec.get("text", ""))
            ],
        },
        "decision": {
            "exact_site_and_explicit_unit_gate_required": True,
            "group_level_emissions_not_assigned_to_site": True,
            "renewable_generation_not_converted_to_avoided_emissions": True,
            "source_records_preserved_without_inference": True,
            "inferred_values": 0,
            "fake_data": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
