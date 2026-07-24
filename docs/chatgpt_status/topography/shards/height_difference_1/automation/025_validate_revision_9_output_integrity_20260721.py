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
PAYLOAD_REVISION = 9
ATTEMPT_ID = "official-source-batch-004-revision-9-height-difference-metric"
MEASURED_SEMANTICS = "MEASURED_OFFICIAL_PARCEL_GROUND_HEIGHT_DIFFERENCE"
SAFETY_FALSE_FIELDS = (
    "final_ready",
    "product_final_ready",
    "fake_data",
    "db_write",
    "migration",
    "production_deploy",
)


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


def boundary_bulk_ok(boundary: Any) -> bool:
    if not isinstance(boundary, dict):
        return False
    parts: list[str] = []
    for key in ("source", "authority", "method", "provider", "source_type"):
        if boundary.get(key) is not None:
            parts.append(str(boundary[key]))
    for key in ("bulk_match", "gml_match", "monthly_gml"):
        nested = boundary.get(key)
        if isinstance(nested, dict):
            parts.extend(str(nested.get(name, "")) for name in ("source", "authority", "method"))
    text = " ".join(parts).upper()
    marker = any(token in text for token in ("HMLR_INSPIRE_GML", "MONTHLY_GML", "BULK_GML"))
    source_digest = bool(
        boundary.get("source_sha256")
        or boundary.get("gml_sha256")
        or boundary.get("bulk_sha256")
        or (isinstance(boundary.get("bulk_match"), dict) and boundary["bulk_match"].get("source_sha256"))
    )
    geometry = bool(boundary.get("ring") or boundary.get("polygon") or boundary.get("coordinates"))
    return marker and source_digest and geometry


