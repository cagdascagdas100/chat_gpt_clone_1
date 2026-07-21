#!/usr/bin/env python3
"""Validate the official Ofcom Spring 2026 all-premises postcode V2 package.

Read-only and fail-closed. The validator verifies the 7 July 2026 correction,
including the exact r2 naming contract and the two duplicate-file defects fixed
by Ofcom (CW!=CV and MK!=ME). It also enforces the documented postcode CSV
format and records denominator/network semantics so coverage fields are not
misrepresented as parcel performance or full-fibre postcode evidence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

R2_GLOB = "202601_fixed_postcode_coverage_r2_*.csv"
R1_GLOB = "202601_fixed_postcode_coverage_r1_*.csv"
EXPECTED_FILES = 121
EXPECTED_ROWS = 1_741_096
V2_DATE = "2026-07-07"
EXPECTED_R2_PARENT = "postcode_files"
REQUIRED_FIELDS = {
    "postcode": ["postcode"],
    "postcode_space": ["postcode_space"],
    "postcode_area": ["postcode area", "postcode_area"],
    "sfbb": ["SFBB availability (% premises)"],
    "ufbb100": ["UFBB (100Mbit/s) availability (% premises)"],
    "ufbb300": ["UFBB availability (% premises)"],
    "gigabit": ["Gigabit availability (% premises)"],
    "unable30": ["% of premises unable to receive 30Mbit/s"],
    "unable_decent": ["% of premises unable to receive decent broadband from fixed or FWA"],
}
FORBIDDEN_POSTCODE_FIELDS = {
    "full fibre availability premises": "Full Fibre availability (% premises)",
    "number of premises with full fibre availability": "Number of premises with Full Fibre availability",
}
FORBIDDEN_POSTCODE_COUNT_EXACT = {
    "all premises",
    "all matched premises",
}
FORBIDDEN_POSTCODE_COUNT_PREFIXES = (
    "number of premises",
)
POSTCODE_RE = re.compile(r"^(GIR0AA|[A-Z]{1,2}[0-9][A-Z0-9]?[0-9][A-Z]{2})$")
POSTCODE_SPACE_RE = re.compile(r"^(GIR 0AA|[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2})$")


def normalise_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def first_present(row: dict[str, Any], aliases: Iterable[str]) -> Any:
    normalised = {normalise_key(k): v for k, v in row.items()}
    for alias in aliases:
        key = normalise_key(alias)
        if key in normalised:
            return normalised[key]
    return None


def normalise_postcode(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", "", str(value)).upper().strip()
    return text or None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_percent(value: Any, *, field: str, file_name: str, row_number: int) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("%", "")
    if not text or text.lower() in {"null", "none", "na", "n/a", "-"}:
        return None
    try:
        number = float(text)
    except ValueError as exc:
        raise ValueError(f"Non-numeric percentage {field} in {file_name} row {row_number}: {text}") from exc
    if not math.isfinite(number):
        raise ValueError(f"Non-finite percentage {field} in {file_name} row {row_number}: {text}")
    if not 0 <= number <= 100:
        raise ValueError(f"Percentage outside 0-100 for {field} in {file_name} row {row_number}: {number}")
    return number


def validate_speed_threshold_order(metrics: dict[str, float | None], *, file_name: str, row_number: int) -> None:
    """Higher fixed-line speed thresholds cannot cover more premises than lower thresholds."""
    ordered = ("sfbb", "ufbb100", "ufbb300", "gigabit")
    for lower_name, higher_name in zip(ordered, ordered[1:]):
        lower = metrics[lower_name]
        higher = metrics[higher_name]
        if lower is not None and higher is not None and higher > lower:
            raise ValueError(
                f"Coverage threshold order violation in {file_name} row {row_number}: "
                f"{higher_name}={higher} exceeds {lower_name}={lower}"
            )


def expected_area_from_postcode(postcode: str) -> str:
    match = re.match(r"^([A-Z]{1,3})", postcode)
    return match.group(1) if match else ""


def validate(directory: Path, *, expected_files: int = EXPECTED_FILES, expected_rows: int = EXPECTED_ROWS) -> dict[str, Any]:
    r1 = sorted(directory.rglob(R1_GLOB))
    if r1:
        raise ValueError(f"Superseded r1 all-premises files present: {len(r1)}")
    files = sorted(directory.rglob(R2_GLOB))
    if len(files) != expected_files:
        raise ValueError(f"Expected {expected_files} corrected r2 files, found {len(files)}")

    wrong_parent = [str(path) for path in files if path.parent.name != EXPECTED_R2_PARENT]
    if wrong_parent:
        raise ValueError(
            f"Corrected r2 all-premises files must be inside '{EXPECTED_R2_PARENT}': {wrong_parent[:3]}"
        )

    by_area: dict[str, Path] = {}
    for path in files:
        match = re.search(r"_r2_([A-Za-z]{1,3})\.csv$", path.name)
        if not match:
            raise ValueError(f"Unexpected r2 file name: {path.name}")
        area = match.group(1).upper()
        if area in by_area:
            raise ValueError(f"Duplicate r2 file for postcode area {area}")
        by_area[area] = path

    for area in ("CV", "CW", "ME", "MK"):
        if area not in by_area:
            raise ValueError(f"Required V2 correction area file missing: {area}")

    hashes = {area: sha256_file(path) for area, path in by_area.items()}
    if hashes["CW"] == hashes["CV"]:
        raise ValueError("V2 correction failed: CW file is still an exact duplicate of CV")
    if hashes["MK"] == hashes["ME"]:
        raise ValueError("V2 correction failed: MK file is still an exact duplicate of ME")

    seen_postcodes: set[str] = set()
    total_rows = 0
    null_metric_rows = 0
    percentage_cells_validated = 0
    manifests: list[dict[str, Any]] = []
    for area, path in sorted(by_area.items()):
        file_rows = 0
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            normalised_headers = [normalise_key(h) for h in headers]
            duplicates = sorted({h for h in normalised_headers if normalised_headers.count(h) > 1})
            if duplicates:
                raise ValueError(f"Duplicate normalized CSV headers in {path.name}: {duplicates}")
            header_keys = set(normalised_headers)
            missing = [name for name, aliases in REQUIRED_FIELDS.items() if not any(normalise_key(a) in header_keys for a in aliases)]
            if missing:
                raise ValueError(f"{path.name} missing required fields: {missing}")
            forbidden = [display for key, display in FORBIDDEN_POSTCODE_FIELDS.items() if key in header_keys]
            if forbidden:
                raise ValueError(f"Postcode-level full-fibre field prohibited by V2 schema in {path.name}: {forbidden}")
            wrong_level_counts = sorted(
                key for key in header_keys
                if key in FORBIDDEN_POSTCODE_COUNT_EXACT
                or any(key.startswith(prefix) for prefix in FORBIDDEN_POSTCODE_COUNT_PREFIXES)
            )
            if wrong_level_counts:
                raise ValueError(
                    f"Postcode-level premise-count field prohibited by V2 schema in {path.name}: {wrong_level_counts}"
                )
            percentage_headers = [header for header in headers if "%" in header]
            if not percentage_headers:
                raise ValueError(f"No percentage columns found in postcode file: {path.name}")
            for csv_row_no, row in enumerate(reader, start=2):
                file_rows += 1
                total_rows += 1
                postcode = normalise_postcode(first_present(row, REQUIRED_FIELDS["postcode"]))
                postcode_space_raw = str(first_present(row, REQUIRED_FIELDS["postcode_space"]) or "").strip().upper()
                postcode_space = normalise_postcode(postcode_space_raw)
                postcode_area = str(first_present(row, REQUIRED_FIELDS["postcode_area"]) or "").strip().upper()
                if not postcode or not POSTCODE_RE.fullmatch(postcode):
                    raise ValueError(f"Invalid UK postcode in {path.name} row {csv_row_no}: {postcode}")
                if not POSTCODE_SPACE_RE.fullmatch(postcode_space_raw):
                    raise ValueError(f"postcode_space must contain exactly one inward-code separator in {path.name} row {csv_row_no}: {postcode_space_raw}")
                if postcode_space != postcode:
                    raise ValueError(f"postcode/postcode_space mismatch in {path.name} row {csv_row_no}: {postcode}/{postcode_space}")
                derived_area = expected_area_from_postcode(postcode)
                if postcode_area != derived_area or area != derived_area:
                    raise ValueError(f"Postcode area mismatch in {path.name} row {csv_row_no}: file={area}, field={postcode_area}, postcode={postcode}")
                if postcode in seen_postcodes:
                    raise ValueError(f"Duplicate postcode across corrected r2 files: {postcode}")
                seen_postcodes.add(postcode)
                for percentage_header in percentage_headers:
                    parse_percent(row.get(percentage_header), field=percentage_header, file_name=path.name, row_number=csv_row_no)
                    percentage_cells_validated += 1
                metrics = {
                    name: parse_percent(first_present(row, REQUIRED_FIELDS[name]), field=name, file_name=path.name, row_number=csv_row_no)
                    for name in ("sfbb", "ufbb100", "ufbb300", "gigabit", "unable30", "unable_decent")
                }
                validate_speed_threshold_order(metrics, file_name=path.name, row_number=csv_row_no)
                if all(value is None for value in metrics.values()):
                    null_metric_rows += 1
        if file_rows == 0:
            raise ValueError(f"Empty corrected r2 postcode file: {path.name}")
        manifests.append({"postcode_area": area, "file": path.name, "rows": file_rows, "sha256": hashes[area]})

    if total_rows != expected_rows:
        raise ValueError(f"Expected {expected_rows} postcode rows, found {total_rows}")
    if len(seen_postcodes) != total_rows:
        raise ValueError("Unique postcode count does not equal total row count")

    return {
        "schema_version": 6,
        "source": "Ofcom Connected Nations Spring 2026 fixed broadband coverage",
        "source_snapshot": "2026-01",
        "source_revision": "v2-r2",
        "source_revision_date": V2_DATE,
        "required_pattern": R2_GLOB,
        "required_parent_directory": EXPECTED_R2_PARENT,
        "rejected_pattern": R1_GLOB,
        "file_count": len(files),
        "row_count": total_rows,
        "unique_postcode_count": len(seen_postcodes),
        "all_metrics_null_row_count": null_metric_rows,
        "all_percentage_cells_validated": percentage_cells_validated,
        "cw_sha256": hashes["CW"],
        "cv_sha256": hashes["CV"],
        "mk_sha256": hashes["MK"],
        "me_sha256": hashes["ME"],
        "cw_not_cv_duplicate": True,
        "mk_not_me_duplicate": True,
        "postcode_files_directory_validated": True,
        "postcode_space_exact_single_separator_validated": True,
        "duplicate_normalized_headers_rejected": True,
        "postcode_premise_count_fields_present": False,
        "postcode_full_fibre_field_present": False,
        "all_percentage_columns_range_validated": True,
        "coverage_speed_threshold_order_validated": True,
        "coverage_speed_threshold_order": ["SFBB_30_PLUS", "UFBB_100_PLUS", "UFBB_300_PLUS", "GIGABIT_CAPABLE"],
        "coverage_network_scope": "FIXED_LINE_ONLY_EXCEPT_FIELDS_EXPLICITLY_NAMED_FIXED_OR_FWA",
        "sfbb_ufbb_gigabit_denominator": "ALL_PREMISES_IN_POSTCODE",
        "unable_30mbps_denominator": "MATCHED_PREMISES",
        "unable_decent_fixed_or_fwa_denominator": "ALL_PREMISES_INCLUDING_UNMATCHED_AND_ZERO_PREDICTED_SPEED",
        "postcode_full_fibre_availability_published": False,
        "metric_semantics_source": "Ofcom About this data fixed coverage and full-fibre take-up v2 pages 3-6",
        "files": manifests,
        "status": "PASS_OFFICIAL_V2_R2_CORRECTION_AND_SEMANTICS_VALIDATED",
        "actual_business_data_rows_written": 0,
        "final_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ofcom-postcode-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = validate(args.ofcom_postcode_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "status", "file_count", "row_count", "unique_postcode_count",
        "cw_not_cv_duplicate", "mk_not_me_duplicate",
        "postcode_files_directory_validated", "postcode_space_exact_single_separator_validated",
        "postcode_premise_count_fields_present", "all_percentage_columns_range_validated",
        "coverage_speed_threshold_order_validated", "postcode_full_fibre_availability_published",
        "actual_business_data_rows_written", "final_ready"
    )}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
