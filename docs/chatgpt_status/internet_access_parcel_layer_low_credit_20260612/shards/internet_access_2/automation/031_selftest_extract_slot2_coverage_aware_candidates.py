#!/usr/bin/env python3
"""Deterministic self-test for coverage-aware postcode selection."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).with_name("030_extract_slot2_coverage_aware_candidates.py")
spec = importlib.util.spec_from_file_location("coverage_aware_extractor", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import coverage-aware extractor")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

passed: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    passed.append(name)


coverage = {
    "AA11AA": {"postcode": "AA11AA", "gigabit_available_pct": 80},
    "BB22BB": {"postcode": "BB22BB", "sfbb_30mbps_available_pct": 90},
    "CC33CC": {"postcode": "CC33CC", "ufbb_100mbps_available_pct": 70},
}

cases = [
    ("canonical_current", "AA1 1AA", None, "AA11AA", "CANONICAL", "CANONICAL_CURRENT_R2_SELECTED", True, False),
    ("canonical_same", "AA1 1AA", "AA1 1AA", "AA11AA", "CANONICAL", "CANONICAL_CURRENT_R2_SELECTED_LEGACY_SAME", True, False),
    ("canonical_conflict", "AA1 1AA", "BB2 2BB", "AA11AA", "CANONICAL", "CANONICAL_CURRENT_R2_SELECTED_LEGACY_CONFLICT", True, False),
    ("canonical_invalid_legacy", "BAD", "BB2 2BB", "BB22BB", "LEGACY", "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_INVALID", True, False),
    ("canonical_missing_legacy", None, "BB2 2BB", "BB22BB", "LEGACY", "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_MISSING", True, False),
    ("canonical_not_r2_legacy_current", "DD4 4DD", "BB2 2BB", "BB22BB", "LEGACY", "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_NOT_IN_R2", True, True),
    ("canonical_not_r2_same", "DD4 4DD", "DD4 4DD", "DD44DD", "CANONICAL", "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_SAME", False, False),
    ("canonical_not_r2_conflict", "DD4 4DD", "EE5 5EE", "DD44DD", "CANONICAL", "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_NOT_IN_R2_CONFLICT", False, False),
    ("legacy_not_r2", None, "EE5 5EE", "EE55EE", "LEGACY", "LEGACY_VALID_NOT_IN_CURRENT_R2_CANONICAL_MISSING", False, False),
    ("no_valid", "BAD", None, None, "NONE", "NO_VALID_POSTCODE", False, False),
]
for name, canonical, legacy, selected, origin, resolution, in_r2, fallback in cases:
    result = module.resolve_postcode(canonical, legacy, coverage)
    check(name, (
        result["selected"] == selected
        and result["origin"] == origin
        and result["resolution"] == resolution
        and result["selected_in_current_r2"] is in_r2
        and result["coverage_fallback_from_canonical"] is fallback
    ))

canonical_rows = [
    {"row_no": 1, "parcel_id": "p1", "postcode": "AA1 1AA"},
    {"row_no": 2, "parcel_id": "p2", "postcode": "DD4 4DD"},
    {"row_no": 3, "parcel_id": "p3", "postcode": "BAD"},
    {"row_no": 4, "parcel_id": "p4"},
    {"row_no": 5, "parcel_id": "p5", "postcode": "EE5 5EE"},
]
legacy_rows = {
    2: {"row_no": 2, "postcode": "BB2 2BB"},
    3: {"row_no": 3, "postcode": "CC3 3CC"},
    4: {"row_no": 4, "postcode": "EE5 5EE"},
}
rows = module.build_rows(canonical_rows, legacy_rows, coverage)
check("row_count", len(rows) == 5)
check("direct_status", rows[0]["status"] == module.DIRECT and rows[0]["internet_match_confidence"] == 0.95)
check("coverage_fallback_status", rows[1]["status"] == module.LEGACY and rows[1]["coverage_fallback_from_canonical"] is True)
check("invalid_canonical_fallback", rows[2]["status"] == module.LEGACY and rows[2]["invalid_postcode_candidates"] == ["BAD"])
check("legacy_not_r2_no_data", rows[3]["status"] == module.NO_DATA and rows[3]["internet_match_method"] == "POSTCODE_NOT_IN_CURRENT_R2")
check("canonical_not_r2_no_data", rows[4]["status"] == module.NO_DATA and rows[4]["postcode"] == "EE55EE")
check("selected_flags", all(row["selected_postcode_in_current_r2"] is (row["status"] != module.NO_DATA) for row in rows))
check("no_scores", all(row["internet_availability_quality_percent"] is None for row in rows))
check("review_only", all(row["business_row_written"] is False and row["fake_data"] is False for row in rows))
check("fallback_never_direct", all(not row["coverage_fallback_from_canonical"] or row["status"] == module.LEGACY for row in rows))

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
