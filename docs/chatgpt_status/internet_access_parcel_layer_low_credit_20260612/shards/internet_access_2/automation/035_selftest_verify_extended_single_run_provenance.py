#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("034_verify_extended_single_run_provenance.py")
spec = importlib.util.spec_from_file_location("extended_provenance", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import extended provenance verifier")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.EXPECTED_ROWS = 4

passed: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    passed.append(name)


def dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(root: Path) -> tuple[Path, Path]:
    work = root / "work"
    web = root / "web"
    rows = work / "candidate_outputs/internet_access_2_candidates_latest.jsonl"
    manifest = work / "candidate_outputs/internet_access_2_extraction_manifest_latest.json"
    rows.parent.mkdir(parents=True, exist_ok=True)
    rows.write_text('{"row":1}\n{"row":2}\n{"row":3}\n{"row":4}\n', encoding="utf-8")
    manifest.write_text('{"slot_id":"internet_access_2","rows":4}\n', encoding="utf-8")
    common = {
        "slot_id": "internet_access_2",
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    carrier = dict(common,
        status="PASS_COVERAGE_AWARE_INNER_CARRIER_COMPLETED_REVIEW_ONLY",
        extractor_replacement_count=1,
        base_runner_sha256="d"*64,
        runtime_carrier_sha256="e"*64,
        inner_exit_code=0,
    )
    consistency = dict(common,
        status="PASS_REVIEW_CONTRACT_CONSISTENCY_AUDITED_REVIEW_ONLY",
        combined_validation_passed=394,
        combined_validation_total=394,
    )
    resolution = dict(common,
        status="PASS_COVERAGE_AWARE_POSTCODE_RESOLUTION_AUDITED_REVIEW_ONLY",
        canonical_rows=4,
        candidate_rows_jsonl_sha256=sha(rows),
    )
    candidate = dict(common,
        status="PASS_COMPLETE_CANDIDATE_JSONL_INTEGRITY_REVIEW_ONLY",
        canonical_rows=4,
        candidate_rows_jsonl_sha256=sha(rows),
        extraction_manifest_sha256=sha(manifest),
    )
    dump(work / "internet_access_2_coverage_aware_carrier_latest.json", carrier)
    dump(web / "review_contract_consistency_latest.json", consistency)
    dump(web / "candidate_postcode_resolution_latest.json", resolution)
    dump(web / "candidate_jsonl_integrity_latest.json", candidate)
    return work, web


def base_audit(work_root: Path, web_root: Path, audit_output=None) -> dict:
    rows = work_root / "candidate_outputs/internet_access_2_candidates_latest.jsonl"
    manifest = work_root / "candidate_outputs/internet_access_2_extraction_manifest_latest.json"
    return {
        "schema_version": 3,
        "slot_id": "internet_access_2",
        "status": "PASS_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY",
        "provenance_artifact_count": 12,
        "canonical_rows": 4,
        "provenance_chain_sha256": "a"*64,
        "candidate_rows_jsonl_sha256": sha(rows),
        "extraction_manifest_sha256": sha(manifest),
        "visible_example_rows": 3,
        "zip_sha256": "b"*64,
        "zip_bytes": 4,
        "zip_container_status": "PASS_SAFE_OFFICIAL_ZIP_CONTAINER_REVIEW_ONLY",
        "zip_container_entry_count": 4,
        "zip_container_r1_postcode_file_count": 0,
        "zip_container_r2_postcode_file_count": 4,
        "zip_container_audit_sha256": "c"*64,
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


module.base.audit = base_audit


def expect_fail(name: str, mutate, text: str) -> None:
    with tempfile.TemporaryDirectory() as temp:
        work, web = fixture(Path(temp))
        mutate(work, web)
        try:
            module.audit(work, web)
        except ValueError as exc:
            if text not in str(exc):
                raise AssertionError(f"{name}: {exc}")
            passed.append(name)
        else:
            raise AssertionError(name)


with tempfile.TemporaryDirectory() as temp:
    work, web = fixture(Path(temp))
    output = web / "runner_provenance_audit_latest.json"
    report = module.audit(work, web, output)
    for name, condition in [
        ("status", report["status"] == "PASS_EXTENDED_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY"),
        ("artifact_count_16", report["provenance_artifact_count"] == 16),
        ("base_artifact_count_12", report["base_provenance_artifact_count"] == 12),
        ("extended_audit_count_4", report["extended_audit_artifact_count"] == 4),
        ("chain_sha", len(report["provenance_chain_sha256"]) == 64),
        ("audit_hashes", all(len(report[key]) == 64 for key in (
            "coverage_aware_inner_carrier_sha256",
            "review_contract_consistency_audit_sha256",
            "candidate_postcode_resolution_audit_sha256",
            "candidate_jsonl_integrity_audit_sha256",
        ))),
        ("validation_total", report["combined_validation_passed"] == report["combined_validation_total"] == 394),
        ("output_written", output.is_file()),
        ("no_business", report["actual_business_data_rows_written"] == 0),
        ("not_final", report["final_ready"] is False),
    ]:
        check(name, condition)

expect_fail("carrier_status_rejected", lambda w, v: (
    (w / "internet_access_2_coverage_aware_carrier_latest.json").write_text(
        (w / "internet_access_2_coverage_aware_carrier_latest.json").read_text().replace(
            "PASS_COVERAGE_AWARE_INNER_CARRIER_COMPLETED_REVIEW_ONLY", "FAIL"
        )
    )
), "carrier status")
expect_fail("consistency_status_rejected", lambda w, v: (
    (v / "review_contract_consistency_latest.json").write_text(
        (v / "review_contract_consistency_latest.json").read_text().replace(
            "PASS_REVIEW_CONTRACT_CONSISTENCY_AUDITED_REVIEW_ONLY", "FAIL"
        )
    )
), "consistency status")
expect_fail("validation_total_rejected", lambda w, v: (
    (v / "review_contract_consistency_latest.json").write_text(
        (v / "review_contract_consistency_latest.json").read_text().replace('"combined_validation_total": 394', '"combined_validation_total": 393')
    )
), "validation total")
expect_fail("resolution_rows_rejected", lambda w, v: (
    (v / "candidate_postcode_resolution_latest.json").write_text(
        (v / "candidate_postcode_resolution_latest.json").read_text().replace('"canonical_rows": 4', '"canonical_rows": 3')
    )
), "resolution row count")
expect_fail("resolution_hash_rejected", lambda w, v: (
    (v / "candidate_postcode_resolution_latest.json").write_text(
        (v / "candidate_postcode_resolution_latest.json").read_text().replace(
            '"candidate_rows_jsonl_sha256": "', '"candidate_rows_jsonl_sha256": "' + "0"*64 + '", "old": "'
        )
    )
), "resolution audit/candidate")
expect_fail("candidate_hash_rejected", lambda w, v: (
    (v / "candidate_jsonl_integrity_latest.json").write_text(
        (v / "candidate_jsonl_integrity_latest.json").read_text().replace(
            '"candidate_rows_jsonl_sha256": "', '"candidate_rows_jsonl_sha256": "' + "0"*64 + '", "old": "'
        )
    )
), "candidate integrity/candidate")
expect_fail("manifest_hash_rejected", lambda w, v: (
    (v / "candidate_jsonl_integrity_latest.json").write_text(
        (v / "candidate_jsonl_integrity_latest.json").read_text().replace(
            '"extraction_manifest_sha256": "', '"extraction_manifest_sha256": "' + "0"*64 + '", "old": "'
        )
    )
), "candidate integrity/extraction")
expect_fail("wrong_slot_rejected", lambda w, v: (
    (v / "candidate_postcode_resolution_latest.json").write_text(
        (v / "candidate_postcode_resolution_latest.json").read_text().replace("internet_access_2", "internet_access_3")
    )
), "slot_id")
expect_fail("business_write_rejected", lambda w, v: (
    (v / "candidate_jsonl_integrity_latest.json").write_text(
        (v / "candidate_jsonl_integrity_latest.json").read_text().replace(
            '"actual_business_data_rows_written": 0', '"actual_business_data_rows_written": 1'
        )
    )
), "business rows")
expect_fail("final_ready_rejected", lambda w, v: (
    (v / "review_contract_consistency_latest.json").write_text(
        (v / "review_contract_consistency_latest.json").read_text().replace('"final_ready": false', '"final_ready": true')
    )
), "final_ready")

expected = 20
if len(passed) != expected:
    raise AssertionError(f"{len(passed)} != {expected}: {passed}")
print(json.dumps({
    "status": "PASS",
    "tests_passed": len(passed),
    "tests_total": expected,
    "test_names": passed,
    "actual_business_data_rows_written": 0,
    "final_ready": False,
}, sort_keys=True))
