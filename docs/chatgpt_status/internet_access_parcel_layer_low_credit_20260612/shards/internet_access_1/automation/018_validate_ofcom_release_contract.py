#!/usr/bin/env python3
"""Validate the official Ofcom Spring 2026 fixed-broadband release contract.

This validator is metadata-only and fail-closed. It never downloads the archive,
never emits broadband values, and never performs a business-data write.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

POSTCODE_PATTERN = re.compile(r"^202601_fixed_postcode_coverage_r2_[A-Z]{1,2}\.csv$")
RES_POSTCODE_PATTERN = re.compile(r"^202601_fixed_postcode_res_coverage_r1_[A-Z]{1,2}\.csv$")

EXPECTED = {
    "publication_date": "2026-05-13",
    "snapshot": "2026-01",
    "revision": "v2",
    "revision_date": "2026-07-07",
    "fixed_providers": 52,
    "fwa_providers": 18,
    "licence": "Open Government Licence",
    "archive_name": "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip",
    "postcode_folder": "postcode_files",
    "postcode_member_count": 121,
    "postcode_rows": 1741096,
    "postcode_uncompressed_mb": 165,
    "res_postcode_folder": "postcode_res_files",
    "res_postcode_member_count": 121,
    "res_postcode_rows": 1606191,
    "res_postcode_uncompressed_mb": 151,
    "rm_member": "202601_fixed_postcode_coverage_r2_RM.csv",
}

REQUIRED_SEMANTICS = {
    "postcode",
    "postcode_space",
    "postcode_area",
    "sfbb_availability_pct",
    "ufbb_100_availability_pct",
    "ufbb_300_availability_pct",
    "gigabit_availability_pct",
    "unable_30mbps_pct",
}

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)

def validate_contract(payload: dict[str, Any]) -> dict[str, Any]:
    for key, value in EXPECTED.items():
        require(payload.get(key) == value, f"{key}: expected {value!r}, got {payload.get(key)!r}")

    members = payload.get("postcode_members")
    require(isinstance(members, list), "postcode_members must be a list")
    require(len(members) == EXPECTED["postcode_member_count"], "postcode member count mismatch")
    require(len(set(members)) == len(members), "duplicate postcode member")
    require(all(POSTCODE_PATTERN.fullmatch(name) for name in members), "invalid corrected-r2 postcode member name")
    require(EXPECTED["rm_member"] in members, "RM corrected-r2 member missing")

    res_members = payload.get("res_postcode_members")
    require(isinstance(res_members, list), "res_postcode_members must be a list")
    require(len(res_members) == EXPECTED["res_postcode_member_count"], "res postcode member count mismatch")
    require(len(set(res_members)) == len(res_members), "duplicate residential postcode member")
    require(all(RES_POSTCODE_PATTERN.fullmatch(name) for name in res_members), "invalid residential postcode member name")

    semantics = set(payload.get("postcode_field_semantics") or [])
    require(REQUIRED_SEMANTICS.issubset(semantics), "required postcode field semantics missing")
    require("full_fibre_availability_pct" not in semantics, "postcode full-fibre field must be absent")
    require(payload.get("postcode_full_fibre_withheld_reason") == "commercial_confidentiality", "postcode full-fibre confidentiality rule missing")
    require(payload.get("coverage_scope") == "fixed_line_except_explicit_fwa_fields", "coverage scope guardrail mismatch")
    require(payload.get("corrected_areas") == ["CW", "MK"], "corrected area list mismatch")
    require(payload.get("superseded_duplicates") == {"CW": "CV", "MK": "ME"}, "superseded duplicate mapping mismatch")

    return {
        "status": "PASS",
        "postcode_member_count": len(members),
        "res_postcode_member_count": len(res_members),
        "required_semantics_count": len(REQUIRED_SEMANTICS),
        "rm_member_present": True,
        "broadband_rows_read": 0,
        "business_rows_written": 0,
        "migration_applied": False,
        "final_ready": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    result = validate_contract(payload)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
