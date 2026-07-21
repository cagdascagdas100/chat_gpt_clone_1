#!/usr/bin/env python3
"""Fail-closed safety and payload audit for the downloaded Ofcom ZIP container."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

SLOT_ID = "internet_access_2"
EXPECTED_R2_COUNT = 121
R2_NAME = re.compile(r"^202601_fixed_postcode_coverage_r2_([A-Z0-9]{1,3})\.csv$")
R1_NAME = re.compile(r"^202601_fixed_postcode_coverage_r1_[A-Z0-9]{1,3}\.csv$")
ALLOWED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
MAX_TOTAL_UNCOMPRESSED_BYTES = 8_000_000_000
MAX_SINGLE_ENTRY_BYTES = 2_000_000_000


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_name(name: str) -> str:
    return name.replace("\\", "/")


def validate_entries(infos: Iterable[Any]) -> dict[str, Any]:
    entries = list(infos)
    if not entries:
        raise ValueError("ZIP container is empty")
    normalized_seen: set[str] = set()
    r2_areas: list[str] = []
    r1_count = 0
    file_count = 0
    total_compressed = 0
    total_uncompressed = 0

    for info in entries:
        raw_name = str(info.filename)
        if not raw_name or "\x00" in raw_name or any(ord(ch) < 32 for ch in raw_name):
            raise ValueError("ZIP entry contains an empty, NUL or control-character path")
        name = normalize_name(raw_name)
        path = PurePosixPath(name)
        parts = path.parts
        if name.startswith("/") or name.startswith("\\") or re.match(r"^[A-Za-z]:", name):
            raise ValueError(f"ZIP entry uses an absolute or drive path: {raw_name}")
        if any(part in ("", ".", "..") for part in parts):
            raise ValueError(f"ZIP entry contains unsafe path segments: {raw_name}")
        key = name.rstrip("/").casefold()
        if key in normalized_seen:
            raise ValueError(f"ZIP entry path is duplicated after normalization: {raw_name}")
        normalized_seen.add(key)

        if int(getattr(info, "flag_bits", 0)) & 0x1:
            raise ValueError(f"Encrypted ZIP entry is not accepted: {raw_name}")
        unix_mode = (int(getattr(info, "external_attr", 0)) >> 16) & 0xFFFF
        if stat.S_ISLNK(unix_mode):
            raise ValueError(f"Symlink ZIP entry is not accepted: {raw_name}")

        is_dir = bool(getattr(info, "is_dir", lambda: raw_name.endswith("/"))())
        if is_dir:
            continue
        file_count += 1
        compress_type = int(getattr(info, "compress_type", -1))
        if compress_type not in ALLOWED_COMPRESSION:
            raise ValueError(f"Unsupported ZIP compression method: {raw_name}")
        file_size = int(getattr(info, "file_size", -1))
        compress_size = int(getattr(info, "compress_size", -1))
        if file_size <= 0:
            raise ValueError(f"ZIP file entry is empty or has invalid size: {raw_name}")
        if compress_size < 0:
            raise ValueError(f"ZIP compressed size is invalid: {raw_name}")
        if file_size > MAX_SINGLE_ENTRY_BYTES:
            raise ValueError(f"ZIP entry exceeds safety size limit: {raw_name}")
        total_uncompressed += file_size
        total_compressed += compress_size
        if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
            raise ValueError("ZIP total uncompressed size exceeds safety limit")

        base = path.name
        if R1_NAME.fullmatch(base):
            r1_count += 1
        match = R2_NAME.fullmatch(base)
        if match:
            if path.parent.name != "postcode_files":
                raise ValueError(f"Corrected r2 postcode file is outside postcode_files: {raw_name}")
            r2_areas.append(match.group(1))

    if r1_count != 0:
        raise ValueError(f"Superseded internal r1 postcode files found: {r1_count}")
    if len(r2_areas) != EXPECTED_R2_COUNT:
        raise ValueError(f"Expected {EXPECTED_R2_COUNT} corrected r2 postcode files, found {len(r2_areas)}")
    if len(set(r2_areas)) != EXPECTED_R2_COUNT:
        raise ValueError("Corrected r2 postcode area identifiers are not unique")

    return {
        "entry_count": len(entries),
        "file_entry_count": file_count,
        "total_compressed_bytes": total_compressed,
        "total_uncompressed_bytes": total_uncompressed,
        "r1_postcode_file_count": r1_count,
        "r2_postcode_file_count": len(r2_areas),
        "r2_postcode_area_count": len(set(r2_areas)),
        "path_traversal_rejected": True,
        "duplicate_normalized_paths_rejected": True,
        "encrypted_entries_rejected": True,
        "symlink_entries_rejected": True,
        "unsupported_compression_rejected": True,
    }


def audit(zip_path: Path, output: Path | None = None) -> dict[str, Any]:
    if not zip_path.is_file():
        raise ValueError(f"ZIP file is missing: {zip_path}")
    if zip_path.stat().st_size <= 0:
        raise ValueError("ZIP file is empty")
    try:
        with zipfile.ZipFile(zip_path) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP CRC validation failed")
            stats = validate_entries(archive.infolist())
    except zipfile.BadZipFile as exc:
        raise ValueError("Downloaded file is not a valid ZIP container") from exc

    result = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "status": "PASS_SAFE_OFFICIAL_ZIP_CONTAINER_REVIEW_ONLY",
        "zip_sha256": sha256_file(zip_path),
        "zip_bytes": zip_path.stat().st_size,
        **stats,
        "crc_validation_passed": True,
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.zip, args.output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
