#!/usr/bin/env python3
"""Fail-closed read-only audit for the quarantined Parcel Label artifact.

The script never promotes rows to canonical status. It selects an existing
source only when its exact Git blob SHA matches the historical checkpoint,
computes deterministic ID/schema/geometry counts, and writes audit JSON only.
"""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
SOURCE_CANDIDATES = [
    REPO_ROOT / "england_map_web/data/distance_property_types/parcel_label_1_historical_198_quarantine.json",
    REPO_ROOT / "england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json",
]
OUTPUT = REPO_ROOT / "docs/chatgpt_status/parcel_label/runner_outputs/parcel_label_1_historical_198_full_audit_latest.json"
WEB_OUTPUT = REPO_ROOT / "england_map_web/data/distance_property_types/parcel_label_1_historical_198_audit_result_latest.json"
EXPECTED_BLOB_SHA = "bda76aee331acc0b9f33cccdf968c4314fe433a9"
SLOT_START = 1
SLOT_END = 30761


def count_by(values: list[str]) -> dict[str, int]:
    return dict(sorted(collections.Counter(values).items(), key=lambda item: (-item[1], item[0])))


def nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (dict, list)):
        return bool(value)
    return bool(str(value).strip())


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def select_verified_source() -> tuple[Path, bytes, list[dict[str, Any]]]:
    observations: list[dict[str, Any]] = []
    for source in SOURCE_CANDIDATES:
        if not source.is_file():
            observations.append({"path": source.relative_to(REPO_ROOT).as_posix(), "exists": False})
            continue
        raw = source.read_bytes()
        actual_sha = git_blob_sha(raw)
        observations.append({
            "path": source.relative_to(REPO_ROOT).as_posix(),
            "exists": True,
            "git_blob_sha": actual_sha,
            "sha_matches_checkpoint": actual_sha == EXPECTED_BLOB_SHA,
        })
        if actual_sha == EXPECTED_BLOB_SHA:
            return source, raw, observations
    raise RuntimeError(
        "VERIFIED_SOURCE_NOT_FOUND expected_blob_sha="
        + EXPECTED_BLOB_SHA
        + " observations="
        + json.dumps(observations, sort_keys=True)
    )


def main() -> None:
    source, raw, source_observations = select_verified_source()
    payload = json.loads(raw.decode("utf-8-sig"))
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise RuntimeError("ROWS_ARRAY_MISSING")

    ids = [str(row.get("parcel_id") or "") for row in rows]
    id_counts = collections.Counter(ids)
    duplicate_ids = {key: value for key, value in sorted(id_counts.items()) if key and value > 1}
    canonical_ids = [value for value in ids if value.startswith("parcel_") and value[7:].isdigit()]
    canonical_in_slot = [value for value in canonical_ids if SLOT_START <= int(value[7:]) <= SLOT_END]
    source_ids = [value for value in ids if value.upper().startswith("SOURCE_")]

    geometry_rows = [
        row for row in rows
        if nonempty(row.get("geometry_wkt")) or nonempty(row.get("geometry"))
    ]
    geometry_row_ids = {id(row) for row in geometry_rows}
    centroid_rows = [
        row for row in rows
        if nonempty(row.get("centroid_lat")) and nonempty(row.get("centroid_lon"))
    ]
    schema_signatures = ["|".join(sorted(str(key) for key in row.keys())) for row in rows]
    property_types = [str(row.get("selected_property_type") or row.get("candidate_property_type") or "(empty)") for row in rows]
    geometry_states = [
        str(row.get("geometry_status") or ("GEOMETRY_PRESENT" if id(row) in geometry_row_ids else "EMPTY_GEOMETRY"))
        for row in rows
    ]

    result = {
        "schema_version": 5,
        "slot_id": "parcel_label_1",
        "task_id": "parcel_label_1_historical_198_full_audit_v5_1_20260721",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_path": source.relative_to(REPO_ROOT).as_posix(),
        "source_candidates_observed": source_observations,
        "source_git_blob_sha": EXPECTED_BLOB_SHA,
        "source_git_blob_sha_matches_checkpoint": True,
        "expected_checkpoint_rows": 198,
        "json_rows": len(rows),
        "row_count_matches_checkpoint": len(rows) == 198,
        "unique_nonempty_ids": len({value for value in ids if value}),
        "empty_id_rows": sum(1 for value in ids if not value),
        "duplicate_id_occurrences": sum(value - 1 for value in duplicate_ids.values()),
        "duplicate_ids": duplicate_ids,
        "source_placeholder_ids": len(source_ids),
        "canonical_parcel_ids": len(canonical_ids),
        "canonical_ids_in_slot": len(canonical_in_slot),
        "nonempty_geometry_rows": len(geometry_rows),
        "complete_centroid_rows": len(centroid_rows),
        "schema_signature_count": len(set(schema_signatures)),
        "schema_signatures": count_by(schema_signatures),
        "property_type_counts": count_by(property_types),
        "geometry_state_counts": count_by(geometry_states),
        "canonical_replacement": False,
        "verified_slot_rows": 0,
        "exact_geometry_rows": 0,
        "exact_polygon_rows": 0,
        "property_bindings": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    WEB_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    OUTPUT.write_text(text, encoding="utf-8")
    WEB_OUTPUT.write_text(text, encoding="utf-8")
    print(json.dumps({
        "status": "ok",
        "json_rows": len(rows),
        "source": source.relative_to(REPO_ROOT).as_posix(),
        "output": OUTPUT.relative_to(REPO_ROOT).as_posix(),
        "final_ready": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
