#!/usr/bin/env python3
"""Fail-closed audit of canonical/legacy postcode selection for internet_access_2.

This validates that malformed postcode candidates never become selected lookup
keys, valid legacy postcodes are used only as an explicit fallback, and
canonical/legacy conflicts remain visible without inventing parcel evidence.
"""
from __future__ import annotations

import argparse
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
    "CANONICAL_VALID",
    "CANONICAL_VALID_LEGACY_SAME",
    "CANONICAL_VALID_LEGACY_CONFLICT_IGNORED",
    "CANONICAL_VALID_LEGACY_INVALID_IGNORED",
    "LEGACY_VALID_FALLBACK_CANONICAL_MISSING",
    "LEGACY_VALID_FALLBACK_CANONICAL_INVALID",
    "NO_VALID_POSTCODE",
}


def normalize(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", "", str(value)).upper().strip()
    return text or None


def valid(value: str | None) -> bool:
    return bool(value and POSTCODE_RE.fullmatch(value))


def audit(rows_jsonl: Path, audit_output: Path | None = None) -> dict[str, Any]:
    if not rows_jsonl.is_file():
        raise ValueError("candidate JSONL missing")
    row_count = 0
    parcel_ids: set[str] = set()
    resolution_counts = {key: 0 for key in sorted(RESOLUTIONS)}
    fallback_rows = 0
    conflict_rows = 0
    invalid_candidate_rows = 0

    with rows_jsonl.open("r", encoding="utf-8-sig") as handle:
        for line_no, raw in enumerate(handle, start=1):
            if not raw.strip():
                raise ValueError(f"blank candidate JSONL line {line_no}")
            row = json.loads(raw)
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
            if row.get("canonical_postcode_valid") is not canonical_valid:
                raise ValueError(f"canonical postcode validity flag mismatch at line {line_no}")
            if row.get("legacy_postcode_valid") is not legacy_valid:
                raise ValueError(f"legacy postcode validity flag mismatch at line {line_no}")

            invalid_expected = [value for value, ok in ((canonical, canonical_valid), (legacy, legacy_valid)) if value and not ok]
            invalid_actual = row.get("invalid_postcode_candidates")
            if invalid_actual != invalid_expected:
                raise ValueError(f"invalid postcode candidate list mismatch at line {line_no}")
            if invalid_expected:
                invalid_candidate_rows += 1

            conflict = bool(canonical_valid and legacy_valid and canonical != legacy)
            if row.get("postcode_conflict") is not conflict:
                raise ValueError(f"postcode conflict flag mismatch at line {line_no}")
            if conflict:
                conflict_rows += 1

            resolution = row.get("postcode_resolution")
            if resolution not in RESOLUTIONS:
                raise ValueError(f"unsupported postcode resolution at line {line_no}")
            resolution_counts[resolution] += 1

            if canonical_valid:
                if selected != canonical:
                    raise ValueError(f"valid canonical postcode was not selected at line {line_no}")
                expected_resolution = (
                    "CANONICAL_VALID_LEGACY_CONFLICT_IGNORED" if conflict else
                    "CANONICAL_VALID_LEGACY_SAME" if legacy_valid else
                    "CANONICAL_VALID_LEGACY_INVALID_IGNORED" if legacy else
                    "CANONICAL_VALID"
                )
            elif legacy_valid:
                if selected != legacy:
                    raise ValueError(f"valid legacy fallback was not selected at line {line_no}")
                expected_resolution = "LEGACY_VALID_FALLBACK_CANONICAL_INVALID" if canonical else "LEGACY_VALID_FALLBACK_CANONICAL_MISSING"
                fallback_rows += 1
            else:
                if selected is not None:
                    raise ValueError(f"invalid postcode leaked into selected postcode at line {line_no}")
                expected_resolution = "NO_VALID_POSTCODE"
            if resolution != expected_resolution:
                raise ValueError(f"postcode resolution reason mismatch at line {line_no}")

            status = row.get("status")
            method = row.get("internet_match_method")
            confidence = float(row.get("internet_match_confidence", -1))
            if status == DIRECT:
                if method != "CANONICAL_POSTCODE" or confidence != 0.95 or not canonical_valid or selected != canonical:
                    raise ValueError(f"direct postcode resolution boundary mismatch at line {line_no}")
            elif status == LEGACY:
                if method != "LEGACY_POSTCODE_PROXY" or confidence != 0.70 or canonical_valid or not legacy_valid or selected != legacy:
                    raise ValueError(f"legacy postcode resolution boundary mismatch at line {line_no}")
            elif status == NO_DATA:
                if confidence != 0:
                    raise ValueError(f"NO_DATA confidence mismatch at line {line_no}")
                if method == "NO_POSTCODE" and selected is not None:
                    raise ValueError(f"NO_POSTCODE selected value mismatch at line {line_no}")
                if method == "POSTCODE_NOT_IN_CURRENT_R2" and not valid(selected):
                    raise ValueError(f"POSTCODE_NOT_IN_CURRENT_R2 selected value mismatch at line {line_no}")
                if method not in {"NO_POSTCODE", "POSTCODE_NOT_IN_CURRENT_R2"}:
                    raise ValueError(f"unsupported NO_DATA method at line {line_no}")
            else:
                raise ValueError(f"unsupported candidate status at line {line_no}")

            if row.get("business_row_written") is not False or row.get("fake_data") is not False:
                raise ValueError(f"review-only write boundary mismatch at line {line_no}")
            if row.get("internet_availability_quality_percent") is not None:
                raise ValueError(f"score unexpectedly emitted at line {line_no}")
            row_count += 1

    if row_count != EXPECTED_ROWS or ROW_START + row_count - 1 != ROW_END or len(parcel_ids) != EXPECTED_ROWS:
        raise ValueError(f"candidate postcode resolution exact row/range mismatch: {row_count}")

    result = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "status": "PASS_CANDIDATE_POSTCODE_RESOLUTION_AUDITED_REVIEW_ONLY",
        "canonical_rows": row_count,
        "row_start": ROW_START,
        "row_end": ROW_END,
        "resolution_counts": {key: value for key, value in resolution_counts.items() if value},
        "legacy_fallback_rows": fallback_rows,
        "canonical_legacy_conflict_rows": conflict_rows,
        "invalid_postcode_candidate_rows": invalid_candidate_rows,
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
