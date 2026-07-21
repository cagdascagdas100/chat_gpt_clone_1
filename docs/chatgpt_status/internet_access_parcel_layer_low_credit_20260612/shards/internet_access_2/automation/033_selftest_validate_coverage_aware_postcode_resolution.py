#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("032_validate_coverage_aware_postcode_resolution.py")
spec = importlib.util.spec_from_file_location("coverage_resolution", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import coverage-aware resolution validator")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROW_START = 1
module.ROW_END = 7
module.EXPECTED_ROWS = 7

passed: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    passed.append(name)


def common(i: int) -> dict:
    return {
        "slot_id": "internet_access_2",
        "canonical_row_no": i,
        "canonical_program_parcel_id": f"parcel_{i}",
        "internet_availability_quality_percent": None,
        "promotion_state": "REVIEW_ONLY_NOT_PROMOTED",
        "business_row_written": False,
        "fake_data": False,
    }


def base_rows() -> list[dict]:
    return [
        dict(common(1), postcode="AA11AA", postcode_selected_origin="CANONICAL", selected_postcode_in_current_r2=True,
             canonical_postcode_candidate="AA11AA", canonical_postcode_valid=True, canonical_postcode_in_current_r2=True,
             legacy_postcode_candidate=None, legacy_postcode_valid=False, legacy_postcode_in_current_r2=False,
             postcode_resolution="CANONICAL_CURRENT_R2_SELECTED", postcode_conflict=False,
             coverage_fallback_from_canonical=False, invalid_postcode_candidates=[],
             status=module.DIRECT, internet_match_method="CANONICAL_POSTCODE", internet_match_confidence=.95),
        dict(common(2), postcode="BB22BB", postcode_selected_origin="LEGACY", selected_postcode_in_current_r2=True,
             canonical_postcode_candidate=None, canonical_postcode_valid=False, canonical_postcode_in_current_r2=False,
             legacy_postcode_candidate="BB22BB", legacy_postcode_valid=True, legacy_postcode_in_current_r2=True,
             postcode_resolution="LEGACY_CURRENT_R2_FALLBACK_CANONICAL_MISSING", postcode_conflict=False,
             coverage_fallback_from_canonical=False, invalid_postcode_candidates=[],
             status=module.LEGACY, internet_match_method="LEGACY_POSTCODE_PROXY", internet_match_confidence=.70),
        dict(common(3), postcode="CC33CC", postcode_selected_origin="LEGACY", selected_postcode_in_current_r2=True,
             canonical_postcode_candidate="BAD", canonical_postcode_valid=False, canonical_postcode_in_current_r2=False,
             legacy_postcode_candidate="CC33CC", legacy_postcode_valid=True, legacy_postcode_in_current_r2=True,
             postcode_resolution="LEGACY_CURRENT_R2_FALLBACK_CANONICAL_INVALID", postcode_conflict=False,
             coverage_fallback_from_canonical=False, invalid_postcode_candidates=["BAD"],
             status=module.LEGACY, internet_match_method="LEGACY_POSTCODE_PROXY", internet_match_confidence=.70),
        dict(common(4), postcode="AA11AA", postcode_selected_origin="CANONICAL", selected_postcode_in_current_r2=True,
             canonical_postcode_candidate="AA11AA", canonical_postcode_valid=True, canonical_postcode_in_current_r2=True,
             legacy_postcode_candidate="BB22BB", legacy_postcode_valid=True, legacy_postcode_in_current_r2=True,
             postcode_resolution="CANONICAL_CURRENT_R2_SELECTED_LEGACY_CONFLICT", postcode_conflict=True,
             coverage_fallback_from_canonical=False, invalid_postcode_candidates=[],
             status=module.DIRECT, internet_match_method="CANONICAL_POSTCODE", internet_match_confidence=.95),
        dict(common(5), postcode="BB22BB", postcode_selected_origin="LEGACY", selected_postcode_in_current_r2=True,
             canonical_postcode_candidate="DD44DD", canonical_postcode_valid=True, canonical_postcode_in_current_r2=False,
             legacy_postcode_candidate="BB22BB", legacy_postcode_valid=True, legacy_postcode_in_current_r2=True,
             postcode_resolution="LEGACY_CURRENT_R2_FALLBACK_CANONICAL_NOT_IN_R2", postcode_conflict=True,
             coverage_fallback_from_canonical=True, invalid_postcode_candidates=[],
             status=module.LEGACY, internet_match_method="LEGACY_POSTCODE_PROXY", internet_match_confidence=.70),
        dict(common(6), postcode="DD44DD", postcode_selected_origin="CANONICAL", selected_postcode_in_current_r2=False,
             canonical_postcode_candidate="DD44DD", canonical_postcode_valid=True, canonical_postcode_in_current_r2=False,
             legacy_postcode_candidate="EE55EE", legacy_postcode_valid=True, legacy_postcode_in_current_r2=False,
             postcode_resolution="CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_NOT_IN_R2_CONFLICT", postcode_conflict=True,
             coverage_fallback_from_canonical=False, invalid_postcode_candidates=[],
             status=module.NO_DATA, internet_match_method="POSTCODE_NOT_IN_CURRENT_R2", internet_match_confidence=0),
        dict(common(7), postcode=None, postcode_selected_origin="NONE", selected_postcode_in_current_r2=False,
             canonical_postcode_candidate="BAD", canonical_postcode_valid=False, canonical_postcode_in_current_r2=False,
             legacy_postcode_candidate=None, legacy_postcode_valid=False, legacy_postcode_in_current_r2=False,
             postcode_resolution="NO_VALID_POSTCODE", postcode_conflict=False,
             coverage_fallback_from_canonical=False, invalid_postcode_candidates=["BAD"],
             status=module.NO_DATA, internet_match_method="NO_POSTCODE", internet_match_confidence=0),
    ]


def write_rows(root: Path, rows: list[dict]) -> tuple[Path, Path]:
    rows_path = root / "rows.jsonl"
    audit_path = root / "audit.json"
    rows_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return rows_path, audit_path


def expect_fail(name: str, mutate, text: str) -> None:
    rows = base_rows()
    mutate(rows)
    with tempfile.TemporaryDirectory() as temp:
        rows_path, _ = write_rows(Path(temp), rows)
        try:
            module.audit(rows_path)
        except ValueError as exc:
            if text not in str(exc):
                raise AssertionError(f"{name}: {exc}")
            passed.append(name)
        else:
            raise AssertionError(name)


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    rows_path, audit_path = write_rows(root, base_rows())
    result = module.audit(rows_path, audit_path)
    for name, condition in [
        ("status", result["status"] == "PASS_COVERAGE_AWARE_POSTCODE_RESOLUTION_AUDITED_REVIEW_ONLY"),
        ("exact_rows", result["canonical_rows"] == 7),
        ("resolution_counts", sum(result["resolution_counts"].values()) == 7),
        ("legacy_rows", result["legacy_current_r2_rows"] == 3),
        ("coverage_fallback_count", result["coverage_fallback_from_canonical_rows"] == 1),
        ("conflict_count", result["canonical_legacy_conflict_rows"] == 3),
        ("invalid_count", result["invalid_postcode_candidate_rows"] == 2),
        ("selected_not_r2_count", result["selected_postcode_not_in_current_r2_rows"] == 1),
        ("rows_hash", len(result["candidate_rows_jsonl_sha256"]) == 64),
        ("audit_written", audit_path.is_file()),
        ("no_business", result["actual_business_data_rows_written"] == 0),
        ("not_final", result["final_ready"] is False),
    ]:
        check(name, condition)

expect_fail("canonical_membership_rejected", lambda r: r[0].update(canonical_postcode_in_current_r2=False), "resolution reason")
expect_fail("invalid_membership_rejected", lambda r: r[2].update(canonical_postcode_in_current_r2=True), "invalid canonical")
expect_fail("coverage_fallback_flag_rejected", lambda r: r[4].update(coverage_fallback_from_canonical=False), "coverage fallback")
expect_fail("coverage_fallback_selected_rejected", lambda r: r[4].update(postcode="DD44DD"), "selected postcode")
expect_fail("coverage_fallback_origin_rejected", lambda r: r[4].update(postcode_selected_origin="CANONICAL"), "origin")
expect_fail("coverage_fallback_resolution_rejected", lambda r: r[4].update(postcode_resolution="CANONICAL_VALID_NOT_IN_CURRENT_R2"), "resolution reason")
expect_fail("direct_requires_current_r2", lambda r: r[0].update(selected_postcode_in_current_r2=False), "selected current-r2")
expect_fail("legacy_requires_current_r2", lambda r: r[1].update(legacy_postcode_in_current_r2=False), "resolution reason")
expect_fail("no_data_cannot_current_r2", lambda r: r[5].update(selected_postcode_in_current_r2=True), "selected current-r2")
expect_fail("conflict_flag_rejected", lambda r: r[5].update(postcode_conflict=False), "conflict flag")
expect_fail("invalid_list_rejected", lambda r: r[2].update(invalid_postcode_candidates=[]), "invalid postcode candidate")
expect_fail("duplicate_parcel_rejected", lambda r: r[1].update(canonical_program_parcel_id="parcel_1"), "duplicate")

expected = 24
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
