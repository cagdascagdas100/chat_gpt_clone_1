#!/usr/bin/env python3
"""Wave373: count bounded tar-member stem metadata without reading member bodies."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import PurePosixPath, Path
from typing import Any

MAX_RECORDS = 128
MAX_STEM_LENGTH = 256


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


def normalize_stem(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or value in {".", ".."} or len(value) > MAX_STEM_LENGTH:
        return None
    if "/" in value or "\\" in value:
        return None
    return value


def basename_from_record(record: Any) -> tuple[str | None, str | None]:
    if not isinstance(record, dict):
        return None, None
    explicit_basename = record.get("basename")
    if isinstance(explicit_basename, str) and explicit_basename.strip():
        name = PurePosixPath(explicit_basename.strip().replace("\\", "/")).name
        if name and name not in {".", ".."}:
            return name, "derived_from_explicit_basename"

    parts = record.get("path_parts")
    if isinstance(parts, list) and parts and all(isinstance(part, str) for part in parts):
        name = PurePosixPath(parts[-1].replace("\\", "/")).name
        if name and name not in {".", ".."}:
            return name, "derived_from_path_parts"

    for key in ("member_name", "normalized_path", "path"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            name = PurePosixPath(value.replace("\\", "/")).name
            if name and name not in {".", ".."}:
                return name, f"derived_from_{key}"
    return None, None


def stem_from_record(record: Any) -> tuple[str | None, str | None]:
    if not isinstance(record, dict):
        return None, None
    explicit = normalize_stem(record.get("stem"))
    if explicit:
        return explicit, "explicit_stem"

    basename, basename_provenance = basename_from_record(record)
    if basename is None or basename_provenance is None:
        return None, None
    derived = normalize_stem(PurePosixPath(basename).stem)
    if derived:
        return derived, basename_provenance.replace("derived_from_", "stem_from_")
    return None, None


def assess(prior: dict[str, Any], source: dict[str, Any], accessed_at: str) -> dict[str, Any]:
    if prior.get("slot_id") != "gas_emissions_2" or prior.get("wave") != 372:
        raise ValueError("PRIOR_WAVE372_SLOT_MISMATCH")
    if source.get("slot_id") != "gas_emissions_2" or source.get("wave") != 368:
        raise ValueError("SOURCE_WAVE368_SLOT_MISMATCH")

    source_records = source.get("tar_member_path_prefix_records", []) or []
    bounded_records = source_records[:MAX_RECORDS]
    extracted: list[tuple[str, str]] = []
    for record in bounded_records:
        stem, provenance = stem_from_record(record)
        if stem is not None and provenance is not None:
            extracted.append((stem, provenance))

    counts = Counter(stem for stem, _ in extracted)
    provenance_counts = Counter(provenance for _, provenance in extracted)
    frequencies = [
        {"stem": stem, "record_count": count}
        for stem, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    blockers: list[str] = []
    if not source_records:
        blockers.append("WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO")
    if not extracted:
        blockers.append("TAR_MEMBER_STEMS_NOT_AVAILABLE")
    blockers.extend([
        "TAR_MEMBER_STEM_FREQUENCY_ALONE_DOES_NOT_PROVE_FILE_CONTENT",
        "TAR_MEMBER_STEM_FREQUENCY_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
        "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
        "THREE_EXACT_UPRNS_NOT_ACQUIRED",
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
    ])

    prior_sha = sha256_bytes(canonical_bytes(prior))
    source_sha = sha256_bytes(canonical_bytes(source))
    excerpt = (
        f"prior_wave372_sha256={prior_sha};source_wave368_sha256={source_sha};"
        f"source_path_prefix_records={len(source_records)};"
        f"valid_stem_records={len(extracted)};"
        f"unique_stems={len(frequencies)};"
        "business_rows=0;parcel_rows=0"
    )
    runtime_evidence = {
        "source_url": (
            "repo://england_map_web/data/aays_21_slots/gas_emissions_2/"
            "wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json"
        ),
        "accessed_at": accessed_at,
        "content_sha256": sha256_bytes(excerpt.encode("utf-8")),
        "hash_scope": "normalized_runtime_receipt_utf8",
        "record_scope": (
            "Only explicit stem values or PurePath.stem values derived from bounded Wave368 "
            "metadata were counted; no archive member body was read."
        ),
        "relevant_record_ids_or_excerpt": excerpt,
        "supports_fields": [
            "stem_frequencies",
            "valid_stem_record_count",
            "unique_stem_count",
            "stem_provenance_counts",
            "no_member_body_read",
        ],
        "license_or_terms_url": "https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.stem",
    }

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 373,
        "accessed_at": accessed_at,
        "prior_wave": 372,
        "prior_state": prior.get("state"),
        "prior_output_sha256": prior_sha,
        "source_wave": 368,
        "source_output_sha256": source_sha,
        "assessments": (source.get("assessments") or [])[:3],
        "source_tar_member_path_prefix_count": len(source_records),
        "valid_stem_record_count": len(extracted),
        "unique_stem_count": len(frequencies),
        "stem_frequencies": frequencies,
        "stem_provenance_counts": [
            {"provenance": provenance, "record_count": count}
            for provenance, count in sorted(provenance_counts.items())
        ],
        "member_body_read": False,
        "archive_extraction_performed": False,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "decision": "GHCR_BOTTLE_LAYER_TAR_MEMBER_STEM_FREQUENCIES_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": (
            "ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_SUFFIX_CHAIN_FREQUENCIES_OR_NO_DATA_CONTINUE"
        ),
        "source_evidence_manifest": source.get("source_evidence_manifest", []),
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }


def self_test() -> None:
    prior = {"slot_id": "gas_emissions_2", "wave": 372, "state": "NO_DATA_CONTINUE"}
    source = {
        "slot_id": "gas_emissions_2",
        "wave": 368,
        "assessments": [{"parcel_id": "parcel_30762"}],
        "tar_member_path_prefix_records": [
            {"stem": "explicit"},
            {"basename": "data.json"},
            {"path_parts": ["usr", "share", "data.json"]},
            {"member_name": "opt/maps/buildings.parquet"},
            {"normalized_path": "tmp/archive.tar.gz"},
            {"path": r"etc\config.yaml"},
            {"basename": " .. "},
            {"path": "/"},
        ],
        "source_evidence_manifest": [],
    }
    out = assess(prior, source, "2026-08-03T19:50:00Z")
    assert out["valid_stem_record_count"] == 6
    assert out["unique_stem_count"] == 5
    assert out["stem_frequencies"] == [
        {"stem": "data", "record_count": 2},
        {"stem": "archive.tar", "record_count": 1},
        {"stem": "buildings", "record_count": 1},
        {"stem": "config", "record_count": 1},
        {"stem": "explicit", "record_count": 1},
    ]
    assert out["business_rows_produced"] == 0
    assert out["parcel_rows_bound"] == 0

    empty = dict(source)
    empty["tar_member_path_prefix_records"] = []
    empty_out = assess(prior, empty, "2026-08-03T19:50:00Z")
    assert empty_out["valid_stem_record_count"] == 0
    assert empty_out["stem_frequencies"] == []
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
        prior = json.load(handle)
    with open(args.source, encoding="utf-8") as handle:
        source = json.load(handle)
    atomic_json(args.output, assess(prior, source, args.accessed_at))


if __name__ == "__main__":
    main()