def validate_payload(payload: Any) -> tuple[list[str], dict[str, Any]]:
    blockers: list[str] = []
    facts: dict[str, Any] = {}
    if not isinstance(payload, dict):
        return ["OUTPUT_ROOT_NOT_OBJECT"], facts

    if str(payload.get("task_id") or "") != TASK_ID:
        blockers.append("OUTPUT_TASK_ID_MISMATCH")
    if int(payload.get("payload_revision", -1) or -1) != PAYLOAD_REVISION:
        blockers.append("OUTPUT_PAYLOAD_REVISION_MISMATCH")
    if str(payload.get("attempt_id") or "") != ATTEMPT_ID:
        blockers.append("OUTPUT_ATTEMPT_ID_MISMATCH")

    for field in SAFETY_FALSE_FIELDS:
        if payload.get(field) is not False:
            blockers.append(f"OUTPUT_SAFETY_FLAG_NOT_FALSE:{field}")

    rows = payload.get("rows")
    if not isinstance(rows, list):
        blockers.append("OUTPUT_ROWS_NOT_LIST")
        rows = []
    counts = payload.get("counts")
    if not isinstance(counts, dict):
        blockers.append("OUTPUT_COUNTS_NOT_OBJECT")
        counts = {}

    accepted_indices: list[int] = []
    invalid_accepted: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            blockers.append(f"OUTPUT_ROW_NOT_OBJECT:{index}")
            continue
        if not bool(row.get("accepted_measured_row")):
            continue
        accepted_indices.append(index)
        reasons: list[str] = []
        if not boundary_bulk_ok(row.get("boundary")):
            reasons.append("HMLR_BULK_GML_EVIDENCE_INVALID")
        if bool(row.get("human_review_required") or row.get("hmlr_bulk_wfs_conflict")):
            reasons.append("HUMAN_REVIEW_OR_HMLR_CONFLICT")
        ea = row.get("ea_dtm_1m_polygon")
        if not isinstance(ea, dict) or not bool(ea.get("ok")):
            reasons.append("EA_DTM_1M_NOT_OK")
        metric = row.get("height_difference")
        if not isinstance(metric, dict) or not bool(metric.get("ok")):
            reasons.append("HEIGHT_DIFFERENCE_NOT_OK")
        else:
            if not finite_number(metric.get("height_difference_m")) or float(metric["height_difference_m"]) < 0:
                reasons.append("HEIGHT_DIFFERENCE_NON_NUMERIC_OR_NEGATIVE")
            if not finite_number(metric.get("pixel_count")) or int(metric["pixel_count"]) < 3:
                reasons.append("HEIGHT_DIFFERENCE_PIXEL_COUNT_BELOW_3")
            if metric.get("metric_definition") != "maximum_minus_minimum_EA_DTM_1m_pixels_inside_official_HMLR_polygon":
                reasons.append("HEIGHT_DIFFERENCE_DEFINITION_MISMATCH")
        os_sample = row.get("os_terrain50")
        if not isinstance(os_sample, dict) or not bool(os_sample.get("ok")):
            reasons.append("OS_TERRAIN50_NOT_OK")
        if row.get("output_semantics") != MEASURED_SEMANTICS:
            reasons.append("MEASURED_OUTPUT_SEMANTICS_MISMATCH")
        if str(row.get("accuracy_score_4") or "") != "3.5/4":
            reasons.append("MEASURED_ACCURACY_SCORE_MISMATCH")
        if reasons:
            invalid_accepted.append({"row_index": index, "reasons": reasons})

    accepted_count = len(accepted_indices)
    candidate_count = len(rows)
    expected_candidate = counts.get("candidate_rows")
    if not finite_number(expected_candidate) or int(expected_candidate) != candidate_count:
        blockers.append("COUNT_CANDIDATE_ROWS_MISMATCH")
    for key in ("official_three_source_height_difference_rows", "official_three_source_measured_rows"):
        value = counts.get(key)
        if not finite_number(value) or int(value) != accepted_count:
            blockers.append(f"COUNT_ACCEPTED_ROWS_MISMATCH:{key}")
    if invalid_accepted:
        blockers.append("ACCEPTED_ROWS_FAIL_EVIDENCE_GATE")

    expected_status = "MEASURED_OFFICIAL_HEIGHT_DIFFERENCE_ROWS_AVAILABLE" if accepted_count else "NO_DATA_NOT_INFERRED"
    if payload.get("status") != expected_status:
        blockers.append("OUTPUT_STATUS_COUNT_MISMATCH")

    facts.update(
        {
            "candidate_rows": candidate_count,
            "accepted_rows": accepted_count,
            "accepted_row_indices": accepted_indices,
            "invalid_accepted_rows": invalid_accepted,
            "expected_status": expected_status,
        }
    )
    return blockers, facts


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(os.environ.get("AAYS_REPO_ROOT", ".")))
    parser.add_argument("--runner-output", type=Path)
    parser.add_argument("--web-output", type=Path)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--readback", type=Path)
    args = parser.parse_args(argv)
    repo = args.repo_root.resolve()
    runner = args.runner_output or repo / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/011_height_difference_metric_gate_latest.json"
    web = args.web_output or repo / "england_map_web/data/aays_21_slots/height_difference_1/height_difference_metric_gate_latest.json"
    snapshot = args.snapshot or repo / "docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/011_height_difference_metric_gate_manifest_latest.json"
    report = args.report or repo / "docs/chatgpt_status/topography/shards/height_difference_1/reports/016_height_difference_1_height_difference_metric_gate_result.md"
    readback = args.readback or repo / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/019_revision_9_output_integrity_readback_latest.json"

    paths = {"runner_output": runner, "web_output": web, "snapshot": snapshot, "report": report}
    blockers: list[str] = []
    for name, path in paths.items():
        if not path.is_file():
            blockers.append(f"MISSING_REQUIRED_ARTIFACT:{name}")

    facts: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    if runner.is_file():
        try:
            payload = read_json(runner)
            payload_blockers, facts = validate_payload(payload)
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
            snapshot_facts = {
                "task_id": snap.get("task_id"),
                "payload_revision": snap.get("payload_revision"),
                "valid_height_difference_rows": snap.get("valid_height_difference_rows"),
                "accepted_official_height_difference_rows": snap.get("accepted_official_height_difference_rows"),
            }
            if snap.get("task_id") != TASK_ID:
                blockers.append("SNAPSHOT_TASK_ID_MISMATCH")
            if int(snap.get("payload_revision", -1) or -1) != PAYLOAD_REVISION:
                blockers.append("SNAPSHOT_PAYLOAD_REVISION_MISMATCH")
            accepted_snapshot = snap.get("accepted_official_height_difference_rows", -1)
            if not finite_number(accepted_snapshot) or int(accepted_snapshot) != int(facts.get("accepted_rows", -2)):
                blockers.append("SNAPSHOT_ACCEPTED_COUNT_MISMATCH")
            for field in ("final_ready", "fake_data", "db_write", "migration", "production_deploy"):
                if snap.get(field) is not False:
                    blockers.append(f"SNAPSHOT_SAFETY_FLAG_NOT_FALSE:{field}")
            hashes["snapshot_sha256"] = sha256(snapshot)
        except Exception as exc:
            blockers.append(f"SNAPSHOT_PARSE_ERROR:{type(exc).__name__}")
    if report.is_file():
        hashes["report_sha256"] = sha256(report)

    status = "REVISION_9_OUTPUT_INTEGRITY_VERIFIED" if not blockers else "REVISION_9_OUTPUT_INTEGRITY_BLOCKED"
    result = {
        "schema_version": 1,
        "slot_id": "height_difference_1",
        "task_id": TASK_ID,
        "payload_revision": PAYLOAD_REVISION,
        "status": status,
        "blockers": blockers,
        "facts": facts,
        "snapshot_facts": snapshot_facts,
        "artifact_paths": {key: str(value) for key, value in paths.items()},
        "artifact_sha256": hashes,
        "terminal_marker_trust_allowed": not blockers,
        "measured_rows_trust_allowed": not blockers and int(facts.get("accepted_rows", 0)) > 0,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    readback.parent.mkdir(parents=True, exist_ok=True)
    readback.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not blockers, "status": status, "blockers": blockers, "readback": str(readback)}))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
