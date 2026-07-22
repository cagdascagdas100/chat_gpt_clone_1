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


def fixture(root: Path) -> tuple[Path, Path, Path]:
    work = root / "work"
    web = root / "web"
    code = root / "automation"
    code.mkdir(parents=True, exist_ok=True)
    base_text = (
        '$automationRoot = "fixture"\n'
        '$extractor = Join-Path $automationRoot "002_extract_slot2_ofcom_2026_candidates.py"\n'
        'Write-Output "runner"\n'
    )
    expected_runtime = base_text.replace(
        '$extractor = Join-Path $automationRoot "002_extract_slot2_ofcom_2026_candidates.py"',
        '$extractor = Join-Path $automationRoot "030_extract_slot2_coverage_aware_candidates.py"',
    )
    (code / module.BASE_RUNNER_NAME).write_text(base_text, encoding="utf-8")
    (code / module.COVERAGE_EXTRACTOR_NAME).write_text("print('coverage-aware')\n", encoding="utf-8")
    (code / module.CARRIER_SCRIPT_NAME).write_text("Write-Output 'carrier'\n", encoding="utf-8")
    (work / module.RUNTIME_SCRIPT_NAME).parent.mkdir(parents=True, exist_ok=True)
    (work / module.RUNTIME_SCRIPT_NAME).write_text(expected_runtime, encoding="utf-8")

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
    carrier = dict(
        common,
        status="PASS_COVERAGE_AWARE_INNER_CARRIER_COMPLETED_REVIEW_ONLY",
        extractor_replacement_count=1,
        base_runner_sha256=sha(code / module.BASE_RUNNER_NAME),
        runtime_carrier_sha256=sha(work / module.RUNTIME_SCRIPT_NAME),
        coverage_aware_extractor=str(code / module.COVERAGE_EXTRACTOR_NAME),
        inner_exit_code=0,
    )
    consistency = dict(common, status="PASS_REVIEW_CONTRACT_CONSISTENCY_AUDITED_REVIEW_ONLY", combined_validation_passed=415, combined_validation_total=415)
    resolution = dict(common, status="PASS_COVERAGE_AWARE_POSTCODE_RESOLUTION_AUDITED_REVIEW_ONLY", canonical_rows=4, candidate_rows_jsonl_sha256=sha(rows))
    candidate = dict(common, status="PASS_COMPLETE_CANDIDATE_JSONL_INTEGRITY_REVIEW_ONLY", canonical_rows=4, candidate_rows_jsonl_sha256=sha(rows), extraction_manifest_sha256=sha(manifest))
    dump(work / "internet_access_2_coverage_aware_carrier_latest.json", carrier)
    dump(web / "review_contract_consistency_latest.json", consistency)
    dump(web / "candidate_postcode_resolution_latest.json", resolution)
    dump(web / "candidate_jsonl_integrity_latest.json", candidate)
    return work, web, code


def base_audit(work_root: Path, web_root: Path, audit_output=None) -> dict:
    rows = work_root / "candidate_outputs/internet_access_2_candidates_latest.jsonl"
    manifest = work_root / "candidate_outputs/internet_access_2_extraction_manifest_latest.json"
    return {
        "schema_version": 3, "slot_id": "internet_access_2", "status": "PASS_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY",
        "provenance_artifact_count": 12, "canonical_rows": 4, "provenance_chain_sha256": "a" * 64,
        "candidate_rows_jsonl_sha256": sha(rows), "extraction_manifest_sha256": sha(manifest), "visible_example_rows": 3,
        "zip_sha256": "b" * 64, "zip_bytes": 4, "zip_container_status": "PASS_SAFE_OFFICIAL_ZIP_CONTAINER_REVIEW_ONLY",
        "zip_container_entry_count": 4, "zip_container_r1_postcode_file_count": 0, "zip_container_r2_postcode_file_count": 4,
        "zip_container_audit_sha256": "c" * 64, "actual_business_data_rows_written": 0, "scores_written": 0,
        "db_write": False, "migration": False, "production_deploy": False, "final_ready": False,
    }


module.base.audit = base_audit


def mutate_json(path: Path, mutator) -> None:
    payload = json.loads(path.read_text())
    mutator(payload)
    dump(path, payload)


def expect_fail(name: str, mutate, text: str) -> None:
    with tempfile.TemporaryDirectory() as temp:
        work, web, code = fixture(Path(temp))
        mutate(work, web, code)
        try:
            module.audit(work, web, automation_root=code)
        except ValueError as exc:
            if text not in str(exc):
                raise AssertionError(f"{name}: {exc}")
            passed.append(name)
        else:
            raise AssertionError(name)


