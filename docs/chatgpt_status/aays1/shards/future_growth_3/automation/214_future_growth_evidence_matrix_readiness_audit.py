#!/usr/bin/env python3
"""Audit cross-shard readiness for the 92,283-row future-growth evidence matrix.

This task never emits scores or parcel-level business values. It validates three
canonical current-task records, proves partition coverage, and publishes a
compact readiness/evidence pair.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

INPUT_PATHS = [
    "docs/chatgpt_status/_shared/slots_21/future_growth_1/current_task_latest.json",
    "docs/chatgpt_status/_shared/slots_21/future_growth_2/current_task_latest.json",
    "docs/chatgpt_status/aays1/queue/0000_004_future_growth_3_exact_point_intersection_entity_1705636_20260801.task.json",
]
MANIFEST_PATH = "england_map_web/data/aays_21_slots/future_growth_3/future_growth_evidence_matrix_readiness_source_manifest_latest.json"
OUTPUT_PATH = "england_map_web/data/aays_21_slots/future_growth_3/future_growth_evidence_matrix_readiness_audit_latest.json"
EVIDENCE_PATH = "england_map_web/data/aays_21_slots/future_growth_3/future_growth_evidence_matrix_readiness_audit_evidence_latest.json"
EXPECTED_TOTAL = 92283
TERMINAL_STATES = {"PUBLISHED", "DONE", "COMPLETED", "NO_DATA_CONTINUE", "TERMINAL"}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _safe_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe relative path: {relative}")
    resolved = (root / path).resolve()
    root_resolved = root.resolve()
    if root_resolved != resolved and root_resolved not in resolved.parents:
        raise ValueError(f"path escapes repository root: {relative}")
    return resolved


def _load_json(root: Path, relative: str) -> dict[str, Any]:
    path = _safe_path(root, relative)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {relative}")
    return data


def _projection(data: dict[str, Any]) -> dict[str, Any]:
    partition = data.get("parcel_partition")
    if not isinstance(partition, dict):
        raise ValueError("parcel_partition missing or invalid")
    return {
        "slot_id": data.get("slot_id"),
        "task_id": data.get("task_id"),
        "state": data.get("state"),
        "parcel_partition": {
            "start": partition.get("start"),
            "end": partition.get("end"),
            "count": partition.get("count"),
        },
    }


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    payload = _canonical_bytes(value) + b"\n"
    with tmp.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def run(root: Path, validate_only: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _load_json(root, MANIFEST_PATH)
    sources = manifest.get("sources")
    if not isinstance(sources, list) or len(sources) != 3:
        raise ValueError("source manifest must contain exactly three sources")
    manifest_by_path = {item.get("path"): item for item in sources if isinstance(item, dict)}
    if set(manifest_by_path) != set(INPUT_PATHS):
        raise ValueError("source manifest paths do not exactly match task inputs")

    audited: list[dict[str, Any]] = []
    partitions: list[tuple[int, int, int, str]] = []
    for expected_index, relative in enumerate(INPUT_PATHS, start=1):
        data = _load_json(root, relative)
        projection = _projection(data)
        expected_slot = f"future_growth_{expected_index}"
        if projection["slot_id"] != expected_slot:
            raise ValueError(f"slot mismatch for {relative}: {projection['slot_id']}")
        digest = hashlib.sha256(_canonical_bytes(projection)).hexdigest()
        expected_digest = manifest_by_path[relative].get("projection_sha256")
        if digest != expected_digest:
            raise ValueError(f"projection SHA-256 mismatch for {relative}")
        partition = projection["parcel_partition"]
        start, end, count = partition["start"], partition["end"], partition["count"]
        if not all(isinstance(v, int) for v in (start, end, count)):
            raise ValueError(f"partition values must be integers for {relative}")
        if end - start + 1 != count:
            raise ValueError(f"partition count mismatch for {relative}")
        state = str(projection["state"] or "UNKNOWN")
        terminal = state.upper() in TERMINAL_STATES
        partitions.append((start, end, count, expected_slot))
        audited.append({
            "slot_id": expected_slot,
            "task_id": projection["task_id"],
            "state": state,
            "terminal": terminal,
            "parcel_partition": partition,
            "source_path": relative,
            "projection_sha256": digest,
        })

    partitions.sort()
    cursor = 1
    total = 0
    for start, end, count, slot_id in partitions:
        if start != cursor:
            raise ValueError(f"partition gap or overlap before {slot_id}: expected {cursor}, got {start}")
        cursor = end + 1
        total += count
    if total != EXPECTED_TOTAL or cursor != EXPECTED_TOTAL + 1:
        raise ValueError(f"partition coverage mismatch: total={total}, cursor={cursor}")

    terminal_count = sum(1 for item in audited if item["terminal"])
    pending = [{"slot_id": item["slot_id"], "state": item["state"]} for item in audited if not item["terminal"]]
    matrix_ready = terminal_count == 3
    result = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_3",
        "state": "READY_FOR_MATRIX_BUILD" if matrix_ready else "PREREQUISITES_PENDING",
        "panel_status": "BİLGİ TOPLANIYOR",
        "fake_data": False,
        "produced_business_rows": 0,
        "produced_evidence_records": 3,
        "score_rows_produced": 0,
        "matrix_ready": matrix_ready,
        "partition_coverage_valid": True,
        "partition_total": total,
        "terminal_shard_count": terminal_count,
        "pending_prerequisites": pending,
        "audited_shards": audited,
        "progress": {"completed_count": 3, "target_count": 3, "progress_percent": 100.0},
        "next_step": "BUILD_VERIFIED_92283_ROW_FUTURE_GROWTH_EVIDENCE_MATRIX_THEN_SCORE_WITH_CONFIDENCE" if matrix_ready else "WAIT_FOR_PENDING_SHARDS_THEN_RERUN_READINESS_AUDIT",
    }
    evidence = {
        "schema_version": 1,
        "architecture_version": 3,
        "slot_id": "future_growth_3",
        "state": result["state"],
        "fake_data": False,
        "method": "CANONICAL_CURRENT_TASK_PROJECTION_SHA256_AND_CONTIGUOUS_PARTITION_AUDIT",
        "source_manifest_path": MANIFEST_PATH,
        "source_manifest_sha256": hashlib.sha256(_canonical_bytes(manifest)).hexdigest(),
        "exact_read_paths": INPUT_PATHS + [MANIFEST_PATH],
        "exact_write_paths": [OUTPUT_PATH, EVIDENCE_PATH],
        "record_scope": "three future_growth shard current-task records and partitions covering ordinals 1-92283",
        "proven_fields": ["slot_id", "task_id", "state", "parcel_partition.start", "parcel_partition.end", "parcel_partition.count"],
        "partition_coverage_valid": True,
        "partition_total": total,
        "terminal_shard_count": terminal_count,
        "pending_prerequisites": pending,
    }
    if not validate_only:
        _atomic_write(_safe_path(root, OUTPUT_PATH), result)
        _atomic_write(_safe_path(root, EVIDENCE_PATH), evidence)
    return result, evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    result, _ = run(Path(args.repo_root), validate_only=args.validate_only)
    print(json.dumps({"state": result["state"], "matrix_ready": result["matrix_ready"], "completed_count": 3, "target_count": 3}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
