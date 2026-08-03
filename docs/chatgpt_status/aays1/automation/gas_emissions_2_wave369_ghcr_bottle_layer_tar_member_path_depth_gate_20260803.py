#!/usr/bin/env python3
"""Wave369: summarize bounded path-depth evidence from Wave368 records only."""
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
MAX_REPORTED_DEPTH = 32


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


def normalize_depth(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and 0 <= value <= MAX_REPORTED_DEPTH:
        return value
    return None


def assess(prior: dict[str, Any], accessed_at: str) -> dict[str, Any]:
    if prior.get("slot_id") != "gas_emissions_2" or prior.get("wave") != 368:
        raise ValueError("PRIOR_WAVE368_SLOT_MISMATCH")

    source_records = prior.get("tar_member_path_prefix_records", []) or []
    bounded_records = source_records[:MAX_RECORDS]
    depths = [depth for record in bounded_records if (depth := normalize_depth(record.get("path_depth"))) is not None]
    histogram_counter = Counter(depths)
    histogram = [
        {"path_depth": depth, "record_count": histogram_counter[depth]}
        for depth in sorted(histogram_counter)
    ]
    shallow_count = sum(1 for depth in depths if depth <= 2)
    medium_count = sum(1 for depth in depths if 3 <= depth <= 5)
    deep_count = sum(1 for depth in depths if depth >= 6)
    min_depth = min(depths) if depths else None
    max_depth = max(depths) if depths else None

    blockers: list[str] = []
    if not source_records:
        blockers.append("WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO")
    if not depths:
        blockers.append("TAR_MEMBER_PATH_DEPTHS_NOT_AVAILABLE")
    blockers.extend([
        "TAR_MEMBER_PATH_DEPTH_ALONE_DOES_NOT_PROVE_FILE_CONTENT",
        "TAR_MEMBER_PATH_DEPTH_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
        "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
        "THREE_EXACT_UPRNS_NOT_ACQUIRED",
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
    ])

    prior_sha = sha256_bytes(canonical_bytes(prior))
    evidence_excerpt = (
        f"prior_output_sha256={prior_sha};source_path_prefix_records={len(source_records)};"
        f"valid_path_depth_records={len(depths)};histogram_bins={len(histogram)};"
        f"min_depth={min_depth};max_depth={max_depth};shallow={shallow_count};"
        f"medium={medium_count};deep={deep_count};business_rows=0;parcel_rows=0"
    )
    runtime_evidence = {
        "source_url": "repo://england_map_web/data/aays_21_slots/gas_emissions_2/"
                      "wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json",
        "accessed_at": accessed_at,
        "content_sha256": sha256_bytes(evidence_excerpt.encode("utf-8")),
        "hash_scope": "normalized_runtime_receipt_utf8",
        "record_scope": "Wave368 acquired path-depth integers only; no archive member body or content inference.",
        "relevant_record_ids_or_excerpt": evidence_excerpt,
        "supports_fields": [
            "path_depth_histogram", "minimum_path_depth", "maximum_path_depth",
            "shallow_path_count", "medium_path_count", "deep_path_count",
            "no_member_body_read",
        ],
        "license_or_terms_url": "https://docs.python.org/3/library/collections.html#collections.Counter",
    }

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 369,
        "accessed_at": accessed_at,
        "prior_wave": 368,
        "prior_state": prior.get("state"),
        "prior_output_sha256": prior_sha,
        "assessments": (prior.get("assessments") or [])[:3],
        "source_tar_member_path_prefix_count": len(source_records),
        "valid_path_depth_record_count": len(depths),
        "path_depth_histogram": histogram,
        "minimum_path_depth": min_depth,
        "maximum_path_depth": max_depth,
        "shallow_path_count": shallow_count,
        "medium_path_count": medium_count,
        "deep_path_count": deep_count,
        "member_body_read": False,
        "archive_extraction_performed": False,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "decision": "GHCR_BOTTLE_LAYER_TAR_MEMBER_PATH_DEPTH_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": "ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_ROOT_COMPONENT_FREQUENCIES_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": prior.get("source_evidence_manifest", []),
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }


def self_test() -> None:
    prior = {
        "slot_id": "gas_emissions_2",
        "wave": 368,
        "state": "NO_DATA_CONTINUE",
        "assessments": [{"parcel_id": "parcel_30762"}],
        "tar_member_path_prefix_records": [
            {"member_name": "bin/overturemaps", "path_depth": 2},
            {"member_name": "share/overture/buildings/a.parquet", "path_depth": 4},
            {"member_name": "a/b/c/d/e/f", "path_depth": 6},
            {"member_name": "invalid", "path_depth": "1"},
        ],
        "source_evidence_manifest": [],
    }
    out = assess(prior, "2026-08-03T16:32:00Z")
    assert out["valid_path_depth_record_count"] == 3
    assert out["path_depth_histogram"] == [
        {"path_depth": 2, "record_count": 1},
        {"path_depth": 4, "record_count": 1},
        {"path_depth": 6, "record_count": 1},
    ]
    assert out["minimum_path_depth"] == 2
    assert out["maximum_path_depth"] == 6
    assert out["shallow_path_count"] == 1
    assert out["medium_path_count"] == 1
    assert out["deep_path_count"] == 1
    assert out["business_rows_produced"] == 0

    empty = dict(prior)
    empty["tar_member_path_prefix_records"] = []
    empty_out = assess(empty, "2026-08-03T16:32:00Z")
    assert empty_out["valid_path_depth_record_count"] == 0
    assert empty_out["path_depth_histogram"] == []
    assert "WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO" in empty_out["blocker"]
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
