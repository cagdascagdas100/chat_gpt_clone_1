#!/usr/bin/env python3
"""Wave370: count explicit root-component evidence from bounded Wave368 records only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

MAX_RECORDS = 128
MAX_COMPONENT_LENGTH = 256


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


def explicit_root_component(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    value = record.get("root_component")
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or len(value) > MAX_COMPONENT_LENGTH:
        return None
    return value


def assess(chain: dict[str, Any], source: dict[str, Any], accessed_at: str) -> dict[str, Any]:
    if chain.get("slot_id") != "gas_emissions_2" or chain.get("wave") != 369:
        raise ValueError("PRIOR_WAVE369_SLOT_MISMATCH")
    if source.get("slot_id") != "gas_emissions_2" or source.get("wave") != 368:
        raise ValueError("SOURCE_WAVE368_SLOT_MISMATCH")

    source_records = source.get("tar_member_path_prefix_records", []) or []
    bounded_records = source_records[:MAX_RECORDS]
    roots = [
        root
        for record in bounded_records
        if (root := explicit_root_component(record)) is not None
    ]
    counts = Counter(roots)
    frequencies = [
        {"root_component": component, "record_count": count}
        for component, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    blockers: list[str] = []
    if not source_records:
        blockers.append("WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO")
    if not roots:
        blockers.append("TAR_MEMBER_ROOT_COMPONENTS_NOT_AVAILABLE")
    blockers.extend([
        "TAR_MEMBER_ROOT_COMPONENT_FREQUENCY_ALONE_DOES_NOT_PROVE_FILE_CONTENT",
        "TAR_MEMBER_ROOT_COMPONENT_FREQUENCY_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
        "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
        "THREE_EXACT_UPRNS_NOT_ACQUIRED",
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
    ])

    chain_sha = sha256_bytes(canonical_bytes(chain))
    source_sha = sha256_bytes(canonical_bytes(source))
    evidence_excerpt = (
        f"prior_wave369_sha256={chain_sha};source_wave368_sha256={source_sha};"
        f"source_path_prefix_records={len(source_records)};"
        f"valid_root_component_records={len(roots)};"
        f"unique_root_components={len(frequencies)};"
        f"business_rows=0;parcel_rows=0"
    )
    runtime_evidence = {
        "source_url": (
            "repo://england_map_web/data/aays_21_slots/gas_emissions_2/"
            "wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json"
        ),
        "accessed_at": accessed_at,
        "content_sha256": sha256_bytes(evidence_excerpt.encode("utf-8")),
        "hash_scope": "normalized_runtime_receipt_utf8",
        "record_scope": (
            "Only explicit Wave368 root_component strings were counted; "
            "no archive member body or content inference."
        ),
        "relevant_record_ids_or_excerpt": evidence_excerpt,
        "supports_fields": [
            "root_component_frequency",
            "valid_root_component_record_count",
            "unique_root_component_count",
            "no_member_body_read",
        ],
        "license_or_terms_url": "https://docs.python.org/3/library/collections.html#collections.Counter",
    }

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 370,
        "accessed_at": accessed_at,
        "prior_wave": 369,
        "prior_state": chain.get("state"),
        "prior_output_sha256": chain_sha,
        "source_wave": 368,
        "source_output_sha256": source_sha,
        "assessments": (source.get("assessments") or [])[:3],
        "source_tar_member_path_prefix_count": len(source_records),
        "valid_root_component_record_count": len(roots),
        "unique_root_component_count": len(frequencies),
        "root_component_frequencies": frequencies,
        "member_body_read": False,
        "archive_extraction_performed": False,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "decision": "GHCR_BOTTLE_LAYER_TAR_MEMBER_ROOT_COMPONENT_FREQUENCIES_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": (
            "ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_FILE_EXTENSION_FREQUENCIES_OR_NO_DATA_CONTINUE"
        ),
        "source_evidence_manifest": source.get("source_evidence_manifest", []),
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }


def self_test() -> None:
    chain = {
        "slot_id": "gas_emissions_2",
        "wave": 369,
        "state": "NO_DATA_CONTINUE",
    }
    source = {
        "slot_id": "gas_emissions_2",
        "wave": 368,
        "assessments": [{"parcel_id": "parcel_30762"}],
        "tar_member_path_prefix_records": [
            {"root_component": "usr"},
            {"root_component": "usr"},
            {"root_component": "opt"},
            {"root_component": ""},
            {"path_depth": 3},
        ],
        "source_evidence_manifest": [],
    }
    out = assess(chain, source, "2026-08-03T17:22:00Z")
    assert out["valid_root_component_record_count"] == 3
    assert out["unique_root_component_count"] == 2
    assert out["root_component_frequencies"] == [
        {"root_component": "usr", "record_count": 2},
        {"root_component": "opt", "record_count": 1},
    ]
    assert out["business_rows_produced"] == 0
    assert out["parcel_rows_bound"] == 0

    empty = dict(source)
    empty["tar_member_path_prefix_records"] = []
    empty_out = assess(chain, empty, "2026-08-03T17:22:00Z")
    assert empty_out["valid_root_component_record_count"] == 0
    assert empty_out["root_component_frequencies"] == []
    assert "WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO" in empty_out["blocker"]
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior")
    parser.add_argument("--source")
    parser.add_argument("--output")
    parser.add_argument("--accessed-at")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.prior or not args.source or not args.output or not args.accessed_at:
        parser.error("--prior, --source, --output and --accessed-at are required")
    with open(args.prior, encoding="utf-8") as handle:
        chain = json.load(handle)
    with open(args.source, encoding="utf-8") as handle:
        source = json.load(handle)
    atomic_json(args.output, assess(chain, source, args.accessed_at))


if __name__ == "__main__":
    main()
