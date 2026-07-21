#!/usr/bin/env python3
"""Fail-closed Ofcom Spring 2026 postcode r2 refresh for internet_access_1.

Default mode is preview-only. It never writes database rows, migrations, or production
artifacts. The script reads the existing canonical London internet matrix, extracts
slot rows 1..30761, and joins them to the corrected Ofcom postcode r2 CSV files
inside the official Spring 2026 ZIP package.

Expected official package:
https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-spring-2026/202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip

The ZIP package name remains r1, while the corrected all-premises postcode files
inside it are named 202601_fixed_postcode_coverage_r2_XX.csv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "internet_access_1"
PARCEL_START = 1
PARCEL_END = 30761
OFFICIAL_ZIP_URL = (
    "https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/"
    "multi-sector/infrastructure-research/connected-nations-spring-2026/"
    "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip?v=422620"
)
EXPECTED_MEMBER_RE = re.compile(
    r"(?:^|/)postcode_files/202601_fixed_postcode_coverage_r2_([A-Z0-9]+)\.csv$",
    re.IGNORECASE,
)
LEGACY_VALUE_RE = re.compile(
    r"^(?P<band>[^;]+);\s*postcode=(?P<postcode>[A-Z0-9 ]+);"
    r"\s*gigabit=(?P<gigabit>[0-9.]+)%;"
    r"\s*ufbb100=(?P<ufbb100>[0-9.]+)%;"
    r"\s*sfbb=(?P<sfbb>[0-9.]+)%;"
    r"\s*unable30=(?P<unable30>[0-9.]+)%$"
)

HEADER_ALIASES = {
    "postcode": ("postcode",),
    "gigabit": ("gigabit availability (% premises)",),
    "ufbb100": ("ufbb (100mbit/s) availability (% premises)",),
    "sfbb": ("sfbb availability (% premises)",),
    "unable30": ("% of premises unable to receive 30mbit/s",),
}


def normalise_header(value: str) -> str:
    return " ".join(value.strip().lower().replace("\ufeff", "").split())


def postcode_area(postcode: str) -> str:
    match = re.match(r"^[A-Z]+", postcode.replace(" ", "").upper())
    if not match:
        raise ValueError(f"Invalid postcode: {postcode!r}")
    return match.group(0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def obtain_zip(local_path: Path | None, download_path: Path | None) -> Path:
    if local_path is not None:
        if not local_path.is_file():
            raise FileNotFoundError(f"Ofcom ZIP not found: {local_path}")
        return local_path

    if download_path is None:
        raise ValueError("Provide --ofcom-zip or --download-to")

    download_path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        OFFICIAL_ZIP_URL,
        headers={"User-Agent": "TerraYield-AAYS-internet_access_1/1.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.status != 200:
            raise RuntimeError(f"Ofcom download HTTP status {response.status}")
        with download_path.open("wb") as target:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                target.write(block)
    return download_path


def parse_legacy_feature(feature: dict[str, Any]) -> dict[str, Any] | None:
    properties = feature.get("properties") or {}
    try:
        row_no = int(properties.get("row_no"))
    except (TypeError, ValueError):
        return None
    if not (PARCEL_START <= row_no <= PARCEL_END):
        return None

    raw = properties.get("internet_level_value")
    if not isinstance(raw, str):
        return None
    match = LEGACY_VALUE_RE.match(raw.strip())
    if not match:
        return None

    values = match.groupdict()
    return {
        "row_no": row_no,
        "parcel_id": properties.get("parcel_id"),
        "hmlr_inspire_id": properties.get("hmlr_inspire_id"),
        "postcode": values["postcode"].replace(" ", "").upper(),
        "legacy_quality_band": values["band"].strip(),
        "legacy_gigabit_pct": float(values["gigabit"]),
        "legacy_ufbb100_pct": float(values["ufbb100"]),
        "legacy_sfbb_pct": float(values["sfbb"]),
        "legacy_unable30_pct": float(values["unable30"]),
        "legacy_accuracy": properties.get("internet_level_accuracy"),
        "london_authority": properties.get("london_authority"),
    }


def load_slot_rows(matrix_path: Path) -> list[dict[str, Any]]:
    with matrix_path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Canonical matrix has no features array")
    rows = [row for feature in features if (row := parse_legacy_feature(feature))]
    rows.sort(key=lambda item: item["row_no"])
    return rows


def choose_headers(fieldnames: Iterable[str]) -> dict[str, str]:
    normalised = {normalise_header(name): name for name in fieldnames}
    selected: dict[str, str] = {}
    for logical_name, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            if alias in normalised:
                selected[logical_name] = normalised[alias]
                break
        if logical_name not in selected:
            raise ValueError(
                f"Required Ofcom column not found for {logical_name}; "
                f"available={sorted(normalised)}"
            )
    return selected


def load_ofcom_rows(zip_path: Path, required_postcodes: set[str]) -> dict[str, dict[str, float]]:
    required_areas = {postcode_area(code) for code in required_postcodes}
    output: dict[str, dict[str, float]] = {}

    with zipfile.ZipFile(zip_path) as archive:
        members_by_area: dict[str, str] = {}
        for member in archive.namelist():
            match = EXPECTED_MEMBER_RE.search(member)
            if match:
                members_by_area[match.group(1).upper()] = member

        missing_areas = sorted(required_areas - set(members_by_area))
        if missing_areas:
            raise ValueError(f"Corrected r2 postcode files missing for areas: {missing_areas}")

        for area in sorted(required_areas):
            member = members_by_area[area]
            with archive.open(member) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                reader = csv.DictReader(text)
                if not reader.fieldnames:
                    raise ValueError(f"Empty CSV header: {member}")
                headers = choose_headers(reader.fieldnames)
                for record in reader:
                    code = (record.get(headers["postcode"]) or "").replace(" ", "").upper()
                    if code not in required_postcodes:
                        continue
                    output[code] = {
                        "gigabit_available_pct": float(record[headers["gigabit"]]),
                        "ultrafast_or_100mbps_available_pct": float(record[headers["ufbb100"]]),
                        "superfast_30mbps_available_pct": float(record[headers["sfbb"]]),
                        "unable_30mbps_pct": float(record[headers["unable30"]]),
                    }
    return output


def build_preview(
    rows: list[dict[str, Any]],
    ofcom_rows: dict[str, dict[str, float]],
    zip_path: Path,
) -> dict[str, Any]:
    refreshed = []
    no_data = []
    for row in rows:
        official = ofcom_rows.get(row["postcode"])
        if official is None:
            no_data.append(
                {
                    "row_no": row["row_no"],
                    "parcel_id": row["parcel_id"],
                    "postcode": row["postcode"],
                    "status": "NO_DATA_NOT_INFERRED",
                }
            )
            continue
        refreshed.append(
            {
                "row_no": row["row_no"],
                "parcel_id": row["parcel_id"],
                "hmlr_inspire_id": row["hmlr_inspire_id"],
                "postcode": row["postcode"],
                "source_level": "POSTCODE_PROXY",
                **official,
                "internet_match_method": "CANONICAL_EXISTING_POSTCODE_TO_OFCom_R2",
                "internet_match_confidence": 0.75,
                "migration_state": "VERIFIED_PREVIEW_NOT_APPLIED",
            }
        )

    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "parcel_partition": {"start": PARCEL_START, "end": PARCEL_END},
        "official_zip_url": OFFICIAL_ZIP_URL,
        "official_zip_path": str(zip_path),
        "official_zip_sha256": sha256_file(zip_path),
        "legacy_rows_in_slot": len(rows),
        "unique_postcodes": len({row["postcode"] for row in rows}),
        "refreshed_preview_rows": len(refreshed),
        "no_data_rows": len(no_data),
        "postcode_area_counts": dict(
            sorted(Counter(postcode_area(row["postcode"]) for row in rows).items())
        ),
        "rows": refreshed,
        "no_data": no_data,
        "actual_business_rows_written": 0,
        "migration_applied": False,
        "fake_data": False,
        "db_write": False,
        "production_deploy": False,
        "final_ready": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--ofcom-zip", type=Path)
    source.add_argument("--download-to", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    zip_path = obtain_zip(args.ofcom_zip, args.download_to)
    rows = load_slot_rows(args.matrix)
    if not rows:
        raise RuntimeError("No canonical internet rows found in internet_access_1 range")
    required_postcodes = {row["postcode"] for row in rows}
    official_rows = load_ofcom_rows(zip_path, required_postcodes)
    preview = build_preview(rows, official_rows, zip_path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "slot_id": SLOT_ID,
                "legacy_rows": len(rows),
                "unique_postcodes": len(required_postcodes),
                "refreshed_preview_rows": preview["refreshed_preview_rows"],
                "no_data_rows": preview["no_data_rows"],
                "output": str(args.output),
                "migration_applied": False,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps(
                {
                    "slot_id": SLOT_ID,
                    "status": "BLOCKED_FAIL_CLOSED",
                    "error": f"{type(exc).__name__}: {exc}",
                    "migration_applied": False,
                    "fake_data": False,
                    "final_ready": False,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise
