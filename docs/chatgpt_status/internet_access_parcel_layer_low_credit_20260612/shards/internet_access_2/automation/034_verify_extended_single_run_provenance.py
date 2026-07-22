#!/usr/bin/env python3
"""Extend the base twelve-artifact provenance chain with audits and execution-code identity."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

AUTOMATION_ROOT = Path(__file__).resolve().parent
BASE_SCRIPT = AUTOMATION_ROOT / "019_verify_single_run_provenance.py"
spec = importlib.util.spec_from_file_location("internet_access_2_base_provenance", BASE_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import base provenance verifier: {BASE_SCRIPT}")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

SLOT_ID = "internet_access_2"
EXPECTED_ROWS = 30761
HEX64 = re.compile(r"^[0-9a-f]{64}$")
BASE_RUNNER_NAME = "009_probe_download_slice_join_publish_slot2.ps1"
COVERAGE_EXTRACTOR_NAME = "030_extract_slot2_coverage_aware_candidates.py"
CARRIER_SCRIPT_NAME = "036_run_coverage_aware_inner_carrier.ps1"
RUNTIME_SCRIPT_NAME = "internet_access_2_coverage_aware_inner_runtime.ps1"
BASE_EXTRACTOR_LINE = '$extractor = Join-Path $automationRoot "002_extract_slot2_ofcom_2026_candidates.py"'
COVERAGE_EXTRACTOR_LINE = '$extractor = Join-Path $automationRoot "030_extract_slot2_coverage_aware_candidates.py"'


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"Required provenance artifact missing: {path.name}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Required extended provenance file missing: {path.name}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def require_hex64(value: Any, label: str) -> str:
    text = str(value or "")
    if not HEX64.fullmatch(text):
        raise ValueError(f"{label} is not a lowercase SHA-256")
    return text


def require_review_only(payload: dict[str, Any], label: str) -> None:
    if payload.get("slot_id") != SLOT_ID:
        raise ValueError(f"{label} slot_id mismatch")
    if int(payload.get("actual_business_data_rows_written", -1)) != 0:
        raise ValueError(f"{label} reports business rows")
    if "scores_written" in payload and int(payload.get("scores_written", -1)) != 0:
        raise ValueError(f"{label} reports scores")
    for key in ("db_write", "migration", "production_deploy"):
        if key in payload and payload.get(key) is not False:
            raise ValueError(f"{label} {key} must be false")
    if payload.get("final_ready") is not False:
        raise ValueError(f"{label} final_ready must be false")


def normalized_script(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig")
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def recorded_name(value: Any) -> str:
    return str(value or "").replace("\\", "/").rstrip("/").split("/")[-1]


def audit(
    work_root: Path,
    web_root: Path,
    audit_output: Path | None = None,
    automation_root: Path | None = None,
) -> dict[str, Any]:
    code_root = (automation_root or AUTOMATION_ROOT).resolve()
    base_report = base.audit(work_root, web_root, None)
    if base_report.get("status") != "PASS_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY":
        raise ValueError("base provenance status mismatch")
    if int(base_report.get("provenance_artifact_count", -1)) != 12:
        raise ValueError("base provenance artifact count mismatch")
    if int(base_report.get("canonical_rows", -1)) != EXPECTED_ROWS:
        raise ValueError("base provenance canonical row count mismatch")
    base_chain = require_hex64(base_report.get("provenance_chain_sha256"), "base provenance chain")

    carrier_path = work_root / "internet_access_2_coverage_aware_carrier_latest.json"
    consistency_path = web_root / "review_contract_consistency_latest.json"
    resolution_path = web_root / "candidate_postcode_resolution_latest.json"
    candidate_path = web_root / "candidate_jsonl_integrity_latest.json"
    rows_path = work_root / "candidate_outputs/internet_access_2_candidates_latest.jsonl"
    manifest_path = work_root / "candidate_outputs/internet_access_2_extraction_manifest_latest.json"
    base_runner_path = code_root / BASE_RUNNER_NAME
    extractor_path = code_root / COVERAGE_EXTRACTOR_NAME
    carrier_script_path = code_root / CARRIER_SCRIPT_NAME
    runtime_script_path = work_root / RUNTIME_SCRIPT_NAME

    carrier = load_json(carrier_path, "coverage-aware inner carrier")
    consistency = load_json(consistency_path, "review consistency")
    resolution = load_json(resolution_path, "coverage-aware postcode resolution")
    candidate = load_json(candidate_path, "candidate integrity")
    for label, payload in (
        ("coverage-aware inner carrier", carrier),
        ("review consistency", consistency),
        ("coverage-aware postcode resolution", resolution),
        ("candidate integrity", candidate),
    ):
        require_review_only(payload, label)

    if carrier.get("status") != "PASS_COVERAGE_AWARE_INNER_CARRIER_COMPLETED_REVIEW_ONLY":
        raise ValueError("coverage-aware inner carrier status mismatch")
    if int(carrier.get("extractor_replacement_count", -1)) != 1:
        raise ValueError("coverage-aware inner carrier replacement count mismatch")
    if int(carrier.get("inner_exit_code", -1)) != 0:
        raise ValueError("coverage-aware inner carrier exit code mismatch")
    if recorded_name(carrier.get("coverage_aware_extractor")) != COVERAGE_EXTRACTOR_NAME:
        raise ValueError("coverage-aware inner carrier extractor path mismatch")

    base_runner_sha = sha256_file(base_runner_path)
    runtime_script_sha = sha256_file(runtime_script_path)
    coverage_extractor_sha = sha256_file(extractor_path)
    carrier_script_sha = sha256_file(carrier_script_path)
    if require_hex64(carrier.get("base_runner_sha256"), "carrier base runner SHA") != base_runner_sha:
        raise ValueError("carrier base runner SHA does not match actual code")
    if require_hex64(carrier.get("runtime_carrier_sha256"), "carrier runtime SHA") != runtime_script_sha:
        raise ValueError("carrier runtime SHA does not match actual runtime script")

    base_text = normalized_script(base_runner_path)
    runtime_text = normalized_script(runtime_script_path)
    if base_text.count(BASE_EXTRACTOR_LINE) != 1:
        raise ValueError("base runner exact extractor line count mismatch")
    expected_runtime = base_text.replace(BASE_EXTRACTOR_LINE, COVERAGE_EXTRACTOR_LINE)
    if runtime_text != expected_runtime:
        raise ValueError("runtime script contains changes beyond exact extractor substitution")
    if runtime_text.count(COVERAGE_EXTRACTOR_LINE) != 1 or BASE_EXTRACTOR_LINE in runtime_text:
        raise ValueError("runtime script exact extractor substitution mismatch")

    if consistency.get("status") != "PASS_REVIEW_CONTRACT_CONSISTENCY_AUDITED_REVIEW_ONLY":
        raise ValueError("review consistency status mismatch")
    passed = int(consistency.get("combined_validation_passed", -1))
    total = int(consistency.get("combined_validation_total", -1))
    if passed <= 0 or passed != total:
        raise ValueError("review consistency validation total mismatch")

    if resolution.get("status") != "PASS_COVERAGE_AWARE_POSTCODE_RESOLUTION_AUDITED_REVIEW_ONLY":
        raise ValueError("coverage-aware postcode resolution status mismatch")
    if int(resolution.get("canonical_rows", -1)) != EXPECTED_ROWS:
        raise ValueError("coverage-aware postcode resolution row count mismatch")

    if candidate.get("status") != "PASS_COMPLETE_CANDIDATE_JSONL_INTEGRITY_REVIEW_ONLY":
        raise ValueError("candidate integrity status mismatch")
    if int(candidate.get("canonical_rows", -1)) != EXPECTED_ROWS:
        raise ValueError("candidate integrity row count mismatch")

    rows_sha = sha256_file(rows_path)
    manifest_sha = sha256_file(manifest_path)
    if require_hex64(resolution.get("candidate_rows_jsonl_sha256"), "resolution rows SHA") != rows_sha:
        raise ValueError("resolution audit/candidate JSONL SHA chain mismatch")
    if require_hex64(candidate.get("candidate_rows_jsonl_sha256"), "candidate audit rows SHA") != rows_sha:
        raise ValueError("candidate integrity/candidate JSONL SHA chain mismatch")
    if require_hex64(candidate.get("extraction_manifest_sha256"), "candidate audit manifest SHA") != manifest_sha:
        raise ValueError("candidate integrity/extraction manifest SHA chain mismatch")
    if require_hex64(base_report.get("candidate_rows_jsonl_sha256"), "base candidate rows SHA") != rows_sha:
        raise ValueError("base provenance/candidate JSONL SHA chain mismatch")
    if require_hex64(base_report.get("extraction_manifest_sha256"), "base extraction manifest SHA") != manifest_sha:
        raise ValueError("base provenance/extraction manifest SHA chain mismatch")

    carrier_sha = sha256_file(carrier_path)
    consistency_sha = sha256_file(consistency_path)
    resolution_sha = sha256_file(resolution_path)
    candidate_audit_sha = sha256_file(candidate_path)
    chain_inputs = [
        base_chain,
        carrier_sha,
        consistency_sha,
        resolution_sha,
        candidate_audit_sha,
        base_runner_sha,
        runtime_script_sha,
        coverage_extractor_sha,
        carrier_script_sha,
    ]
    extended_chain = hashlib.sha256("\n".join(chain_inputs).encode("ascii")).hexdigest()

    result = dict(base_report)
    result.update({
        "schema_version": 5,
        "status": "PASS_EXTENDED_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY",
        "base_provenance_artifact_count": 12,
        "extended_audit_artifact_count": 4,
        "execution_code_artifact_count": 4,
        "provenance_artifact_count": 20,
        "base_provenance_chain_sha256": base_chain,
        "coverage_aware_inner_carrier_sha256": carrier_sha,
        "review_contract_consistency_audit_sha256": consistency_sha,
        "candidate_postcode_resolution_audit_sha256": resolution_sha,
        "candidate_jsonl_integrity_audit_sha256": candidate_audit_sha,
        "base_runner_code_sha256": base_runner_sha,
        "runtime_runner_code_sha256": runtime_script_sha,
        "coverage_aware_extractor_code_sha256": coverage_extractor_sha,
        "coverage_aware_carrier_code_sha256": carrier_script_sha,
        "runtime_exact_extractor_substitution_verified": True,
        "runtime_extractor_replacement_count": 1,
        "provenance_chain_sha256": extended_chain,
        "combined_validation_passed": passed,
        "combined_validation_total": total,
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    })
    if audit_output is not None:
        audit_output.parent.mkdir(parents=True, exist_ok=True)
        audit_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--web-root", required=True, type=Path)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.work_root, args.web_root, args.audit_output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
