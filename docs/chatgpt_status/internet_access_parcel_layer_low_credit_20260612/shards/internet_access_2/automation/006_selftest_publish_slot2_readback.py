#!/usr/bin/env python3
"""Deterministic safety test for the internet_access_2 readback publisher."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("005_publish_slot2_readback.py")
spec = importlib.util.spec_from_file_location("internet_access_2_publisher", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import publisher: {SCRIPT}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROW_START = 1
module.ROW_END = 6
module.EXPECTED_ROWS = 6

passed: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    passed.append(name)


with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    manifest_path = root / "manifest.json"
    rows_path = root / "rows.jsonl"
    out = root / "web"
    manifest = {
        "slot_id": "internet_access_2",
        "canonical_rows": 6,
        "direct_current_r2_matches": 2,
        "legacy_current_r2_matches_pending_spatial_qa": 2,
        "no_data_rows": 2,
        "scores_written": 0,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    statuses = [
        "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW",
        "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW",
        "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA",
        "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA",
        "NO_DATA",
        "NO_DATA",
    ]
    rows = []
    for index, status in enumerate(statuses, start=1):
        rows.append({
            "slot_id": "internet_access_2",
            "canonical_row_no": index,
            "canonical_program_parcel_id": f"parcel_{index}",
            "postcode": None if status == "NO_DATA" else f"AA1{index}AA",
            "status": status,
            "internet_match_method": "NO_POSTCODE" if status == "NO_DATA" else "CANONICAL_POSTCODE",
            "source_level": "NO_DATA" if status == "NO_DATA" else "POSTCODE_PROXY",
            "internet_match_confidence": 0.0 if status == "NO_DATA" else 0.95,
            "internet_availability_quality_percent": None,
            "promotion_state": "REVIEW_ONLY_NOT_PROMOTED",
            "business_row_written": False,
            "fake_data": False,
        })
    rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    readback = module.publish(manifest_path, rows_path, out)
    check("readback_status", readback["status"] == "REAL_RUN_READBACK_VALIDATED_REVIEW_ONLY")
    check("exact_row_count", readback["canonical_rows"] == 6)
    check("status_counts_match", sum(readback["status_counts"].values()) == 6)
    check("hashes_present", len(readback["manifest_sha256"]) == 64 and len(readback["rows_jsonl_sha256"]) == 64)
    check("web_files_written", (out / "runner_readback_latest.json").exists() and (out / "verified_examples_latest.json").exists())
    examples = json.loads((out / "verified_examples_latest.json").read_text(encoding="utf-8"))
    check("examples_truth_boundary", examples["data_level"] == "POSTCODE_LEVEL_ONLY" and examples["actual_business_data_rows_written"] == 0)
    check("no_score_or_promotion", all(row["business_row_written"] is False for row in examples["rows"]))
    check("final_ready_false", readback["final_ready"] is False)

    bad_manifest = dict(manifest)
    bad_manifest["actual_business_data_rows_written"] = 1
    bad_manifest_path = root / "bad_manifest.json"
    bad_manifest_path.write_text(json.dumps(bad_manifest), encoding="utf-8")
    try:
        module.load_manifest(bad_manifest_path)
    except ValueError:
        check("business_write_rejected", True)
    else:
        raise AssertionError("business_write_rejected")

    bad_rows = list(rows)
    bad_rows[0] = dict(bad_rows[0])
    bad_rows[0]["internet_availability_quality_percent"] = 50
    bad_rows_path = root / "bad_rows.jsonl"
    bad_rows_path.write_text("\n".join(json.dumps(row) for row in bad_rows) + "\n", encoding="utf-8")
    try:
        module.load_rows(bad_rows_path)
    except ValueError:
        check("score_rejected", True)
    else:
        raise AssertionError("score_rejected")

print(json.dumps({"status": "PASS", "tests_passed": len(passed), "tests_total": 10, "test_names": passed, "actual_business_data_rows_written": 0, "final_ready": False}, sort_keys=True))
