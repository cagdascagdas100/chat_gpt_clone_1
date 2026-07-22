#!/usr/bin/env python3
"""Bind the measurement polygon identifier to the HMLR INSPIRE receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

SLOT_ID = "height_difference_1"
SCRIPT_VERSION = "1.0-measurement-inspire-identity-binding-injector"

EXPECTED_MAIN_INSERTION_MARKER = """  $patched = Replace-ExactlyOnce -Text $patched -Old $oldProbeRasterValidation -New $newProbeRasterValidation -Label 'PROBE_RASTER_CONTENT_GATE'

  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1'
"""
EXPECTED_HMLR_HANDOFF_MARKER = """  $identifierSetHash = ([string]$hmlrDocument.artifacts.hmlr_gml.structure.identifier_set_sha256).ToLowerInvariant()
  if ($identifierSetHash -notmatch '^[0-9a-f]{64}$') { throw 'HMLR_INSPIRE_IDENTIFIER_SET_HASH_INVALID' }
  $allowedZipHosts = @('use-land-property-data.service.gov.uk','datapub-prd-s3-bucket.s3.amazonaws.com')
"""
EXPECTED_CLEANUP_MARKER = """  Remove-Item Env:HMLR_VERIFIED_ZIP_SHA256 -ErrorAction SilentlyContinue
  Remove-Item Env:HMLR_VERIFIED_ZIP_FINAL_HOST -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $tempMetadataMap -Force -ErrorAction SilentlyContinue
"""

INJECTED_MAIN_BLOCK = r"""  $patched = Replace-ExactlyOnce -Text $patched -Old $oldProbeRasterValidation -New $newProbeRasterValidation -Label 'PROBE_RASTER_CONTENT_GATE'

  $oldChoosePolygonIdColumn = @'
def choose_polygon_id_column(columns: Iterable[str]) -> str:
    lowered = {str(c).lower(): str(c) for c in columns}
    for key in ("inspireid", "inspire_id", "landregistry-inspire-id", "gml_id", "gml:id", "id"):
        if key in lowered:
            return lowered[key]
    raise EvidenceError("HMLR_POLYGON_ID_COLUMN_NOT_RESOLVED")
'@
  $newChoosePolygonIdColumn = @'
def choose_polygon_id_column(columns: Iterable[str]) -> str:
    originals = [str(c) for c in columns]
    expected = str(os.environ.get("HMLR_VERIFIED_IDENTIFIER_COLUMN") or "").strip()
    compact = expected.lower().replace("_", "").replace(":", "").replace("-", "")
    if not expected or "inspire" not in compact or "id" not in compact:
        raise EvidenceError(f"HMLR_VERIFIED_INSPIRE_IDENTIFIER_COLUMN_INVALID:{expected}")
    exact = [column for column in originals if column == expected]
    if len(exact) != 1:
        raise EvidenceError(
            f"HMLR_VERIFIED_INSPIRE_IDENTIFIER_COLUMN_NOT_EXACTLY_ONCE:{expected}:found={len(exact)}"
        )
    return exact[0]
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldChoosePolygonIdColumn -New $newChoosePolygonIdColumn -Label 'MEASUREMENT_INSPIRE_COLUMN_BINDING_GATE'

  $oldCandidateIdentityProvenance = @'
                    "hmlr_gml_sha256": result["artifacts"]["hmlr_gml"]["sha256"],
                    "hmlr_zip_sha256": os.environ.get("HMLR_VERIFIED_ZIP_SHA256"),
                    "hmlr_zip_final_host": os.environ.get("HMLR_VERIFIED_ZIP_FINAL_HOST"),
                    "dtm_sha256": full_receipts["DTM_1M"]["sha256"],
                    "dsm_sha256": full_receipts.get("DSM_LZ_1M", {}).get("sha256"),
'@
  $newCandidateIdentityProvenance = @'
                    "hmlr_gml_sha256": result["artifacts"]["hmlr_gml"]["sha256"],
                    "hmlr_zip_sha256": os.environ.get("HMLR_VERIFIED_ZIP_SHA256"),
                    "hmlr_zip_final_host": os.environ.get("HMLR_VERIFIED_ZIP_FINAL_HOST"),
                    "hmlr_identifier_column": os.environ.get("HMLR_VERIFIED_IDENTIFIER_COLUMN"),
                    "hmlr_identifier_set_sha256": os.environ.get("HMLR_VERIFIED_IDENTIFIER_SET_SHA256"),
                    "dtm_sha256": full_receipts["DTM_1M"]["sha256"],
                    "dsm_sha256": full_receipts.get("DSM_LZ_1M", {}).get("sha256"),
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldCandidateIdentityProvenance -New $newCandidateIdentityProvenance -Label 'CANDIDATE_INSPIRE_IDENTITY_PROVENANCE'

  $oldBusinessIdentityGate = @'
                if candidate.get("hmlr_zip_final_host") not in {
                    "use-land-property-data.service.gov.uk",
                    "datapub-prd-s3-bucket.s3.amazonaws.com",
                }:
                    raise EvidenceError("HMLR_ZIP_FINAL_HOST_REQUIRED_FOR_BUSINESS_ROW")
                try:
                    metadata = validate_survey_metadata_entry(parcel_id, survey_metadata.get(parcel_id))
