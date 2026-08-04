#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

MAX_RECORDS = 128
MAX_SUFFIXES = 8
MAX_TOKEN_LENGTH = 32

ARCHIVE_SUFFIX_TO_FORMAT = {
    ".tar": "tar",
    ".tar.gz": "tar+gzip",
    ".tgz": "tar+gzip",
    ".tar.gzip": "tar+gzip",
    ".tar.bz2": "tar+bzip2",
    ".tbz": "tar+bzip2",
    ".tbz2": "tar+bzip2",
    ".tar.xz": "tar+xz",
    ".txz": "tar+xz",
    ".tar.lzma": "tar+lzma",
    ".tlz": "tar+lzma",
    ".tar.zst": "tar+zstd",
    ".tar.zstd": "tar+zstd",
    ".tzst": "tar+zstd",
}

def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def atomic_write_json(path: str, value: object) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as handle:
        handle.write(canonical_bytes(value))
        temporary = handle.name
    os.replace(temporary, output)

def valid_suffix_token(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    token = value.strip().lower()
    if (
        not token.startswith(".")
        or token in {".", ".."}
        or "/" in token
        or "\\" in token
        or len(token) > MAX_TOKEN_LENGTH
    ):
        return None
    return token

def normalize_suffixes(value: object) -> list[str]:
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_SUFFIXES:
        return []
    normalized: list[str] = []
    for item in value:
        token = valid_suffix_token(item)
        if token is None:
            return []
        normalized.append(token)
    return normalized

def member_basename(record: object) -> tuple[str | None, str | None]:
    if not isinstance(record, dict):
        return None, None
    explicit = record.get("basename")
    if isinstance(explicit, str) and explicit.strip():
        name = PurePosixPath(explicit.strip().replace("\\", "/")).name
        if name not in {"", ".", ".."}:
            return name, "explicit_basename"
    parts = record.get("path_parts")
    if isinstance(parts, list) and parts and all(isinstance(item, str) for item in parts):
        name = PurePosixPath(parts[-1].replace("\\", "/")).name
        if name not in {"", ".", ".."}:
            return name, "path_parts"
    for key in ("member_name", "normalized_path", "path"):
        candidate = record.get(key)
        if isinstance(candidate, str) and candidate.strip():
            name = PurePosixPath(candidate.replace("\\", "/")).name
            if name not in {"", ".", ".."}:
                return name, key
    return None, None

def classify_suffixes(suffixes: list[str]) -> str | None:
    if not suffixes:
        return None
    candidates: list[str] = []
    if len(suffixes) >= 2:
        candidates.append("".join(suffixes[-2:]))
    candidates.append(suffixes[-1])
    for candidate in candidates:
        if candidate in ARCHIVE_SUFFIX_TO_FORMAT:
            return candidate
    return None

def archive_suffix(record: object) -> tuple[str | None, str | None, str | None]:
    if not isinstance(record, dict):
        return None, None, None

    explicit = valid_suffix_token(record.get("archive_suffix"))
    if explicit in ARCHIVE_SUFFIX_TO_FORMAT:
        return explicit, ARCHIVE_SUFFIX_TO_FORMAT[explicit], "archive_suffix"

    explicit_chain = record.get("archive_suffix_chain")
    suffixes = normalize_suffixes(explicit_chain)
    classified = classify_suffixes(suffixes)
    if classified:
        return classified, ARCHIVE_SUFFIX_TO_FORMAT[classified], "archive_suffix_chain"

    for key in ("suffixes", "suffix_chain", "suffix_tokens"):
        suffixes = normalize_suffixes(record.get(key))
        classified = classify_suffixes(suffixes)
        if classified:
            return classified, ARCHIVE_SUFFIX_TO_FORMAT[classified], key

    name, provenance = member_basename(record)
    if name:
        suffixes = normalize_suffixes(list(PurePosixPath(name).suffixes))
        classified = classify_suffixes(suffixes)
        if classified:
            return classified, ARCHIVE_SUFFIX_TO_FORMAT[classified], f"derived_from_{provenance}"

    return None, None, None

def assess(prior: dict, source: dict, accessed_at: str) -> dict:
    if prior.get("slot_id") != "gas_emissions_2" or prior.get("wave") != 377:
        raise ValueError("PRIOR_WAVE377_SLOT_MISMATCH")
    if source.get("slot_id") != "gas_emissions_2" or source.get("wave") != 368:
        raise ValueError("SOURCE_WAVE368_SLOT_MISMATCH")

    records = (source.get("tar_member_path_prefix_records") or [])[:MAX_RECORDS]
    observations = [archive_suffix(record) for record in records]
    observations = [
        (suffix, archive_format, provenance)
        for suffix, archive_format, provenance in observations
        if suffix and archive_format and provenance
    ]
    suffix_counts = Counter(suffix for suffix, _, _ in observations)
    format_counts = Counter(archive_format for _, archive_format, _ in observations)
    provenance_counts = Counter(provenance for _, _, provenance in observations)
    suffix_frequencies = [
        {
            "archive_suffix": suffix,
            "archive_format": ARCHIVE_SUFFIX_TO_FORMAT[suffix],
            "record_count": count,
        }
        for suffix, count in sorted(suffix_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    blockers: list[str] = []
    if not records:
        blockers.append("WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO")
    if not suffix_counts:
        blockers.append("TAR_MEMBER_ARCHIVE_SUFFIXES_NOT_AVAILABLE")
    blockers.extend(
        [
            "TAR_MEMBER_ARCHIVE_SUFFIX_FREQUENCY_ALONE_DOES_NOT_PROVE_FILE_CONTENT",
            "TAR_MEMBER_ARCHIVE_SUFFIX_FREQUENCY_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
            "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
            "THREE_EXACT_UPRNS_NOT_ACQUIRED",
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
        ]
    )

    prior_sha = sha256_bytes(canonical_bytes(prior))
    source_sha = sha256_bytes(canonical_bytes(source))
    excerpt = (
        f"prior_wave377_sha256={prior_sha};source_wave368_sha256={source_sha};"
        f"source_path_prefix_records={len(records)};records_with_archive_suffixes={len(observations)};"
        f"unique_archive_suffixes={len(suffix_frequencies)};business_rows=0;parcel_rows=0"
    )
    runtime_evidence = {
        "source_url": "repo://england_map_web/data/aays_21_slots/gas_emissions_2/wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json",
        "accessed_at": accessed_at,
        "content_sha256": sha256_bytes(excerpt.encode("utf-8")),
        "hash_scope": "normalized_runtime_receipt_utf8",
        "record_scope": "Only explicit suffix metadata or PurePath.suffixes-derived terminal archive suffix chains from bounded Wave368 metadata were counted; no archive member body was read.",
        "relevant_record_ids_or_excerpt": excerpt,
        "supports_fields": [
            "archive_suffix_frequencies",
            "archive_format_frequencies",
            "records_with_archive_suffixes",
            "unique_archive_suffix_count",
            "archive_suffix_provenance_counts",
            "no_member_body_read",
        ],
        "license_or_terms_url": "https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.suffixes",
    }

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 378,
        "accessed_at": accessed_at,
        "prior_wave": 377,
        "prior_state": prior.get("state"),
        "prior_output_sha256": prior_sha,
        "source_wave": 368,
        "source_output_sha256": source_sha,
        "assessments": (source.get("assessments") or [])[:3],
        "source_tar_member_path_prefix_count": len(records),
        "records_with_archive_suffixes": len(observations),
        "unique_archive_suffix_count": len(suffix_frequencies),
        "archive_suffix_frequencies": suffix_frequencies,
        "archive_format_frequencies": [
            {"archive_format": key, "record_count": value}
            for key, value in sorted(format_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "archive_suffix_provenance_counts": [
            {"provenance": key, "record_count": value}
            for key, value in sorted(provenance_counts.items())
        ],
        "archive_suffix_allowlist": [
            {"suffix": suffix, "archive_format": archive_format}
            for suffix, archive_format in sorted(ARCHIVE_SUFFIX_TO_FORMAT.items())
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
        "decision": "GHCR_BOTTLE_LAYER_TAR_MEMBER_ARCHIVE_SUFFIX_FREQUENCIES_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": "ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_GEODATA_SUFFIX_FREQUENCIES_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": source.get("source_evidence_manifest", []),
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }

def self_test() -> None:
    prior = {"slot_id": "gas_emissions_2", "wave": 377, "state": "NO_DATA_CONTINUE"}
    source = {
        "slot_id": "gas_emissions_2",
        "wave": 368,
        "tar_member_path_prefix_records": [
            {"archive_suffix": ".tar"},
            {"archive_suffix_chain": [".tar", ".gz"]},
            {"suffixes": [".tar", ".bz2"]},
            {"suffix_chain": [".tar", ".xz"]},
            {"suffix_tokens": [".tar", ".zst"]},
            {"basename": "archive.tgz"},
            {"path_parts": ["x", "dataset.tbz2"]},
            {"member_name": "x/data.txz"},
            {"normalized_path": "x/data.tzst"},
            {"path": r"x\single.tar"},
            {"basename": "single.json"},
            {"suffixes": [".zip"]},
            {"archive_suffix": "bad"},
        ],
    }
    output = assess(prior, source, "2026-08-03T23:58:00Z")
    assert output["records_with_archive_suffixes"] == 10
    assert output["unique_archive_suffix_count"] == 9
    assert output["archive_suffix_frequencies"][0]["record_count"] == 2
    assert output["business_rows_produced"] == output["parcel_rows_bound"] == 0
    empty = dict(source)
    empty["tar_member_path_prefix_records"] = []
    zero = assess(prior, empty, "2026-08-03T23:58:00Z")
    assert zero["archive_suffix_frequencies"] == []
    assert "WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO" in zero["blocker"]
    assert "TAR_MEMBER_ARCHIVE_SUFFIXES_NOT_AVAILABLE" in zero["blocker"]
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
    if not all((args.prior, args.source, args.output, args.accessed_at)):
        parser.error("required arguments missing")
    with open(args.prior, encoding="utf-8") as handle:
        prior = json.load(handle)
    with open(args.source, encoding="utf-8") as handle:
        source = json.load(handle)
    atomic_write_json(args.output, assess(prior, source, args.accessed_at))

if __name__ == "__main__":
    main()
