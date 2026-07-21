#!/usr/bin/env python3
"""Validate a completed internet_access_2 extraction and publish review-only web readback.

This publisher consumes runner outputs only. It never writes business datasets,
changes parcel geometry, emits a score, applies a migration, or marks final ready.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
ROW_START = 30762
ROW_END = 61522
EXPECTED_ROWS = 30761
ALLOWED_STATUS = {
    "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW",
    "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA",
    "NO_DATA",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    if manifest.get("slot_id") != SLOT_ID:
        raise ValueError("Manifest slot_id mismatch")
    if int(manifest.get("canonical_rows", -1)) != EXPECTED_ROWS:
        raise ValueError(f"Manifest must contain {EXPECTED_ROWS} canonical rows")
    direct = int(manifest.get("direct_current_r2_matches", -1))
    legacy = int(manifest.get("legacy_current_r2_matches_pending_spatial_qa", -1))
    no_data = int(manifest.get("no_data_rows", -1))
    if min(direct, legacy, no_data) < 0 or direct + legacy + no_data != EXPECTED_ROWS:
        raise ValueError("Manifest status counts do not sum to the exact slot size")
    if int(manifest.get("scores_written", -1)) != 0:
        raise ValueError("Scores must remain zero in review-only output")
    if int(manifest.get("actual_business_data_rows_written", -1)) != 0:
        raise ValueError("Business rows must remain zero")
    if manifest.get("final_ready") is not False:
        raise ValueError("final_ready must remain false")
    return manifest


def load_rows(path: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    row_numbers: set[int] = set()
    parcel_ids: set[str] = set()
    counts = {status: 0 for status in ALLOWED_STATUS}

    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("slot_id") != SLOT_ID:
                raise ValueError(f"line {line_no}: slot_id mismatch")
            number = int(row.get("canonical_row_no"))
            if not ROW_START <= number <= ROW_END:
                raise ValueError(f"line {line_no}: row outside slot range")
            parcel_id = str(row.get("canonical_program_parcel_id") or "").strip()
            if not parcel_id:
                raise ValueError(f"line {line_no}: blank parcel id")
            if number in row_numbers or parcel_id in parcel_ids:
                raise ValueError(f"line {line_no}: duplicate row number or parcel id")
            row_numbers.add(number)
            parcel_ids.add(parcel_id)

            status = row.get("status")
            if status not in ALLOWED_STATUS:
                raise ValueError(f"line {line_no}: unsupported status {status!r}")
            counts[status] += 1
            if row.get("internet_availability_quality_percent") is not None:
                raise ValueError(f"line {line_no}: score unexpectedly emitted")
            if row.get("business_row_written") is not False:
                raise ValueError(f"line {line_no}: business row flag must be false")
            if row.get("fake_data") is not False:
                raise ValueError(f"line {line_no}: fake_data must be false")
            if status == "NO_DATA" and float(row.get("internet_match_confidence", 0)) != 0.0:
                raise ValueError(f"line {line_no}: NO_DATA confidence must be zero")
            rows.append(row)

    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} JSONL rows, found {len(rows)}")
    if min(row_numbers) != ROW_START or max(row_numbers) != ROW_END:
        raise ValueError("JSONL range endpoints are incomplete")
    return rows, counts


def select_examples(rows: list[dict[str, Any]], per_status: int = 3) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen = {status: 0 for status in ALLOWED_STATUS}
    for row in rows:
        status = row["status"]
        if seen[status] >= per_status:
            continue
        selected.append({
            "canonical_row_no": row["canonical_row_no"],
            "canonical_program_parcel_id": row["canonical_program_parcel_id"],
            "hmlr_inspire_id": row.get("hmlr_inspire_id"),
            "postcode": row.get("postcode"),
            "status": status,
            "internet_match_method": row.get("internet_match_method"),
            "source_level": row.get("source_level"),
            "internet_match_confidence": row.get("internet_match_confidence"),
            "gigabit_available_pct": row.get("gigabit_available_pct"),
            "ufbb_100mbps_available_pct": row.get("ufbb_100mbps_available_pct"),
            "sfbb_30mbps_available_pct": row.get("sfbb_30mbps_available_pct"),
            "unable_30mbps_pct": row.get("unable_30mbps_pct"),
            "source_file": row.get("source_file"),
            "promotion_state": row.get("promotion_state"),
            "business_row_written": False,
        })
        seen[status] += 1
        if all(value >= per_status for value in seen.values()):
            break
    return selected


def publish(manifest_path: Path, rows_path: Path, output_root: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    rows, counts = load_rows(rows_path)
    expected_counts = {
        "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW": int(manifest["direct_current_r2_matches"]),
        "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA": int(manifest["legacy_current_r2_matches_pending_spatial_qa"]),
        "NO_DATA": int(manifest["no_data_rows"]),
    }
    if counts != expected_counts:
        raise ValueError(f"JSONL counts differ from manifest: {counts} != {expected_counts}")

    output_root.mkdir(parents=True, exist_ok=True)
    examples = select_examples(rows)
    readback = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "status": "REAL_RUN_READBACK_VALIDATED_REVIEW_ONLY",
        "canonical_rows": EXPECTED_ROWS,
        "row_start": ROW_START,
        "row_end": ROW_END,
        "status_counts": counts,
        "manifest_sha256": sha256_file(manifest_path),
        "rows_jsonl_sha256": sha256_file(rows_path),
        "visible_example_rows": len(examples),
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    examples_payload = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "data_level": "POSTCODE_LEVEL_ONLY",
        "truth_boundary": "Examples are review-only postcode proxies. No row is a measured parcel speed or promoted business value.",
        "rows": examples,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
    }
    (output_root / "runner_readback_latest.json").write_text(
        json.dumps(readback, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_root / "verified_examples_latest.json").write_text(
        json.dumps(examples_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return readback


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--rows-jsonl", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    result = publish(args.manifest, args.rows_jsonl, args.output_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
