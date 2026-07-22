#!/usr/bin/env python3
"""Inject fail-closed EA raster and HMLR identifier runtime guards into the slot carrier."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

SLOT_ID = "height_difference_1"
SCRIPT_VERSION = "1.1-runtime-raster-and-hmlr-id-guard-injector"
EXPECTED_MAIN_MARKER = """  $patched = Replace-ExactlyOnce -Text $patched -Old $oldMetadataStart -New $newMetadataStart -Label 'BUSINESS_ROW_PROVENANCE_GATE'

  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1'
"""
EXPECTED_HMLR_RECEIPT_MARKER = """  if ($hmlrDocument.slot_id -ne 'height_difference_1' -or $hmlrDocument.state -ne 'COMPLETED_ZIP_AND_GML_VERIFIED') {
    throw 'HMLR_ZIP_RECEIPT_INVALID'
  }
  $allowedZipHosts = @('use-land-property-data.service.gov.uk','datapub-prd-s3-bucket.s3.amazonaws.com')
"""
EXPECTED_OLD_TASK_VERSION = "Write-Output 'TASK_VERSION=1.7-dtm-required-dsm-optional-provenance-strict'"
NEW_TASK_VERSION = "Write-Output 'TASK_VERSION=1.12-runtime-raster-and-hmlr-id-guard-integrated'"

INJECTED_MAIN_BLOCK = r"""  $patched = Replace-ExactlyOnce -Text $patched -Old $oldMetadataStart -New $newMetadataStart -Label 'BUSINESS_ROW_PROVENANCE_GATE'

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

