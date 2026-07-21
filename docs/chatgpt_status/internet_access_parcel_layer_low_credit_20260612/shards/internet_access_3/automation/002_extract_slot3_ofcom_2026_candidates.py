#!/usr/bin/env python3
"""Build truthful internet_access_3 candidate rows from canonical rows and Ofcom 2026 postcode files.

This program never invents a parcel, postcode or score. It rejects the superseded
all-premises r1 postcode files documented by Ofcom on 7 July 2026 and accepts only
202601_fixed_postcode_coverage_r2_*.csv for the current all-premises snapshot.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "internet_access_3"
ROW_START = 61523
ROW_END = 92283
EXPECTED_ROWS = 30761
R2_GLOB = "202601_fixed_postcode_coverage_r2_*.csv"
R1_GLOB = "202601_fixed_postcode_coverage_r1_*.csv"


def normalise_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def normalise_postcode(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"\s+", "", str(value)).upper().strip()
    return cleaned or None


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("%", "")
    if not text or text.lower() in {"null", "none", "na", "n/a", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def first_present(row: dict[str, Any], aliases: Iterable[str]) -> Any:
    normalised = {normalise_key(k): v for k, v in row.items()}
    for alias in aliases:
        key = normalise_key(alias)
        if key in normalised:
            return normalised[key]
    return None


def row_number(row: dict[str, Any]) -> int | None:
    value = first_present(row, ["row_no", "row number", "canonical_row_no", "matrix_row", "parcel_index"])
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def canonical_id(row: dict[str, Any]) -> str | None:
    value = first_present(row, ["canonical_program_parcel_id", "parcel_id", "canonical parcel id"])
    return str(value).strip() if value not in (None, "") else None


def load_canonical(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    elif suffix in {".json", ".geojson"}:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict) and isinstance(payload.get("features"), list):
            rows = []
            for feature in payload["features"]:
                properties = dict(feature.get("properties") or {})
                geometry = feature.get("geometry")
                if geometry is not None:
                    properties["geometry"] = geometry
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
    if len(set(numbers)) != EXPECTED_ROWS or min(numbers) != ROW_START or max(numbers) != ROW_END:
        raise ValueError("Canonical slot range has duplicate rows or a gap")
    return sorted(selected, key=lambda row: row_number(row) or 0)


def load_legacy_internet(path: Path | None) -> dict[int, dict[str, Any]]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    result: dict[int, dict[str, Any]] = {}
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        number = row_number(properties)
        if number is not None and ROW_START <= number <= ROW_END:
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
    return as_float(first_present(row, aliases))


def load_ofcom_postcodes(directory: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    superseded = sorted(directory.glob(R1_GLOB))
    if superseded:
        names = ", ".join(path.name for path in superseded[:5])
        raise ValueError(f"Superseded all-premises r1 postcode files present: {names}")

    files = sorted(directory.glob(R2_GLOB))
    if not files:
        raise ValueError(f"No files matched required pattern {R2_GLOB}")

    coverage: dict[str, dict[str, Any]] = {}
    duplicate_postcodes: set[str] = set()
    for file_path in files:
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                postcode = normalise_postcode(first_present(row, ["postcode", "postcode_space"]))
                if not postcode:
                    continue
                record = {
                    "postcode": postcode,
                    "postcode_space": first_present(row, ["postcode_space"]),
                    "postcode_area": first_present(row, ["postcode area", "postcode_area"]),
                    "sfbb_30mbps_available_pct": ofcom_value(row, ["SFBB availability (% premises)"]),
                    "ufbb_100mbps_available_pct": ofcom_value(row, ["UFBB (100Mbit/s) availability (% premises)"]),
                    "ufbb_300mbps_available_pct": ofcom_value(row, ["UFBB availability (% premises)"]),
                    "gigabit_available_pct": ofcom_value(row, ["Gigabit availability (% premises)"]),
                    "unable_30mbps_pct": ofcom_value(row, ["% of premises unable to receive 30Mbit/s", "% of premises unable to receive [X]Mbit/s"]),
                    "unable_decent_fixed_or_fwa_pct": ofcom_value(row, ["% of premises unable to receive decent broadband from fixed or FWA"]),
                    "source_file": file_path.name,
                    "source_snapshot_date": "2026-01",
                    "source_revision": "r2",
                }
                if postcode in coverage and coverage[postcode] != record:
                    duplicate_postcodes.add(postcode)
                coverage[postcode] = record

    if duplicate_postcodes:
        raise ValueError(f"Conflicting duplicate Ofcom postcode rows: {len(duplicate_postcodes)}")
    return coverage, [path.name for path in files]


def build_rows(
    canonical_rows: list[dict[str, Any]],
    legacy_rows: dict[int, dict[str, Any]],
    coverage: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for canonical in canonical_rows:
        number = row_number(canonical)
        assert number is not None
        direct_postcode = normalise_postcode(first_present(canonical, ["postcode", "postcode_space"]))
        legacy_postcode = parse_legacy_postcode(legacy_rows.get(number, {}))
        postcode = direct_postcode or legacy_postcode
        match_method = "CANONICAL_POSTCODE" if direct_postcode else "LEGACY_VERIFIED_PROXY_POSTCODE" if legacy_postcode else "NO_POSTCODE"
        source = coverage.get(postcode or "")

        record: dict[str, Any] = {
            "slot_id": SLOT_ID,
            "canonical_row_no": number,
            "canonical_program_parcel_id": canonical_id(canonical),
            "hmlr_inspire_id": first_present(canonical, ["hmlr_inspire_id", "inspire_id"]),
            "parcel_centroid_lon": as_float(first_present(canonical, ["parcel_centroid_lon", "hmlr_lon", "lon", "longitude"])),
            "parcel_centroid_lat": as_float(first_present(canonical, ["parcel_centroid_lat", "hmlr_lat", "lat", "latitude"])),
            "postcode": postcode,
            "internet_match_method": match_method,
            "source_level": "POSTCODE_PROXY" if source else "NO_DATA",
            "internet_match_confidence": 0.95 if source and direct_postcode else 0.80 if source and legacy_postcode else 0.0,
            "internet_availability_quality_percent": None,
            "internet_quality_band": None,
            "internet_accuracy": "SCHEMA_VERIFIED_SCORE_NOT_YET_APPROVED" if source else "NO_DATA",
            "calculation_version": None,
            "calculation_explanation": "No score emitted until a column-aware scoring contract is approved.",
            "status": "CURRENT_POSTCODE_COVERAGE_READY_FOR_SCORING" if source else "NO_DATA",
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
    jsonl_path = args.output_dir / "internet_access_3_candidates_latest.jsonl"
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    ready = sum(row["status"] == "CURRENT_POSTCODE_COVERAGE_READY_FOR_SCORING" for row in rows)
    no_data = len(rows) - ready
    direct = sum(row["internet_match_method"] == "CANONICAL_POSTCODE" and row["status"] != "NO_DATA" for row in rows)
    legacy = sum(row["internet_match_method"] == "LEGACY_VERIFIED_PROXY_POSTCODE" and row["status"] != "NO_DATA" for row in rows)
    manifest = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "parcel_start": ROW_START,
        "parcel_end": ROW_END,
        "canonical_rows": len(rows),
        "candidate_ready_for_scoring_rows": ready,
        "no_data_rows": no_data,
        "direct_canonical_postcode_matches": direct,
        "legacy_proxy_postcode_matches": legacy,
        "ofcom_postcodes_loaded": len(coverage),
        "ofcom_files_loaded": len(source_files),
        "ofcom_required_pattern": R2_GLOB,
        "scores_written": 0,
        "actual_business_data_rows_written": 0,
        "migration": False,
        "fake_data": False,
        "final_ready": False,
        "samples": rows[:3],
    }
    manifest_path = args.output_dir / "internet_access_3_candidate_manifest_latest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
