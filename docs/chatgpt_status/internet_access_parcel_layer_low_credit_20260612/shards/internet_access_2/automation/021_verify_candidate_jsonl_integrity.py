#!/usr/bin/env python3
"""Stream and fail-close the complete internet_access_2 candidate JSONL.

This is review-only validation. It verifies every candidate row, the exact slot
range, status-specific truth boundaries, manifest totals and the candidate file
SHA-256. It never writes parcel/business data or marks the slot final.
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
POSTCODE_RE = re.compile(r"^(GIR0AA|[A-Z]{1,2}[0-9][A-Z0-9]?[0-9][A-Z]{2})$")
DIRECT = "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW"
LEGACY = "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA"
NO_DATA = "NO_DATA"
ALLOWED_STATUS = (DIRECT, LEGACY, NO_DATA)
METRIC_FIELDS = (
    "sfbb_30mbps_available_pct", "ufbb_100mbps_available_pct",
    "ufbb_300mbps_available_pct", "gigabit_available_pct",
    "unable_30mbps_pct", "unable_decent_fixed_or_fwa_pct",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Required {label} missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def normalize_postcode(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", "", str(value)).upper().strip()
    return text or None


def require_review_fields(row: dict[str, Any], line_no: int) -> None:
    if row.get("business_row_written") is not False:
        raise ValueError(f"candidate line {line_no} business_row_written must be false")
    if row.get("fake_data") is not False:
        raise ValueError(f"candidate line {line_no} fake_data must be false")
    if row.get("promotion_state") != "REVIEW_ONLY_NOT_PROMOTED":
        raise ValueError(f"candidate line {line_no} promotion_state mismatch")
    for field in ("internet_availability_quality_percent", "internet_quality_band", "calculation_version"):
        if row.get(field) is not None:
            raise ValueError(f"candidate line {line_no} score field must be null: {field}")


def validate_status_semantics(row: dict[str, Any], line_no: int) -> None:
    status = row.get("status")
    postcode = normalize_postcode(row.get("postcode"))
    confidence = float(row.get("internet_match_confidence", -1))
    method = row.get("internet_match_method")
    level = row.get("source_level")
    metrics = [row.get(field) for field in METRIC_FIELDS]
    if status == DIRECT:
        if method != "CANONICAL_POSTCODE" or level != "POSTCODE_PROXY" or confidence != 0.95:
            raise ValueError(f"candidate line {line_no} direct-match truth boundary mismatch")
        if not postcode or not POSTCODE_RE.fullmatch(postcode):
            raise ValueError(f"candidate line {line_no} direct postcode invalid")
        if all(value is None for value in metrics):
            raise ValueError(f"candidate line {line_no} direct match has no published metrics")
    elif status == LEGACY:
        if method != "LEGACY_POSTCODE_PROXY" or level != "POSTCODE_PROXY_LEGACY_MATCH" or confidence != 0.70:
            raise ValueError(f"candidate line {line_no} legacy-match truth boundary mismatch")
        if not postcode or not POSTCODE_RE.fullmatch(postcode):
            raise ValueError(f"candidate line {line_no} legacy postcode invalid")
        if all(value is None for value in metrics):
            raise ValueError(f"candidate line {line_no} legacy match has no published metrics")
    elif status == NO_DATA:
        if level != "NO_DATA" or confidence != 0:
            raise ValueError(f"candidate line {line_no} NO_DATA confidence/source mismatch")
        if method == "NO_POSTCODE":
            if postcode is not None:
                raise ValueError(f"candidate line {line_no} NO_POSTCODE must not retain a postcode")
        elif method == "POSTCODE_NOT_IN_CURRENT_R2":
            if not postcode or not POSTCODE_RE.fullmatch(postcode):
                raise ValueError(f"candidate line {line_no} unmatched postcode invalid")
        else:
            raise ValueError(f"candidate line {line_no} unsupported NO_DATA match method")
        if any(value is not None for value in metrics):
            raise ValueError(f"candidate line {line_no} NO_DATA metrics must be null")
    else:
        raise ValueError(f"candidate line {line_no} unsupported status")


def audit(rows_jsonl: Path, manifest_path: Path, audit_output: Path | None = None) -> dict[str, Any]:
    manifest = load_object(manifest_path, "extraction manifest")
    if manifest.get("slot_id") != SLOT_ID:
        raise ValueError("extraction manifest slot_id mismatch")
    if int(manifest.get("canonical_rows", -1)) != EXPECTED_ROWS:
        raise ValueError("extraction manifest canonical row count mismatch")
    if int(manifest.get("actual_business_data_rows_written", -1)) != 0 or int(manifest.get("scores_written", -1)) != 0:
        raise ValueError("extraction manifest reports business rows or scores")
    if manifest.get("final_ready") is not False:
        raise ValueError("extraction manifest final_ready must be false")
    if not rows_jsonl.is_file():
        raise ValueError("candidate JSONL missing")
    counts = {status: 0 for status in ALLOWED_STATUS}
    parcel_ids: set[str] = set()
    row_count = 0
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
            if int(row.get("canonical_row_no", -1)) != expected_row:
                raise ValueError(f"candidate row sequence mismatch at line {line_no}")
            if row.get("slot_id") != SLOT_ID:
                raise ValueError(f"candidate line {line_no} slot_id mismatch")
            parcel_id = str(row.get("canonical_program_parcel_id") or "").strip()
            if not parcel_id or parcel_id in parcel_ids:
                raise ValueError(f"candidate line {line_no} parcel identity missing or duplicate")
            parcel_ids.add(parcel_id)
            require_review_fields(row, line_no)
            validate_status_semantics(row, line_no)
            counts[row["status"]] += 1
            row_count += 1
    if row_count != EXPECTED_ROWS or ROW_START + row_count - 1 != ROW_END:
        raise ValueError(f"candidate JSONL exact row count/range mismatch: {row_count}")
    if len(parcel_ids) != EXPECTED_ROWS:
        raise ValueError("candidate parcel identity count mismatch")
    manifest_counts = {
        DIRECT: int(manifest.get("direct_current_r2_matches", -1)),
        LEGACY: int(manifest.get("legacy_current_r2_matches_pending_spatial_qa", -1)),
        NO_DATA: int(manifest.get("no_data_rows", -1)),
    }
    if counts != manifest_counts:
        raise ValueError("candidate JSONL and extraction manifest status counts mismatch")
    result = {
        "schema_version": 1, "slot_id": SLOT_ID,
        "status": "PASS_COMPLETE_CANDIDATE_JSONL_INTEGRITY_REVIEW_ONLY",
        "row_start": ROW_START, "row_end": ROW_END, "canonical_rows": row_count,
        "unique_parcel_ids": len(parcel_ids), "status_counts": counts,
        "candidate_rows_jsonl_sha256": sha256_file(rows_jsonl),
        "extraction_manifest_sha256": sha256_file(manifest_path),
        "actual_business_data_rows_written": 0, "scores_written": 0,
        "db_write": False, "migration": False, "production_deploy": False,
        "final_ready": False,
    }
    if audit_output is not None:
        audit_output.parent.mkdir(parents=True, exist_ok=True)
        audit_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows-jsonl", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.rows_jsonl, args.manifest, args.audit_output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