INJECTED_HMLR_RECEIPT_BLOCK = """  if ($hmlrDocument.slot_id -ne 'height_difference_1' -or $hmlrDocument.state -ne 'COMPLETED_ZIP_AND_GML_VERIFIED') {
    throw 'HMLR_ZIP_RECEIPT_INVALID'
  }
  $identifierColumn = [string]$hmlrDocument.artifacts.hmlr_gml.structure.identifier_column
  $identifierColumnCompact = (($identifierColumn.ToLowerInvariant()) -replace '[_:\-]', '')
  if ([string]::IsNullOrWhiteSpace($identifierColumn) -or $identifierColumnCompact -notmatch 'inspire' -or $identifierColumnCompact -notmatch 'id') {
    throw "HMLR_INSPIRE_IDENTIFIER_COLUMN_REQUIRED: $identifierColumn"
  }
  $featureCount = [int64]$hmlrDocument.artifacts.hmlr_gml.structure.feature_count
  $uniqueIdentifierCount = [int64]$hmlrDocument.artifacts.hmlr_gml.structure.unique_identifier_count
  if ($featureCount -lt 1 -or $uniqueIdentifierCount -ne $featureCount) {
    throw "HMLR_INSPIRE_IDENTIFIER_COUNT_MISMATCH: feature=$featureCount unique=$uniqueIdentifierCount"
  }
  $identifierSetHash = ([string]$hmlrDocument.artifacts.hmlr_gml.structure.identifier_set_sha256).ToLowerInvariant()
  if ($identifierSetHash -notmatch '^[0-9a-f]{64}$') { throw 'HMLR_INSPIRE_IDENTIFIER_SET_HASH_INVALID' }
  $allowedZipHosts = @('use-land-property-data.service.gov.uk','datapub-prd-s3-bucket.s3.amazonaws.com')
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
    main_marker_count = normalized.count(EXPECTED_MAIN_MARKER)
    if main_marker_count != 1:
        raise InjectionError(f"RUNTIME_GUARD_MAIN_MARKER_COUNT_INVALID:{main_marker_count}")
    receipt_marker_count = normalized.count(EXPECTED_HMLR_RECEIPT_MARKER)
    if receipt_marker_count != 1:
        raise InjectionError(f"HMLR_IDENTIFIER_RECEIPT_MARKER_COUNT_INVALID:{receipt_marker_count}")
    task_version_count = normalized.count(EXPECTED_OLD_TASK_VERSION)
    if task_version_count != 1:
        raise InjectionError(f"CARRIER_TASK_VERSION_COUNT_INVALID:{task_version_count}")
    patched = normalized.replace(EXPECTED_MAIN_MARKER, INJECTED_MAIN_BLOCK, 1)
    patched = patched.replace(EXPECTED_HMLR_RECEIPT_MARKER, INJECTED_HMLR_RECEIPT_BLOCK, 1)
    patched = patched.replace(EXPECTED_OLD_TASK_VERSION, NEW_TASK_VERSION, 1)
    required_tokens = (
        "CLASSIC_TIFF_HEADER_VALIDATOR",
        "EA_OFFICIAL_NODATA_RUNTIME_FILTER",
        "HMLR_INSPIRE_IDENTIFIER_COLUMN_REQUIRED",
        "HMLR_INSPIRE_IDENTIFIER_COUNT_MISMATCH",
        "HMLR_INSPIRE_IDENTIFIER_SET_HASH_INVALID",
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
    fixture = (
        "header\n"
        + EXPECTED_MAIN_MARKER
        + "\n"
        + EXPECTED_HMLR_RECEIPT_MARKER
        + "\n"
        + EXPECTED_OLD_TASK_VERSION
        + "\nfooter\n"
    )
    patched = patch_carrier_text(fixture)
    checks = {
        "main_marker_replaced_once": patched.count("CLASSIC_TIFF_HEADER_VALIDATOR") == 1,
        "nodata_patch_once": patched.count("EA_OFFICIAL_NODATA_RUNTIME_FILTER") == 1,
        "hmlr_identifier_gate_once": patched.count("HMLR_INSPIRE_IDENTIFIER_COLUMN_REQUIRED") == 1,
        "little_endian_header_present": 'b"II*\\x00"' in patched,
        "big_endian_header_present": 'b"MM\\x00*"' in patched,
        "official_sentinel_present": "-3.4028235e38" in patched,
        "empty_after_filter_error_present": "NO_FINITE_NON_NODATA_RASTER_PIXELS_INSIDE_POLYGON" in patched,
        "identifier_count_gate_present": "HMLR_INSPIRE_IDENTIFIER_COUNT_MISMATCH" in patched,
        "identifier_hash_gate_present": "HMLR_INSPIRE_IDENTIFIER_SET_HASH_INVALID" in patched,
        "task_version_upgraded": NEW_TASK_VERSION in patched,
        "source_markers_removed": EXPECTED_MAIN_MARKER not in patched and EXPECTED_HMLR_RECEIPT_MARKER not in patched,
    }
    if not all(checks.values()):
        raise InjectionError(f"SELF_TEST_FAILED:{checks}")

    duplicate_main_rejected = False
    try:
        patch_carrier_text(fixture.replace(EXPECTED_MAIN_MARKER, EXPECTED_MAIN_MARKER + EXPECTED_MAIN_MARKER))
    except InjectionError:
        duplicate_main_rejected = True
    if not duplicate_main_rejected:
        raise InjectionError("SELF_TEST_DUPLICATE_MAIN_MARKER_NOT_REJECTED")

    duplicate_receipt_rejected = False
    try:
        patch_carrier_text(
            fixture.replace(
                EXPECTED_HMLR_RECEIPT_MARKER,
                EXPECTED_HMLR_RECEIPT_MARKER + EXPECTED_HMLR_RECEIPT_MARKER,
            )
        )
    except InjectionError:
        duplicate_receipt_rejected = True
    if not duplicate_receipt_rejected:
        raise InjectionError("SELF_TEST_DUPLICATE_RECEIPT_MARKER_NOT_REJECTED")

    return {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
        "state": "PASS",
        "checks": 13,
        "details": checks
        | {
            "duplicate_main_marker_rejected": duplicate_main_rejected,
            "duplicate_receipt_marker_rejected": duplicate_receipt_rejected,
        },
        "official_nodata_sentinel": -3.4028235e38,
        "runtime_patch_labels": [
            "CLASSIC_TIFF_HEADER_VALIDATOR",
            "EA_OFFICIAL_NODATA_RUNTIME_FILTER",
            "HMLR_INSPIRE_IDENTIFIER_RECEIPT_GATE",
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
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
        "state": "COMPLETED_RUNTIME_GUARDS_INJECTED",
        "source_path": str(args.carrier.resolve()),
        "output_path": str(args.output.resolve()),
        "source_sha256": sha256_bytes(source),
        "output_sha256": sha256_bytes(patched_bytes),
        "source_bytes": len(source),
        "output_bytes": len(patched_bytes),
        "runtime_patch_count": 3,
        "runtime_patch_labels": [
            "CLASSIC_TIFF_HEADER_VALIDATOR",
            "EA_OFFICIAL_NODATA_RUNTIME_FILTER",
            "HMLR_INSPIRE_IDENTIFIER_RECEIPT_GATE",
        ],
        "official_nodata_sentinel": -3.4028235e38,
        "hmlr_identifier_column_semantics": "column name must contain INSPIRE and ID",
        "hmlr_identifier_count_must_equal_feature_count": True,
        "hmlr_identifier_set_sha256_required": True,
        "classic_tiff_headers_hex": ["49492a00", "4d4d002a"],
        "fake_data": False,
        "final_ready": False,
    }
    atomic_write(args.receipt, (json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
