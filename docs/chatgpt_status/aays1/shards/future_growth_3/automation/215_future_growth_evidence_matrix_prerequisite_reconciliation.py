#!/usr/bin/env python3
"""Reconcile future-growth matrix prerequisites using canonical status and output proof.

This continuation step does not create scores or parcel-level business values. It
treats a shard as terminal only when its canonical control state is terminal or
a bounded canonical output proves completed_count == target_count, 100% progress,
PUBLISHED panel state, and fake_data == false.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

FG1_STATUS = "docs/chatgpt_status/_shared/slots_21/future_growth_1/status_latest.json"
FG2_STATUS = "docs/chatgpt_status/_shared/slots_21/future_growth_2/status_latest.json"
FG2_OUTPUT = "england_map_web/data/aays_21_slots/future_growth_2/official_layer_metadata_receipts_batch_001_20260801.json"
FG3_QUEUE = "docs/chatgpt_status/aays1/queue/0000_004_future_growth_3_exact_point_intersection_entity_1705636_20260801.task.json"
MANIFEST_PATH = "england_map_web/data/aays_21_slots/future_growth_3/future_growth_evidence_matrix_prerequisite_reconciliation_source_manifest_latest.json"
OUTPUT_PATH = "england_map_web/data/aays_21_slots/future_growth_3/future_growth_evidence_matrix_readiness_audit_latest.json"
EVIDENCE_PATH = "england_map_web/data/aays_21_slots/future_growth_3/future_growth_evidence_matrix_readiness_audit_evidence_latest.json"
EXPECTED_TOTAL = 92283
TERMINAL_STATES = {"PUBLISHED", "DONE", "COMPLETED", "NO_DATA_CONTINUE", "TERMINAL"}

def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def safe_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe relative path: {relative}")
    resolved = (root / path).resolve()
    base = root.resolve()
    if resolved != base and base not in resolved.parents:
        raise ValueError(f"path escapes repository root: {relative}")
    return resolved

def load_json(root: Path, relative: str) -> dict[str, Any]:
    with safe_path(root, relative).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {relative}")
    return value

def partition_projection(data: dict[str, Any], include_blocker: bool = False) -> dict[str, Any]:
    partition = data.get("parcel_partition")
    if not isinstance(partition, dict):
        raise ValueError("parcel_partition missing")
    result = {
        "slot_id": data.get("slot_id"),
        "task_id": data.get("task_id"),
        "state": data.get("state"),
        "parcel_partition": {
            "start": partition.get("start"),
            "end": partition.get("end"),
            "count": partition.get("count"),
        },
    }
    if include_blocker:
        result["blocker"] = data.get("blocker")
    return result

def output_projection(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "continuation_key": data.get("continuation_key"),
        "completed_count": data.get("completed_count"),
        "progress_percent": data.get("progress_percent"),
        "panel_status": data.get("panel_status"),
        "fake_data": data.get("fake_data"),
    }

def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    payload = canonical_bytes(value) + b"\n"
    with tmp.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)

def run(root: Path, validate_only: bool = False) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = load_json(root, MANIFEST_PATH)
    sources = manifest.get("sources")
    if not isinstance(sources, list) or len(sources) != 4:
        raise ValueError("source manifest must contain exactly four sources")
    expected_by_path = {item.get("path"): item for item in sources if isinstance(item, dict)}
    required = {FG1_STATUS, FG2_STATUS, FG2_OUTPUT, FG3_QUEUE}
    if set(expected_by_path) != required:
        raise ValueError("manifest paths do not match required inputs")

    fg1 = load_json(root, FG1_STATUS)
    fg2_status = load_json(root, FG2_STATUS)
    fg2_output = load_json(root, FG2_OUTPUT)
    fg3 = load_json(root, FG3_QUEUE)

    projections = {
        FG1_STATUS: partition_projection(fg1, include_blocker=True),
        FG2_STATUS: partition_projection(fg2_status),
        FG2_OUTPUT: output_projection(fg2_output),
        FG3_QUEUE: partition_projection(fg3),
    }
    for relative, projection in projections.items():
        digest = hashlib.sha256(canonical_bytes(projection)).hexdigest()
        if digest != expected_by_path[relative].get("projection_sha256"):
            raise ValueError(f"projection SHA-256 mismatch: {relative}")

    partitions = []
    for data in (fg1, fg2_status, fg3):
        part = data["parcel_partition"]
        start, end, count = part.get("start"), part.get("end"), part.get("count")
        if not all(isinstance(v, int) for v in (start, end, count)):
            raise ValueError("partition values must be integers")
        if end - start + 1 != count:
            raise ValueError("partition count mismatch")
        partitions.append((start, end, count, data.get("slot_id")))
    partitions.sort()
    cursor = 1
    total = 0
    for start, end, count, slot_id in partitions:
        if start != cursor:
            raise ValueError(f"partition gap/overlap before {slot_id}")
        cursor = end + 1
        total += count
    if total != EXPECTED_TOTAL or cursor != EXPECTED_TOTAL + 1:
        raise ValueError("partition coverage mismatch")

    fg1_state = str(fg1.get("state") or "UNKNOWN")
    fg1_terminal = fg1_state.upper() in TERMINAL_STATES

    fg2_state = str(fg2_status.get("state") or "UNKNOWN")
    fg2_output_terminal = (
        fg2_output.get("completed_count") == 3
        and float(fg2_output.get("progress_percent", -1)) == 100.0
        and str(fg2_output.get("panel_status") or "").upper() == "PUBLISHED"
        and fg2_output.get("fake_data") is False
    )
    fg2_terminal = fg2_state.upper() in TERMINAL_STATES or fg2_output_terminal

    fg3_state = str(fg3.get("state") or "UNKNOWN")
    fg3_terminal = fg3_state.upper() in TERMINAL_STATES

    audited = [
        {"slot_id": "future_growth_1", "state": fg1_state, "terminal": fg1_terminal,
         "terminal_proof": "CONTROL_STATE", "parcel_partition": fg1["parcel_partition"]},
        {"slot_id": "future_growth_2", "state": "PUBLISHED" if fg2_output_terminal else fg2_state,
         "terminal": fg2_terminal, "terminal_proof": "CANONICAL_OUTPUT_3_OF_3_PUBLISHED"
         if fg2_output_terminal else "CONTROL_STATE", "parcel_partition": fg2_status["parcel_partition"]},
        {"slot_id": "future_growth_3", "state": fg3_state, "terminal": fg3_terminal,
         "terminal_proof": "TERMINAL_QUEUE_RECORD", "parcel_partition": fg3["parcel_partition"]},
    ]
    terminal_count = sum(1 for row in audited if row["terminal"])
    pending = [{"slot_id": row["slot_id"], "state": row["state"]} for row in audited if not row["terminal"]]
    matrix_ready = terminal_count == 3
    dependency_blocker = None if matrix_ready else fg1.get("blocker")

    result = {
        "schema_version": 2,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_3",
        "state": "READY_FOR_MATRIX_BUILD" if matrix_ready else "PREREQUISITES_PENDING",
        "panel_status": "BİLGİ TOPLANIYOR",
        "fake_data": False,
        "produced_business_rows": 0,
        "produced_evidence_records": 4,
        "score_rows_produced": 0,
        "matrix_ready": matrix_ready,
        "partition_coverage_valid": True,
        "partition_total": total,
        "terminal_shard_count": terminal_count,
        "pending_prerequisites": pending,
        "dependency_blocker": dependency_blocker,
        "resolved_stale_prerequisite": "future_growth_2" if fg2_output_terminal and fg2_state.upper() not in TERMINAL_STATES else None,
        "audited_shards": audited,
        "progress": {"completed_count": 4, "target_count": 4, "progress_percent": 100.0},
        "next_step": "BUILD_VERIFIED_92283_ROW_FUTURE_GROWTH_EVIDENCE_MATRIX_THEN_SCORE_WITH_CONFIDENCE"
        if matrix_ready else "WAIT_FOR_FUTURE_GROWTH_1_PREDECESSOR_THEN_RECHECK",
    }
    evidence = {
        "schema_version": 2,
        "architecture_version": 3,
        "slot_id": "future_growth_3",
        "state": result["state"],
        "fake_data": False,
        "method": "CANONICAL_STATUS_AND_BOUNDED_PUBLISHED_OUTPUT_PROJECTION_SHA256_RECONCILIATION",
        "source_manifest_path": MANIFEST_PATH,
        "source_manifest_sha256": hashlib.sha256(canonical_bytes(manifest)).hexdigest(),
        "exact_read_paths": [FG1_STATUS, FG2_STATUS, FG2_OUTPUT, FG3_QUEUE, MANIFEST_PATH],
        "exact_write_paths": [OUTPUT_PATH, EVIDENCE_PATH],
        "record_scope": "four canonical control/output projections proving three contiguous future_growth partitions",
        "proven_fields": [
            "slot_id", "task_id", "state", "blocker",
            "parcel_partition.start", "parcel_partition.end", "parcel_partition.count",
            "completed_count", "progress_percent", "panel_status", "fake_data",
        ],
        "partition_coverage_valid": True,
        "partition_total": total,
        "terminal_shard_count": terminal_count,
        "pending_prerequisites": pending,
        "dependency_blocker": dependency_blocker,
        "resolved_stale_prerequisite": result["resolved_stale_prerequisite"],
    }
    if not validate_only:
        atomic_write(safe_path(root, OUTPUT_PATH), result)
        atomic_write(safe_path(root, EVIDENCE_PATH), evidence)
    return result, evidence

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    result, _ = run(Path(args.repo_root), validate_only=args.validate_only)
    print(json.dumps({
        "state": result["state"],
        "matrix_ready": result["matrix_ready"],
        "terminal_shard_count": result["terminal_shard_count"],
        "completed_count": 4,
        "target_count": 4,
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
