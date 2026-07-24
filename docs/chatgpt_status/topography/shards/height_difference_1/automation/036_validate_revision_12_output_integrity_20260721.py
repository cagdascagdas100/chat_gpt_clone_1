#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
from pathlib import Path
from typing import Any

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
PAYLOAD_REVISION = 12
ATTEMPT_ID = "official-source-batch-004-revision-12-direct-ea-pixel-center-resample"
IDEMPOTENCY_KEY = "height_difference_1-004-20260720"
SCRIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_1/automation/035_height_difference_1_revision_12_direct_ea_pixel_center_resample_20260721.py"
MEASURED_SEMANTICS = "MEASURED_OFFICIAL_PARCEL_GROUND_HEIGHT_DIFFERENCE_PIXEL_CENTER_GATED"
SAFETY_FALSE_FIELDS = ("final_ready", "product_final_ready", "fake_data", "db_write", "migration", "production_deploy")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
OFFICIAL_WCS_PREFIX = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"


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


def git_blob_sha(repo: Path, path: Path) -> str:
    process = subprocess.run(["git", "-C", str(repo), "hash-object", "--", str(path)], text=True, capture_output=True, check=False)
    return process.stdout.strip() if process.returncode == 0 else ""


def valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value.strip()))


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
    wcs = payload.get("ea_wcs_source_contract")
    if not isinstance(wcs, dict):
        blockers.append("EA_WCS_SOURCE_CONTRACT_MISSING")
        wcs = {}
    if not str(wcs.get("base_url") or "").startswith(OFFICIAL_WCS_PREFIX):
        blockers.append("EA_WCS_BASE_URL_NOT_OFFICIAL_PERSISTENT_ENDPOINT")
    if wcs.get("service") != "WCS" or wcs.get("version") != "2.0.1":
        blockers.append("EA_WCS_PROTOCOL_MISMATCH")
    if not str(wcs.get("coverage_id") or "").strip():
        blockers.append("EA_WCS_COVERAGE_ID_MISSING")
    if not valid_sha256(wcs.get("capabilities_sha256")):
        blockers.append("EA_WCS_CAPABILITIES_SHA256_INVALID")
    if not valid_sha256(wcs.get("describe_sha256")):
        blockers.append("EA_WCS_DESCRIBE_SHA256_INVALID")
    if wcs.get("horizontal_crs") != "EPSG:27700":
        blockers.append("EA_WCS_HORIZONTAL_CRS_MISMATCH")
    if wcs.get("vertical_crs") != "EPSG:5701":
        blockers.append("EA_WCS_VERTICAL_CRS_MISMATCH")
    rows = payload.get("rows")
    counts = payload.get("counts")
    if not isinstance(rows, list):
        blockers.append("OUTPUT_ROWS_NOT_LIST")
        rows = []
    if not isinstance(counts, dict):
        blockers.append("OUTPUT_COUNTS_NOT_OBJECT")
        counts = {}
    direct_ok = 0
    direct_errors = 0
    provenance_ok = 0
    accepted = 0
    invalid_accepted: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            blockers.append(f"OUTPUT_ROW_NOT_OBJECT:{index}")
            continue
        direct = row.get("revision_12_direct_ea_resample")
        stats = row.get("ea_dtm_1m_polygon")
        gate11 = row.get("revision_11_sampling_provenance_gate")
        provenance = gate11.get("sampling_provenance") if isinstance(gate11, dict) else None
        if isinstance(direct, dict) and direct.get("ok") is True:
            direct_ok += 1
        else:
            direct_errors += 1
        if isinstance(provenance, dict) and provenance.get("ok") is True:
            provenance_ok += 1
        if not bool(row.get("accepted_measured_row")):
            continue
        accepted += 1
        reasons: list[str] = []
        if not isinstance(direct, dict) or direct.get("ok") is not True:
            reasons.append("DIRECT_EA_RESAMPLE_NOT_OK")
        if not isinstance(stats, dict) or stats.get("ok") is not True:
            reasons.append("EA_DTM1M_STATS_NOT_OK")
        else:
            if not valid_sha256(stats.get("geotiff_sha256")):
                reasons.append("EA_GEOTIFF_SHA256_INVALID")
            if not valid_sha256(stats.get("capabilities_sha256")):
                reasons.append("EA_ROW_CAPABILITIES_SHA256_INVALID")
            if not valid_sha256(stats.get("describe_coverage_sha256")):
                reasons.append("EA_ROW_DESCRIBE_SHA256_INVALID")
            if stats.get("coverage_id") != wcs.get("coverage_id"):
                reasons.append("EA_ROW_COVERAGE_ID_MISMATCH")
            if stats.get("centroid_fallback_used") is not False:
                reasons.append("CENTROID_FALLBACK_USED")
            if stats.get("horizontal_crs") != "EPSG:27700":
                reasons.append("EA_HORIZONTAL_CRS_MISMATCH")
            if stats.get("vertical_crs") != "EPSG:5701":
                reasons.append("EA_VERTICAL_CRS_MISMATCH")
            if not finite_number(stats.get("pixel_count")) or int(stats["pixel_count"]) < 3:
                reasons.append("EA_PIXEL_COUNT_BELOW_3")
        if not isinstance(gate11, dict) or gate11.get("accepted") is not True:
            reasons.append("REVISION_11_GATE_NOT_ACCEPTED")
        if not isinstance(provenance, dict) or provenance.get("ok") is not True:
            reasons.append("SAMPLING_PROVENANCE_NOT_OK")
        else:
            if provenance.get("all_touched") is not False:
                reasons.append("ALL_TOUCHED_NOT_FALSE")
            if provenance.get("pixel_centers_inside_polygon") is not True:
                reasons.append("PIXEL_CENTERS_NOT_VERIFIED")
            if not valid_sha256(provenance.get("mask_sha256")):
                reasons.append("MASK_SHA256_INVALID")
            raw_stats_provenance = stats.get("sampling_provenance") if isinstance(stats, dict) else None
            selected_centers_sha = raw_stats_provenance.get("selected_pixel_centers_sha256") if isinstance(raw_stats_provenance, dict) else None
            if not valid_sha256(selected_centers_sha):
                reasons.append("SELECTED_PIXEL_CENTERS_SHA256_INVALID")
            if not finite_number(provenance.get("valid_pixel_count")) or not finite_number(stats.get("pixel_count")) or int(provenance["valid_pixel_count"]) != int(stats["pixel_count"]):
                reasons.append("PROVENANCE_PIXEL_COUNT_MISMATCH")
        if row.get("output_semantics") != MEASURED_SEMANTICS:
            reasons.append("MEASURED_SEMANTICS_MISMATCH")
        if str(row.get("accuracy_score_4") or "") != "3.5/4":
            reasons.append("MEASURED_ACCURACY_SCORE_MISMATCH")
        if reasons:
            invalid_accepted.append({"row_index": index, "reasons": reasons})
    expected_counts = {"candidate_rows": len(rows), "revision_12_direct_ea_resample_rows": direct_ok, "revision_12_direct_ea_resample_error_rows": direct_errors, "pixel_center_sampling_provenance_rows": provenance_ok, "official_three_source_height_difference_rows": accepted, "official_three_source_measured_rows": accepted}
    for key, expected in expected_counts.items():
        value = counts.get(key)
        if not finite_number(value) or int(value) != expected:
            blockers.append(f"COUNT_MISMATCH:{key}")
    if direct_errors:
        blockers.append("DIRECT_EA_RESAMPLE_ERRORS_PRESENT")
    if invalid_accepted:
        blockers.append("ACCEPTED_ROWS_FAIL_REVISION_12_DIRECT_SAMPLING_GATE")
    expected_status = "MEASURED_OFFICIAL_HEIGHT_DIFFERENCE_ROWS_AVAILABLE" if accepted else "NO_DATA_NOT_INFERRED"
    if direct_errors:
        expected_status = "BLOCKED_DIRECT_EA_PIXEL_CENTER_RESAMPLE"
    if payload.get("status") != expected_status:
        blockers.append("OUTPUT_STATUS_COUNT_OR_ERROR_MISMATCH")
    facts.update({"candidate_rows": len(rows), "direct_ea_resample_rows": direct_ok, "direct_ea_resample_error_rows": direct_errors, "sampling_provenance_rows": provenance_ok, "accepted_rows": accepted, "invalid_accepted_rows": invalid_accepted, "expected_status": expected_status})
    return blockers, facts


