#!/usr/bin/env python3
"""Run exact slot-3 review directly against the validated official Ofcom ZIP.

The orchestrator reuses validated ZIP/download primitives, streams the canonical
slot slice, and scans all corrected postcode CSV members without extracting them
to disk. Detailed values are retained only for identity-matched slot postcodes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import urllib.parse
from typing import Any

SLOT_ID = "internet_access_3"
EXPECTED_CANONICAL_ROWS = 30_761
AUTOMATION_ROOT_RELATIVE = Path(
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/"
    "shards/internet_access_3/automation"
)
REQUIRED_AUTOMATION = (
    "002_extract_slot3_ofcom_2026_candidates.py",
    "003_selftest_slot3_extractor.py",
    "005_stream_extract_slot3_inputs.py",
    "006_selftest_stream_extract_slot3_inputs.py",
    "008_download_validate_run_slot3.py",
    "012_extract_slot3_ofcom_needed_postcodes.py",
    "013_selftest_targeted_postcode_join.py",
    "016_selftest_targeted_pipeline_wiring.py",
    "017_stream_ofcom_zip_needed_postcodes.py",
    "018_selftest_direct_zip_stream_join.py",
)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--ofcom-zip", type=Path)
    parser.add_argument("--ofcom-url")
    parser.add_argument("--download-retries", type=int, default=4)
    parser.add_argument("--download-timeout-seconds", type=int, default=600)
    return parser.parse_args()


def build_targeted_command(
    automation_root: Path,
    slice_root: Path,
    zip_path: Path,
    output_root: Path,
) -> list[str]:
    return [
        sys.executable,
        str(automation_root / "017_stream_ofcom_zip_needed_postcodes.py"),
        "--canonical",
        str(slice_root / "internet_access_3_canonical_slice_latest.geojson"),
        "--legacy-internet-geojson",
        str(slice_root / "internet_access_3_legacy_slice_latest.geojson"),
        "--ofcom-zip",
        str(zip_path),
        "--output-dir",
        str(output_root),
    ]


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    work_root = (args.work_root or (repo_root / "outputs/internet_access_3_verified_run")).resolve()
    automation_root = repo_root / AUTOMATION_ROOT_RELATIVE
    canonical_source = repo_root / "england_map_web/data/program_layer_matrix/security.geojson"
    legacy_source = repo_root / "england_map_web/data/program_layer_matrix/internet.geojson"
    stage_root = work_root / "stage"
    cache_zip = stage_root / "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"
    slice_root = work_root / "slot_inputs"
    output_root = work_root / "candidate_outputs"
    diagnostics_path = work_root / "internet_access_3_network_and_execution_diagnostics_latest.json"

    base = load_module(automation_root / "008_download_validate_run_slot3.py", "internet_access_3_download_base")
    ofcom_url = args.ofcom_url or base.OFFICIAL_ZIP_URL
    diagnostics = base.initial_diagnostics(repo_root, work_root, ofcom_url)
    diagnostics["pipeline_entrypoint"] = Path(__file__).name
    diagnostics["join_strategy"] = "DIRECT_ZIP_STREAM_SCAN_ALL_R2_ROWS_RETAIN_ONLY_NEEDED_SLOT3_POSTCODES"
    diagnostics["memory_strategy"] = "AREA_PARTITIONED_EXACT_UNIQUENESS_PLUS_NEEDED_POSTCODE_ROWS_ONLY"
    diagnostics["csv_extraction_mode"] = "NONE_DIRECT_ZIP_STREAM"
    diagnostics["ofcom_csv_extracted_to_disk"] = False
    stage_root.mkdir(parents=True, exist_ok=True)
    slice_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)

    try:
        required_paths = [canonical_source, legacy_source]
        required_paths.extend(automation_root / name for name in REQUIRED_AUTOMATION)
        for required in required_paths:
            if not required.is_file():
                raise base.GateError(f"Required source or automation missing: {required}")

        host = urllib.parse.urlparse(ofcom_url).hostname or "www.ofcom.org.uk"
        dns = base.diagnose_dns(host)
        diagnostics["dns_state"] = dns["state"]
        diagnostics["dns_detail"] = dns

        selected = base.choose_existing_zip(args.ofcom_zip, cache_zip)
        if selected:
            mode, zip_path, zip_metadata = selected
            diagnostics["zip_source_mode"] = mode
            diagnostics["download_state"] = "NOT_REQUIRED_VALIDATED_EXISTING_ZIP"
        else:
            zip_metadata = base.download_and_validate(
                ofcom_url,
                cache_zip,
                diagnostics,
                retries=args.download_retries,
                timeout=args.download_timeout_seconds,
            )
            zip_path = cache_zip
            diagnostics["zip_source_mode"] = "VALIDATED_NETWORK_DOWNLOAD"
            diagnostics["download_state"] = "PASS"

        diagnostics.update(
            {
                "zip_path": str(zip_path),
                "zip_bytes": zip_metadata["bytes"],
                "zip_sha256": zip_metadata["sha256"],
                "r1_file_count": zip_metadata["r1_file_count"],
                "r2_file_count": zip_metadata["r2_file_count"],
                "extracted_r2_files": 0,
            }
        )

        base.run_checked([sys.executable, str(automation_root / "003_selftest_slot3_extractor.py")], diagnostics, "IDENTITY_EXTRACTOR_SELFTEST")
        base.run_checked([sys.executable, str(automation_root / "006_selftest_stream_extract_slot3_inputs.py")], diagnostics, "STREAMING_SLICER_SELFTEST")
        base.run_checked([sys.executable, str(automation_root / "013_selftest_targeted_postcode_join.py")], diagnostics, "TARGETED_POSTCODE_JOIN_SELFTEST")
        base.run_checked([sys.executable, str(automation_root / "018_selftest_direct_zip_stream_join.py")], diagnostics, "DIRECT_ZIP_STREAM_JOIN_SELFTEST")
        base.run_checked([sys.executable, str(automation_root / "016_selftest_targeted_pipeline_wiring.py")], diagnostics, "TARGETED_PIPELINE_WIRING_SELFTEST")
        base.run_checked(
            [
                sys.executable,
                str(automation_root / "005_stream_extract_slot3_inputs.py"),
                "--canonical",
                str(canonical_source),
                "--legacy-internet",
                str(legacy_source),
                "--output-dir",
                str(slice_root),
            ],
            diagnostics,
            "EXACT_SLOT3_STREAM_SLICE",
        )

        slice_manifest_path = slice_root / "internet_access_3_stream_slice_manifest_latest.json"
        slice_manifest = json.loads(slice_manifest_path.read_text(encoding="utf-8"))
        canonical_rows = int(slice_manifest["canonical"]["rows"])
        if canonical_rows != EXPECTED_CANONICAL_ROWS:
            raise base.GateError(f"Canonical slice row count mismatch: {canonical_rows}")
        diagnostics["canonical_slice_rows"] = canonical_rows
        diagnostics["canonical_slice_sha256"] = slice_manifest["canonical"]["output_sha256"]
        diagnostics["legacy_slice_rows"] = int(slice_manifest["legacy_internet"]["rows"])
        diagnostics["legacy_slice_sha256"] = slice_manifest["legacy_internet"]["output_sha256"]
        diagnostics["canonical_first_rows"] = slice_manifest["canonical"]["first_rows"]

        base.run_checked(
            build_targeted_command(automation_root, slice_root, zip_path, output_root),
            diagnostics,
            "DIRECT_ZIP_STREAM_TARGETED_REVIEW_ONLY_R2_JOIN",
        )
        candidate_manifest_path = output_root / "internet_access_3_candidate_manifest_latest.json"
        candidate_manifest = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
        if int(candidate_manifest["canonical_rows"]) != EXPECTED_CANONICAL_ROWS:
            raise base.GateError("Candidate manifest canonical row count mismatch")
        matched = int(candidate_manifest["current_r2_postcode_proxy_rows"])
        no_data = int(candidate_manifest["no_data_rows"])
        if matched + no_data != EXPECTED_CANONICAL_ROWS:
            raise base.GateError(f"Candidate partition mismatch: matched={matched}, no_data={no_data}")
        if int(candidate_manifest.get("ofcom_postcodes_scanned", -1)) != base.EXPECTED_OFCOM_POSTCODE_ROWS:
            raise base.GateError("Direct ZIP join did not scan the exact Ofcom postcode row count")
        if candidate_manifest.get("ofcom_source_mode") != "DIRECT_ZIP_STREAM_NO_CSV_EXTRACTION":
            raise base.GateError("Candidate manifest did not report direct ZIP streaming")
        if candidate_manifest.get("ofcom_csv_extracted_to_disk") is not False:
            raise base.GateError("Candidate manifest reported CSV extraction to disk")
        if candidate_manifest.get("ofcom_zip_sha256") != zip_metadata["sha256"]:
            raise base.GateError("Candidate manifest ZIP SHA256 does not match validated source")
        if candidate_manifest.get("postcode_uniqueness_strategy") != "AREA_PARTITIONED_EXACT_PER_MEMBER_SET":
            raise base.GateError("Candidate manifest did not use area-partitioned exact uniqueness")
        if int(candidate_manifest.get("postcode_area_member_count", -1)) != base.EXPECTED_OFCOM_FILE_COUNT:
            raise base.GateError("Candidate manifest postcode-area member count mismatch")
        if int(candidate_manifest.get("actual_business_data_rows_written", -1)) != 0:
            raise base.GateError("Review-only extractor reported business writes")

        diagnostics["candidate_manifest"] = str(candidate_manifest_path)
        diagnostics["current_r2_postcode_proxy_rows"] = matched
        diagnostics["identity_conflict_rows"] = int(candidate_manifest["identity_conflict_rows"])
        diagnostics["postcode_not_found_in_current_r2_rows"] = int(candidate_manifest["postcode_not_found_in_current_r2_rows"])
        diagnostics["no_verified_postcode_rows"] = int(candidate_manifest["no_verified_postcode_rows"])
        diagnostics["no_data_rows"] = no_data
        diagnostics["needed_postcodes"] = int(candidate_manifest["needed_postcodes"])
        diagnostics["ofcom_postcodes_retained"] = int(candidate_manifest["ofcom_postcodes_retained"])
        diagnostics["zip_member_stream_sha256_count"] = int(candidate_manifest["zip_member_stream_sha256_count"])
        diagnostics["postcode_uniqueness_strategy"] = candidate_manifest["postcode_uniqueness_strategy"]
        diagnostics["postcode_area_member_count"] = int(candidate_manifest["postcode_area_member_count"])
        diagnostics["peak_member_unique_postcodes"] = int(candidate_manifest["peak_member_unique_postcodes"])
        diagnostics["samples"] = candidate_manifest.get("samples", [])
        base.save_diagnostics(
            diagnostics_path,
            diagnostics,
            "COMPLETE_DIRECT_ZIP_TARGETED_REVIEW_OUTPUT_READY",
            "Official ZIP, exact hashes, bounded slice and direct-stream targeted counts completed. No CSV extraction, migration or business write occurred.",
        )
        print(json.dumps({k: v for k, v in diagnostics.items() if k not in {"download_attempts", "stages", "samples"}}, sort_keys=True))
        return 0
    except Exception as exc:
        diagnostics["error"] = f"{type(exc).__name__}: {exc}"
        base.save_diagnostics(
            diagnostics_path,
            diagnostics,
            "BLOCKED_DIRECT_ZIP_TARGETED_EXECUTION",
            "Direct ZIP targeted execution stopped at a verified gate. No migration or business write occurred.",
        )
        print(diagnostics["error"], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
