#!/usr/bin/env python3
"""Build truthful internet_access_3 review candidates.

The canonical 92,283-row matrix does not itself contain postcodes. Therefore this
extractor only reuses postcode evidence already attached to the same canonical
row in the existing internet matrix. It never assigns the nearest postcode,
creates parcel geometry, or emits a parcel score.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
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
EXPECTED_OFCOM_FILE_COUNT = 121
EXPECTED_OFCOM_POSTCODE_ROWS = 1741096

FIELD_ALIASES = {
    "postcode": ["postcode", "postcode_space", "Postcode with spaces removed"],
    "postcode_space": ["postcode_space", "Postcode with spaces"],
    "postcode_area": ["postcode area", "postcode_area"],
    "sfbb": ["SFBB availability (% premises)"],
    "ufbb100": ["UFBB (100Mbit/s) availability (% premises)"],
    "ufbb300": ["UFBB availability (% premises)"],
    "gigabit": ["Gigabit availability (% premises)"],
    "unable30": [
        "% of premises unable to receive 30Mbit/s",
        "% of premises unable to receive [X]Mbit/s",
    ],
    "unable_decent": [
        "% of premises unable to receive decent broadband from fixed or FWA"
    ],
}
REQUIRED_OFCOM_FIELDS = ("postcode", "sfbb", "ufbb100", "ufbb300", "gigabit")


def normalise_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def normalise_postcode(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = re.sub(r"[^A-Z0-9]", "", str(value).upper())
    return cleaned or None


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"null", "none", "na", "n/a", "-"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_percentage(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("%", "")
    if not text or text.lower() in {"null", "none", "na", "n/a", "-"}:
        return None
    try:
        number = float(text)
    except ValueError:
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
    value = first_present(row, ["row_no", "row number", "canonical_row_no", "matrix_row"])
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def parcel_id(row: dict[str, Any]) -> str | None:
    value = first_present(row, ["parcel_id", "canonical_program_parcel_id"])
    return str(value).strip() if value not in (None, "") else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_geojson_features(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise ValueError(f"Expected GeoJSON FeatureCollection: {path}")
    return payload["features"]


def load_canonical(path: Path) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for feature in load_geojson_features(path):
        properties = dict(feature.get("properties") or {})
        number = row_number(properties)
        if number is None or not ROW_START <= number <= ROW_END:
            continue
        properties["geometry"] = feature.get("geometry")
        selected.append(properties)

    if len(selected) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} canonical slot rows, found {len(selected)}")
    numbers = [row_number(row) for row in selected]
    ids = [parcel_id(row) for row in selected]
    if len(set(numbers)) != EXPECTED_ROWS or min(numbers) != ROW_START or max(numbers) != ROW_END:
        raise ValueError("Canonical slot range has duplicate row numbers or a gap")
    if any(not value for value in ids) or len(set(ids)) != EXPECTED_ROWS:
        raise ValueError("Canonical slot has missing or duplicate parcel IDs")
    return sorted(selected, key=lambda row: row_number(row) or 0)


def parse_legacy_postcode(properties: dict[str, Any]) -> str | None:
    direct = first_present(properties, ["postcode", "postcode_space"])
    if direct:
        return normalise_postcode(direct)
    value = str(properties.get("internet_level_value") or "")
    match = re.search(r"(?:^|;)\s*postcode\s*=\s*([A-Z0-9 ]+?)(?:;|$)", value, flags=re.I)
    return normalise_postcode(match.group(1)) if match else None


def load_legacy_internet(path: Path) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for feature in load_geojson_features(path):
        properties = dict(feature.get("properties") or {})
        number = row_number(properties)
        if number is None or not ROW_START <= number <= ROW_END:
            continue
        if number in result:
            raise ValueError(f"Duplicate legacy internet row_no: {number}")
        result[number] = properties
    return result


def identity_match(canonical: dict[str, Any], legacy: dict[str, Any]) -> tuple[bool, str]:
    if parcel_id(canonical) != parcel_id(legacy):
        return False, "PARCEL_ID_MISMATCH"
    canonical_inspire = str(canonical.get("hmlr_inspire_id") or "").strip()
    legacy_inspire = str(legacy.get("hmlr_inspire_id") or "").strip()
    if canonical_inspire and legacy_inspire and canonical_inspire != legacy_inspire:
        return False, "HMLR_INSPIRE_ID_MISMATCH"
    return True, "ROW_AND_OFFICIAL_ID_MATCH"


def load_ofcom_postcodes(directory: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    superseded = sorted(directory.rglob(R1_GLOB))
    if superseded:
        raise ValueError(f"Superseded all-premises r1 files present: {len(superseded)}")
    files = sorted(directory.rglob(R2_GLOB))
    if len(files) != EXPECTED_OFCOM_FILE_COUNT:
        raise ValueError(f"Expected {EXPECTED_OFCOM_FILE_COUNT} r2 files, found {len(files)}")

    coverage: dict[str, dict[str, Any]] = {}
    manifest: list[dict[str, Any]] = []
    total_rows = 0
    for file_path in files:
        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            missing = [name for name in REQUIRED_OFCOM_FIELDS if not has_alias(headers, FIELD_ALIASES[name])]
            if missing:
                raise ValueError(f"{file_path.name} missing fields: {missing}")
            file_rows = 0
            for row in reader:
                file_rows += 1
                total_rows += 1
                postcode = normalise_postcode(first_present(row, FIELD_ALIASES["postcode"]))
                if not postcode:
                    raise ValueError(f"Blank postcode in {file_path.name} row {file_rows + 1}")
                if postcode in coverage:
                    raise ValueError(f"Duplicate Ofcom postcode: {postcode}")
                coverage[postcode] = {
                    "postcode": postcode,
                    "postcode_space": first_present(row, FIELD_ALIASES["postcode_space"]),
                    "postcode_area": first_present(row, FIELD_ALIASES["postcode_area"]),
                    "sfbb_30mbps_available_pct": parse_percentage(first_present(row, FIELD_ALIASES["sfbb"])),
                    "ufbb_100mbps_available_pct": parse_percentage(first_present(row, FIELD_ALIASES["ufbb100"])),
                    "ufbb_300mbps_available_pct": parse_percentage(first_present(row, FIELD_ALIASES["ufbb300"])),
                    "gigabit_available_pct": parse_percentage(first_present(row, FIELD_ALIASES["gigabit"])),
                    "unable_30mbps_pct": parse_percentage(first_present(row, FIELD_ALIASES["unable30"])),
                    "unable_decent_fixed_or_fwa_pct": parse_percentage(first_present(row, FIELD_ALIASES["unable_decent"])),
                    "source_file": file_path.name,
                    "source_snapshot_date": "2026-01",
                    "source_revision": "r2",
                }
        manifest.append({"file": file_path.name, "rows": file_rows, "sha256": sha256_file(file_path)})
    if total_rows != EXPECTED_OFCOM_POSTCODE_ROWS:
        raise ValueError(f"Expected {EXPECTED_OFCOM_POSTCODE_ROWS} rows, found {total_rows}")
    return coverage, manifest


def build_rows(
    canonical_rows: list[dict[str, Any]],
    legacy_rows: dict[int, dict[str, Any]],
    coverage: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for canonical in canonical_rows:
        number = row_number(canonical)
        assert number is not None
        legacy = legacy_rows.get(number)
        postcode = parse_legacy_postcode(legacy or {})
        official = coverage.get(postcode or "")
        identity_ok, identity_reason = identity_match(canonical, legacy) if legacy else (False, "NO_LEGACY_ROW")

        if legacy and postcode and identity_ok and official:
            status = "CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW"
            confidence = 0.90
            source_level = "POSTCODE_PROXY"
        elif legacy and not identity_ok:
            status = "IDENTITY_CONFLICT_NO_DATA"
            confidence = 0.0
            source_level = "NO_DATA"
        elif legacy and postcode and not official:
            status = "POSTCODE_NOT_FOUND_IN_CURRENT_R2_NO_DATA"
            confidence = 0.0
            source_level = "NO_DATA"
        else:
            status = "NO_VERIFIED_POSTCODE_NO_DATA"
            confidence = 0.0
            source_level = "NO_DATA"

        row: dict[str, Any] = {
            "slot_id": SLOT_ID,
            "canonical_row_no": number,
            "canonical_program_parcel_id": parcel_id(canonical),
            "hmlr_row_id": canonical.get("hmlr_row_id"),
            "hmlr_inspire_id": canonical.get("hmlr_inspire_id"),
            "parcel_centroid_lon": parse_number(canonical.get("hmlr_lon")),
            "parcel_centroid_lat": parse_number(canonical.get("hmlr_lat")),
            "postcode": postcode,
            "identity_check": identity_reason,
            "source_level": source_level,
            "internet_match_confidence": confidence,
            "internet_availability_quality_percent": None,
            "internet_quality_band": None,
            "calculation_version": None,
            "calculation_explanation": "Current Ofcom postcode fields retained individually; no parcel score emitted.",
            "status": status,
            "business_row_written": False,
        }
        if official and identity_ok:
            row.update(official)
        output.append(row)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument("--legacy-internet-geojson", required=True, type=Path)
    parser.add_argument("--ofcom-postcode-dir", required=True, type=Path)
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

    matched = sum(row["status"] == "CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW" for row in rows)
    conflicts = sum(row["status"] == "IDENTITY_CONFLICT_NO_DATA" for row in rows)
    no_data = len(rows) - matched
    manifest = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "parcel_start": ROW_START,
        "parcel_end": ROW_END,
        "canonical_rows": len(rows),
        "current_r2_postcode_proxy_rows": matched,
        "identity_conflict_rows": conflicts,
        "no_data_rows": no_data,
        "ofcom_postcodes_loaded": len(coverage),
        "ofcom_files_loaded": len(source_files),
        "canonical_source_sha256": sha256_file(args.canonical),
        "legacy_internet_source_sha256": sha256_file(args.legacy_internet_geojson),
        "ofcom_source_files": source_files,
        "scores_written": 0,
        "actual_business_data_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "samples": rows[:5],
    }
    manifest_path = args.output_dir / "internet_access_3_candidate_manifest_latest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k not in {"ofcom_source_files", "samples"}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
