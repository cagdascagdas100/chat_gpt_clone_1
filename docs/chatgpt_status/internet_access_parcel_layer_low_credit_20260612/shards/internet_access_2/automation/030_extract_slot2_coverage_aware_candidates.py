#!/usr/bin/env python3
"""Coverage-aware review-only extractor for internet_access_2.

The base extractor validates the official Ofcom r2 package and bounded inputs.
This layer adds one fail-closed selection rule: when a syntactically valid
canonical postcode is absent from current r2 but a different valid legacy
postcode is present in current r2, the row is retained only as a lower-confidence
legacy postcode proxy pending spatial QA. No score or business row is emitted.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

BASE_SCRIPT = Path(__file__).with_name("002_extract_slot2_ofcom_2026_candidates.py")
spec = importlib.util.spec_from_file_location("internet_access_2_base_extractor", BASE_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import base extractor: {BASE_SCRIPT}")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

SLOT_ID = base.SLOT_ID
ROW_START = base.ROW_START
ROW_END = base.ROW_END
EXPECTED_ROWS = base.EXPECTED_ROWS

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


def resolve_postcode(
    canonical_value: Any,
    legacy_value: Any,
    coverage: dict[str, dict[str, Any]] | set[str],
) -> dict[str, Any]:
    canonical = base.normalise_postcode(canonical_value)
    legacy = base.normalise_postcode(legacy_value)
    canonical_valid = base.valid_postcode(canonical)
    legacy_valid = base.valid_postcode(legacy)
    canonical_in_r2 = bool(canonical_valid and canonical in coverage)
    legacy_in_r2 = bool(legacy_valid and legacy in coverage)
    invalid = [value for value, ok in ((canonical, canonical_valid), (legacy, legacy_valid)) if value and not ok]
    conflict = bool(canonical_valid and legacy_valid and canonical != legacy)
    coverage_fallback = False

    if canonical_in_r2:
        selected = canonical
        origin = "CANONICAL"
        selected_in_r2 = True
        if conflict:
            resolution = "CANONICAL_CURRENT_R2_SELECTED_LEGACY_CONFLICT"
        elif legacy_valid:
            resolution = "CANONICAL_CURRENT_R2_SELECTED_LEGACY_SAME"
        elif legacy:
            resolution = "CANONICAL_CURRENT_R2_SELECTED_LEGACY_INVALID"
        else:
            resolution = "CANONICAL_CURRENT_R2_SELECTED"
    elif legacy_in_r2:
        selected = legacy
        origin = "LEGACY"
        selected_in_r2 = True
        if canonical_valid:
            resolution = "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_NOT_IN_R2"
            coverage_fallback = True
        elif canonical:
            resolution = "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_INVALID"
        else:
            resolution = "LEGACY_CURRENT_R2_FALLBACK_CANONICAL_MISSING"
    elif canonical_valid:
        selected = canonical
        origin = "CANONICAL"
        selected_in_r2 = False
        if conflict:
            resolution = "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_NOT_IN_R2_CONFLICT"
        elif legacy_valid:
            resolution = "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_SAME"
        elif legacy:
            resolution = "CANONICAL_VALID_NOT_IN_CURRENT_R2_LEGACY_INVALID"
        else:
            resolution = "CANONICAL_VALID_NOT_IN_CURRENT_R2"
    elif legacy_valid:
        selected = legacy
        origin = "LEGACY"
        selected_in_r2 = False
        resolution = (
            "LEGACY_VALID_NOT_IN_CURRENT_R2_CANONICAL_INVALID"
            if canonical
            else "LEGACY_VALID_NOT_IN_CURRENT_R2_CANONICAL_MISSING"
        )
    else:
        selected = None
        origin = "NONE"
        selected_in_r2 = False
        resolution = "NO_VALID_POSTCODE"

    return {
        "selected": selected,
        "origin": origin,
        "selected_in_current_r2": selected_in_r2,
        "resolution": resolution,
        "canonical": canonical,
        "canonical_valid": canonical_valid,
        "canonical_in_current_r2": canonical_in_r2,
        "legacy": legacy,
        "legacy_valid": legacy_valid,
        "legacy_in_current_r2": legacy_in_r2,
        "conflict": conflict,
        "coverage_fallback_from_canonical": coverage_fallback,
        "invalid": invalid,
    }


def build_rows(
    canonical_rows: list[dict[str, Any]],
    legacy_rows: dict[int, dict[str, Any]],
    coverage: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for canonical in canonical_rows:
        number = base.row_number(canonical)
        if number is None:
            raise ValueError("Canonical row has no row number")
        canonical_raw = base.first_present(canonical, ["postcode", "postcode_space"])
        legacy_raw = base.parse_legacy_postcode(legacy_rows.get(number, {}))
        resolved = resolve_postcode(canonical_raw, legacy_raw, coverage)
        postcode = resolved["selected"]
        source = coverage.get(postcode or "")

        if source and resolved["origin"] == "CANONICAL":
            match_method = "CANONICAL_POSTCODE"
            source_level = "POSTCODE_PROXY"
            confidence = 0.95
            accuracy = "CURRENT_R2_POSTCODE_COVERAGE_DIRECT"
            status = DIRECT
        elif source and resolved["origin"] == "LEGACY":
            match_method = "LEGACY_POSTCODE_PROXY"
            source_level = "POSTCODE_PROXY_LEGACY_MATCH"
            confidence = 0.70
            accuracy = "CURRENT_R2_COVERAGE_LEGACY_POSTCODE_REQUIRES_SPATIAL_QA"
            status = LEGACY
        else:
            match_method = "NO_POSTCODE" if not postcode else "POSTCODE_NOT_IN_CURRENT_R2"
            source_level = "NO_DATA"
            confidence = 0.0
            accuracy = "NO_DATA"
            status = NO_DATA

        record: dict[str, Any] = {
            "slot_id": SLOT_ID,
            "canonical_row_no": number,
            "canonical_program_parcel_id": base.canonical_id(canonical),
            "hmlr_inspire_id": base.first_present(canonical, ["hmlr_inspire_id", "inspire_id"]),
            "parcel_centroid_lon": base.as_number(base.first_present(canonical, ["parcel_centroid_lon", "hmlr_lon", "lon", "longitude"])),
            "parcel_centroid_lat": base.as_number(base.first_present(canonical, ["parcel_centroid_lat", "hmlr_lat", "lat", "latitude"])),
            "existing_geometry_type": canonical.get("_existing_geometry_type"),
            "postcode": postcode,
            "postcode_selected_origin": resolved["origin"],
            "selected_postcode_in_current_r2": resolved["selected_in_current_r2"],
            "canonical_postcode_candidate": resolved["canonical"],
            "canonical_postcode_valid": resolved["canonical_valid"],
            "canonical_postcode_in_current_r2": resolved["canonical_in_current_r2"],
            "legacy_postcode_candidate": resolved["legacy"],
            "legacy_postcode_valid": resolved["legacy_valid"],
            "legacy_postcode_in_current_r2": resolved["legacy_in_current_r2"],
            "postcode_resolution": resolved["resolution"],
            "postcode_conflict": resolved["conflict"],
            "coverage_fallback_from_canonical": resolved["coverage_fallback_from_canonical"],
            "invalid_postcode_candidates": resolved["invalid"],
            "internet_match_method": match_method,
            "source_level": source_level,
            "internet_match_confidence": confidence,
            "internet_availability_quality_percent": None,
            "internet_quality_band": None,
            "internet_accuracy": accuracy,
            "calculation_version": None,
            "calculation_explanation": "No score emitted until column-aware scoring and required spatial QA pass.",
            "status": status,
            "promotion_state": "REVIEW_ONLY_NOT_PROMOTED",
            "business_row_written": False,
            "fake_data": False,
        }
        if source:
            record.update(source)
        output.append(record)
    return output


def write_outputs(
    canonical_path: Path,
    legacy_path: Path | None,
    output_dir: Path,
    rows: list[dict[str, Any]],
    coverage: dict[str, dict[str, Any]],
    source_files: list[dict[str, Any]],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / "internet_access_2_candidates_latest.jsonl"
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    direct = sum(row["status"] == DIRECT for row in rows)
    legacy = sum(row["status"] == LEGACY for row in rows)
    no_data = sum(row["status"] == NO_DATA for row in rows)
    resolution_counts: dict[str, int] = {}
    for row in rows:
        key = str(row["postcode_resolution"])
        resolution_counts[key] = resolution_counts.get(key, 0) + 1

    manifest = {
        "schema_version": 5,
        "slot_id": SLOT_ID,
        "parcel_start": ROW_START,
        "parcel_end": ROW_END,
        "canonical_source": str(canonical_path),
        "canonical_source_sha256": base.sha256_file(canonical_path),
        "legacy_internet_source": str(legacy_path) if legacy_path else None,
        "legacy_internet_source_sha256": base.sha256_file(legacy_path) if legacy_path else None,
        "canonical_rows": len(rows),
        "direct_current_r2_matches": direct,
        "legacy_current_r2_matches_pending_spatial_qa": legacy,
        "no_data_rows": no_data,
        "postcode_resolution_counts": resolution_counts,
        "coverage_fallback_from_canonical_rows": sum(bool(row["coverage_fallback_from_canonical"]) for row in rows),
        "selected_postcode_not_in_current_r2_rows": sum(
            bool(row["postcode"]) and not bool(row["selected_postcode_in_current_r2"]) for row in rows
        ),
        "invalid_postcode_candidate_rows": sum(bool(row["invalid_postcode_candidates"]) for row in rows),
        "canonical_legacy_postcode_conflict_rows": sum(bool(row["postcode_conflict"]) for row in rows),
        "ofcom_postcodes_loaded": len(coverage),
        "ofcom_files_loaded": len(source_files),
        "ofcom_required_pattern": base.R2_GLOB,
        "ofcom_source_files": source_files,
        "scores_written": 0,
        "actual_business_data_rows_written": 0,
        "migration": False,
        "db_write": False,
        "production_deploy": False,
        "fake_data": False,
        "final_ready": False,
        "samples": rows[:5],
    }
    manifest_path = output_dir / "internet_access_2_extraction_manifest_latest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "slot_id": SLOT_ID,
        "canonical_rows": len(rows),
        "direct_current_r2_matches": direct,
        "legacy_current_r2_matches_pending_spatial_qa": legacy,
        "no_data_rows": no_data,
        "coverage_fallback_from_canonical_rows": manifest["coverage_fallback_from_canonical_rows"],
        "postcode_resolution_counts": resolution_counts,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "manifest": str(manifest_path),
        "jsonl": str(jsonl_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument("--ofcom-postcode-dir", required=True, type=Path)
    parser.add_argument("--legacy-internet-geojson", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    canonical_rows = base.load_canonical(args.canonical)
    legacy_rows = base.load_legacy_internet(args.legacy_internet_geojson)
    coverage, source_files = base.load_ofcom_postcodes(args.ofcom_postcode_dir)
    rows = build_rows(canonical_rows, legacy_rows, coverage)
    print(json.dumps(
        write_outputs(args.canonical, args.legacy_internet_geojson, args.output_dir, rows, coverage, source_files),
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
