#!/usr/bin/env python3
"""Build truthful internet_access_3 candidates with bounded Ofcom retention.

All 1,741,096 corrected Ofcom postcode rows are scanned and globally checked for
blank/duplicate postcodes, schema, postcode-area consistency and percentage ranges.
Only postcode records actually needed by identity-matched slot-3 legacy rows are
retained in memory. No postcode is inferred, no parcel score is emitted and no
business data is written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
EXPECTED_ROWS = 30_761
EXPECTED_OFCOM_FILE_COUNT = 121
EXPECTED_OFCOM_POSTCODE_ROWS = 1_741_096
R2_GLOB = "202601_fixed_postcode_coverage_r2_*.csv"
R1_GLOB = "202601_fixed_postcode_coverage_r1_*.csv"
STRICT_REQUIRED_FIELDS = (
    "postcode",
    "postcode_space",
    "postcode_area",
    "sfbb",
    "ufbb100",
    "ufbb300",
    "gigabit",
    "unable30",
    "unable_decent",
)
STATUS_ORDER = (
    "CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW",
    "IDENTITY_CONFLICT_NO_DATA",
    "POSTCODE_NOT_FOUND_IN_CURRENT_R2_NO_DATA",
    "NO_VERIFIED_POSTCODE_NO_DATA",
)


class GateError(RuntimeError):
    """Raised when a source, identity or truth gate fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_base_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("internet_access_3_base_extractor", path)
    if spec is None or spec.loader is None:
        raise GateError(f"Cannot load base extractor: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def filename_postcode_area(path: Path) -> str:
    match = re.fullmatch(r"202601_fixed_postcode_coverage_r2_([A-Za-z]+)\.csv", path.name)
    if not match:
        raise GateError(f"Unexpected corrected postcode filename: {path.name}")
    return match.group(1).upper()


def postcode_area_from_postcode(postcode: str) -> str:
    match = re.match(r"^([A-Z]+)", postcode)
    if not match:
        raise GateError(f"Postcode has no alphabetic area prefix: {postcode}")
    return match.group(1)


def required_value(row: dict[str, Any], base: Any, field: str, file_name: str, row_no: int) -> Any:
    value = base.first_present(row, base.FIELD_ALIASES[field])
    if value is None or str(value).strip() == "":
        raise GateError(f"Blank required field {field} in {file_name} row {row_no}")
    return value


def prepare_slot_rows(canonical_rows: list[dict[str, Any]], legacy_rows: dict[int, dict[str, Any]], base: Any) -> set[str]:
    needed: set[str] = set()
    for canonical in canonical_rows:
        number = base.row_number(canonical)
        if number is None:
            raise GateError("Canonical row has no row number")
        legacy = legacy_rows.get(number)
        if not legacy:
            continue
        identity_ok, _ = base.identity_match(canonical, legacy)
        if not identity_ok:
            continue
        postcode = base.parse_legacy_postcode(legacy)
        if postcode:
            needed.add(postcode)
    return needed


def scan_ofcom_postcodes(
    directory: Path,
    needed_postcodes: set[str],
    base: Any,
    *,
    expected_file_count: int = EXPECTED_OFCOM_FILE_COUNT,
    expected_total_rows: int = EXPECTED_OFCOM_POSTCODE_ROWS,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    superseded = sorted(directory.rglob(R1_GLOB))
    if superseded:
        raise GateError(f"Superseded all-premises r1 files present: {len(superseded)}")
    files = sorted(directory.rglob(R2_GLOB))
    if len(files) != expected_file_count:
        raise GateError(f"Expected {expected_file_count} corrected r2 files, found {len(files)}")

    selected: dict[str, dict[str, Any]] = {}
    seen_postcodes: set[str] = set()
    source_files: list[dict[str, Any]] = []
    total_rows = 0

    for file_path in files:
        expected_area = filename_postcode_area(file_path)
        file_rows = 0
        retained_rows = 0
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            missing = [
                field
                for field in STRICT_REQUIRED_FIELDS
                if not base.has_alias(headers, base.FIELD_ALIASES[field])
            ]
            if missing:
                raise GateError(f"{file_path.name} missing strict fields: {missing}")

            for row in reader:
                file_rows += 1
                total_rows += 1
                logical_row = file_rows + 1
                postcode = base.normalise_postcode(
                    required_value(row, base, "postcode", file_path.name, logical_row)
                )
                postcode_space = base.normalise_postcode(
                    required_value(row, base, "postcode_space", file_path.name, logical_row)
                )
                if not postcode:
                    raise GateError(f"Blank postcode in {file_path.name} row {logical_row}")
                if postcode != postcode_space:
                    raise GateError(
                        f"postcode/postcode_space mismatch in {file_path.name} row {logical_row}: "
                        f"{postcode!r} != {postcode_space!r}"
                    )
                if postcode in seen_postcodes:
                    raise GateError(f"Duplicate Ofcom postcode: {postcode}")
                seen_postcodes.add(postcode)

                area_value = str(
                    required_value(row, base, "postcode_area", file_path.name, logical_row)
                ).strip().upper()
                derived_area = postcode_area_from_postcode(postcode)
                if area_value != expected_area or derived_area != expected_area:
                    raise GateError(
                        f"Postcode area mismatch in {file_path.name} row {logical_row}: "
                        f"field={area_value}, derived={derived_area}, file={expected_area}"
                    )

                percentages: dict[str, float] = {}
                for field in ("sfbb", "ufbb100", "ufbb300", "gigabit", "unable30", "unable_decent"):
                    raw = required_value(row, base, field, file_path.name, logical_row)
                    value = base.parse_percentage(raw)
                    if value is None:
                        raise GateError(f"Non-numeric required percentage {field} in {file_path.name} row {logical_row}")
                    percentages[field] = value

                if postcode in needed_postcodes:
                    selected[postcode] = {
                        "postcode": postcode,
                        "postcode_space": base.first_present(row, base.FIELD_ALIASES["postcode_space"]),
                        "postcode_area": area_value,
                        "sfbb_30mbps_available_pct": percentages["sfbb"],
                        "ufbb_100mbps_available_pct": percentages["ufbb100"],
                        "ufbb_300mbps_available_pct": percentages["ufbb300"],
                        "gigabit_available_pct": percentages["gigabit"],
                        "unable_30mbps_pct": percentages["unable30"],
                        "unable_decent_fixed_or_fwa_pct": percentages["unable_decent"],
                        "source_file": file_path.name,
                        "source_snapshot_date": "2026-01",
                        "source_revision": "r2",
                    }
                    retained_rows += 1

        source_files.append(
            {
                "file": file_path.name,
                "postcode_area": expected_area,
                "rows": file_rows,
                "retained_needed_rows": retained_rows,
                "sha256": sha256_file(file_path),
            }
        )

    if total_rows != expected_total_rows:
        raise GateError(f"Expected {expected_total_rows} Ofcom postcode rows, found {total_rows}")
    if len(seen_postcodes) != total_rows:
        raise GateError("Global Ofcom postcode uniqueness count does not equal scanned rows")

    stats = {
        "ofcom_postcodes_scanned": total_rows,
        "ofcom_unique_postcodes": len(seen_postcodes),
        "needed_postcodes": len(needed_postcodes),
        "retained_postcodes": len(selected),
        "needed_postcodes_not_found": len(needed_postcodes - set(selected)),
    }
    return selected, source_files, stats


def choose_samples(rows: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_rows: set[int] = set()
    for status in STATUS_ORDER:
        match = next((row for row in rows if row.get("status") == status), None)
        if match is not None:
            selected.append(match)
            selected_rows.add(int(match["canonical_row_no"]))
    for row in rows:
        row_no = int(row["canonical_row_no"])
        if row_no not in selected_rows:
            selected.append(row)
            selected_rows.add(row_no)
        if len(selected) >= limit:
            break
    return selected[:limit]


def build_manifest(
    canonical_path: Path,
    legacy_path: Path,
    canonical_rows: list[dict[str, Any]],
    legacy_rows: dict[int, dict[str, Any]],
    selected_coverage: dict[str, dict[str, Any]],
    source_files: list[dict[str, Any]],
    scan_stats: dict[str, int],
    base: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = base.build_rows(canonical_rows, legacy_rows, selected_coverage)
    if len(rows) != EXPECTED_ROWS:
        raise GateError(f"Expected {EXPECTED_ROWS} candidate rows, found {len(rows)}")

    counts = {status: sum(row.get("status") == status for row in rows) for status in STATUS_ORDER}
    matched = counts["CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW"]
    no_data = len(rows) - matched
    if sum(counts.values()) != len(rows) or matched + no_data != EXPECTED_ROWS:
        raise GateError("Candidate status partition is not complete and disjoint")
    if any(row.get("business_row_written") is not False for row in rows):
        raise GateError("A review row reported a business write")
    if any(row.get("internet_availability_quality_percent") is not None for row in rows):
        raise GateError("A parcel score was emitted")

    manifest = {
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "parcel_start": 61523,
        "parcel_end": 92283,
        "canonical_rows": len(rows),
        "current_r2_postcode_proxy_rows": matched,
        "identity_conflict_rows": counts["IDENTITY_CONFLICT_NO_DATA"],
        "postcode_not_found_in_current_r2_rows": counts["POSTCODE_NOT_FOUND_IN_CURRENT_R2_NO_DATA"],
        "no_verified_postcode_rows": counts["NO_VERIFIED_POSTCODE_NO_DATA"],
        "no_data_rows": no_data,
        "ofcom_postcodes_loaded": scan_stats["ofcom_postcodes_scanned"],
        "ofcom_postcodes_scanned": scan_stats["ofcom_postcodes_scanned"],
        "ofcom_unique_postcodes": scan_stats["ofcom_unique_postcodes"],
        "needed_postcodes": scan_stats["needed_postcodes"],
        "ofcom_postcodes_retained": scan_stats["retained_postcodes"],
        "needed_postcodes_not_found": scan_stats["needed_postcodes_not_found"],
        "ofcom_files_loaded": len(source_files),
        "memory_strategy": "GLOBAL_POSTCODE_UNIQUENESS_SET_PLUS_NEEDED_POSTCODE_ROWS_ONLY",
        "canonical_source_sha256": sha256_file(canonical_path),
        "legacy_internet_source_sha256": sha256_file(legacy_path),
        "ofcom_source_files": source_files,
        "scores_written": 0,
        "actual_business_data_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "samples": choose_samples(rows),
    }
    return rows, manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument("--legacy-internet-geojson", required=True, type=Path)
    parser.add_argument("--ofcom-postcode-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--base-extractor",
        type=Path,
        default=Path(__file__).with_name("002_extract_slot3_ofcom_2026_candidates.py"),
    )
    args = parser.parse_args()

    base = load_base_module(args.base_extractor)
    canonical_rows = base.load_canonical(args.canonical)
    legacy_rows = base.load_legacy_internet(args.legacy_internet_geojson)
    needed_postcodes = prepare_slot_rows(canonical_rows, legacy_rows, base)
    selected_coverage, source_files, scan_stats = scan_ofcom_postcodes(
        args.ofcom_postcode_dir, needed_postcodes, base
    )
    rows, manifest = build_manifest(
        args.canonical,
        args.legacy_internet_geojson,
        canonical_rows,
        legacy_rows,
        selected_coverage,
        source_files,
        scan_stats,
        base,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = args.output_dir / "internet_access_3_candidates_latest.jsonl"
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    manifest_path = args.output_dir / "internet_access_3_candidate_manifest_latest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k not in {"ofcom_source_files", "samples"}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
