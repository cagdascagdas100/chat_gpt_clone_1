#!/usr/bin/env python3
"""Wave367: classify bounded tar-member name patterns from Wave366 metadata only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

MAX_RECORDS = 128
DATA_SUFFIXES = {
    ".parquet", ".pmtiles", ".fgb", ".geojson", ".json", ".ndjson",
    ".duckdb", ".db", ".sqlite", ".csv", ".tsv",
}
DOC_BASENAMES = {"license", "license.txt", "notice", "notice.txt", "readme", "readme.md"}


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


def classify_name(name: str) -> dict[str, Any]:
    normalized = name.replace("\\", "/").strip().lower()
    basename = normalized.rsplit("/", 1)[-1]
    suffix = Path(basename).suffix.lower()
    tokens = [token for token in re.split(r"[^a-z0-9]+", normalized) if token]
    categories: list[str] = []
    if normalized.endswith("/bin/overturemaps") or basename in {"overturemaps", "overturemaps.exe"}:
        categories.append("OVERTUREMAPS_BINARY_NAME")
    if suffix in DATA_SUFFIXES:
        categories.append("DATA_FILE_SUFFIX")
    if any(token in {"building", "buildings"} for token in tokens):
        categories.append("BUILDING_NAME_TOKEN")
    if any(token in {"overture", "overturemaps"} for token in tokens):
        categories.append("OVERTURE_NAME_TOKEN")
    if basename in DOC_BASENAMES:
        categories.append("DOCUMENTATION_OR_LICENSE_NAME")
    if not categories:
        categories.append("UNCLASSIFIED_NAME")
    return {
        "normalized_member_name": normalized,
        "basename": basename,
        "suffix": suffix or None,
        "name_categories": categories,
        "candidate_by_name_only": bool(
            {"DATA_FILE_SUFFIX", "BUILDING_NAME_TOKEN", "OVERTURE_NAME_TOKEN"}.intersection(categories)
        ),
    }


def assess(prior: dict[str, Any], accessed_at: str) -> dict[str, Any]:
    if prior.get("slot_id") != "gas_emissions_2" or prior.get("wave") != 366:
        raise ValueError("PRIOR_WAVE366_SLOT_MISMATCH")
    source_records = prior.get("tar_member_metadata_records", []) or []
    records: list[dict[str, Any]] = []
    for source in source_records[:MAX_RECORDS]:
        name = source.get("member_name")
        if not isinstance(name, str) or not name.strip():
            continue
        classified = classify_name(name)
        record = {
            "member_name": name,
            "member_name_sha256": sha256_bytes(name.encode("utf-8")),
            "member_size": source.get("member_size"),
            "member_typeflag": source.get("member_typeflag"),
            **classified,
        }
        record["pattern_record_sha256"] = sha256_bytes(
            json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        records.append(record)

    candidate_count = sum(1 for item in records if item["candidate_by_name_only"])
    blockers: list[str] = []
    if not source_records:
        blockers.append("WAVE366_TAR_MEMBER_METADATA_COUNT_ZERO")
    if not records:
        blockers.append("TAR_MEMBER_NAME_PATTERNS_NOT_AVAILABLE")
    blockers.extend([
        "TAR_MEMBER_NAME_PATTERN_ALONE_DOES_NOT_PROVE_FILE_CONTENT",
        "TAR_MEMBER_NAME_PATTERN_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
        "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
        "THREE_EXACT_UPRNS_NOT_ACQUIRED",
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
    ])

    prior_sha = sha256_bytes(canonical_bytes(prior))
    evidence_excerpt = (
        f"prior_output_sha256={prior_sha};source_metadata_records={len(source_records)};"
        f"classified_name_records={len(records)};candidate_by_name_only={candidate_count};"
        "business_rows=0;parcel_rows=0"
    )
    runtime_evidence = {
        "source_url": "repo://england_map_web/data/aays_21_slots/gas_emissions_2/"
                      "wave366_ghcr_bottle_layer_tar_member_metadata_gate_20260803.json",
        "accessed_at": accessed_at,
        "content_sha256": sha256_bytes(evidence_excerpt.encode("utf-8")),
        "hash_scope": "normalized_runtime_receipt_utf8",
        "record_scope": "Wave366 member-name strings only; no archive member body or content inference.",
        "relevant_record_ids_or_excerpt": evidence_excerpt,
        "supports_fields": [
            "member_name", "member_name_sha256", "basename", "suffix",
            "name_categories", "candidate_by_name_only", "no_member_body_read",
        ],
        "license_or_terms_url": "https://docs.python.org/3/library/pathlib.html",
    }

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 367,
        "accessed_at": accessed_at,
        "prior_wave": 366,
        "prior_state": prior.get("state"),
        "prior_output_sha256": prior_sha,
        "assessments": (prior.get("assessments") or [])[:3],
        "source_tar_member_metadata_count": len(source_records),
        "tar_member_name_pattern_records": records,
        "tar_member_name_pattern_count": len(records),
        "candidate_by_name_only_count": candidate_count,
        "member_body_read": False,
        "archive_extraction_performed": False,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "decision": "GHCR_BOTTLE_LAYER_TAR_MEMBER_NAME_PATTERNS_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": "ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_PATH_PREFIXES_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": prior.get("source_evidence_manifest", []),
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }


def self_test() -> None:
    assert classify_name("bin/overturemaps")["name_categories"] == ["OVERTUREMAPS_BINARY_NAME", "OVERTURE_NAME_TOKEN"]
    data = classify_name("share/overture/buildings/part-000.parquet")
    assert data["candidate_by_name_only"] is True
    assert "DATA_FILE_SUFFIX" in data["name_categories"]
    assert "BUILDING_NAME_TOKEN" in data["name_categories"]
    prior = {
        "slot_id": "gas_emissions_2",
        "wave": 366,
        "state": "NO_DATA_CONTINUE",
        "assessments": [{"parcel_id": "parcel_30762"}],
        "tar_member_metadata_records": [
            {"member_name": "bin/overturemaps", "member_size": 123, "member_typeflag": "0"},
            {"member_name": "share/LICENSE", "member_size": 456, "member_typeflag": "0"},
        ],
        "source_evidence_manifest": [],
    }
    out = assess(prior, "2026-08-03T14:50:00Z")
    assert out["tar_member_name_pattern_count"] == 2
    assert out["candidate_by_name_only_count"] == 1
    assert out["business_rows_produced"] == 0
    empty = dict(prior)
    empty["tar_member_metadata_records"] = []
    empty_out = assess(empty, "2026-08-03T14:50:00Z")
    assert empty_out["tar_member_name_pattern_count"] == 0
    assert "WAVE366_TAR_MEMBER_METADATA_COUNT_ZERO" in empty_out["blocker"]
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
