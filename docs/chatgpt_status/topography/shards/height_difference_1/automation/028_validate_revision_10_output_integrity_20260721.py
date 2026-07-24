#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
PAYLOAD_REVISION = 10
ATTEMPT_ID = "official-source-batch-004-revision-10-explicit-identity-evidence-gate"
IDEMPOTENCY_KEY = "height_difference_1-004-20260720"
SCRIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_1/automation/027_height_difference_1_revision_10_explicit_identity_evidence_gate_20260721.py"
MEASURED_SEMANTICS = "MEASURED_OFFICIAL_PARCEL_GROUND_HEIGHT_DIFFERENCE"
SAFETY_FALSE_FIELDS = ("final_ready", "product_final_ready", "fake_data", "db_write", "migration", "production_deploy")


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_payload(payload: Any, expected_script_sha256: str) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    facts: dict[str, Any] = {}
    if not isinstance(payload, dict):
        return ["OUTPUT_ROOT_NOT_OBJECT"], facts
    identity = {
        "task_id": payload.get("task_id"),
        "payload_revision": payload.get("payload_revision"),
        "attempt_id": payload.get("attempt_id"),
        "idempotency_key": payload.get("idempotency_key"),
        "script_path": payload.get("script_path"),
        "script_sha256": payload.get("script_sha256"),
    }
    expected = {
        "task_id": TASK_ID,
        "payload_revision": PAYLOAD_REVISION,
        "attempt_id": ATTEMPT_ID,
        "idempotency_key": IDEMPOTENCY_KEY,
        "script_path": SCRIPT_REL,
        "script_sha256": expected_script_sha256,
    }
    for key, value in expected.items():
        actual = identity.get(key)
        if key == "payload_revision":
            try:
                actual = int(actual)
            except Exception:
                actual = -1
        if actual != value:
            blockers.append(f"OUTPUT_IDENTITY_MISMATCH:{key}")
    for field in SAFETY_FALSE_FIELDS:
        if payload.get(field) is not False:
            blockers.append(f"OUTPUT_SAFETY_FLAG_NOT_FALSE:{field}")

    rows = payload.get("rows")
    counts = payload.get("counts")
    if not isinstance(rows, list):
        blockers.append("OUTPUT_ROWS_NOT_LIST")
        rows = []
    if not isinstance(counts, dict):
        blockers.append("OUTPUT_COUNTS_NOT_OBJECT")
        counts = {}

    accepted_indices: list[int] = []
    invalid_accepted: list[dict[str, Any]] = []
    human_review_count = 0
    valid_metric_count = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            blockers.append(f"OUTPUT_ROW_NOT_OBJECT:{index}")
            continue
        evidence = row.get("revision_10_evidence_gate")
        metric = row.get("height_difference")
        if isinstance(metric, dict) and bool(metric.get("ok")):
            valid_metric_count += 1
        if bool(row.get("human_review_required")):
            human_review_count += 1
        if not bool(row.get("accepted_measured_row")):
            continue
        accepted_indices.append(index)
        reasons: list[str] = []
        if not isinstance(evidence, dict) or not bool(evidence.get("accepted")):
            reasons.append("REVISION_10_EVIDENCE_GATE_NOT_ACCEPTED")
        else:
            boundary = evidence.get("boundary")
            ea = evidence.get("ea_height_difference")
            os_check = evidence.get("os_independent_crosscheck")
            if not isinstance(boundary, dict) or not bool(boundary.get("ok")):
                reasons.append("HMLR_BOUNDARY_EVIDENCE_INVALID")
            if not isinstance(ea, dict) or not bool(ea.get("ok")):
                reasons.append("EA_HEIGHT_DIFFERENCE_EVIDENCE_INVALID")
            if not isinstance(os_check, dict) or not bool(os_check.get("ok")):
                reasons.append("OS_INDEPENDENT_EVIDENCE_INVALID")
            if evidence.get("conflict_free") is not True:
                reasons.append("EVIDENCE_CONFLICT_NOT_CLEARED")
            difference = evidence.get("ea_os_median_absolute_difference_m")
            if not finite_number(difference) or float(difference) > 8.0:
                reasons.append("EA_OS_DIFFERENCE_INVALID_OR_OVER_8M")
        if not isinstance(metric, dict) or not bool(metric.get("ok")):
            reasons.append("HEIGHT_DIFFERENCE_NOT_OK")
        else:
            if not finite_number(metric.get("height_difference_m")) or float(metric["height_difference_m"]) < 0:
                reasons.append("HEIGHT_DIFFERENCE_NON_NUMERIC_OR_NEGATIVE")
            if not finite_number(metric.get("pixel_count")) or int(metric["pixel_count"]) < 3:
                reasons.append("HEIGHT_DIFFERENCE_PIXEL_COUNT_BELOW_3")
            if metric.get("horizontal_crs") != "EPSG:27700":
                reasons.append("EA_HORIZONTAL_CRS_MISMATCH")
            if metric.get("vertical_crs") != "EPSG:5701":
                reasons.append("EA_VERTICAL_CRS_MISMATCH")
        if row.get("output_semantics") != MEASURED_SEMANTICS:
            reasons.append("MEASURED_OUTPUT_SEMANTICS_MISMATCH")
        if str(row.get("accuracy_score_4") or "") != "3.5/4":
            reasons.append("MEASURED_ACCURACY_SCORE_MISMATCH")
        if reasons:
            invalid_accepted.append({"row_index": index, "reasons": reasons})

    accepted_count = len(accepted_indices)
    expected_counts = {
        "candidate_rows": len(rows),
        "ea_1m_valid_height_difference_rows": valid_metric_count,
        "official_three_source_height_difference_rows": accepted_count,
        "official_three_source_measured_rows": accepted_count,
        "human_review_rows": human_review_count,
    }
    for key, expected_value in expected_counts.items():
        value = counts.get(key)
        if not finite_number(value) or int(value) != expected_value:
            blockers.append(f"COUNT_MISMATCH:{key}")
    if invalid_accepted:
        blockers.append("ACCEPTED_ROWS_FAIL_REVISION_10_EVIDENCE_GATE")
    expected_status = "MEASURED_OFFICIAL_HEIGHT_DIFFERENCE_ROWS_AVAILABLE" if accepted_count else "NO_DATA_NOT_INFERRED"
    if payload.get("status") != expected_status:
        blockers.append("OUTPUT_STATUS_COUNT_MISMATCH")
    facts.update({"identity": identity, "candidate_rows": len(rows), "valid_metric_rows": valid_metric_count, "accepted_rows": accepted_count, "human_review_rows": human_review_count, "accepted_row_indices": accepted_indices, "invalid_accepted_rows": invalid_accepted, "expected_status": expected_status})
    return blockers, facts


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(os.environ.get("AAYS_REPO_ROOT", ".")))
    args = parser.parse_args(argv)
    repo = args.repo_root.resolve()
    script = repo / SCRIPT_REL
    queue = repo / "docs/chatgpt_status/topography/queue/height_difference_1_004_official_boundary_numeric_samples_20260720.v3.task.json"
    runner = repo / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/012_revision_10_explicit_identity_evidence_gate_latest.json"
    web = repo / "england_map_web/data/aays_21_slots/height_difference_1/revision_10_explicit_identity_evidence_gate_latest.json"
    snapshot = repo / "docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/012_revision_10_explicit_identity_evidence_manifest_latest.json"
    report = repo / "docs/chatgpt_status/topography/shards/height_difference_1/reports/017_height_difference_1_revision_10_explicit_identity_evidence_result.md"
    readback = repo / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/020_revision_10_output_integrity_readback_latest.json"
    paths = {"script": script, "queue": queue, "runner_output": runner, "web_output": web, "snapshot": snapshot, "report": report}
    blockers: list[str] = []
    for name, path in paths.items():
        if not path.is_file():
            blockers.append(f"MISSING_REQUIRED_ARTIFACT:{name}")
    hashes: dict[str, str] = {}
    facts: dict[str, Any] = {}
    expected_script_sha = sha256(script) if script.is_file() else ""
    if script.is_file():
        hashes["script_sha256"] = expected_script_sha
    if queue.is_file():
        try:
            q = read_json(queue)
            expected_queue = {"task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "attempt_id": ATTEMPT_ID, "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL}
            for key, expected in expected_queue.items():
                actual = q.get(key)
                if key == "payload_revision":
                    try:
                        actual = int(actual)
                    except Exception:
                        actual = -1
                if actual != expected:
                    blockers.append(f"QUEUE_IDENTITY_MISMATCH:{key}")
            if q.get("script_blob_sha") and q.get("script_blob_sha") != "9fdb1336dc418a8606ac3836a05d00475bc6602e":
                blockers.append("QUEUE_SCRIPT_BLOB_SHA_MISMATCH")
            hashes["queue_sha256"] = sha256(queue)
        except Exception as exc:
            blockers.append(f"QUEUE_PARSE_ERROR:{type(exc).__name__}")
    if runner.is_file():
        try:
            payload = read_json(runner)
            payload_blockers, facts = validate_payload(payload, expected_script_sha)
            blockers.extend(payload_blockers)
            hashes["runner_output_sha256"] = sha256(runner)
        except Exception as exc:
            blockers.append(f"RUNNER_OUTPUT_PARSE_ERROR:{type(exc).__name__}")
    if web.is_file():
        hashes["web_output_sha256"] = sha256(web)
    if runner.is_file() and web.is_file() and hashes.get("runner_output_sha256") != hashes.get("web_output_sha256"):
        blockers.append("RUNNER_AND_WEB_OUTPUT_HASH_MISMATCH")
    snapshot_facts: dict[str, Any] = {}
    if snapshot.is_file():
        try:
            snap = read_json(snapshot)
            snapshot_facts = {key: snap.get(key) for key in ("task_id", "payload_revision", "attempt_id", "idempotency_key", "script_path", "script_sha256", "runner_web_output_sha256", "candidate_rows", "valid_height_difference_rows", "accepted_official_height_difference_rows", "human_review_rows")}
            expected_snap = {"task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "attempt_id": ATTEMPT_ID, "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL, "script_sha256": expected_script_sha}
            for key, expected in expected_snap.items():
                actual = snap.get(key)
                if key == "payload_revision":
                    try:
                        actual = int(actual)
                    except Exception:
                        actual = -1
                if actual != expected:
                    blockers.append(f"SNAPSHOT_IDENTITY_MISMATCH:{key}")
            if runner.is_file() and snap.get("runner_web_output_sha256") != hashes.get("runner_output_sha256"):
                blockers.append("SNAPSHOT_OUTPUT_SHA256_MISMATCH")
            count_pairs = {"candidate_rows": "candidate_rows", "valid_height_difference_rows": "valid_metric_rows", "accepted_official_height_difference_rows": "accepted_rows", "human_review_rows": "human_review_rows"}
            for snap_key, fact_key in count_pairs.items():
                if not finite_number(snap.get(snap_key)) or int(snap[snap_key]) != int(facts.get(fact_key, -1)):
                    blockers.append(f"SNAPSHOT_COUNT_MISMATCH:{snap_key}")
            for field in SAFETY_FALSE_FIELDS:
                if snap.get(field) is not False:
                    blockers.append(f"SNAPSHOT_SAFETY_FLAG_NOT_FALSE:{field}")
            hashes["snapshot_sha256"] = sha256(snapshot)
        except Exception as exc:
            blockers.append(f"SNAPSHOT_PARSE_ERROR:{type(exc).__name__}")
    if report.is_file():
        hashes["report_sha256"] = sha256(report)
    status = "REVISION_10_OUTPUT_INTEGRITY_VERIFIED" if not blockers else "REVISION_10_OUTPUT_INTEGRITY_BLOCKED"
    result = {"schema_version": 1, "slot_id": "height_difference_1", "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "status": status, "blockers": blockers, "facts": facts, "snapshot_facts": snapshot_facts, "artifact_paths": {key: str(value) for key, value in paths.items()}, "artifact_sha256": hashes, "terminal_marker_trust_allowed": not blockers, "measured_rows_trust_allowed": not blockers and int(facts.get("accepted_rows", 0)) > 0, "valid_no_data_terminal": not blockers and int(facts.get("accepted_rows", 0)) == 0, "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    readback.parent.mkdir(parents=True, exist_ok=True)
    readback.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not blockers, "status": status, "blockers": blockers, "readback": str(readback)}))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