'@
  $newBusinessIdentityGate = @'
                if candidate.get("hmlr_zip_final_host") not in {
                    "use-land-property-data.service.gov.uk",
                    "datapub-prd-s3-bucket.s3.amazonaws.com",
                }:
                    raise EvidenceError("HMLR_ZIP_FINAL_HOST_REQUIRED_FOR_BUSINESS_ROW")
                expected_identifier_column = str(os.environ.get("HMLR_VERIFIED_IDENTIFIER_COLUMN") or "")
                if (
                    not expected_identifier_column
                    or id_column != expected_identifier_column
                    or candidate.get("hmlr_identifier_column") != expected_identifier_column
                    or result["artifacts"]["hmlr_gml"].get("polygon_id_column") != expected_identifier_column
                ):
                    raise EvidenceError("HMLR_MEASUREMENT_IDENTIFIER_COLUMN_RECEIPT_MISMATCH")
                identifier_set_digest = str(candidate.get("hmlr_identifier_set_sha256") or "").lower()
                if len(identifier_set_digest) != 64 or any(
                    char not in "0123456789abcdef" for char in identifier_set_digest
                ):
                    raise EvidenceError("HMLR_IDENTIFIER_SET_SHA256_REQUIRED_FOR_BUSINESS_ROW")
                if not polygon_id.strip():
                    raise EvidenceError("HMLR_BOUND_POLYGON_IDENTIFIER_EMPTY")
                try:
                    metadata = validate_survey_metadata_entry(parcel_id, survey_metadata.get(parcel_id))
'@
  $patched = Replace-ExactlyOnce -Text $patched -Old $oldBusinessIdentityGate -New $newBusinessIdentityGate -Label 'BUSINESS_ROW_INSPIRE_IDENTITY_PROVENANCE_GATE'

  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_height_difference_1'
"""

INJECTED_HMLR_HANDOFF = """  $identifierSetHash = ([string]$hmlrDocument.artifacts.hmlr_gml.structure.identifier_set_sha256).ToLowerInvariant()
  if ($identifierSetHash -notmatch '^[0-9a-f]{64}$') { throw 'HMLR_INSPIRE_IDENTIFIER_SET_HASH_INVALID' }
  $env:HMLR_VERIFIED_IDENTIFIER_COLUMN = $identifierColumn
  $env:HMLR_VERIFIED_IDENTIFIER_SET_SHA256 = $identifierSetHash
  $allowedZipHosts = @('use-land-property-data.service.gov.uk','datapub-prd-s3-bucket.s3.amazonaws.com')
"""

INJECTED_CLEANUP = """  Remove-Item Env:HMLR_VERIFIED_ZIP_SHA256 -ErrorAction SilentlyContinue
  Remove-Item Env:HMLR_VERIFIED_ZIP_FINAL_HOST -ErrorAction SilentlyContinue
  Remove-Item Env:HMLR_VERIFIED_IDENTIFIER_COLUMN -ErrorAction SilentlyContinue
  Remove-Item Env:HMLR_VERIFIED_IDENTIFIER_SET_SHA256 -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $tempMetadataMap -Force -ErrorAction SilentlyContinue
