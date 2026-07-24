#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
PAYLOAD_REVISION = 11
ATTEMPT_ID = "official-source-batch-004-revision-11-pixel-center-sampling-provenance"
IDEMPOTENCY_KEY = "height_difference_1-004-20260720"
SCRIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_1/automation/032_height_difference_1_revision_11_pixel_center_sampling_provenance_20260721.py"
MEASURED_SEMANTICS = "MEASURED_OFFICIAL_PARCEL_GROUND_HEIGHT_DIFFERENCE_PIXEL_CENTER_GATED"
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
    expected_identity = {"task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "attempt_id": ATTEMPT_ID, "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL, "script_sha256": expected_script_sha256}
    for key, expected in expected_identity.items():
        actual = payload.get(key)
        if key == "payload_revision":
            try:
                actual = int(actual)
            except Exception:
                actual = -1
        if actual != expected:
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

    accepted = 0
    provenance_ok = 0
    invalid_accepted: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            blockers.append(f"OUTPUT_ROW_NOT_OBJECT:{index}")
            continue
        gate = row.get("revision_11_sampling_provenance_gate")
        provenance = gate.get("sampling_provenance") if isinstance(gate, dict) else None
        if isinstance(provenance, dict) and bool(provenance.get("ok")):
            provenance_ok += 1
        if not bool(row.get("accepted_measured_row")):
            continue
        accepted += 1
        reasons: list[str] = []
        if not isinstance(gate, dict) or gate.get("accepted") is not True:
            reasons.append("REVISION_11_GATE_NOT_ACCEPTED")
        if not isinstance(provenance, dict) or not bool(provenance.get("ok")):
            reasons.append("SAMPLING_PROVENANCE_NOT_OK")
        else:
            if provenance.get("all_touched") is not False:
                reasons.append("ALL_TOUCHED_NOT_FALSE")
            policy = str(provenance.get("pixel_inclusion_policy") or "").lower()
            if "pixel_center" not in policy and "pixel centre" not in policy and "pixel-centre" not in policy:
                reasons.append("PIXEL_CENTER_POLICY_MISSING")
            if provenance.get("pixel_centers_inside_polygon") is not True:
                reasons.append("PIXEL_CENTERS_NOT_VERIFIED")
            if len(str(provenance.get("mask_sha256") or "")) != 64:
                reasons.append("MASK_SHA256_INVALID")
            if not finite_number(provenance.get("computed_polygon_area_m2")) or float(provenance["computed_polygon_area_m2"]) <= 0:
                reasons.append("COMPUTED_POLYGON_AREA_INVALID")
            if not finite_number(provenance.get("declared_polygon_area_m2")) or float(provenance["declared_polygon_area_m2"]) <= 0:
                reasons.append("DECLARED_POLYGON_AREA_INVALID")
        if row.get("output_semantics") != MEASURED_SEMANTICS:
            reasons.append("MEASURED_SEMANTICS_MISMATCH")
        if str(row.get("accuracy_score_4") or "") != "3.5/4":
            reasons.append("MEASURED_ACCURACY_SCORE_MISMATCH")
        if reasons:
            invalid_accepted.append({"row_index": index, "reasons": reasons})

    expected_counts = {"candidate_rows": len(rows), "pixel_center_sampling_provenance_rows": provenance_ok, "official_three_source_height_difference_rows": accepted, "official_three_source_measured_rows": accepted}
    for key, expected in expected_counts.items():
        value = counts.get(key)
        if not finite_number(value) or int(value) != expected:
            blockers.append(f"COUNT_MISMATCH:{key}")
    if invalid_accepted:
        blockers.append("ACCEPTED_ROWS_FAIL_REVISION_11_SAMPLING_GATE")
    expected_status = "MEASURED_OFFICIAL_HEIGHT_DIFFERENCE_ROWS_AVAILABLE" if accepted else "NO_DATA_NOT_INFERRED"
    if payload.get("status") != expected_status:
        blockers.append("OUTPUT_STATUS_COUNT_MISMATCH")
    facts.update({"candidate_rows": len(rows), "sampling_provenance_rows": provenance_ok, "accepted_rows": accepted, "invalid_accepted_rows": invalid_accepted, "expected_status": expected_status})
    return blockers, facts


def main() -> int:
    script = REPO / SCRIPT_REL
    queue = REPO / "docs/chatgpt_status/topography/queue/height_difference_1_004_official_boundary_numeric_samples_20260720.v3.task.json"
    runner = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/013_revision_11_pixel_center_sampling_provenance_latest.json"
    web = REPO / "england_map_web/data/aays_21_slots/height_difference_1/revision_11_pixel_center_sampling_provenance_latest.json"
    snapshot = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/013_revision_11_pixel_center_sampling_provenance_manifest_latest.json"
    report = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/reports/018_height_difference_1_revision_11_pixel_center_sampling_provenance_result.md"
    readback = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/022_revision_11_output_integrity_readback_latest.json"
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
            snapshot_facts = {key: snap.get(key) for key in ("task_id", "payload_revision", "attempt_id", "idempotency_key", "script_path", "script_sha256", "runner_web_output_sha256", "candidate_rows", "pixel_center_sampling_provenance_rows", "accepted_official_height_difference_rows")}
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
            count_pairs = {"candidate_rows": "candidate_rows", "pixel_center_sampling_provenance_rows": "sampling_provenance_rows", "accepted_official_height_difference_rows": "accepted_rows"}
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
    status = "REVISION_11_OUTPUT_INTEGRITY_VERIFIED" if not blockers else "REVISION_11_OUTPUT_INTEGRITY_BLOCKED"
    result = {"schema_version": 1, "slot_id": "height_difference_1", "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "status": status, "blockers": blockers, "facts": facts, "snapshot_facts": snapshot_facts, "artifact_paths": {key: str(value) for key, value in paths.items()}, "artifact_sha256": hashes, "terminal_marker_trust_allowed": not blockers, "measured_rows_trust_allowed": not blockers and int(facts.get("accepted_rows", 0)) > 0, "valid_no_data_terminal": not blockers and int(facts.get("accepted_rows", 0)) == 0, "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    readback.parent.mkdir(parents=True, exist_ok=True)
    readback.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not blockers, "status": status, "blockers": blockers, "readback": str(readback)}))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
