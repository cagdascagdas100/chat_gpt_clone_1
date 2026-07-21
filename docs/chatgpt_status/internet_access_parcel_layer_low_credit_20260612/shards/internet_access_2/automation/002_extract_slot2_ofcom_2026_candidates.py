#!/usr/bin/env python3
"""Build review-only internet_access_2 rows from canonical parcels and Ofcom 2026 postcode files.

No parcel, postcode, coverage value, score, confidence, or geometry is invented.
The all-premises postcode input must be the corrected Ofcom January 2026 r2 release.
Outputs are candidate/readback artifacts only; business rows remain unchanged.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "internet_access_2"
ROW_START = 30762
ROW_END = 61522
EXPECTED_ROWS = 30761
R2_GLOB = "202601_fixed_postcode_coverage_r2_*.csv"
R1_GLOB = "202601_fixed_postcode_coverage_r1_*.csv"
EXPECTED_OFCOM_FILE_COUNT = 121
EXPECTED_OFCOM_POSTCODE_ROWS = 1741096
POSTCODE_RE = re.compile(r"^(GIR0AA|[A-Z]{1,2}[0-9][A-Z0-9]?[0-9][A-Z]{2})$")

FIELD_ALIASES = {
    "postcode": ["postcode", "postcode_space"],
    "sfbb": ["SFBB availability (% premises)"],
    "ufbb100": ["UFBB (100Mbit/s) availability (% premises)"],
    "ufbb300": ["UFBB availability (% premises)"],
    "gigabit": ["Gigabit availability (% premises)"],
    "unable30": ["% of premises unable to receive 30Mbit/s"],
    "unable_decent": ["% of premises unable to receive decent broadband from fixed or FWA"],
}


def normalise_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def normalise_postcode(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", "", str(value)).upper().strip()
    return cleaned or None


def valid_postcode(value: str | None) -> bool:
    return bool(value and POSTCODE_RE.fullmatch(value))


def as_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("%", "")
    if not text or text.lower() in {"null", "none", "na", "n/a", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def as_percent(value: Any) -> float | None:
    number = as_number(value)
    if number is None:
        return None
    if not 0 <= number <= 100:
        raise ValueError(f"Coverage percentage outside 0-100: {number}")
    return number


def first_present(row: dict[str, Any], aliases: Iterable[str]) -> Any:
    normalised = {normalise_key(k): v for k, v in row.items()}
    for alias in aliases:
        key = normalise_key(alias)
        if key in normalised:
            return normalised[key]
    return None


def has_alias(headers: Iterable[str], aliases: Iterable[str]) -> bool:
    keys = {normalise_key(header) for header in headers}
    return any(normalise_key(alias) in keys for alias in aliases)


def row_number(row: dict[str, Any]) -> int | None:
    value = first_present(row, ["row_no", "row number", "canonical_row_no", "matrix_row", "parcel_index"])
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def canonical_id(row: dict[str, Any]) -> str | None:
    value = first_present(row, ["canonical_program_parcel_id", "parcel_id", "canonical parcel id"])
    return str(value).strip() if value not in (None, "") else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_canonical(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    elif suffix in {".json", ".geojson"}:
        with path.open("r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict) and isinstance(payload.get("features"), list):
            rows = []
            for feature in payload["features"]:
                properties = dict(feature.get("properties") or {})
                geometry = feature.get("geometry")
                properties["_existing_geometry_type"] = (geometry or {}).get("type")
                rows.append(properties)
        elif isinstance(payload, list):
            rows = payload
        else:
            raise ValueError("Canonical JSON must be a list or GeoJSON FeatureCollection")
    else:
        raise ValueError(f"Unsupported canonical input: {path}")

    selected = [row for row in rows if (number := row_number(row)) is not None and ROW_START <= number <= ROW_END]
    if len(selected) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} canonical slot rows, found {len(selected)}")
    numbers = [row_number(row) for row in selected]
    ids = [canonical_id(row) for row in selected]
    if len(set(numbers)) != EXPECTED_ROWS or min(numbers) != ROW_START or max(numbers) != ROW_END:
        raise ValueError("Canonical slot range has duplicate rows or a gap")
    if any(not parcel_id for parcel_id in ids) or len(set(ids)) != EXPECTED_ROWS:
        raise ValueError("Canonical slot has missing or duplicate parcel IDs")
    return sorted(selected, key=lambda row: row_number(row) or 0)


def load_legacy_internet(path: Path | None) -> dict[int, dict[str, Any]]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    result: dict[int, dict[str, Any]] = {}
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        number = row_number(properties)
        if number is not None and ROW_START <= number <= ROW_END:
            if number in result:
                raise ValueError(f"Duplicate legacy internet row_no: {number}")
            result[number] = properties
    return result


def parse_legacy_postcode(properties: dict[str, Any]) -> str | None:
    direct = first_present(properties, ["postcode", "postcode_space"])
    if direct:
        return normalise_postcode(direct)
    value = str(properties.get("internet_level_value") or "")
    match = re.search(r"postcode=([A-Z0-9 ]+?)(?:;|$)", value, flags=re.IGNORECASE)
    return normalise_postcode(match.group(1)) if match else None


def ofcom_value(row: dict[str, Any], aliases: list[str]) -> float | None:
    return as_percent(first_present(row, aliases))


def load_ofcom_postcodes(directory: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    superseded = sorted(directory.rglob(R1_GLOB))
    if superseded:
        names = ", ".join(path.name for path in superseded[:5])
        raise ValueError(f"Superseded all-premises r1 postcode files present: {names}")

    files = sorted(directory.rglob(R2_GLOB))
    if len(files) != EXPECTED_OFCOM_FILE_COUNT:
        raise ValueError(f"Expected {EXPECTED_OFCOM_FILE_COUNT} Ofcom r2 postcode files, found {len(files)}")

    coverage: dict[str, dict[str, Any]] = {}
    duplicate_postcodes: set[str] = set()
    file_manifest: list[dict[str, Any]] = []
    total_rows = 0
    for file_path in files:
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            missing = [field for field, aliases in FIELD_ALIASES.items() if not has_alias(headers, aliases)]
            if missing:
                raise ValueError(f"{file_path.name} missing required fields: {missing}")
            file_rows = 0
            for row in reader:
                file_rows += 1
                total_rows += 1
                postcode = normalise_postcode(first_present(row, FIELD_ALIASES["postcode"]))
                if not postcode:
                    raise ValueError(f"Blank postcode in {file_path.name} row {file_rows + 1}")
                record = {
                    "postcode": postcode,
                    "postcode_space": first_present(row, ["postcode_space"]),
                    "postcode_area": first_present(row, ["postcode area", "postcode_area"]),
                    "sfbb_30mbps_available_pct": ofcom_value(row, FIELD_ALIASES["sfbb"]),
                    "ufbb_100mbps_available_pct": ofcom_value(row, FIELD_ALIASES["ufbb100"]),
                    "ufbb_300mbps_available_pct": ofcom_value(row, FIELD_ALIASES["ufbb300"]),
                    "gigabit_available_pct": ofcom_value(row, FIELD_ALIASES["gigabit"]),
                    "unable_30mbps_pct": ofcom_value(row, FIELD_ALIASES["unable30"]),
                    "unable_decent_fixed_or_fwa_pct": ofcom_value(row, FIELD_ALIASES["unable_decent"]),
                    "source_file": file_path.name,
                    "source_snapshot_date": "2026-01",
                    "source_revision": "r2",
                }
                if postcode in coverage and coverage[postcode] != record:
                    duplicate_postcodes.add(postcode)
                coverage[postcode] = record
        file_manifest.append({"file": file_path.name, "rows": file_rows, "sha256": sha256_file(file_path)})

    if total_rows != EXPECTED_OFCOM_POSTCODE_ROWS:
        raise ValueError(f"Expected {EXPECTED_OFCOM_POSTCODE_ROWS} Ofcom postcode rows, found {total_rows}")
    if duplicate_postcodes:
        raise ValueError(f"Conflicting duplicate Ofcom postcode rows: {len(duplicate_postcodes)}")
    return coverage, file_manifest


def resolve_postcode(canonical_value: Any, legacy_value: Any) -> dict[str, Any]:
    canonical = normalise_postcode(canonical_value)
    legacy = normalise_postcode(legacy_value)
    canonical_valid = valid_postcode(canonical)
    legacy_valid = valid_postcode(legacy)
    invalid = [value for value, ok in ((canonical, canonical_valid), (legacy, legacy_valid)) if value and not ok]
    conflict = bool(canonical_valid and legacy_valid and canonical != legacy)

    if canonical_valid:
        selected = canonical
        origin = "CANONICAL"
        if conflict:
            resolution = "CANONICAL_VALID_LEGACY_CONFLICT_IGNORED"
        elif legacy_valid:
            resolution = "CANONICAL_VALID_LEGACY_SAME"
        elif legacy:
            resolution = "CANONICAL_VALID_LEGACY_INVALID_IGNORED"
        else:
            resolution = "CANONICAL_VALID"
    elif legacy_valid:
        selected = legacy
        origin = "LEGACY"
        resolution = "LEGACY_VALID_FALLBACK_CANONICAL_INVALID" if canonical else "LEGACY_VALID_FALLBACK_CANONICAL_MISSING"
    else:
        selected = None
        origin = "NONE"
        resolution = "NO_VALID_POSTCODE"

    return {
        "selected": selected,
        "origin": origin,
        "resolution": resolution,
        "canonical": canonical,
        "canonical_valid": canonical_valid,
        "legacy": legacy,
        "legacy_valid": legacy_valid,
        "conflict": conflict,
        "invalid": invalid,
    }


def build_rows(
    canonical_rows: list[dict[str, Any]],
    legacy_rows: dict[int, dict[str, Any]],
    coverage: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for canonical in canonical_rows:
        number = row_number(canonical)
        assert number is not None
        canonical_raw = first_present(canonical, ["postcode", "postcode_space"])
        legacy_raw = parse_legacy_postcode(legacy_rows.get(number, {}))
        resolved = resolve_postcode(canonical_raw, legacy_raw)
        postcode = resolved["selected"]
        source = coverage.get(postcode or "")
        if source and resolved["origin"] == "CANONICAL":
            match_method = "CANONICAL_POSTCODE"
            source_level = "POSTCODE_PROXY"
            confidence = 0.95
            accuracy = "CURRENT_R2_POSTCODE_COVERAGE_DIRECT"
            status = "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW"
        elif source and resolved["origin"] == "LEGACY":
            match_method = "LEGACY_POSTCODE_PROXY"
            source_level = "POSTCODE_PROXY_LEGACY_MATCH"
            confidence = 0.70
            accuracy = "CURRENT_R2_COVERAGE_LEGACY_POSTCODE_REQUIRES_SPATIAL_QA"
            status = "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA"
        else:
            match_method = "NO_POSTCODE" if not postcode else "POSTCODE_NOT_IN_CURRENT_R2"
            source_level = "NO_DATA"
            confidence = 0.0
            accuracy = "NO_DATA"
            status = "NO_DATA"

        record: dict[str, Any] = {
            "slot_id": SLOT_ID,
            "canonical_row_no": number,
            "canonical_program_parcel_id": canonical_id(canonical),
            "hmlr_inspire_id": first_present(canonical, ["hmlr_inspire_id", "inspire_id"]),
            "parcel_centroid_lon": as_number(first_present(canonical, ["parcel_centroid_lon", "hmlr_lon", "lon", "longitude"])),
            "parcel_centroid_lat": as_number(first_present(canonical, ["parcel_centroid_lat", "hmlr_lat", "lat", "latitude"])),
            "existing_geometry_type": canonical.get("_existing_geometry_type"),
            "postcode": postcode,
            "canonical_postcode_candidate": resolved["canonical"],
            "canonical_postcode_valid": resolved["canonical_valid"],
            "legacy_postcode_candidate": resolved["legacy"],
            "legacy_postcode_valid": resolved["legacy_valid"],
            "postcode_resolution": resolved["resolution"],
            "postcode_conflict": resolved["conflict"],
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument("--ofcom-postcode-dir", required=True, type=Path)
    parser.add_argument("--legacy-internet-geojson", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    canonical_rows = load_canonical(args.canonical)
    legacy_rows = load_legacy_internet(args.legacy_internet_geojson)
    coverage, source_files = load_ofcom_postcodes(args.ofcom_postcode_dir)
    rows = build_rows(canonical_rows, legacy_rows, coverage)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = args.output_dir / "internet_access_2_candidates_latest.jsonl"
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    direct = sum(row["status"] == "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW" for row in rows)
    legacy = sum(row["status"] == "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA" for row in rows)
    no_data = sum(row["status"] == "NO_DATA" for row in rows)
    resolution_counts: dict[str, int] = {}
    for row in rows:
        key = str(row["postcode_resolution"])
        resolution_counts[key] = resolution_counts.get(key, 0) + 1
    manifest = {
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "parcel_start": ROW_START,
        "parcel_end": ROW_END,
        "canonical_source": str(args.canonical),
        "canonical_source_sha256": sha256_file(args.canonical),
        "legacy_internet_source": str(args.legacy_internet_geojson) if args.legacy_internet_geojson else None,
        "legacy_internet_source_sha256": sha256_file(args.legacy_internet_geojson) if args.legacy_internet_geojson else None,
        "canonical_rows": len(rows),
        "direct_current_r2_matches": direct,
        "legacy_current_r2_matches_pending_spatial_qa": legacy,
        "no_data_rows": no_data,
        "postcode_resolution_counts": resolution_counts,
        "invalid_postcode_candidate_rows": sum(bool(row["invalid_postcode_candidates"]) for row in rows),
        "canonical_legacy_postcode_conflict_rows": sum(bool(row["postcode_conflict"]) for row in rows),
        "ofcom_postcodes_loaded": len(coverage),
        "ofcom_files_loaded": len(source_files),
        "ofcom_required_pattern": R2_GLOB,
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
    manifest_path = args.output_dir / "internet_access_2_extraction_manifest_latest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "slot_id": SLOT_ID,
        "canonical_rows": len(rows),
        "direct_current_r2_matches": direct,
        "legacy_current_r2_matches_pending_spatial_qa": legacy,
        "no_data_rows": no_data,
        "postcode_resolution_counts": resolution_counts,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "manifest": str(manifest_path),
        "jsonl": str(jsonl_path),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
