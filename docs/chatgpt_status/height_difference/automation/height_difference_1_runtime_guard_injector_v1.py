#!/usr/bin/env python3
"""Inject fail-closed EA TIFF/NoData runtime patches into the slot carrier."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

SLOT_ID = "height_difference_1"
SCRIPT_VERSION = "1.0-runtime-raster-guard-injector"
EXPECTED_MARKER = """  $patched = Replace-ExactlyOnce -Text $patched -Old $oldMetadataStart -New $newMetadataStart -Label 'BUSINESS_ROW_PROVENANCE_GATE'

  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1'
"""
EXPECTED_OLD_TASK_VERSION = "Write-Output 'TASK_VERSION=1.7-dtm-required-dsm-optional-provenance-strict'"
NEW_TASK_VERSION = "Write-Output 'TASK_VERSION=1.11-runtime-raster-guard-integrated'"

INJECTED_BLOCK = r"""  $patched = Replace-ExactlyOnce -Text $patched -Old $oldMetadataStart -New $newMetadataStart -Label 'BUSINESS_ROW_PROVENANCE_GATE'

  $oldTiffValidator = @'
def validate_tiff_bytes(data: bytes, content_type: str | None) -> None:
    if len(data) < 8 or data[:2] not in (b"II", b"MM"):
        raise EvidenceError("WCS_RESPONSE_NOT_TIFF_MAGIC")
    if content_type and "tiff" not in content_type.lower() and "octet-stream" not in content_type.lower():
        raise EvidenceError(f"UNEXPECTED_WCS_CONTENT_TYPE:{content_type}")
'@
  $newTiffValidator = @'
def validate_tiff_bytes(data: bytes, content_type: str | None) -> None:
    if len(data) < 8:
        raise EvidenceError("WCS_RESPONSE_NOT_TIFF_MAGIC")
    if data[:4] not in (b"II*\x00", b"MM\x00*"):
        raise EvidenceError(f"WCS_RESPONSE_NOT_CLASSIC_TIFF_HEADER:{data[:4].hex()}")
    if content_type and "tiff" not in content_type.lower() and "octet-stream" not in content_type.lower():
        raise EvidenceError(f"UNEXPECTED_WCS_CONTENT_TYPE:{content_type}")
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldTiffValidator -New $newTiffValidator -Label 'CLASSIC_TIFF_HEADER_VALIDATOR'

  $oldRasterValues = @'
        band = clipped[0]
        values = band.compressed() if hasattr(band, "compressed") else band[np.isfinite(band)]
        values = values[np.isfinite(values)]
        if src.nodata is not None:
            values = values[values != src.nodata]
        if values.size < 1:
            raise EvidenceError("NO_FINITE_RASTER_PIXELS_INSIDE_POLYGON")
'@
  $newRasterValues = @'
        band = clipped[0]
        values = band.compressed() if hasattr(band, "compressed") else band[np.isfinite(band)]
        values = values[np.isfinite(values)]
        if src.nodata is not None:
            values = values[values != src.nodata]
        values = values[~np.isclose(values, -3.4028235e38, rtol=1e-6, atol=0.0)]
        if values.size < 1:
            raise EvidenceError("NO_FINITE_NON_NODATA_RASTER_PIXELS_INSIDE_POLYGON")
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldRasterValues -New $newRasterValues -Label 'EA_OFFICIAL_NODATA_RUNTIME_FILTER'

  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1'
