#!/usr/bin/env python3
"""Wave366: assess bounded tar-member metadata already evidenced by Wave365."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

MAX_MEMBERS = 128

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

def extract_member_metadata(prior: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for tag_record in prior.get("tag_records", []) or []:
        tag = tag_record.get("tag")
        for child in tag_record.get("children", []) or []:
            platform = child.get("platform") or {}
            for layer in child.get("layers", []) or []:
                descriptor = layer.get("descriptor") or {}
                index = layer.get("tar_member_index") or {}
                for member in index.get("members", []) or []:
                    if len(records) >= MAX_MEMBERS:
                        return records
                    normalized = {
                        "tag": tag,
                        "platform_os": platform.get("os"),
                        "platform_architecture": platform.get("architecture"),
                        "layer_digest": descriptor.get("digest"),
                        "layer_media_type": descriptor.get("mediaType"),
                        "layer_declared_size": descriptor.get("size"),
                        "member_index": member.get("index"),
                        "member_name": member.get("name"),
                        "member_size": member.get("size"),
                        "member_typeflag": member.get("typeflag"),
                        "member_header_offset": member.get("header_offset"),
                    }
                    normalized["metadata_sha256"] = sha256_bytes(
                        json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    )
                    records.append(normalized)
    return records

def assess(prior: dict[str, Any], accessed_at: str) -> dict[str, Any]:
    if prior.get("slot_id") != "gas_emissions_2" or prior.get("wave") != 365:
        raise ValueError("PRIOR_WAVE365_SLOT_MISMATCH")
    records = extract_member_metadata(prior)
    blockers: list[str] = []
    if not records:
        blockers.extend([
            "WAVE365_TAR_MEMBER_COUNT_ZERO",
            "TAR_MEMBER_METADATA_NOT_AVAILABLE",
        ])
    blockers.extend([
        "TAR_MEMBER_METADATA_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
        "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
        "THREE_EXACT_UPRNS_NOT_ACQUIRED",
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
    ])
    evidence_excerpt = (
        f"prior_output_sha256={sha256_bytes(canonical_bytes(prior))};"
        f"tar_member_metadata_records={len(records)};"
        f"business_rows=0;parcel_rows=0"
    )
    runtime_evidence = {
        "source_url": "repo://england_map_web/data/aays_21_slots/gas_emissions_2/"
                      "wave365_ghcr_bottle_layer_bounded_tar_member_index_gate_20260803.json",
        "accessed_at": accessed_at,
        "content_sha256": sha256_bytes(evidence_excerpt.encode("utf-8")),
        "hash_scope": "normalized_runtime_receipt_utf8",
        "record_scope": "Wave365 bounded tar-member metadata records only; no member bodies.",
        "relevant_record_ids_or_excerpt": evidence_excerpt,
        "supports_fields": [
            "member_name", "member_size", "member_typeflag",
            "member_header_offset", "metadata_record_count", "no_member_body"
        ],
        "license_or_terms_url": "https://docs.python.org/3/library/tarfile.html",
    }
    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 366,
        "accessed_at": accessed_at,
        "prior_wave": 365,
        "prior_state": prior.get("state"),
        "prior_output_sha256": sha256_bytes(canonical_bytes(prior)),
        "assessments": (prior.get("assessments") or [])[:3],
        "tar_member_metadata_records": records,
        "tar_member_metadata_count": len(records),
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "decision": "GHCR_BOTTLE_LAYER_TAR_MEMBER_METADATA_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": "ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_NAME_PATTERNS_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": prior.get("source_evidence_manifest", []),
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }

def self_test() -> None:
    prior = {
        "slot_id": "gas_emissions_2",
        "wave": 365,
        "state": "NO_DATA_CONTINUE",
        "assessments": [{"parcel_id": "parcel_30762"}],
        "tag_records": [{
            "tag": "1.0.1_1",
            "children": [{
                "platform": {"os": "linux", "architecture": "amd64"},
                "layers": [{
                    "descriptor": {
                        "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                        "digest": "sha256:test",
                        "size": 1000,
                    },
                    "tar_member_index": {
                        "members": [
                            {"index": 0, "name": "bin/overturemaps", "size": 123,
                             "typeflag": "0", "header_offset": 0},
                            {"index": 1, "name": "share/LICENSE", "size": 456,
                             "typeflag": "0", "header_offset": 1024},
                        ]
                    },
                }],
            }],
        }],
        "source_evidence_manifest": [],
    }
    out = assess(prior, "2026-08-03T14:02:00Z")
    assert out["tar_member_metadata_count"] == 2
    assert out["tar_member_metadata_records"][0]["member_name"] == "bin/overturemaps"
    assert out["business_rows_produced"] == 0
    empty = dict(prior)
    empty["tag_records"] = []
    empty_out = assess(empty, "2026-08-03T14:02:00Z")
    assert empty_out["tar_member_metadata_count"] == 0
    assert "WAVE365_TAR_MEMBER_COUNT_ZERO" in empty_out["blocker"]
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
