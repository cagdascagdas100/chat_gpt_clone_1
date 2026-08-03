#!/usr/bin/env python3
"""Wave368: classify bounded tar-member path prefixes from Wave367 name records only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

MAX_RECORDS = 128
MAX_PREFIX_DEPTH = 3


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def atomic_json(path: str, obj: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_bytes(obj)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
        handle.write(raw)
        temp_name = handle.name
    os.replace(temp_name, target)


def classify_path(name: str) -> dict[str, Any]:
    normalized = name.replace("\\", "/").strip()
    posix = PurePosixPath(normalized)
    raw_parts = list(posix.parts)
    content_parts = [part for part in raw_parts if part not in {"/", ""}]
    lower_parts = [part.lower() for part in content_parts]
    prefixes = [
        "/".join(content_parts[:depth])
        for depth in range(1, min(len(content_parts), MAX_PREFIX_DEPTH) + 1)
    ]
    parent_reference = any(part == ".." for part in content_parts)
    current_reference = any(part == "." for part in content_parts)
    windows_drive_prefix = bool(re.match(r"^[A-Za-z]:/", normalized))
    absolute_path = normalized.startswith("/") or windows_drive_prefix
    candidate_tokens = {"overture", "overturemaps", "building", "buildings", "data", "share", "lib", "bin"}
    candidate_by_path_only = bool(candidate_tokens.intersection(lower_parts))
    return {
        "normalized_member_name": normalized,
        "path_parts": content_parts,
        "path_prefixes": prefixes,
        "root_component": content_parts[0] if content_parts else None,
        "path_depth": len(content_parts),
        "absolute_path": absolute_path,
        "windows_drive_prefix": windows_drive_prefix,
        "parent_reference": parent_reference,
        "current_reference": current_reference,
        "candidate_by_path_only": candidate_by_path_only,
    }


def assess(prior: dict[str, Any], accessed_at: str) -> dict[str, Any]:
    if prior.get("slot_id") != "gas_emissions_2" or prior.get("wave") != 367:
        raise ValueError("PRIOR_WAVE367_SLOT_MISMATCH")
    source_records = prior.get("tar_member_name_pattern_records", []) or []
    records: list[dict[str, Any]] = []
    for source in source_records[:MAX_RECORDS]:
        name = source.get("member_name")
        if not isinstance(name, str) or not name.strip():
            continue
        classified = classify_path(name)
        record = {
            "member_name": name,
            "member_name_sha256": source.get("member_name_sha256") or sha256_bytes(name.encode("utf-8")),
            **classified,
        }
        record["path_prefix_record_sha256"] = sha256_bytes(
            json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        records.append(record)

    candidate_count = sum(1 for item in records if item["candidate_by_path_only"])
    suspicious_count = sum(
        1 for item in records
        if item["absolute_path"] or item["parent_reference"] or item["windows_drive_prefix"]
    )
    blockers: list[str] = []
    if not source_records:
        blockers.append("WAVE367_TAR_MEMBER_NAME_PATTERN_COUNT_ZERO")
    if not records:
        blockers.append("TAR_MEMBER_PATH_PREFIXES_NOT_AVAILABLE")
    blockers.extend([
        "TAR_MEMBER_PATH_PREFIX_ALONE_DOES_NOT_PROVE_FILE_CONTENT",
        "TAR_MEMBER_PATH_PREFIX_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
        "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
        "THREE_EXACT_UPRNS_NOT_ACQUIRED",
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
    ])

    prior_sha = sha256_bytes(canonical_bytes(prior))
    evidence_excerpt = (
        f"prior_output_sha256={prior_sha};source_name_records={len(source_records)};"
        f"classified_path_prefix_records={len(records)};candidate_by_path_only={candidate_count};"
        f"suspicious_path_records={suspicious_count};business_rows=0;parcel_rows=0"
    )
    runtime_evidence = {
        "source_url": "repo://england_map_web/data/aays_21_slots/gas_emissions_2/"
                      "wave367_ghcr_bottle_layer_tar_member_name_pattern_gate_20260803.json",
        "accessed_at": accessed_at,
        "content_sha256": sha256_bytes(evidence_excerpt.encode("utf-8")),
        "hash_scope": "normalized_runtime_receipt_utf8",
        "record_scope": "Wave367 acquired member-name strings only; no archive member body or content inference.",
        "relevant_record_ids_or_excerpt": evidence_excerpt,
        "supports_fields": [
            "path_parts", "path_prefixes", "root_component", "path_depth",
            "absolute_path", "windows_drive_prefix", "parent_reference",
            "candidate_by_path_only", "no_member_body_read",
        ],
        "license_or_terms_url": "https://docs.python.org/3/library/pathlib.html",
    }

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 368,
        "accessed_at": accessed_at,
        "prior_wave": 367,
        "prior_state": prior.get("state"),
        "prior_output_sha256": prior_sha,
        "assessments": (prior.get("assessments") or [])[:3],
        "source_tar_member_name_pattern_count": len(source_records),
        "tar_member_path_prefix_records": records,
        "tar_member_path_prefix_count": len(records),
        "candidate_by_path_only_count": candidate_count,
        "suspicious_path_record_count": suspicious_count,
        "member_body_read": False,
        "archive_extraction_performed": False,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "decision": "GHCR_BOTTLE_LAYER_TAR_MEMBER_PATH_PREFIXES_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": "ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_PATH_DEPTH_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": prior.get("source_evidence_manifest", []),
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }


def self_test() -> None:
    binary = classify_path("bin/overturemaps")
    assert binary["path_parts"] == ["bin", "overturemaps"]
    assert binary["path_prefixes"] == ["bin", "bin/overturemaps"]
    assert binary["candidate_by_path_only"] is True
    data = classify_path("share/overture/buildings/part-000.parquet")
    assert data["root_component"] == "share"
    assert data["path_depth"] == 4
    assert data["path_prefixes"] == ["share", "share/overture", "share/overture/buildings"]
    unsafe = classify_path("../escape/file")
    assert unsafe["parent_reference"] is True
    absolute = classify_path("/etc/passwd")
    assert absolute["absolute_path"] is True
    prior = {
        "slot_id": "gas_emissions_2",
        "wave": 367,
        "state": "NO_DATA_CONTINUE",
        "assessments": [{"parcel_id": "parcel_30762"}],
        "tar_member_name_pattern_records": [
            {"member_name": "bin/overturemaps"},
            {"member_name": "share/LICENSE"},
        ],
        "source_evidence_manifest": [],
    }
    out = assess(prior, "2026-08-03T15:42:00Z")
    assert out["tar_member_path_prefix_count"] == 2
    assert out["candidate_by_path_only_count"] == 2
    assert out["business_rows_produced"] == 0
    empty = dict(prior)
    empty["tar_member_name_pattern_records"] = []
    empty_out = assess(empty, "2026-08-03T15:42:00Z")
    assert empty_out["tar_member_path_prefix_count"] == 0
    assert "WAVE367_TAR_MEMBER_NAME_PATTERN_COUNT_ZERO" in empty_out["blocker"]
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior")
    parser.add_argument("--output")
    parser.add_argument("--accessed-at")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.prior or not args.output or not args.accessed_at:
        parser.error("--prior, --output and --accessed-at are required")
    with open(args.prior, encoding="utf-8") as handle:
        prior = json.load(handle)
    atomic_json(args.output, assess(prior, args.accessed_at))


if __name__ == "__main__":
    main()
