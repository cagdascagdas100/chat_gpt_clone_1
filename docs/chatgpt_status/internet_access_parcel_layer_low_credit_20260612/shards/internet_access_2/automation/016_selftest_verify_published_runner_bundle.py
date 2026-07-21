#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("015_verify_published_runner_bundle.py")
spec = importlib.util.spec_from_file_location("bundle_verifier", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import bundle verifier")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROW_START = 1
module.ROW_END = 6
module.EXPECTED_ROWS = 6

passed: list[str] = []


def check(name: str, ok: bool) -> None:
    if not ok:
        raise AssertionError(name)
    passed.append(name)


def expect_fail(name: str, fn, text: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if text not in str(exc):
            raise AssertionError(f"{name}: {exc}")
        passed.append(name)
    else:
        raise AssertionError(name)


def base_payloads():
    counts = {
        "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW": 2,
        "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA": 2,
        "NO_DATA": 2,
    }
    readback = {
        "schema_version": 3,
        "slot_id": "internet_access_2",
        "status": "REAL_RUN_READBACK_VALIDATED_REVIEW_ONLY",
        "canonical_rows": 6,
        "row_start": 1,
        "row_end": 6,
        "status_counts": counts,
        "manifest_sha256": "a" * 64,
        "rows_jsonl_sha256": "b" * 64,
        "visible_example_rows": 6,
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    rows = []
    statuses = (
        ["CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW"] * 2
        + ["CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA"] * 2
        + ["NO_DATA"] * 2
    )
    for index, status in enumerate(statuses, start=1):
        no_data = status == "NO_DATA"
        rows.append({
            "canonical_row_no": index,
            "canonical_program_parcel_id": f"parcel_{index}",
            "postcode": None if no_data else f"AA{index} 1AA",
            "status": status,
            "internet_match_confidence": 0 if no_data else 0.95,
            "gigabit_available_pct": None if no_data else 80,
            "ufbb_100mbps_available_pct": None if no_data else 90,
            "sfbb_30mbps_available_pct": None if no_data else 99,
            "unable_30mbps_pct": None if no_data else 1,
            "business_row_written": False,
        })
    examples = {
        "schema_version": 3,
        "slot_id": "internet_access_2",
        "data_level": "POSTCODE_LEVEL_ONLY",
        "truth_boundary": "review only",
        "rows": rows,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
    }
    return readback, examples


with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    audit_path = root / "runner_bundle_audit_latest.json"
    readback, examples = base_payloads()
    (root / "runner_readback_latest.json").write_text(json.dumps(readback), encoding="utf-8")
    (root / "verified_examples_latest.json").write_text(json.dumps(examples), encoding="utf-8")
    result = module.audit(root, audit_path)
    check("status", result["status"] == "PASS_REAL_RUN_WEB_BUNDLE_AUDITED_REVIEW_ONLY")
    check("exact_rows", result["canonical_rows"] == 6 and sum(result["status_counts"].values()) == 6)
    check("bundle_hashes", len(result["runner_readback_file_sha256"]) == 64 and len(result["verified_examples_file_sha256"]) == 64)
    check("source_hashes", result["source_manifest_sha256"] == "a" * 64 and result["source_rows_jsonl_sha256"] == "b" * 64)
    check("example_count", result["visible_example_rows"] == 6)
    check("audit_written", audit_path.exists())
    check("truth_boundary", result["data_level"] == "POSTCODE_LEVEL_ONLY")
    check("no_business_write", result["actual_business_data_rows_written"] == 0 and result["scores_written"] == 0)
    check("not_final", result["final_ready"] is False)

    bad = dict(readback)
    bad["manifest_sha256"] = "x"
    expect_fail("bad_hash_rejected", lambda: module.validate_readback(bad), "not a lowercase SHA-256")
    bad = dict(readback)
    bad["status_counts"] = dict(readback["status_counts"])
    bad["status_counts"]["NO_DATA"] = 1
    expect_fail("count_sum_rejected", lambda: module.validate_readback(bad), "do not sum")
    bad = dict(readback)
    bad["final_ready"] = True
    expect_fail("final_ready_rejected", lambda: module.validate_readback(bad), "final_ready")

    bad_examples = dict(examples)
    bad_examples["rows"] = list(examples["rows"])
    bad_examples["rows"][0] = dict(bad_examples["rows"][0])
    bad_examples["rows"][0]["canonical_row_no"] = 2
    expect_fail("duplicate_identity_rejected", lambda: module.validate_examples(bad_examples, readback["status_counts"], 6), "duplicates")
    bad_examples = dict(examples)
    bad_examples["rows"] = list(examples["rows"])
    bad_examples["rows"][4] = dict(bad_examples["rows"][4])
    bad_examples["rows"][4]["postcode"] = "AA1 1AA"
    expect_fail("no_data_postcode_rejected", lambda: module.validate_examples(bad_examples, readback["status_counts"], 6), "NO_DATA truth boundary")
    bad_examples = dict(examples)
    bad_examples["rows"] = list(examples["rows"])
    bad_examples["rows"][4] = dict(bad_examples["rows"][4])
    bad_examples["rows"][4]["gigabit_available_pct"] = 0
    expect_fail("no_data_metric_rejected", lambda: module.validate_examples(bad_examples, readback["status_counts"], 6), "NO_DATA metric")
    bad_examples = dict(examples)
    bad_examples["rows"] = list(examples["rows"])
    bad_examples["rows"][0] = dict(bad_examples["rows"][0])
    bad_examples["rows"][0]["business_row_written"] = True
    expect_fail("business_flag_rejected", lambda: module.validate_examples(bad_examples, readback["status_counts"], 6), "business_row_written")
    bad_examples = dict(examples)
    bad_examples["data_level"] = "PARCEL_LEVEL"
    expect_fail("data_level_rejected", lambda: module.validate_examples(bad_examples, readback["status_counts"], 6), "postcode-only")
    bad_examples = dict(examples)
    bad_examples["rows"] = list(examples["rows"][:5])
    expect_fail("visible_count_rejected", lambda: module.validate_examples(bad_examples, readback["status_counts"], 6), "disagrees")

print(json.dumps({"status": "PASS", "tests_passed": len(passed), "tests_total": 18, "test_names": passed, "actual_business_data_rows_written": 0, "final_ready": False}, sort_keys=True))
