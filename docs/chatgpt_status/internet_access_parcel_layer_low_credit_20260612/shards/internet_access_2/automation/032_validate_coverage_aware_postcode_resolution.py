#!/usr/bin/env python3
"""Fail-closed audit of coverage-aware postcode selection for internet_access_2."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
ROW_START = 30762
ROW_END = 61522
EXPECTED_ROWS = 30761
POSTCODE_RE = re.compile(r"^(GIR0AA|[A-Z]{1,2}[0-9][A-Z0-9]?[0-9][A-Z]{2})$")
DIRECT = "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW"
LEGACY = "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA"
NO_DATA = "NO_DATA"

RESOLUTIONS = {
    "CANONICAL_CURRENT_R2_SELECTED",
    "CANONICAL_CURRENT_R2_SELECTED_LEGACY_SAME",
    "CANONICAL_CURRENT_R2_SELECTED_LEGACY_CONFLICT",
    "CANONICAL_CURRENT_R2_SELECTED_LEGACY_INVALID",
    "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_MISSING",
    "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_INVALID",
    "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_NOT_IN_R2",
    "CANONICAL_VALID_NOT_IN_CURRENT_R2",
    "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_SAME",
    "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_NOT_IN_R2_CONFLICT",
    "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_INVALID",
    "LEGACY_VALID_NOT_IN_CURRENT_R2_CANONICAL_MISSING",
    "LEGACY_VALID_NOT_IN_CURRENT_R2_CANONICAL_INVALID",
    "NO_VALID_POSTCODE",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", "", str(value)).upper().strip()
    return text or None


def valid(value: str | None) -> bool:
    return bool(value and POSTCODE_RE.fullmatch(value))


def expected_selection(
    canonical: str | None,
    legacy: str | None,
    canonical_valid: bool,
    legacy_valid: bool,
    canonical_in_r2: bool,
    legacy_in_r2: bool,
) -> tuple[str | None, str, str, bool]:
    conflict = bool(canonical_valid and legacy_valid and canonical != legacy)
    if canonical_in_r2:
        if conflict:
            resolution = "CANONICAL_CURRENT_R2_SELECTED_LEGACY_CONFLICT"
        elif legacy_valid:
            resolution = "CANONICAL_CURRENT_R2_SELECTED_LEGACY_SAME"
        elif legacy:
            resolution = "CANONICAL_CURRENT_R2_SELECTED_LEGACY_INVALID"
        else:
            resolution = "CANONICAL_CURRENT_R2_SELECTED"
        return canonical, "CANONICAL", resolution, False
    if legacy_in_r2:
        if canonical_valid:
            return legacy, "LEGACY", "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_NOT_IN_R2", True
        if canonical:
            return legacy, "LEGACY", "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_INVALID", False
        return legacy, "LEGACY", "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_MISSING", False
    if canonical_valid:
        if conflict:
            resolution = "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_NOT_IN_R2_CONFLICT"
        elif legacy_valid:
            resolution = "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_SAME"
        elif legacy:
            resolution = "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_INVALID"
        else:
            resolution = "CANONICAL_VALID_NOT_IN_CURRENT_R2"
        return canonical, "CANONICAL", resolution, False
    if legacy_valid:
        resolution = (
            "LEGACY_VALID_NOT_IN_CURRENT_R2_CANONICAL_INVALID"
            if canonical
            else "LEGACY_VALID_NOT_IN_CURRENT_R2_CANONICAL_MISSING"
        )
        return legacy, "LEGACY", resolution, False
    return None, "NONE", "NO_VALID_POSTCODE", False


def audit(rows_jsonl: Path, audit_output: Path | None = None) -> dict[str, Any]:
    if not rows_jsonl.is_file():
        raise ValueError("candidate JSONL missing")

    row_count = 0
    parcel_ids: set[str] = set()
    resolution_counts = {key: 0 for key in sorted(RESOLUTIONS)}
    fallback_rows = 0
    legacy_rows = 0
    conflict_rows = 0
    invalid_candidate_rows = 0
    selected_not_in_r2_rows = 0

    with rows_jsonl.open("r", encoding="utf-8-sig") as handle:
        for line_no, raw in enumerate(handle, start=1):
            if not raw.strip():
                raise ValueError(f"blank candidate JSONL line {line_no}")
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid candidate JSONL line {line_no}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"candidate line {line_no} must be an object")
            expected_row = ROW_START + row_count
            if row.get("slot_id") != SLOT_ID or int(row.get("canonical_row_no", -1)) != expected_row:
                raise ValueError(f"candidate identity/sequence mismatch at line {line_no}")
            parcel_id = str(row.get("canonical_program_parcel_id") or "").strip()
            if not parcel_id or parcel_id in parcel_ids:
                raise ValueError(f"candidate parcel identity missing or duplicate at line {line_no}")
            parcel_ids.add(parcel_id)

            selected = normalize(row.get("postcode"))
            canonical = normalize(row.get("canonical_postcode_candidate"))
            legacy = normalize(row.get("legacy_postcode_candidate"))
            canonical_valid = valid(canonical)
            legacy_valid = valid(legacy)
            canonical_in_r2 = row.get("canonical_postcode_in_current_r2")
            legacy_in_r2 = row.get("legacy_postcode_in_current_r2")
            selected_in_r2 = row.get("selected_postcode_in_current_r2")
            if row.get("canonical_postcode_valid") is not canonical_valid:
                raise ValueError(f"canonical postcode validity flag mismatch at line {line_no}")
            if row.get("legacy_postcode_valid") is not legacy_valid:
                raise ValueError(f"legacy postcode validity flag mismatch at line {line_no}")
            if not isinstance(canonical_in_r2, bool) or not isinstance(legacy_in_r2, bool) or not isinstance(selected_in_r2, bool):
                raise ValueError(f"current-r2 membership flags must be boolean at line {line_no}")
            if canonical_in_r2 and not canonical_valid:
                raise ValueError(f"invalid canonical postcode marked current-r2 at line {line_no}")
            if legacy_in_r2 and not legacy_valid:
                raise ValueError(f"invalid legacy postcode marked current-r2 at line {line_no}")

            invalid_expected = [value for value, ok in ((canonical, canonical_valid), (legacy, legacy_valid)) if value and not ok]
            if row.get("invalid_postcode_candidates") != invalid_expected:
                raise ValueError(f"invalid postcode candidate list mismatch at line {line_no}")
            if invalid_expected:
                invalid_candidate_rows += 1

            conflict = bool(canonical_valid and legacy_valid and canonical != legacy)
            if row.get("postcode_conflict") is not conflict:
                raise ValueError(f"postcode conflict flag mismatch at line {line_no}")
            if conflict:
                conflict_rows += 1

            expected_selected, expected_origin, expected_resolution, expected_fallback = expected_selection(
                canonical, legacy, canonical_valid, legacy_valid, canonical_in_r2, legacy_in_r2
            )
            if selected != expected_selected:
                raise ValueError(f"coverage-aware selected postcode mismatch at line {line_no}")
            if row.get("postcode_selected_origin") != expected_origin:
                raise ValueError(f"selected postcode origin mismatch at line {line_no}")
            if row.get("postcode_resolution") not in RESOLUTIONS or row.get("postcode_resolution") != expected_resolution:
                raise ValueError(f"coverage-aware postcode resolution reason mismatch at line {line_no}")
            if row.get("coverage_fallback_from_canonical") is not expected_fallback:
                raise ValueError(f"coverage fallback flag mismatch at line {line_no}")

            expected_selected_in_r2 = (
                canonical_in_r2 if expected_origin == "CANONICAL"
                else legacy_in_r2 if expected_origin == "LEGACY"
                else False
            )
            if selected_in_r2 is not expected_selected_in_r2:
                raise ValueError(f"selected current-r2 membership mismatch at line {line_no}")
            if selected and not selected_in_r2:
                selected_not_in_r2_rows += 1
            if expected_fallback:
                fallback_rows += 1

            status = row.get("status")
            method = row.get("internet_match_method")
            confidence = float(row.get("internet_match_confidence", -1))
            if status == DIRECT:
                if (
                    method != "CANONICAL_POSTCODE"
                    or confidence != 0.95
                    or expected_origin != "CANONICAL"
                    or not canonical_in_r2
                    or not selected_in_r2
                ):
                    raise ValueError(f"direct coverage-aware boundary mismatch at line {line_no}")
            elif status == LEGACY:
                legacy_rows += 1
                if (
                    method != "LEGACY_POSTCODE_PROXY"
                    or confidence != 0.70
                    or expected_origin != "LEGACY"
                    or not legacy_in_r2
                    or not selected_in_r2
                ):
                    raise ValueError(f"legacy coverage-aware boundary mismatch at line {line_no}")
            elif status == NO_DATA:
                if confidence != 0 or selected_in_r2:
                    raise ValueError(f"NO_DATA coverage-aware boundary mismatch at line {line_no}")
                if method == "NO_POSTCODE":
                    if selected is not None:
                        raise ValueError(f"NO_POSTCODE selected value mismatch at line {line_no}")
                elif method == "POSTCODE_NOT_IN_CURRENT_R2":
                    if not valid(selected):
                        raise ValueError(f"POSTCODE_NOT_IN_CURRENT_R2 selected value mismatch at line {line_no}")
                else:
                    raise ValueError(f"unsupported NO_DATA method at line {line_no}")
            else:
                raise ValueError(f"unsupported candidate status at line {line_no}")

            if row.get("business_row_written") is not False or row.get("fake_data") is not False:
                raise ValueError(f"review-only write boundary mismatch at line {line_no}")
            if row.get("internet_availability_quality_percent") is not None:
                raise ValueError(f"score unexpectedly emitted at line {line_no}")

            resolution_counts[expected_resolution] += 1
            row_count += 1

    if row_count != EXPECTED_ROWS or ROW_START + row_count - 1 != ROW_END or len(parcel_ids) != EXPECTED_ROWS:
        raise ValueError(f"coverage-aware postcode exact row/range mismatch: {row_count}")

    result = {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "status": "PASS_COVERAGE_AWARE_POSTCODE_RESOLUTION_AUDITED_REVIEW_ONLY",
        "canonical_rows": row_count,
        "row_start": ROW_START,
        "row_end": ROW_END,
        "resolution_counts": {key: value for key, value in resolution_counts.items() if value},
        "legacy_current_r2_rows": legacy_rows,
        "coverage_fallback_from_canonical_rows": fallback_rows,
        "canonical_legacy_conflict_rows": conflict_rows,
        "invalid_postcode_candidate_rows": invalid_candidate_rows,
        "selected_postcode_not_in_current_r2_rows": selected_not_in_r2_rows,
        "candidate_rows_jsonl_sha256": sha256_file(rows_jsonl),
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    if audit_output is not None:
        audit_output.parent.mkdir(parents=True, exist_ok=True)
        audit_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows-jsonl", required=True, type=Path)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.rows_jsonl, args.audit_output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