with tempfile.TemporaryDirectory() as temp:
    work, web, code = fixture(Path(temp))
    output = web / "runner_provenance_audit_latest.json"
    report = module.audit(work, web, output, automation_root=code)
    for name, condition in [
        ("status", report["status"] == "PASS_EXTENDED_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY"),
        ("artifact_count_20", report["provenance_artifact_count"] == 20),
        ("base_artifact_count_12", report["base_provenance_artifact_count"] == 12),
        ("extended_audit_count_4", report["extended_audit_artifact_count"] == 4),
        ("execution_code_count_4", report["execution_code_artifact_count"] == 4),
        ("chain_sha", len(report["provenance_chain_sha256"]) == 64),
        ("audit_hashes", all(len(report[key]) == 64 for key in ("coverage_aware_inner_carrier_sha256", "review_contract_consistency_audit_sha256", "candidate_postcode_resolution_audit_sha256", "candidate_jsonl_integrity_audit_sha256"))),
        ("code_hashes", all(len(report[key]) == 64 for key in ("base_runner_code_sha256", "runtime_runner_code_sha256", "coverage_aware_extractor_code_sha256", "coverage_aware_carrier_code_sha256"))),
        ("exact_substitution", report["runtime_exact_extractor_substitution_verified"] is True),
        ("validation_total", report["combined_validation_passed"] == report["combined_validation_total"] == 415),
        ("output_written", output.is_file()),
        ("review_only", report["actual_business_data_rows_written"] == 0 and report["final_ready"] is False),
    ]:
        check(name, condition)

expect_fail("carrier_status_rejected", lambda w, v, c: mutate_json(w / "internet_access_2_coverage_aware_carrier_latest.json", lambda p: p.update(status="FAIL")), "carrier status")
expect_fail("validation_total_rejected", lambda w, v, c: mutate_json(v / "review_contract_consistency_latest.json", lambda p: p.update(combined_validation_total=414)), "validation total")
expect_fail("resolution_hash_rejected", lambda w, v, c: mutate_json(v / "candidate_postcode_resolution_latest.json", lambda p: p.update(candidate_rows_jsonl_sha256="0" * 64)), "resolution audit/candidate")
expect_fail("candidate_hash_rejected", lambda w, v, c: mutate_json(v / "candidate_jsonl_integrity_latest.json", lambda p: p.update(candidate_rows_jsonl_sha256="0" * 64)), "candidate integrity/candidate")
expect_fail("manifest_hash_rejected", lambda w, v, c: mutate_json(v / "candidate_jsonl_integrity_latest.json", lambda p: p.update(extraction_manifest_sha256="0" * 64)), "candidate integrity/extraction")
expect_fail("wrong_slot_rejected", lambda w, v, c: mutate_json(v / "candidate_postcode_resolution_latest.json", lambda p: p.update(slot_id="internet_access_3")), "slot_id")
expect_fail("business_write_rejected", lambda w, v, c: mutate_json(v / "candidate_jsonl_integrity_latest.json", lambda p: p.update(actual_business_data_rows_written=1)), "business rows")
expect_fail("final_ready_rejected", lambda w, v, c: mutate_json(v / "review_contract_consistency_latest.json", lambda p: p.update(final_ready=True)), "final_ready")
expect_fail("base_code_hash_rejected", lambda w, v, c: mutate_json(w / "internet_access_2_coverage_aware_carrier_latest.json", lambda p: p.update(base_runner_sha256="0" * 64)), "base runner SHA does not match")
expect_fail("runtime_code_hash_rejected", lambda w, v, c: mutate_json(w / "internet_access_2_coverage_aware_carrier_latest.json", lambda p: p.update(runtime_carrier_sha256="0" * 64)), "runtime SHA does not match")

def add_extra_runtime_edit(work: Path, web: Path, code: Path) -> None:
    runtime = work / module.RUNTIME_SCRIPT_NAME
    runtime.write_text(runtime.read_text() + "Write-Output 'extra'\n", encoding="utf-8")
    mutate_json(work / "internet_access_2_coverage_aware_carrier_latest.json", lambda payload: payload.update(runtime_carrier_sha256=sha(runtime)))


expect_fail("runtime_extra_edit_rejected", add_extra_runtime_edit, "changes beyond exact extractor substitution")
expect_fail("extractor_path_rejected", lambda w, v, c: mutate_json(w / "internet_access_2_coverage_aware_carrier_latest.json", lambda p: p.update(coverage_aware_extractor="wrong.py")), "extractor path mismatch")

expected = 24
if len(passed) != expected:
    raise AssertionError(f"{len(passed)} != {expected}: {passed}")
print(json.dumps({"status": "PASS", "tests_passed": len(passed), "tests_total": expected, "test_names": passed, "actual_business_data_rows_written": 0, "final_ready": False}, sort_keys=True))