def main() -> int:
    script = REPO / SCRIPT_REL
    queue = REPO / "docs/chatgpt_status/topography/queue/height_difference_1_004_official_boundary_numeric_samples_20260720.v3.task.json"
    runner = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/014_revision_12_direct_ea_pixel_center_resample_latest.json"
    web = REPO / "england_map_web/data/aays_21_slots/height_difference_1/revision_12_direct_ea_pixel_center_resample_latest.json"
    snapshot = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/014_revision_12_direct_ea_pixel_center_resample_manifest_latest.json"
    report = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/reports/019_height_difference_1_revision_12_direct_ea_pixel_center_resample_result.md"
    readback = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/023_revision_12_output_integrity_readback_latest.json"
    paths = {"script": script, "queue": queue, "runner_output": runner, "web_output": web, "snapshot": snapshot, "report": report}
    blockers: list[str] = []
    for name, path in paths.items():
        if not path.is_file():
            blockers.append(f"MISSING_REQUIRED_ARTIFACT:{name}")
    hashes: dict[str, str] = {}
    facts: dict[str, Any] = {}
    expected_script_sha = sha256(script) if script.is_file() else ""
    expected_script_blob = git_blob_sha(REPO, script) if script.is_file() else ""
    if script.is_file():
        hashes["script_sha256"] = expected_script_sha
        hashes["script_blob_sha"] = expected_script_blob
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
            if q.get("script_blob_sha") != expected_script_blob:
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
            keys = ("task_id", "payload_revision", "attempt_id", "idempotency_key", "script_path", "script_sha256", "runner_web_output_sha256", "candidate_rows", "direct_ea_resample_rows", "direct_ea_resample_error_rows", "pixel_center_sampling_provenance_rows", "accepted_official_height_difference_rows")
            snapshot_facts = {key: snap.get(key) for key in keys}
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
            count_pairs = {"candidate_rows": "candidate_rows", "direct_ea_resample_rows": "direct_ea_resample_rows", "direct_ea_resample_error_rows": "direct_ea_resample_error_rows", "pixel_center_sampling_provenance_rows": "sampling_provenance_rows", "accepted_official_height_difference_rows": "accepted_rows"}
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
    status = "REVISION_12_OUTPUT_INTEGRITY_VERIFIED" if not blockers else "REVISION_12_OUTPUT_INTEGRITY_BLOCKED"
    result = {"schema_version": 1, "slot_id": "height_difference_1", "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "status": status, "blockers": blockers, "facts": facts, "snapshot_facts": snapshot_facts, "artifact_paths": {key: str(value) for key, value in paths.items()}, "artifact_sha256": hashes, "terminal_marker_trust_allowed": not blockers, "measured_rows_trust_allowed": not blockers and int(facts.get("accepted_rows", 0)) > 0, "valid_no_data_terminal": not blockers and int(facts.get("accepted_rows", 0)) == 0, "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    readback.parent.mkdir(parents=True, exist_ok=True)
    readback.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not blockers, "status": status, "blockers": blockers, "readback": str(readback)}))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
