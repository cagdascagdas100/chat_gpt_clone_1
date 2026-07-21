#!/usr/bin/env python3
"""Import a previously validated internet_access_3 runtime bundle into review-only web JSON.

The importer accepts only the PASS output from automation/019_runtime_bundle_gate.py.
It never creates parcel scores or business rows and writes one atomic review file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
ROW_START = 61523
ROW_END = 92283
EXPECTED_ROWS = 30_761
PASS_STATE = "PASS_VALIDATED_RUNTIME_BUNDLE_REVIEW_ONLY"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_STATUSES = (
    "CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW",
    "IDENTITY_CONFLICT_NO_DATA",
    "POSTCODE_NOT_FOUND_IN_CURRENT_R2_NO_DATA",
    "NO_VERIFIED_POSTCODE_NO_DATA",
)


class GateError(RuntimeError):
    """Raised when validated runtime evidence does not satisfy the web import contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GateError(message)


def _integer(value: Any, name: str) -> int:
    _require(not isinstance(value, bool), f"{name}: integer required")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise GateError(f"{name}: integer required") from exc
    _require(isinstance(value, int) or str(parsed) == str(value), f"{name}: exact integer required")
    return parsed


def _load(path: Path) -> dict[str, Any]:
    _require(path.is_file() and path.stat().st_size > 0, f"runtime gate missing or empty: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GateError(f"runtime gate is invalid JSON: {exc}") from exc
    _require(isinstance(value, dict), "runtime gate must be an object")
    return value


def _hash(value: Any, name: str) -> str:
    text = str(value or "").lower()
    _require(SHA256_RE.fullmatch(text) is not None, f"{name}: invalid SHA-256")
    return text


def _truth_flags(value: dict[str, Any]) -> None:
    for key in ("fake_data", "db_write", "migration", "production_deploy", "final_ready"):
        _require(value.get(key) is False, f"{key} must be false")
    _require(_integer(value.get("actual_business_data_rows_written"), "business rows") == 0, "business rows must be zero")
    _require(_integer(value.get("scores_written"), "scores") == 0, "scores must be zero")


def validate_runtime_gate(value: dict[str, Any], *, start: int = ROW_START, end: int = ROW_END, rows: int = EXPECTED_ROWS) -> dict[str, Any]:
    _require(value.get("slot_id") == SLOT_ID, "wrong slot_id")
    _require(value.get("state") == PASS_STATE, "runtime gate is not PASS")
    partition = value.get("row_partition") or {}
    _require((_integer(partition.get("start"), "partition start"), _integer(partition.get("end"), "partition end"), _integer(partition.get("rows"), "partition rows")) == (start, end, rows), "runtime partition mismatch")
    gates = value.get("gates")
    _require(isinstance(gates, list) and len(gates) >= 8, "at least eight runtime gates required")
    gate_numbers: set[int] = set()
    for gate in gates:
        _require(isinstance(gate, dict), "runtime gate row must be an object")
        number = _integer(gate.get("gate_no"), "gate_no")
        _require(number not in gate_numbers, "duplicate gate_no")
        gate_numbers.add(number)
        _require(gate.get("state") == "PASS", f"runtime gate {number} is not PASS")
    counts = value.get("counts") or {}
    canonical_rows = _integer(counts.get("canonical_rows"), "canonical rows")
    _require(canonical_rows == rows, "canonical row count mismatch")
    status_counts = {
        EXPECTED_STATUSES[0]: _integer(counts.get("current_r2_postcode_proxy_rows"), "proxy rows"),
        EXPECTED_STATUSES[1]: _integer(counts.get("identity_conflict_rows"), "identity conflict rows"),
        EXPECTED_STATUSES[2]: _integer(counts.get("postcode_not_found_in_current_r2_rows"), "postcode not found rows"),
        EXPECTED_STATUSES[3]: _integer(counts.get("no_verified_postcode_rows"), "no verified postcode rows"),
    }
    _require(min(status_counts.values()) >= 0 and sum(status_counts.values()) == rows, "four-state count partition mismatch")
    no_data = sum(status_counts[status] for status in EXPECTED_STATUSES[1:])
    _require(_integer(counts.get("no_data_rows"), "no data rows") == no_data, "no_data_rows mismatch")
    hashes = value.get("hashes") or {}
    clean_hashes = {key: _hash(hashes.get(key), key) for key in ("candidate_manifest_sha256", "candidates_jsonl_sha256", "slice_manifest_sha256", "ofcom_zip_sha256", "canonical_slice_sha256", "legacy_slice_sha256")}
    samples = value.get("samples")
    _require(isinstance(samples, list) and 1 <= len(samples) <= 8, "one to eight real runtime samples required")
    seen_rows: set[int] = set()
    clean_samples: list[dict[str, Any]] = []
    for sample in samples:
        _require(isinstance(sample, dict), "runtime sample must be an object")
        row_no = _integer(sample.get("canonical_row_no"), "sample row_no")
        _require(start <= row_no <= end and row_no not in seen_rows, "sample row outside partition or duplicated")
        seen_rows.add(row_no)
        _require(sample.get("slot_id") == SLOT_ID, "sample slot mismatch")
        _require(sample.get("canonical_program_parcel_id") == f"parcel_{row_no}", "sample parcel identity mismatch")
        _require(sample.get("status") in EXPECTED_STATUSES, "sample status invalid")
        _require(sample.get("business_row_written") is False, "sample business write must be false")
        _require(sample.get("internet_availability_quality_percent") is None, "sample parcel score is forbidden")
        clean_samples.append(sample)
    _truth_flags(value)
    return {
        "row_partition": {"start": start, "end": end, "rows": rows},
        "counts": {
            "canonical_rows": rows,
            "current_r2_postcode_proxy_rows": status_counts[EXPECTED_STATUSES[0]],
            "identity_conflict_rows": status_counts[EXPECTED_STATUSES[1]],
            "postcode_not_found_in_current_r2_rows": status_counts[EXPECTED_STATUSES[2]],
            "no_verified_postcode_rows": status_counts[EXPECTED_STATUSES[3]],
            "no_data_rows": no_data,
            "ofcom_postcodes_scanned": _integer(counts.get("ofcom_postcodes_scanned"), "Ofcom rows"),
            "postcode_area_members": _integer(counts.get("postcode_area_members"), "postcode area members"),
        },
        "hashes": clean_hashes,
        "gates": gates,
        "samples": clean_samples,
    }


def build_web_payload(validated: dict[str, Any], source_path: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": "REAL_RUNTIME_BUNDLE_VALIDATED_REVIEW_ONLY",
        "summary": "Gerçek 30.761 runner satırı fail-closed doğrulandı; sonuçlar yalnız inceleme görünümüdür.",
        "source_runtime_gate": str(source_path),
        "source_runtime_gate_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "real_runtime_rows_validated": validated["row_partition"]["rows"],
        "row_partition": validated["row_partition"],
        "counts": validated["counts"],
        "hashes": validated["hashes"],
        "gates": validated["gates"],
        "samples": validated["samples"],
        "sample_truth_boundary": "REAL_RUNTIME_ROWS_ONLY; REVIEW_ONLY; NOT_BUSINESS_DATA; NO_PARCEL_SCORE",
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-gate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    value = _load(args.runtime_gate)
    validated = validate_runtime_gate(value)
    payload = build_web_payload(validated, args.runtime_gate)
    if not args.dry_run:
        atomic_write_json(args.output, payload)
    print(json.dumps({"status": payload["status"], "rows": payload["real_runtime_rows_validated"], "dry_run": args.dry_run}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
