#!/usr/bin/env python3
"""Strict evidence validator for future_growth_1 official source loaders.

This validator never downloads data and never promotes parcel rows. It checks a
runner-produced evidence JSON against the published source-loader contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_MODES = {"live", "fixture", "stub"}
REQUIRED_CONTRACT_FIELDS = (
    "source_key",
    "official_url",
    "mode_contract",
    "acquisition_contract",
    "parser_contract",
    "normalization_contract",
    "spatial_binding_contract",
    "required_evidence",
    "rejection_conditions",
    "promotion_rule",
)
FORBIDDEN_PROMOTION_STATES = {
    "PARTIAL",
    "FAILED",
    "STUB",
    "POINT_ONLY",
    "NEAREST_ASSIGNED",
    "UNVERIFIED_SPATIAL_BINDING",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON {path}: {exc}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sources = contract.get("sources")
    if not isinstance(sources, list) or len(sources) != 16:
        errors.append("contract must contain exactly 16 sources")
        return errors

    keys: set[str] = set()
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            errors.append(f"source[{index}] is not an object")
            continue
        missing = [field for field in REQUIRED_CONTRACT_FIELDS if not source.get(field)]
        if missing:
            errors.append(f"{source.get('source_key', index)} missing contract fields: {missing}")
        key = source.get("source_key")
        if key in keys:
            errors.append(f"duplicate source_key: {key}")
        keys.add(key)
        if source.get("mode_contract") not in ALLOWED_MODES:
            errors.append(f"{key} invalid mode_contract")
        evidence = source.get("required_evidence")
        if not isinstance(evidence, list) or len(evidence) != 6:
            errors.append(f"{key} must define exactly 6 required evidence items")
        if source.get("loader_output_rows") != 0 or source.get("parcel_rows_promoted") != 0:
            errors.append(f"{key} contract file must not claim loader output or promotion")
    return errors


def validate_runner_evidence(
    contract: dict[str, Any], evidence: dict[str, Any]
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    contract_by_key = {item["source_key"]: item for item in contract["sources"]}
    records = evidence.get("sources")
    if not isinstance(records, list):
        return ["evidence.sources must be a list"], {}

    seen: set[str] = set()
    accepted = 0
    promoted_rows = 0
    per_source: list[dict[str, Any]] = []

    for record in records:
        key = record.get("source_key")
        if key not in contract_by_key:
            errors.append(f"unknown source_key: {key}")
            continue
        if key in seen:
            errors.append(f"duplicate evidence source_key: {key}")
            continue
        seen.add(key)
        expected = contract_by_key[key]
        state = str(record.get("execution_state", "")).upper()
        supplied = record.get("evidence", {})
        missing = [name for name in expected["required_evidence"] if not supplied.get(name)]
        rows = int(record.get("loader_output_rows", 0) or 0)
        promoted = int(record.get("parcel_rows_promoted", 0) or 0)
        spatial_verified = bool(record.get("spatial_binding_verified", False))
        payload_path = record.get("payload_path")
        payload_sha = supplied.get("payload_sha256")

        local_errors: list[str] = []
        if missing:
            local_errors.append(f"missing evidence: {missing}")
        if state != "PASS":
            local_errors.append(f"execution_state={state or 'EMPTY'}")
        if state in FORBIDDEN_PROMOTION_STATES:
            local_errors.append("forbidden promotion state")
        if promoted > 0 and not spatial_verified:
            local_errors.append("promotion without verified spatial binding")
        if promoted > rows:
            local_errors.append("promoted rows exceed loader output rows")
        if payload_path:
            path = Path(payload_path)
            if not path.exists():
                local_errors.append("payload_path does not exist")
            elif payload_sha and sha256_file(path) != payload_sha:
                local_errors.append("payload SHA256 mismatch")

        if local_errors:
            errors.append(f"{key}: " + "; ".join(local_errors))
        else:
            accepted += 1
            promoted_rows += promoted
        per_source.append(
            {
                "source_key": key,
                "accepted": not local_errors,
                "loader_output_rows": rows,
                "parcel_rows_promoted": promoted if not local_errors else 0,
                "errors": local_errors,
            }
        )

    missing_sources = sorted(set(contract_by_key) - seen)
    if missing_sources:
        errors.append(f"missing source evidence records: {missing_sources}")

    summary = {
        "source_evidence_records": len(records),
        "accepted_loader_executions": accepted,
        "expected_loader_executions": 16,
        "parcel_rows_promoted": promoted_rows if not errors else 0,
        "final_ready": False,
        "per_source": per_source,
    }
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    contract = load_json(args.contract)
    errors = validate_contract(contract)
    summary: dict[str, Any] = {
        "contract_valid": not errors,
        "loader_execution_claimed": False,
        "parcel_rows_promoted": 0,
        "final_ready": False,
    }

    if args.evidence:
        evidence = load_json(args.evidence)
        evidence_errors, evidence_summary = validate_runner_evidence(contract, evidence)
        errors.extend(evidence_errors)
        summary.update(evidence_summary)

    result = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "summary": summary,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
