#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from collections import Counter
from pathlib import PurePosixPath, Path

MAX_RECORDS = 128
MAX_SUFFIXES = 8
MAX_TOKEN_LEN = 32

def cbytes(obj):
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def atomic(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=p.parent, delete=False) as f:
        f.write(cbytes(obj))
        tmp = f.name
    os.replace(tmp, p)

def valid_token(value):
    if not isinstance(value, str):
        return None
    token = value.strip().lower()
    if (
        not token.startswith(".")
        or token in {".", ".."}
        or "/" in token
        or "\\" in token
        or len(token) > MAX_TOKEN_LEN
    ):
        return None
    return token

def normalize_tokens(value):
    if isinstance(value, str):
        token = valid_token(value)
        return [token] if token else []
    if not isinstance(value, list) or len(value) > MAX_SUFFIXES:
        return []
    out = []
    for item in value:
        token = valid_token(item)
        if not token:
            return []
        out.append(token)
    return out

def member_name(record):
    if not isinstance(record, dict):
        return None, None
    value = record.get("basename")
    if isinstance(value, str) and value.strip():
        name = PurePosixPath(value.strip().replace("\\", "/")).name
        if name not in {"", ".", ".."}:
            return name, "explicit_basename"
    parts = record.get("path_parts")
    if isinstance(parts, list) and parts and all(isinstance(x, str) for x in parts):
        name = PurePosixPath(parts[-1].replace("\\", "/")).name
        if name not in {"", ".", ".."}:
            return name, "path_parts"
    for key in ("member_name", "normalized_path", "path"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            name = PurePosixPath(value.replace("\\", "/")).name
            if name not in {"", ".", ".."}:
                return name, key
    return None, None

def tokens(record):
    if not isinstance(record, dict):
        return [], None
    for key in ("suffix_tokens", "suffixes", "suffix_chain"):
        normalized = normalize_tokens(record.get(key))
        if normalized:
            return normalized, key
    for key in ("suffix_token", "suffix"):
        normalized = normalize_tokens(record.get(key))
        if normalized:
            return normalized, key
    name, provenance = member_name(record)
    derived = normalize_tokens(list(PurePosixPath(name).suffixes)) if name else []
    return (derived, f"derived_from_{provenance}") if derived else ([], None)

def assess(prior, source, accessed_at):
    if prior.get("slot_id") != "gas_emissions_2" or prior.get("wave") != 374:
        raise ValueError("PRIOR_WAVE374_SLOT_MISMATCH")
    if source.get("slot_id") != "gas_emissions_2" or source.get("wave") != 368:
        raise ValueError("SOURCE_WAVE368_SLOT_MISMATCH")

    rows = (source.get("tar_member_path_prefix_records") or [])[:MAX_RECORDS]
    extracted = [tokens(row) for row in rows]
    extracted = [(vals, provenance) for vals, provenance in extracted if vals]
    counts = Counter(token for vals, _ in extracted for token in vals)
    provenance_counts = Counter(provenance for _, provenance in extracted)
    frequencies = [
        {"suffix_token": token, "record_count": count}
        for token, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    blockers = []
    if not rows:
        blockers.append("WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO")
    if not counts:
        blockers.append("TAR_MEMBER_SUFFIX_TOKENS_NOT_AVAILABLE")
    blockers.extend([
        "TAR_MEMBER_SUFFIX_TOKEN_FREQUENCY_ALONE_DOES_NOT_PROVE_FILE_CONTENT",
        "TAR_MEMBER_SUFFIX_TOKEN_FREQUENCY_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
        "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED",
        "THREE_EXACT_UPRNS_NOT_ACQUIRED",
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
    ])

    prior_sha = sha(cbytes(prior))
    source_sha = sha(cbytes(source))
    excerpt = (
        f"prior_wave374_sha256={prior_sha};source_wave368_sha256={source_sha};"
        f"source_path_prefix_records={len(rows)};records_with_suffix_tokens={len(extracted)};"
        f"suffix_token_occurrences={sum(counts.values())};unique_suffix_tokens={len(frequencies)};"
        "business_rows=0;parcel_rows=0"
    )
    runtime_evidence = {
        "source_url": "repo://england_map_web/data/aays_21_slots/gas_emissions_2/wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json",
        "accessed_at": accessed_at,
        "content_sha256": sha(excerpt.encode("utf-8")),
        "hash_scope": "normalized_runtime_receipt_utf8",
        "record_scope": "Only explicit suffix metadata or PurePath.suffixes tokens from bounded Wave368 metadata were counted; no archive member body was read.",
        "relevant_record_ids_or_excerpt": excerpt,
        "supports_fields": [
            "suffix_token_frequencies",
            "records_with_suffix_tokens",
            "suffix_token_occurrence_count",
            "unique_suffix_token_count",
            "suffix_token_provenance_counts",
            "no_member_body_read",
        ],
        "license_or_terms_url": "https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.suffixes",
    }

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 375,
        "accessed_at": accessed_at,
        "prior_wave": 374,
        "prior_state": prior.get("state"),
        "prior_output_sha256": prior_sha,
        "source_wave": 368,
        "source_output_sha256": source_sha,
        "assessments": (source.get("assessments") or [])[:3],
        "source_tar_member_path_prefix_count": len(rows),
        "records_with_suffix_tokens": len(extracted),
        "suffix_token_occurrence_count": sum(counts.values()),
        "unique_suffix_token_count": len(frequencies),
        "suffix_token_frequencies": frequencies,
        "suffix_token_provenance_counts": [
            {"provenance": key, "record_count": value}
            for key, value in sorted(provenance_counts.items())
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
        "decision": "GHCR_BOTTLE_LAYER_TAR_MEMBER_SUFFIX_TOKEN_FREQUENCIES_ASSESSED",
        "state": "NO_DATA_CONTINUE",
        "blocker": ";".join(blockers),
        "first_unverified_step": "ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_COMPOUND_EXTENSION_FREQUENCIES_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": source.get("source_evidence_manifest", []),
        "runtime_source_evidence": [runtime_evidence],
        "fake_data": False,
        "final_ready": False,
    }

def self_test():
    prior = {"slot_id": "gas_emissions_2", "wave": 374, "state": "NO_DATA_CONTINUE"}
    source = {
        "slot_id": "gas_emissions_2",
        "wave": 368,
        "tar_member_path_prefix_records": [
            {"suffix_tokens": [".tar", ".gz"]},
            {"suffixes": [".json"]},
            {"suffix_chain": [".tar", ".gz"]},
            {"suffix_token": ".yaml"},
            {"suffix": ".parquet"},
            {"basename": "data.json"},
            {"path_parts": ["x", "archive.tar.gz"]},
            {"member_name": "x/buildings.parquet"},
            {"normalized_path": "x/archive.tar.gz"},
            {"path": r"x\config.yaml"},
            {"basename": "README"},
        ],
    }
    output = assess(prior, source, "2026-08-03T21:30:00Z")
    assert output["records_with_suffix_tokens"] == 10
    assert output["suffix_token_occurrence_count"] == 14
    assert output["unique_suffix_token_count"] == 5
    assert output["suffix_token_frequencies"][0] == {"suffix_token": ".gz", "record_count": 4}
    assert output["business_rows_produced"] == output["parcel_rows_bound"] == 0
    empty = dict(source)
    empty["tar_member_path_prefix_records"] = []
    zero = assess(prior, empty, "2026-08-03T21:30:00Z")
    assert zero["suffix_token_frequencies"] == []
    assert "WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO" in zero["blocker"]
    print("SELF_TEST_PASS")

def main():
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
    atomic(args.output, assess(prior, source, args.accessed_at))

if __name__ == "__main__":
    main()
