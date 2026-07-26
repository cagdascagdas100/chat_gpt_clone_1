# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
EXPECTED_TOTAL_ROWS = 11013
EXPECTED_REVIEW_ROWS = 2
REVIEW_STATUS = "ONSPD_TERMINATED_REVIEW_REQUIRED"
DEFAULT_INPUT = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/data/005_existing_11013_postcode_identity_candidates.jsonl")
DEFAULT_OUTPUT = Path("england_map_web/data/aays_21_slots/internet_access_2/006_existing_11013_identity_review_rows.json")
DEFAULT_AUDIT = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/recovery/014_006_terminated_identity_review_export.json")


def repo_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / "docs/chatgpt_status").is_dir() and (candidate / "england_map_web").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"INVALID_JSONL_LINE:{line_number}") from exc
            if not isinstance(row, dict):
                raise RuntimeError(f"NON_OBJECT_JSONL_LINE:{line_number}")
            rows.append(row)
    if len(rows) != EXPECTED_TOTAL_ROWS:
        raise RuntimeError(f"EXPECTED_{EXPECTED_TOTAL_ROWS}_ROWS_GOT_{len(rows)}")
    return rows


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    onspd = row.get("onspd") if isinstance(row.get("onspd"), dict) else {}
    return {
        "line": row.get("line"),
        "row_no": row.get("row_no"),
        "parcel_id": row.get("parcel_id"),
        "hmlr_inspire_id": row.get("hmlr_inspire_id"),
        "hmlr_geometry_accuracy": row.get("hmlr_geometry_accuracy"),
        "postcode": row.get("postcode_space") or row.get("postcode"),
        "onspd_snapshot_date": row.get("onspd_snapshot_date"),
        "onspd_source": row.get("onspd_source"),
        "onspd": {
            "dointr": onspd.get("dointr"),
            "doterm": onspd.get("doterm"),
            "lat": onspd.get("lat"),
            "long": onspd.get("long"),
            "lad25cd": onspd.get("lad25cd"),
            "ctry25cd": onspd.get("ctry25cd"),
        },
        "internet_accuracy": row.get("internet_accuracy"),
        "official_coverage_verified": bool(row.get("official_coverage_verified")),
        "candidate_status": row.get("candidate_status"),
        "review_reason": "ONSPD postcode has a termination date; exact current identity requires human review before any coverage join.",
        "fake_data": False,
        "final_ready": False,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export(input_path: Path, output_path: Path, audit_path: Path) -> dict[str, Any]:
    rows = read_rows(input_path)
    review = [row for row in rows if row.get("onspd_status") == REVIEW_STATUS or row.get("candidate_status") == REVIEW_STATUS]
    if len(review) != EXPECTED_REVIEW_ROWS:
        raise RuntimeError(f"EXPECTED_{EXPECTED_REVIEW_ROWS}_REVIEW_ROWS_GOT_{len(review)}")
    if any(str(row.get("internet_accuracy")) != "1/4" for row in review):
        raise RuntimeError("TERMINATED_REVIEW_ACCURACY_MUST_BE_1_OF_4")
    if any(bool(row.get("official_coverage_verified")) for row in review):
        raise RuntimeError("TERMINATED_REVIEW_ROW_CANNOT_HAVE_OFFICIAL_COVERAGE_VERIFIED")

    public_rows = [public_row(row) for row in review]
    payload = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "EXACT_TWO_TERMINATED_ONSPD_IDENTITIES_EXPORTED_FOR_REVIEW",
        "source_total_rows": len(rows),
        "review_row_count": len(public_rows),
        "internet_accuracy": "1/4_TERMINATED_POSTCODE_REVIEW_REQUIRED",
        "official_coverage_verified": 0,
        "rows": public_rows,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    write_json(output_path, payload)

    audit = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "TERMINATED_IDENTITY_REVIEW_EXPORT_PASS",
        "input_path": str(input_path),
        "input_sha256": sha256_file(input_path),
        "source_total_rows": len(rows),
        "expected_review_rows": EXPECTED_REVIEW_ROWS,
        "observed_review_rows": len(public_rows),
        "output_path": str(output_path),
        "output_sha256": sha256_file(output_path),
        "accuracy_guard": "1/4_ONLY",
        "official_coverage_verified": 0,
        "duplicate_task_created": False,
        "second_runner_started": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    write_json(audit_path, audit)
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Export the exact two terminated ONSPD identity rows for review")
    parser.add_argument("--repo-root")
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--audit")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root(Path.cwd())
    input_path = root / Path(args.input) if args.input else root / DEFAULT_INPUT
    output_path = root / Path(args.output) if args.output else root / DEFAULT_OUTPUT
    audit_path = root / Path(args.audit) if args.audit else root / DEFAULT_AUDIT
    audit = export(input_path, output_path, audit_path)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