"""


class InjectionError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def patch_carrier_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    marker_count = normalized.count(EXPECTED_MARKER)
    if marker_count != 1:
        raise InjectionError(f"RUNTIME_GUARD_MARKER_COUNT_INVALID:{marker_count}")
    task_version_count = normalized.count(EXPECTED_OLD_TASK_VERSION)
    if task_version_count != 1:
        raise InjectionError(f"CARRIER_TASK_VERSION_COUNT_INVALID:{task_version_count}")
    patched = normalized.replace(EXPECTED_MARKER, INJECTED_BLOCK, 1)
    patched = patched.replace(EXPECTED_OLD_TASK_VERSION, NEW_TASK_VERSION, 1)
    required_tokens = (
        "CLASSIC_TIFF_HEADER_VALIDATOR",
        "EA_OFFICIAL_NODATA_RUNTIME_FILTER",
        'data[:4] not in (b"II*\\x00", b"MM\\x00*")',
        "np.isclose(values, -3.4028235e38",
        "NO_FINITE_NON_NODATA_RASTER_PIXELS_INSIDE_POLYGON",
        NEW_TASK_VERSION,
    )
    missing = [token for token in required_tokens if token not in patched]
    if missing:
        raise InjectionError(f"RUNTIME_GUARD_TOKEN_MISSING:{missing}")
    return patched


def run_self_test() -> dict[str, Any]:
    fixture = "header\n" + EXPECTED_MARKER + "\n" + EXPECTED_OLD_TASK_VERSION + "\nfooter\n"
    patched = patch_carrier_text(fixture)
    checks = {
        "marker_replaced_once": patched.count("CLASSIC_TIFF_HEADER_VALIDATOR") == 1,
        "nodata_patch_once": patched.count("EA_OFFICIAL_NODATA_RUNTIME_FILTER") == 1,
        "little_endian_header_present": 'b"II*\\x00"' in patched,
        "big_endian_header_present": 'b"MM\\x00*"' in patched,
        "official_sentinel_present": "-3.4028235e38" in patched,
        "empty_after_filter_error_present": "NO_FINITE_NON_NODATA_RASTER_PIXELS_INSIDE_POLYGON" in patched,
        "task_version_upgraded": NEW_TASK_VERSION in patched,
        "source_marker_removed": EXPECTED_MARKER not in patched,
    }
    if not all(checks.values()):
        raise InjectionError(f"SELF_TEST_FAILED:{checks}")
    duplicate_rejected = False
    try:
        patch_carrier_text(fixture.replace(EXPECTED_MARKER, EXPECTED_MARKER + EXPECTED_MARKER))
    except InjectionError:
        duplicate_rejected = True
    if not duplicate_rejected:
        raise InjectionError("SELF_TEST_DUPLICATE_MARKER_NOT_REJECTED")
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
        "state": "PASS",
        "checks": 9,
        "details": checks | {"duplicate_marker_rejected": duplicate_rejected},
        "official_nodata_sentinel": -3.4028235e38,
        "runtime_patch_labels": [
            "CLASSIC_TIFF_HEADER_VALIDATOR",
            "EA_OFFICIAL_NODATA_RUNTIME_FILTER",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--carrier", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(run_self_test(), sort_keys=True))
        return 0
    if args.carrier is None or args.output is None or args.receipt is None:
        raise InjectionError("CARRIER_OUTPUT_AND_RECEIPT_REQUIRED")

    source = args.carrier.read_bytes()
    patched_text = patch_carrier_text(source.decode("utf-8-sig"))
    patched_bytes = patched_text.encode("utf-8")
    atomic_write(args.output, patched_bytes)
    receipt = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
        "state": "COMPLETED_RUNTIME_GUARDS_INJECTED",
        "source_path": str(args.carrier.resolve()),
        "output_path": str(args.output.resolve()),
        "source_sha256": sha256_bytes(source),
        "output_sha256": sha256_bytes(patched_bytes),
        "source_bytes": len(source),
        "output_bytes": len(patched_bytes),
        "runtime_patch_count": 2,
        "runtime_patch_labels": [
            "CLASSIC_TIFF_HEADER_VALIDATOR",
            "EA_OFFICIAL_NODATA_RUNTIME_FILTER",
        ],
        "official_nodata_sentinel": -3.4028235e38,
        "classic_tiff_headers_hex": ["49492a00", "4d4d002a"],
        "fake_data": False,
        "final_ready": False,
    }
    atomic_write(args.receipt, (json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
