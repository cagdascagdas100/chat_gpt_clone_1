#!/usr/bin/env python3
"""Fail-closed audit of the published internet_access_2 runner web bundle.

This tool validates only review outputs produced by the existing canonical runner.
It never invents rows, changes parcel/business data, promotes scores, or marks the
slot final. A successful audit proves that the two published JSON files agree on
row counts, statuses, examples, hashes and truth-boundary flags.
"""
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
MAX_EXAMPLES = 9
MAX_PER_STATUS = 3
ALLOWED_STATUS = {
    "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW",
    "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA",
    "NO_DATA",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Required published file missing: {path.name}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Published file must contain a JSON object: {path.name}")
    return payload


def validate_readback(payload: dict[str, Any]) -> dict[str, int]:
    if payload.get("slot_id") != SLOT_ID:
        raise ValueError("runner readback slot_id mismatch")
    if payload.get("status") != "REAL_RUN_READBACK_VALIDATED_REVIEW_ONLY":
        raise ValueError("runner readback status mismatch")
    if int(payload.get("canonical_rows", -1)) != EXPECTED_ROWS:
        raise ValueError("runner readback canonical row count mismatch")
    if int(payload.get("row_start", -1)) != ROW_START or int(payload.get("row_end", -1)) != ROW_END:
        raise ValueError("runner readback range mismatch")
    raw_counts = payload.get("status_counts")
    if not isinstance(raw_counts, dict) or set(raw_counts) != ALLOWED_STATUS:
        raise ValueError("runner readback status keys mismatch")
    counts = {status: int(raw_counts[status]) for status in ALLOWED_STATUS}
    if min(counts.values()) < 0 or sum(counts.values()) != EXPECTED_ROWS:
        raise ValueError("runner readback status counts do not sum to slot size")
    for key in ("manifest_sha256", "rows_jsonl_sha256"):
        value = str(payload.get(key) or "").lower()
        if not HEX64.fullmatch(value):
            raise ValueError(f"runner readback {key} is not a lowercase SHA-256")
    visible = int(payload.get("visible_example_rows", -1))
    if not 0 <= visible <= MAX_EXAMPLES:
        raise ValueError("runner readback visible example count outside 0-9")
    if int(payload.get("actual_business_data_rows_written", -1)) != 0 or int(payload.get("scores_written", -1)) != 0:
        raise ValueError("runner readback reports business rows or scores")
    for key in ("db_write", "migration", "production_deploy"):
        if payload.get(key) is not False:
            raise ValueError(f"runner readback {key} must be false")
    if payload.get("final_ready") is not False:
        raise ValueError("runner readback final_ready must be false")
    return counts


def validate_examples(payload: dict[str, Any], counts: dict[str, int], expected_visible: int) -> list[dict[str, Any]]:
    if payload.get("slot_id") != SLOT_ID:
        raise ValueError("examples slot_id mismatch")
    if payload.get("data_level") != "POSTCODE_LEVEL_ONLY":
        raise ValueError("examples data level must remain postcode-only")
    if not str(payload.get("truth_boundary") or "").strip():
        raise ValueError("examples truth boundary is missing")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("examples rows must be a list")
    if len(rows) != expected_visible or len(rows) > MAX_EXAMPLES:
        raise ValueError("examples count disagrees with runner readback")
    if int(payload.get("actual_business_data_rows_written", -1)) != 0 or payload.get("final_ready") is not False:
        raise ValueError("examples business/final boundary mismatch")

    row_numbers: set[int] = set()
    parcel_ids: set[str] = set()
    per_status = {status: 0 for status in ALLOWED_STATUS}
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"example {index} is not an object")
        number = int(row.get("canonical_row_no", -1))
        parcel_id = str(row.get("canonical_program_parcel_id") or "").strip()
        status = row.get("status")
        if not ROW_START <= number <= ROW_END or not parcel_id:
            raise ValueError(f"example {index} identity/range mismatch")
        if number in row_numbers or parcel_id in parcel_ids:
            raise ValueError(f"example {index} duplicates row number or parcel id")
        if status not in ALLOWED_STATUS:
            raise ValueError(f"example {index} has unsupported status")
        row_numbers.add(number)
        parcel_ids.add(parcel_id)
        per_status[status] += 1
        if per_status[status] > MAX_PER_STATUS or per_status[status] > counts[status]:
            raise ValueError(f"example status quota exceeds published count: {status}")
        if row.get("business_row_written") is not False:
            raise ValueError(f"example {index} business_row_written must be false")
        confidence = float(row.get("internet_match_confidence") or 0)
        if not 0 <= confidence <= 1:
            raise ValueError(f"example {index} confidence outside 0-1")
        if status == "NO_DATA":
            if confidence != 0 or row.get("postcode") not in (None, "", "NO_DATA"):
                raise ValueError(f"example {index} NO_DATA truth boundary mismatch")
            for field in ("gigabit_available_pct", "ufbb_100mbps_available_pct", "sfbb_30mbps_available_pct", "unable_30mbps_pct"):
                if row.get(field) is not None:
                    raise ValueError(f"example {index} NO_DATA metric must be null: {field}")
    return rows


def audit(output_root: Path, audit_output: Path | None = None) -> dict[str, Any]:
    readback_path = output_root / "runner_readback_latest.json"
    examples_path = output_root / "verified_examples_latest.json"
    readback = load_json(readback_path)
    examples = load_json(examples_path)
    counts = validate_readback(readback)
    rows = validate_examples(examples, counts, int(readback["visible_example_rows"]))
    result = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "status": "PASS_REAL_RUN_WEB_BUNDLE_AUDITED_REVIEW_ONLY",
        "canonical_rows": EXPECTED_ROWS,
        "row_start": ROW_START,
        "row_end": ROW_END,
        "status_counts": counts,
        "visible_example_rows": len(rows),
        "runner_readback_file_sha256": sha256_file(readback_path),
        "verified_examples_file_sha256": sha256_file(examples_path),
        "source_manifest_sha256": str(readback["manifest_sha256"]).lower(),
        "source_rows_jsonl_sha256": str(readback["rows_jsonl_sha256"]).lower(),
        "data_level": "POSTCODE_LEVEL_ONLY",
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
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.output_root, args.audit_output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
