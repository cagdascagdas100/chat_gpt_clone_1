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

TABULAR_SUFFIX_TO_FAMILY = {
    ".arrow": "apache_arrow_ipc",
    ".csv": "csv",
    ".feather": "apache_arrow_feather",
    ".orc": "apache_orc",
    ".parquet": "apache_parquet",
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


def tabular_suffix(record: object) -> tuple[str | None, str | None, str | None]:
    if not isinstance(record, dict):
        return None, None, None

    for key in ("tabular_suffix", "suffix"):
        explicit = valid_suffix_token(record.get(key))
        if explicit in TABULAR_SUFFIX_TO_FAMILY:
            return explicit, TABULAR_SUFFIX_TO_FAMILY[explicit], key

    for key in ("suffixes", "suffix_chain", "suffix_tokens"):
        suffixes = normalize_suffixes(record.get(key))
        if suffixes and suffixes[-1] in TABULAR_SUFFIX_TO_FAMILY:
            suffix = suffixes[-1]
            return suffix, TABULAR_SUFFIX_TO_FAMILY[suffix], key

    name, provenance = member_basename(record)
    if name:
        suffixes = normalize_suffixes(list(PurePosixPath(name).suffixes))
        if suffixes and suffixes[-1] in TABULAR_SUFFIX_TO_FAMILY:
            suffix = suffixes[-1]
            return suffix, TABULAR_SUFFIX_TO_FAMILY[suffix], f"derived_from_{provenance}"

    return None, None, None


def assess(prior: dict, source: dict, accessed_at: str) -> dict:
    if prior.get("slot_id") != "gas_emissions_2" or prior.get("wave") != 379:
        raise ValueError("PRIOR_WAVE379_SLOT_MISMATCH")
    if source.get("slot_id") != "gas_emissions_2" or source.get("wave") != 368:
        raise ValueError("SOURCE_WAVE368_SLOT_MISMATCH")

    records = (source.get("tar_member_path_prefix_records") or [])[:MAX_RECORDS]
    observations = [tabular_suffix(record) for record in records]
    observations = [
        (suffix, family, provenance)
        for suffix, family, provenance in observations
        if suffix and family and provenance
    ]
    suffix_counts = Counter(suffix for suffix, _, _ in observations)
    family_counts = Counter(family for _, family, _ in observations)
    provenance_counts = Counter(provenance for _, _, provenance in observations)
    suffix_frequencies = [
        {
            "tabular_suffix": suffix,
            "tabular_family": TABULAR_SUFFIX_TO_FAMILY[suffix],
            "record_count": count,
        }
        for suffix, count in sorted(suffix_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    blockers: list[str] = []
    if not records:
        blockers.append("WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO")
    if not suffix_counts:
        blockers.append("TAR_MEMBER_TABULAR_SUFFIXES_NOT_AVAILABLE")
    blockers.extend(
        [
            "TAR_MEMBER_TABULAR_SUFFIX_FREQUENCY_ALONE_DOES_NOT_PROVE_FILE_CONTENT",
            "TAR_MEMBER_TABULAR_SUFFIX_FREQUENCY_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
            "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
            "THREE_EXACT_UPRNS_NOT_ACQUIRED",
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
        ]
    )

    prior_sha = sha256_bytes(canonical_bytes(prior))
    source_sha = sha256_bytes(canonical_bytes(source))
    excerpt = (
        f"prior_wave379_sha256={prior_sha};source_wave368_sha256={source_sha};"
        f"source_path_prefix_records={len(records)};records_with_tabular_suffixes={len(observations)};"
        f"unique_tabular_suffixes={len(suffix_frequencies)};business_rows=0;parcel_rows=0"
    )
    runtime_evidence = {
        "source_url": "repo://england_map_web/data/aays_21_slots/gas_emissions_2/wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json",
        "accessed_at": accessed_at,
        "content_sha256": sha256_bytes(excerpt.encode("utf-8")),
        "hash_scope": "normalized_runtime_receipt_utf8",
        "record_scope": "Only explicit suffix metadata or PurePath.suffixes-derived terminal tabular suffixes from bounded Wave368 metadata were counted; no archive member body was read.",
        "relevant_record_ids_or_excerpt": excerpt,
        "supports_fields": [
            "tabular_suffix_frequencies",
            "tabular_family_frequencies",
            "records_with_tabular_suffixes",
            "unique_tabular_suffix_count",
            "tabular_suffix_provenance_counts",
            "no_member_body_read",
        ],
        "license_or_terms_url": "https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.suffixes",
    }

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 380,
        "accessed_at": accessed_at,
        "prior_wave": 379,
        "prior_state": prior.get("state"),
        "prior_output_sha256": prior_sha,
        "source_wave": 368,
        "source_output_sha256": source_sha,
        "assessments": (source.get("assessments") or [])[:3],
        "source_tar_member_path_prefix_count": len(records),
        "records_with_tabular_suffixes": len(observations),
        "unique_tabular_suffix_count": len(suffix_frequencies),
        "tabular_suffix_frequencies": suffix_frequencies,
        "tabular_family_frequencies": [
            {"tabular_family": key, "record_count": value}
            for key, value in sorted(family_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "tabular_suffix_provenance_counts": [
            {"provenance": key, "record_count": value}
            for key, value in sorted(provenance_counts.items())
        ],
        "tabular_suffix_allowlist": [
            {"suffix": suffix, "tabular_family": family}
            for suffix, family in sorted(TABULAR_SUFFIX_TO_FAMILY.items())
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
        "decision": "GHCR_BOTTLE_LAYER_TAR_MEMBER_TABULAR_SUFFIX_FREQUENCIES_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": "ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_TEXT_SUFFIX_FREQUENCIES_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": source.get("source_evidence_manifest", []),
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }


def self_test() -> None:
    prior = {"slot_id": "gas_emissions_2", "wave": 379, "state": "NO_DATA_CONTINUE"}
    source = {
        "slot_id": "gas_emissions_2",
        "wave": 368,
        "tar_member_path_prefix_records": [
            {"tabular_suffix": ".csv"},
            {"suffix": ".parquet"},
            {"suffixes": [".feather"]},
            {"suffix_chain": [".arrow"]},
            {"suffix_tokens": [".orc"]},
            {"basename": "features.csv"},
            {"path_parts": ["x", "features.parquet"]},
            {"member_name": "x/table.feather"},
            {"normalized_path": "x/table.arrow"},
            {"path": r"x\table.orc"},
            {"basename": "generic.tsv"},
            {"suffix": ".json"},
            {"tabular_suffix": "bad"},
        ],
    }
    output = assess(prior, source, "2026-08-04T01:38:00Z")
    assert output["records_with_tabular_suffixes"] == 10
    assert output["unique_tabular_suffix_count"] == 5
    assert output["tabular_suffix_frequencies"][0]["record_count"] == 2
    assert output["business_rows_produced"] == output["parcel_rows_bound"] == 0
    assert all(item["tabular_suffix"] != ".tsv" for item in output["tabular_suffix_frequencies"])
    empty = dict(source)
    empty["tar_member_path_prefix_records"] = []
    zero = assess(prior, empty, "2026-08-04T01:38:00Z")
    assert zero["tabular_suffix_frequencies"] == []
    assert "WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO" in zero["blocker"]
    assert "TAR_MEMBER_TABULAR_SUFFIXES_NOT_AVAILABLE" in zero["blocker"]
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
