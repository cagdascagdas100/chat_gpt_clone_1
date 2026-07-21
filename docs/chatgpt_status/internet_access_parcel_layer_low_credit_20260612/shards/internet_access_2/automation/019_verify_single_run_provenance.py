#!/usr/bin/env python3
"""Cross-file provenance audit for a completed internet_access_2 runner run.

Fail-closed and review-only. This validates that diagnostics, official V2
validation, bounded slice manifests, extraction outputs and published web
artifacts all belong to one coherent run by recomputing and chaining SHA-256
values. It never writes parcel/business data or marks the slot final.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
EXPECTED_ROWS = 30761
EXPECTED_OFcom_FILES = 121
EXPECTED_OFcom_ROWS = 1_741_096
MIN_ZIP_BYTES = 30_000_000
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Required provenance file missing: {path.name}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Provenance file must be a JSON object: {path.name}")
    return payload


def require_hex64(value: Any, label: str) -> str:
    text = str(value or "").lower()
    if not HEX64.fullmatch(text):
        raise ValueError(f"{label} is not a lowercase SHA-256")
    return text


def require_review_only(payload: dict[str, Any], label: str) -> None:
    if int(payload.get("actual_business_data_rows_written", -1)) != 0:
        raise ValueError(f"{label} reports business rows")
    if "scores_written" in payload and int(payload.get("scores_written", -1)) != 0:
        raise ValueError(f"{label} reports scores")
    for key in ("db_write", "migration", "production_deploy"):
        if key in payload and payload.get(key) is not False:
            raise ValueError(f"{label} {key} must be false")
    if payload.get("final_ready") is not False:
        raise ValueError(f"{label} final_ready must be false")


def audit(work_root: Path, web_root: Path, audit_output: Path | None = None) -> dict[str, Any]:
    diagnostics_path = work_root / "internet_access_2_network_and_execution_diagnostics_latest.json"
    v2_path = work_root / "internet_access_2_ofcom_v2_validation_latest.json"
    slice_manifest_path = work_root / "slot_inputs/internet_access_2_stream_slice_manifest_latest.json"
    extraction_manifest_path = work_root / "candidate_outputs/internet_access_2_extraction_manifest_latest.json"
    rows_path = work_root / "candidate_outputs/internet_access_2_candidates_latest.jsonl"
    readback_path = web_root / "runner_readback_latest.json"
    examples_path = web_root / "verified_examples_latest.json"
    bundle_audit_path = web_root / "runner_bundle_audit_latest.json"

    diagnostics = load_json(diagnostics_path)
    v2 = load_json(v2_path)
    slice_manifest = load_json(slice_manifest_path)
    extraction = load_json(extraction_manifest_path)
    readback = load_json(readback_path)
    examples = load_json(examples_path)
    bundle_audit = load_json(bundle_audit_path)

    for label, payload in (
        ("diagnostics", diagnostics),
        ("slice manifest", slice_manifest),
        ("extraction manifest", extraction),
        ("runner readback", readback),
        ("verified examples", examples),
        ("bundle audit", bundle_audit),
    ):
        if payload.get("slot_id") != SLOT_ID:
            raise ValueError(f"{label} slot_id mismatch")
        require_review_only(payload, label)
    require_review_only(v2, "V2 validation")

    if diagnostics.get("state") != "COMPLETE_REVIEW_OUTPUT_READY":
        raise ValueError("diagnostics is not terminal review-output complete")
    zip_sha = require_hex64(diagnostics.get("zip_sha256"), "diagnostics zip_sha256")
    if int(diagnostics.get("zip_bytes", -1)) < MIN_ZIP_BYTES:
        raise ValueError("diagnostics ZIP byte count below minimum")
    if int(diagnostics.get("r1_file_count", -1)) != 0 or int(diagnostics.get("r2_file_count", -1)) != EXPECTED_OFcom_FILES:
        raise ValueError("diagnostics r1/r2 file count mismatch")

    if (
        v2.get("source") != "Ofcom Connected Nations Spring 2026 fixed broadband coverage"
        or v2.get("source_snapshot") != "2026-01"
        or v2.get("source_revision") != "v2-r2"
        or v2.get("source_revision_date") != "2026-07-07"
    ):
        raise ValueError("V2 source identity/revision mismatch")
    if v2.get("status") != "PASS_OFFICIAL_V2_R2_CORRECTION_AND_SEMANTICS_VALIDATED":
        raise ValueError("V2 validation status mismatch")
    if int(v2.get("file_count", -1)) != EXPECTED_OFcom_FILES:
        raise ValueError("V2 validation file count mismatch")
    if int(v2.get("row_count", -1)) != EXPECTED_OFcom_ROWS or int(v2.get("unique_postcode_count", -1)) != EXPECTED_OFcom_ROWS:
        raise ValueError("V2 postcode row/unique count mismatch")

    partition = slice_manifest.get("row_partition") or {}
    if int(partition.get("expected", -1)) != EXPECTED_ROWS:
        raise ValueError("slice manifest expected row count mismatch")
    canonical = slice_manifest.get("canonical") or {}
    legacy = slice_manifest.get("legacy_internet") or {}
    if int(canonical.get("rows", -1)) != EXPECTED_ROWS:
        raise ValueError("canonical slice row count mismatch")
    if int(canonical.get("unique_row_numbers", -1)) != EXPECTED_ROWS or int(canonical.get("unique_parcel_ids", -1)) != EXPECTED_ROWS:
        raise ValueError("canonical slice identity count mismatch")
    canonical_slice_sha = require_hex64(canonical.get("output_sha256"), "canonical slice output_sha256")
    legacy_slice_sha = require_hex64(legacy.get("output_sha256"), "legacy slice output_sha256")

    if int(extraction.get("canonical_rows", -1)) != EXPECTED_ROWS:
        raise ValueError("extraction canonical row count mismatch")
    direct = int(extraction.get("direct_current_r2_matches", -1))
    legacy_count = int(extraction.get("legacy_current_r2_matches_pending_spatial_qa", -1))
    no_data = int(extraction.get("no_data_rows", -1))
    if min(direct, legacy_count, no_data) < 0 or direct + legacy_count + no_data != EXPECTED_ROWS:
        raise ValueError("extraction status counts mismatch")
    if require_hex64(extraction.get("canonical_source_sha256"), "extraction canonical source SHA") != canonical_slice_sha:
        raise ValueError("canonical slice/extraction SHA chain mismatch")
    if require_hex64(extraction.get("legacy_internet_source_sha256"), "extraction legacy source SHA") != legacy_slice_sha:
        raise ValueError("legacy slice/extraction SHA chain mismatch")

    extraction_manifest_sha = sha256_file(extraction_manifest_path)
    rows_sha = sha256_file(rows_path)
    if require_hex64(readback.get("manifest_sha256"), "readback manifest SHA") != extraction_manifest_sha:
        raise ValueError("extraction manifest/readback SHA chain mismatch")
    if require_hex64(readback.get("rows_jsonl_sha256"), "readback rows SHA") != rows_sha:
        raise ValueError("candidate JSONL/readback SHA chain mismatch")
    if int(readback.get("canonical_rows", -1)) != EXPECTED_ROWS:
        raise ValueError("readback canonical row count mismatch")

    status_counts = readback.get("status_counts") or {}
    expected_counts = {
        "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW": direct,
        "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA": legacy_count,
        "NO_DATA": no_data,
    }
    if status_counts != expected_counts:
        raise ValueError("extraction/readback status count chain mismatch")

    readback_sha = sha256_file(readback_path)
    examples_sha = sha256_file(examples_path)
    if require_hex64(bundle_audit.get("runner_readback_file_sha256"), "bundle readback file SHA") != readback_sha:
        raise ValueError("readback/bundle-audit SHA chain mismatch")
    if require_hex64(bundle_audit.get("verified_examples_file_sha256"), "bundle examples file SHA") != examples_sha:
        raise ValueError("examples/bundle-audit SHA chain mismatch")
    if require_hex64(bundle_audit.get("source_manifest_sha256"), "bundle source manifest SHA") != extraction_manifest_sha:
        raise ValueError("manifest/bundle-audit SHA chain mismatch")
    if require_hex64(bundle_audit.get("source_rows_jsonl_sha256"), "bundle source rows SHA") != rows_sha:
        raise ValueError("rows/bundle-audit SHA chain mismatch")
    if int(bundle_audit.get("canonical_rows", -1)) != EXPECTED_ROWS or bundle_audit.get("status_counts") != expected_counts:
        raise ValueError("readback/bundle-audit row count chain mismatch")

    visible = int(readback.get("visible_example_rows", -1))
    rows = examples.get("rows")
    if not isinstance(rows, list) or len(rows) != visible or int(bundle_audit.get("visible_example_rows", -1)) != visible:
        raise ValueError("examples/readback/bundle-audit visible count mismatch")

    chain_inputs = [
        zip_sha,
        sha256_file(v2_path),
        require_hex64(canonical.get("source_sha256"), "canonical source SHA"),
        canonical_slice_sha,
        require_hex64(legacy.get("source_sha256"), "legacy source SHA"),
        legacy_slice_sha,
        extraction_manifest_sha,
        rows_sha,
        readback_sha,
        examples_sha,
        sha256_file(bundle_audit_path),
    ]
    chain_id = hashlib.sha256("\n".join(chain_inputs).encode("ascii")).hexdigest()

    result = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "status": "PASS_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY",
        "canonical_rows": EXPECTED_ROWS,
        "ofcom_r2_file_count": EXPECTED_OFcom_FILES,
        "ofcom_postcode_rows": EXPECTED_OFcom_ROWS,
        "status_counts": expected_counts,
        "visible_example_rows": visible,
        "zip_sha256": zip_sha,
        "canonical_slice_sha256": canonical_slice_sha,
        "legacy_slice_sha256": legacy_slice_sha,
        "extraction_manifest_sha256": extraction_manifest_sha,
        "candidate_rows_jsonl_sha256": rows_sha,
        "runner_readback_sha256": readback_sha,
        "verified_examples_sha256": examples_sha,
        "runner_bundle_audit_sha256": sha256_file(bundle_audit_path),
        "provenance_chain_sha256": chain_id,
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
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--web-root", required=True, type=Path)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.work_root, args.web_root, args.audit_output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
