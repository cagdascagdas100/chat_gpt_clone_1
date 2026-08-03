#!/usr/bin/env python3
"""Wave371: count bounded tar-member file-extension metadata without reading member bodies."""
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
MAX_EXTENSION_LENGTH = 32


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


def normalize_extension(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip().lower()
    if not value:
        return None
    if not value.startswith("."):
        value = "." + value
    if value == "." or len(value) > MAX_EXTENSION_LENGTH:
        return None
    if "/" in value or "\\" in value or any(ch.isspace() for ch in value):
        return None
    return value


def path_name_from_record(record: dict[str, Any]) -> str | None:
    parts = record.get("path_parts")
    if isinstance(parts, list) and parts and all(isinstance(part, str) for part in parts):
        return parts[-1]
    for key in ("member_name", "normalized_path", "path"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.replace("\\", "/").rsplit("/", 1)[-1]
    return None


def file_extension(record: Any) -> tuple[str | None, str | None]:
    if not isinstance(record, dict):
        return None, None
    explicit = normalize_extension(record.get("file_extension"))
    if explicit:
        return explicit, "explicit_file_extension"
    name = path_name_from_record(record)
    if not name:
        return None, None
    derived = normalize_extension(PurePosixPath(name).suffix)
    if derived:
        return derived, "derived_from_member_name_metadata"
    return None, None


def assess(prior: dict[str, Any], source: dict[str, Any], accessed_at: str) -> dict[str, Any]:
    if prior.get("slot_id") != "gas_emissions_2" or prior.get("wave") != 370:
        raise ValueError("PRIOR_WAVE370_SLOT_MISMATCH")
    if source.get("slot_id") != "gas_emissions_2" or source.get("wave") != 368:
        raise ValueError("SOURCE_WAVE368_SLOT_MISMATCH")

    source_records = source.get("tar_member_path_prefix_records", []) or []
    bounded_records = source_records[:MAX_RECORDS]
    extracted: list[tuple[str, str]] = []
    for record in bounded_records:
        extension, provenance = file_extension(record)
        if extension is not None and provenance is not None:
            extracted.append((extension, provenance))

    counts = Counter(extension for extension, _ in extracted)
    provenance_counts = Counter(provenance for _, provenance in extracted)
    frequencies = [
        {"file_extension": extension, "record_count": count}
        for extension, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    blockers: list[str] = []
    if not source_records:
        blockers.append("WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO")
    if not extracted:
        blockers.append("TAR_MEMBER_FILE_EXTENSIONS_NOT_AVAILABLE")
    blockers.extend([
        "TAR_MEMBER_FILE_EXTENSION_FREQUENCY_ALONE_DOES_NOT_PROVE_FILE_CONTENT",
        "TAR_MEMBER_FILE_EXTENSION_FREQUENCY_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
        "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
        "THREE_EXACT_UPRNS_NOT_ACQUIRED",
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
    ])

    prior_sha = sha256_bytes(canonical_bytes(prior))
    source_sha = sha256_bytes(canonical_bytes(source))
    excerpt = (
        f"prior_wave370_sha256={prior_sha};source_wave368_sha256={source_sha};"
        f"source_path_prefix_records={len(source_records)};"
        f"valid_extension_records={len(extracted)};"
        f"unique_extensions={len(frequencies)};"
        f"business_rows=0;parcel_rows=0"
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
            "Only explicit file_extension values or filename suffixes from bounded Wave368 "
            "path metadata were counted; no archive member body was read."
        ),
        "relevant_record_ids_or_excerpt": excerpt,
        "supports_fields": [
            "file_extension_frequencies",
            "valid_file_extension_record_count",
            "unique_file_extension_count",
            "extension_provenance_counts",
            "no_member_body_read",
        ],
        "license_or_terms_url": "https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.suffix",
    }

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 371,
        "accessed_at": accessed_at,
        "prior_wave": 370,
        "prior_state": prior.get("state"),
        "prior_output_sha256": prior_sha,
        "source_wave": 368,
        "source_output_sha256": source_sha,
        "assessments": (source.get("assessments") or [])[:3],
        "source_tar_member_path_prefix_count": len(source_records),
        "valid_file_extension_record_count": len(extracted),
        "unique_file_extension_count": len(frequencies),
        "file_extension_frequencies": frequencies,
        "extension_provenance_counts": [
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
        "decision": "GHCR_BOTTLE_LAYER_TAR_MEMBER_FILE_EXTENSION_FREQUENCIES_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": (
            "ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_BASENAME_FREQUENCIES_OR_NO_DATA_CONTINUE"
        ),
        "source_evidence_manifest": source.get("source_evidence_manifest", []),
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }


def self_test() -> None:
    prior = {"slot_id": "gas_emissions_2", "wave": 370, "state": "NO_DATA_CONTINUE"}
    source = {
        "slot_id": "gas_emissions_2",
        "wave": 368,
        "assessments": [{"parcel_id": "parcel_30762"}],
        "tar_member_path_prefix_records": [
            {"file_extension": "JSON"},
            {"path_parts": ["usr", "share", "data.json"]},
            {"member_name": "opt/maps/buildings.parquet"},
            {"normalized_path": "tmp/archive.tar.gz"},
            {"path": "README"},
            {"file_extension": "   "},
        ],
        "source_evidence_manifest": [],
    }
    out = assess(prior, source, "2026-08-03T18:11:00Z")
    assert out["valid_file_extension_record_count"] == 4
    assert out["unique_file_extension_count"] == 3
    assert out["file_extension_frequencies"] == [
        {"file_extension": ".json", "record_count": 2},
        {"file_extension": ".gz", "record_count": 1},
        {"file_extension": ".parquet", "record_count": 1},
    ]
    assert out["extension_provenance_counts"] == [
        {"provenance": "derived_from_member_name_metadata", "record_count": 3},
        {"provenance": "explicit_file_extension", "record_count": 1},
    ]
    assert out["business_rows_produced"] == 0
    assert out["parcel_rows_bound"] == 0

    empty = dict(source)
    empty["tar_member_path_prefix_records"] = []
    empty_out = assess(prior, empty, "2026-08-03T18:11:00Z")
    assert empty_out["valid_file_extension_record_count"] == 0
    assert empty_out["file_extension_frequencies"] == []
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