"""


class InjectionError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise InjectionError(f"{label}_COUNT_INVALID:{count}")
    return text.replace(old, new, 1)


def patch_carrier_text(text: str) -> str:
    patched = text.replace("\r\n", "\n")
    patched = replace_once(patched, EXPECTED_MAIN_INSERTION_MARKER, INJECTED_MAIN_BLOCK, "MEASUREMENT_IDENTITY_MAIN_MARKER")
    patched = replace_once(patched, EXPECTED_HMLR_HANDOFF_MARKER, INJECTED_HMLR_HANDOFF, "MEASUREMENT_IDENTITY_HMLR_HANDOFF_MARKER")
    patched = replace_once(patched, EXPECTED_CLEANUP_MARKER, INJECTED_CLEANUP, "MEASUREMENT_IDENTITY_CLEANUP_MARKER")
    required = (
        "MEASUREMENT_INSPIRE_COLUMN_BINDING_GATE",
        "CANDIDATE_INSPIRE_IDENTITY_PROVENANCE",
        "BUSINESS_ROW_INSPIRE_IDENTITY_PROVENANCE_GATE",
        "HMLR_VERIFIED_IDENTIFIER_COLUMN",
        "HMLR_VERIFIED_IDENTIFIER_SET_SHA256",
        "HMLR_MEASUREMENT_IDENTIFIER_COLUMN_RECEIPT_MISMATCH",
        "HMLR_IDENTIFIER_SET_SHA256_REQUIRED_FOR_BUSINESS_ROW",
        "HMLR_BOUND_POLYGON_IDENTIFIER_EMPTY",
    )
    missing = [token for token in required if token not in patched]
    if missing:
        raise InjectionError(f"MEASUREMENT_IDENTITY_TOKEN_MISSING:{missing}")
    return patched


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


def run_self_test() -> dict[str, Any]:
    fixture = "header\n" + EXPECTED_MAIN_INSERTION_MARKER + "\n" + EXPECTED_HMLR_HANDOFF_MARKER + "\n" + EXPECTED_CLEANUP_MARKER + "\nfooter\n"
    patched = patch_carrier_text(fixture)
    checks = {
        "main_marker_replaced": EXPECTED_MAIN_INSERTION_MARKER not in patched,
        "handoff_marker_replaced": EXPECTED_HMLR_HANDOFF_MARKER not in patched,
        "cleanup_marker_replaced": EXPECTED_CLEANUP_MARKER not in patched,
        "measurement_column_binding_present": "MEASUREMENT_INSPIRE_COLUMN_BINDING_GATE" in patched,
        "candidate_identity_provenance_present": "CANDIDATE_INSPIRE_IDENTITY_PROVENANCE" in patched,
        "business_identity_gate_present": "BUSINESS_ROW_INSPIRE_IDENTITY_PROVENANCE_GATE" in patched,
        "identifier_column_env_present": "HMLR_VERIFIED_IDENTIFIER_COLUMN" in patched,
        "identifier_hash_env_present": "HMLR_VERIFIED_IDENTIFIER_SET_SHA256" in patched,
        "generic_fallback_removed_from_new_function": 'for key in ("inspireid"' not in patched.split("$newChoosePolygonIdColumn", 1)[1],
        "empty_polygon_id_gate_present": "HMLR_BOUND_POLYGON_IDENTIFIER_EMPTY" in patched,
    }
    duplicate_main_rejected = duplicate_handoff_rejected = duplicate_cleanup_rejected = False
    for label, duplicate in (("main", EXPECTED_MAIN_INSERTION_MARKER + fixture), ("handoff", EXPECTED_HMLR_HANDOFF_MARKER + fixture), ("cleanup", EXPECTED_CLEANUP_MARKER + fixture)):
        try:
            patch_carrier_text(duplicate)
        except InjectionError:
            if label == "main":
                duplicate_main_rejected = True
            elif label == "handoff":
                duplicate_handoff_rejected = True
            else:
                duplicate_cleanup_rejected = True
    checks.update({"duplicate_main_rejected": duplicate_main_rejected, "duplicate_handoff_rejected": duplicate_handoff_rejected, "duplicate_cleanup_rejected": duplicate_cleanup_rejected})
    if not all(checks.values()):
        raise InjectionError(f"SELF_TEST_FAILED:{checks}")
    return {"slot_id": SLOT_ID, "state": "PASS", "script_version": SCRIPT_VERSION, "checks": len(checks), "check_results": checks}


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
    if not args.carrier or not args.output or not args.receipt:
        raise InjectionError("CARRIER_OUTPUT_AND_RECEIPT_REQUIRED")
    source = args.carrier.read_bytes()
    patched = patch_carrier_text(source.decode("utf-8")).encode("utf-8")
    atomic_write(args.output, patched)
    receipt = {
        "slot_id": SLOT_ID,
        "state": "COMPLETED_MEASUREMENT_IDENTITY_BINDING_INJECTED",
        "script_version": SCRIPT_VERSION,
        "runtime_patch_count": 4,
        "runtime_patch_labels": ["HMLR_IDENTIFIER_ENV_HANDOFF", "MEASUREMENT_INSPIRE_COLUMN_BINDING_GATE", "CANDIDATE_INSPIRE_IDENTITY_PROVENANCE", "BUSINESS_ROW_INSPIRE_IDENTITY_PROVENANCE_GATE"],
        "source_path": str(args.carrier.resolve()),
        "output_path": str(args.output.resolve()),
        "source_bytes": len(source),
        "output_bytes": len(patched),
        "source_sha256": sha256_bytes(source),
        "output_sha256": sha256_bytes(patched),
        "identifier_column_env": "HMLR_VERIFIED_IDENTIFIER_COLUMN",
        "identifier_set_hash_env": "HMLR_VERIFIED_IDENTIFIER_SET_SHA256",
    }
    atomic_write(args.receipt, (json.dumps(receipt, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
