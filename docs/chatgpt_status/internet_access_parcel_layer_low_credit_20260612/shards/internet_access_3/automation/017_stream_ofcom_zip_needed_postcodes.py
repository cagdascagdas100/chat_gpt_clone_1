#!/usr/bin/env python3
"""Stream corrected Ofcom postcode CSVs directly from the official ZIP.

Every corrected r2 postcode row is scanned and globally checked. Detailed coverage
values are retained only for postcodes needed by identity-matched internet_access_3
rows. CSV members are never extracted to disk. No postcode is inferred, no parcel
score is emitted, and no business data is written.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

SLOT_ID = "internet_access_3"
EXPECTED_ROWS = 30_761
EXPECTED_OFCOM_FILE_COUNT = 121
EXPECTED_OFCOM_POSTCODE_ROWS = 1_741_096
R2_PATTERN = re.compile(r"202601_fixed_postcode_coverage_r2_([A-Za-z]+)\.csv$")
R1_PATTERN = re.compile(r"202601_fixed_postcode_coverage_r1_[A-Za-z]+\.csv$")
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


class GateError(RuntimeError):
    """Raised when an official ZIP, schema, identity, or truth gate fails."""


class HashingRawReader(io.RawIOBase):
    """Expose a binary stream to TextIOWrapper while hashing bytes in one pass."""

    def __init__(self, source: BinaryIO, digest: Any) -> None:
        super().__init__()
        self._source = source
        self._digest = digest

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: bytearray | memoryview) -> int:
        data = self._source.read(len(buffer))
        if not data:
            return 0
        self._digest.update(data)
        buffer[: len(data)] = data
        return len(data)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise GateError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def member_basename(name: str) -> str:
    return PurePosixPath(name).name


def member_postcode_area(name: str) -> str:
    basename = member_basename(name)
    match = R2_PATTERN.fullmatch(basename)
    if not match:
        raise GateError(f"Unexpected corrected postcode member: {name}")
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


def list_corrected_members(
    archive: zipfile.ZipFile,
    *,
    expected_file_count: int = EXPECTED_OFCOM_FILE_COUNT,
) -> list[zipfile.ZipInfo]:
    files = [info for info in archive.infolist() if not info.is_dir()]
    r1 = [info for info in files if R1_PATTERN.fullmatch(member_basename(info.filename))]
    if r1:
        raise GateError(f"Superseded all-premises r1 postcode members present: {len(r1)}")
    r2 = [info for info in files if R2_PATTERN.fullmatch(member_basename(info.filename))]
    if len(r2) != expected_file_count:
        raise GateError(f"Expected {expected_file_count} corrected r2 members, found {len(r2)}")
    basenames = [member_basename(info.filename) for info in r2]
    if len(set(basenames)) != len(basenames):
        raise GateError("Duplicate corrected r2 member basenames found")
    normalised_areas = [member_postcode_area(info.filename) for info in r2]
    if len(set(normalised_areas)) != len(normalised_areas):
        raise GateError("Duplicate corrected r2 postcode areas found")
    return sorted(r2, key=lambda info: (member_postcode_area(info.filename), member_basename(info.filename)))


def scan_ofcom_zip(
    zip_path: Path,
    needed_postcodes: set[str],
    base: Any,
    *,
    expected_file_count: int = EXPECTED_OFCOM_FILE_COUNT,
    expected_total_rows: int = EXPECTED_OFCOM_POSTCODE_ROWS,
    minimum_zip_bytes: int = 1,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if not zip_path.is_file():
        raise GateError(f"Official ZIP does not exist: {zip_path}")
    zip_bytes = zip_path.stat().st_size
    if zip_bytes < minimum_zip_bytes:
        raise GateError(f"Official ZIP is unexpectedly small: {zip_bytes} bytes")
    with zip_path.open("rb") as handle:
        if handle.read(2) != b"PK":
            raise GateError("Official file does not have a ZIP signature")

    selected: dict[str, dict[str, Any]] = {}
    source_files: list[dict[str, Any]] = []
    total_rows = 0
    unique_postcodes = 0
    peak_member_unique_postcodes = 0

    try:
        with zipfile.ZipFile(zip_path) as archive:
            members = list_corrected_members(archive, expected_file_count=expected_file_count)
            for info in members:
                basename = member_basename(info.filename)
                expected_area = member_postcode_area(info.filename)
                file_rows = 0
                retained_rows = 0
                seen_in_member: set[str] = set()
                digest = hashlib.sha256()

                with archive.open(info, "r") as source:
                    hashing_raw = HashingRawReader(source, digest)
                    with io.BufferedReader(hashing_raw, buffer_size=1024 * 1024) as buffered:
                        with io.TextIOWrapper(buffered, encoding="utf-8-sig", newline="") as text:
                            reader = csv.DictReader(text)
                            headers = reader.fieldnames or []
                            missing = [
                                field
                                for field in STRICT_REQUIRED_FIELDS
                                if not base.has_alias(headers, base.FIELD_ALIASES[field])
                            ]
                            if missing:
                                raise GateError(f"{basename} missing strict fields: {missing}")

                            for row in reader:
                                file_rows += 1
                                total_rows += 1
                                logical_row = file_rows + 1
                                postcode = base.normalise_postcode(
                                    required_value(row, base, "postcode", basename, logical_row)
                                )
                                postcode_space = base.normalise_postcode(
                                    required_value(row, base, "postcode_space", basename, logical_row)
                                )
                                if not postcode:
                                    raise GateError(f"Blank postcode in {basename} row {logical_row}")
                                if postcode != postcode_space:
                                    raise GateError(
                                        f"postcode/postcode_space mismatch in {basename} row {logical_row}: "
                                        f"{postcode!r} != {postcode_space!r}"
                                    )
                                area_value = str(
                                    required_value(row, base, "postcode_area", basename, logical_row)
                                ).strip().upper()
                                derived_area = postcode_area_from_postcode(postcode)
                                if area_value != expected_area or derived_area != expected_area:
                                    raise GateError(
                                        f"Postcode area mismatch in {basename} row {logical_row}: "
                                        f"field={area_value}, derived={derived_area}, file={expected_area}"
                                    )
                                if postcode in seen_in_member:
                                    raise GateError(f"Duplicate Ofcom postcode within {expected_area}: {postcode}")
                                seen_in_member.add(postcode)

                                percentages: dict[str, float] = {}
                                for field in (
                                    "sfbb",
                                    "ufbb100",
                                    "ufbb300",
                                    "gigabit",
                                    "unable30",
                                    "unable_decent",
                                ):
                                    raw = required_value(row, base, field, basename, logical_row)
                                    value = base.parse_percentage(raw)
                                    if value is None:
                                        raise GateError(
                                            f"Non-numeric required percentage {field} in {basename} row {logical_row}"
                                        )
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
                                        "source_file": basename,
                                        "source_zip_member": info.filename,
                                        "source_snapshot_date": "2026-01",
                                        "source_revision": "r2",
                                    }
                                    retained_rows += 1

                unique_postcodes += len(seen_in_member)
                peak_member_unique_postcodes = max(peak_member_unique_postcodes, len(seen_in_member))
                source_files.append(
                    {
                        "file": basename,
                        "zip_member": info.filename,
                        "postcode_area": expected_area,
                        "rows": file_rows,
                        "unique_postcodes": len(seen_in_member),
                        "retained_needed_rows": retained_rows,
                        "uncompressed_bytes": info.file_size,
                        "compressed_bytes": info.compress_size,
                        "crc32": f"{info.CRC:08x}",
                        "sha256": digest.hexdigest(),
                    }
                )
    except zipfile.BadZipFile as exc:
        raise GateError(f"Invalid or CRC-failing ZIP: {exc}") from exc

    if total_rows != expected_total_rows:
        raise GateError(f"Expected {expected_total_rows} Ofcom postcode rows, found {total_rows}")
    if unique_postcodes != total_rows:
        raise GateError("Area-partitioned exact postcode uniqueness count does not equal scanned rows")

    stats: dict[str, Any] = {
        "ofcom_postcodes_scanned": total_rows,
        "ofcom_unique_postcodes": unique_postcodes,
        "postcode_uniqueness_strategy": "AREA_PARTITIONED_EXACT_PER_MEMBER_SET",
        "postcode_area_member_count": len(source_files),
        "peak_member_unique_postcodes": peak_member_unique_postcodes,
        "needed_postcodes": len(needed_postcodes),
        "retained_postcodes": len(selected),
        "needed_postcodes_not_found": len(needed_postcodes - set(selected)),
        "ofcom_zip_bytes": zip_bytes,
        "ofcom_zip_sha256": sha256_file(zip_path),
        "ofcom_csv_extracted_to_disk": False,
        "zip_member_stream_sha256_count": len(source_files),
        "zip_member_crc_verified_by_complete_stream_read": True,
    }
    return selected, source_files, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", required=True, type=Path)
    parser.add_argument("--legacy-internet-geojson", required=True, type=Path)
    parser.add_argument("--ofcom-zip", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--base-extractor",
        type=Path,
        default=Path(__file__).with_name("002_extract_slot3_ofcom_2026_candidates.py"),
    )
    parser.add_argument(
        "--targeted-extractor",
        type=Path,
        default=Path(__file__).with_name("012_extract_slot3_ofcom_needed_postcodes.py"),
    )
    args = parser.parse_args()

    base = load_module(args.base_extractor, "internet_access_3_base_extractor")
    targeted = load_module(args.targeted_extractor, "internet_access_3_targeted_extractor")
    canonical_rows = base.load_canonical(args.canonical)
    legacy_rows = base.load_legacy_internet(args.legacy_internet_geojson)
    needed_postcodes = targeted.prepare_slot_rows(canonical_rows, legacy_rows, base)
    selected_coverage, source_files, scan_stats = scan_ofcom_zip(
        args.ofcom_zip, needed_postcodes, base
    )
    rows, manifest = targeted.build_manifest(
        args.canonical,
        args.legacy_internet_geojson,
        canonical_rows,
        legacy_rows,
        selected_coverage,
        source_files,
        scan_stats,
        base,
    )
    manifest.update(
        {
            "schema_version": 5,
            "ofcom_source_mode": "DIRECT_ZIP_STREAM_NO_CSV_EXTRACTION",
            "ofcom_zip_bytes": scan_stats["ofcom_zip_bytes"],
            "ofcom_zip_sha256": scan_stats["ofcom_zip_sha256"],
            "ofcom_csv_extracted_to_disk": False,
            "zip_member_stream_sha256_count": scan_stats["zip_member_stream_sha256_count"],
            "zip_member_crc_verified_by_complete_stream_read": True,
            "postcode_uniqueness_strategy": scan_stats["postcode_uniqueness_strategy"],
            "postcode_area_member_count": scan_stats["postcode_area_member_count"],
            "peak_member_unique_postcodes": scan_stats["peak_member_unique_postcodes"],
        }
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
