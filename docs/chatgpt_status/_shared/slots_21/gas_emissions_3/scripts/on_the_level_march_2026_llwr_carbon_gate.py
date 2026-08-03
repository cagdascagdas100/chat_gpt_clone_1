#!/usr/bin/env python3
"""Validate whether On the Level March 2026 contains an explicit LLWR numeric carbon row."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

MAX_RECORDS = 20
REQUIRED_RECORD_IDS = (
    "document_identity",
    "licence_and_url",
    "repository_year_numbers",
    "current_campaign_logistics",
    "esc_air_quality_context",
    "repository_carbon_claim",
)
CARBON_TERMS = ("carbon emissions", "co2", "co2e", "greenhouse gas", "ghg")
UNIT_RE = re.compile(r"(?i)\b(?:t(?:onnes?)?\s*(?:co2e|co₂e|co2)|kg\s*(?:co2e|co₂e|co2)|mtco2e)\b")
NUMBER_RE = re.compile(r"(?<![A-Za-z])(?:approximately\s+|around\s+|about\s+|~\s*)?\d[\d,]*(?:\.\d+)?")
PERIOD_RE = re.compile(r"\b(?:20\d{2}/\d{2}|20\d{2})\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


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
    precondition = contract["precondition"]
    if sha256_bytes(prior_bytes) != precondition["prior_output_sha256"]:
        raise ValueError("prior output SHA mismatch")
    if prior.get("task_id") != precondition["required_prior_task_id"]:
        raise ValueError("prior task mismatch")
    if prior.get("state") != precondition["required_prior_state"]:
        raise ValueError("prior state mismatch")
    if prior.get("next_unverified_step") != precondition["required_prior_next_unverified_step"]:
        raise ValueError("prior next step mismatch")
    if sha256_bytes(snapshot_bytes) != contract["source_evidence_manifest"]["snapshot_sha256"]:
        raise ValueError("snapshot SHA mismatch")

    records = snapshot.get("records", [])
    if len(records) > MAX_RECORDS:
        raise ValueError("record limit exceeded")
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        if sha256_bytes(record["text"].encode("utf-8")) != record["sha256"]:
            raise ValueError("record SHA mismatch")
        by_id[record["record_id"]] = record

    base_complete = all(record_id in by_id for record_id in REQUIRED_RECORD_IDS)
    identity_ok = "on the level march 2026 issue 45" in norm(by_id.get("document_identity", {}).get("text", ""))
    licence_ok = "open government licence v3 0" in norm(by_id.get("licence_and_url", {}).get("text", ""))
    repository_context = "repository site" in norm(by_id.get("repository_year_numbers", {}).get("text", ""))
    logistics_text = norm(by_id.get("repository_year_numbers", {}).get("text", "") + " " + by_id.get("current_campaign_logistics", {}).get("text", ""))
    logistics_ok = (
        "200 rail deliveries" in logistics_text
        and "8 868 hgv movements" in logistics_text
        and "168 500 tonnes" in logistics_text
        and "39 trains" in logistics_text
        and "36 539 tonnes" in logistics_text
        and "2 000 hgv journeys" in logistics_text
    )
    esc_ok = "air quality" in norm(by_id.get("esc_air_quality_context", {}).get("text", ""))
    carbon_claim_ok = (
        "llw repository" in norm(by_id.get("repository_carbon_claim", {}).get("text", ""))
        and "cuts carbon emissions" in norm(by_id.get("repository_carbon_claim", {}).get("text", ""))
    )

    matches: list[dict[str, Any]] = []
    for record in records:
        text = record["text"]
        normalized = norm(text)
        site_ok = "low level waste repository" in normalized or "llw repository" in normalized or "repository site" in normalized
        carbon_ok = any(term in normalized for term in CARBON_TERMS)
        number_match = NUMBER_RE.search(text)
        unit_match = UNIT_RE.search(text)
        if site_ok and carbon_ok and number_match and unit_match:
            matches.append(
                {
                    "row_id": f"ON_THE_LEVEL_2026_LLWR_CARBON_{len(matches) + 1}",
                    "metric_type": "site_linked_numeric_carbon_or_ghg",
                    "value_source_token": number_match.group(0),
                    "unit_source_token": unit_match.group(0),
                    "period_source_token": PERIOD_RE.search(text).group(0) if PERIOD_RE.search(text) else None,
                    "source_record_id": record["record_id"],
                    "source_line_start": record["line_start"],
                    "source_line_end": record["line_end"],
                    "source_text": text,
                    "source_sha256": record["sha256"],
                    "unit_conversion_applied": False,
                    "value_inferred": False,
                }
            )

    state = "EXACT_LLWR_NUMERIC_CARBON_ROW_VERIFIED" if matches else "NO_DATA_CONTINUE"
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
        "next_unverified_step": (
            "VALIDATE_AND_PUBLISH_ON_THE_LEVEL_2026_EXACT_LLWR_NUMERIC_CARBON_ROW"
            if matches
            else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_ON_THE_LEVEL_2026_NO_NUMERIC_CARBON_DATA"
        ),
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
            "repository_context_records": 4 if repository_context and logistics_ok and esc_ok and carbon_claim_ok else 0,
            "numeric_site_carbon_rows": len(matches),
            "matched_targets": 1 if matches else 0,
            "matched_rows": len(matches),
            "produced_business_rows": len(matches),
            "produced_source_evidence_records": len(records),
        },
        "progress_percent": 100.0,
        "targets": [
            {
                "target_id": contract["runtime_targets"][0]["target_id"],
                "site_name": "Low Level Waste Repository",
                "attempt_completed": True,
                "decision": state,
                "matched_rows": len(matches),
                "matches": matches,
            }
        ],
        "excluded_evidence": [
            {
                "reason": "LOGISTICS_COUNTS_AND_QUALITATIVE_CARBON_CLAIM_LACK_NUMERIC_CO2E_OR_GHG_QUANTITY",
                "record_ids": ["repository_year_numbers", "current_campaign_logistics", "repository_carbon_claim"],
                "values_preserved": [
                    "200 rail deliveries",
                    "8,868 avoided HGV movements",
                    "168,500 tonnes aggregate",
                    "39 trains",
                    "36,539 tonnes aggregate",
                    "almost 2,000 avoided HGV journeys",
                    "approximately 200 trains",
                    "175,000 tonnes material",
                ],
            }
        ],
        "decision": {
            "official_page_identity_required": True,
            "repository_context_required": True,
            "numeric_carbon_or_ghg_quantity_and_unit_required": True,
            "logistics_to_emissions_conversion_allowed": False,
            "qualitative_carbon_claim_relabelled_as_numeric": False,
            "base_records_complete": base_complete,
            "identity_ok": identity_ok,
            "licence_ok": licence_ok,
            "repository_context_ok": repository_context,
            "logistics_context_ok": logistics_ok,
            "esc_air_quality_context_ok": esc_ok,
            "qualitative_carbon_claim_ok": carbon_claim_ok,
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
