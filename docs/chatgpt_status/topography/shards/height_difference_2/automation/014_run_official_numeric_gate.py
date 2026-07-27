#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
ATTEMPT_ID = "height-difference-2-20260721-020"
TARGET_ROWS = [30762, 46142, 61522]
EXPECTED_EA_COVERAGE_ID = "13787b9a-26a4-4775-8523-806d13af58fc__Lidar_Composite_Elevation_DTM_1m"


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {"command": command, "exit_code": process.returncode, "stdout": process.stdout[-8000:], "stderr": process.stderr[-8000:]}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _web_candidate_payload(payload: dict[str, Any], expected_rows: int) -> dict[str, Any]:
    return {
        "schema_version": 4,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": payload["status"],
        "candidate_count": payload.get("official_numeric_row_count", 0),
        "candidates": payload.get("measured_rows", []),
        "height_difference_metric": "EA_DTM1M_MAX_MINUS_MIN_INSIDE_EXACT_HMLR_POLYGON",
        "parcel_elevation_median_is_distinct_metric": True,
        "height_metric_consistency_passed": payload.get("height_metric_consistency_passed", False),
        "expected_web_operation_rows": expected_rows,
        "web_acceptance_passed": payload.get("web_acceptance_passed", False),
        "final_ready": False,
        "fake_data": False,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--hmlr-exact-matches", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--final-output", type=Path, required=True)
    parser.add_argument("--web-output", type=Path)
    parser.add_argument("--terrain50-archive", type=Path)
    parser.add_argument("--terrain50-root", type=Path)
    parser.add_argument("--wcs-url")
    parser.add_argument("--coverage-id", default=EXPECTED_EA_COVERAGE_ID)
    parser.add_argument("--preserved-metric-evidence", type=Path, required=True)
    parser.add_argument("--height-metric-tolerance-m", type=float, default=0.001)
    parser.add_argument("--web-base-url", default=os.environ.get("AAYS_HEIGHT_DIFFERENCE_2_WEB_BASE_URL", "http://127.0.0.1:8012/"))
    parser.add_argument("--expected-web-operation-rows", type=int, default=int(os.environ.get("AAYS_HEIGHT_DIFFERENCE_2_EXPECTED_WEB_ROWS", "1036")))
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    automation = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/automation"
    ea_script = automation / "012_sample_ea_dtm1m_polygons.py"
    metric_guard = automation / "018_verify_current_height_difference_metric.py"
    terrain_wrapper = automation / "016_prepare_and_crosscheck_os_terrain50.py"
    web_verifier = automation / "017_verify_height_difference_2_web_8012.py"
    ea_output = args.output_dir / "ea_dtm1m_polygon_samples.json"
    metric_output = args.output_dir / "current_height_metric_consistency.json"
    terrain_output = args.output_dir / "os_terrain50_crosschecks.json"
    web_acceptance_output = args.output_dir / "port_8012_web_acceptance.json"
    candidate_preacceptance_output = args.output_dir / "candidates_preacceptance.json"
    execution_output = args.output_dir / "official_numeric_gate_execution.json"
    stages: list[dict[str, Any]] = []

    try:
        if args.coverage_id != EXPECTED_EA_COVERAGE_ID:
            raise ValueError(f"EA CoverageId is not the pinned elevation DTM1m coverage: {args.coverage_id}")
        required_scripts = [ea_script, metric_guard, terrain_wrapper, web_verifier]
        missing = [str(path) for path in required_scripts if not path.is_file()]
        if missing:
            raise FileNotFoundError(f"official numeric gate script missing: {missing}")
        if not args.preserved_metric_evidence.is_file():
            raise FileNotFoundError(f"preserved metric evidence missing: {args.preserved_metric_evidence}")

        ea_command = [
            sys.executable, str(ea_script),
            "--hmlr-exact-matches", str(args.hmlr_exact_matches),
            "--output", str(ea_output),
            "--coverage-id", args.coverage_id,
        ]
        if args.wcs_url:
            ea_command.extend(["--wcs-url", args.wcs_url])
        ea_stage = {"stage": "EA_DTM1M_POLYGON_SAMPLING", **_run(ea_command, repo_root)}
        stages.append(ea_stage)

        if ea_stage["exit_code"] != 0:
            metric_stage = {"stage": "CURRENT_HEIGHT_DIFFERENCE_METRIC_CONSISTENCY", "exit_code": 2, "status": "SKIPPED_EA_DTM1M_GATE_FAILED"}
            terrain_stage = {"stage": "OS_TERRAIN50_PREPARATION_AND_CROSSCHECK", "exit_code": 2, "status": "SKIPPED_EA_DTM1M_GATE_FAILED"}
            stages.extend([metric_stage, terrain_stage])
        else:
            metric_command = [
                sys.executable, str(metric_guard),
                "--ea-samples", str(ea_output),
                "--preserved-evidence", str(args.preserved_metric_evidence),
                "--expected-coverage-id", args.coverage_id,
                "--tolerance-m", str(args.height_metric_tolerance_m),
                "--output", str(metric_output),
            ]
            metric_stage = {"stage": "CURRENT_HEIGHT_DIFFERENCE_METRIC_CONSISTENCY", **_run(metric_command, repo_root)}
            stages.append(metric_stage)

            if metric_stage["exit_code"] != 0:
                terrain_stage = {"stage": "OS_TERRAIN50_PREPARATION_AND_CROSSCHECK", "exit_code": 2, "status": "SKIPPED_CURRENT_HEIGHT_METRIC_GATE_FAILED"}
                stages.append(terrain_stage)
            else:
                terrain_command = [
                    sys.executable, str(terrain_wrapper),
                    "--repo-root", str(repo_root),
                    "--hmlr-exact-matches", str(args.hmlr_exact_matches),
                    "--ea-samples", str(ea_output),
                    "--output-dir", str(args.output_dir / "terrain50_preparation"),
                    "--output", str(terrain_output),
                ]
                archive = args.terrain50_archive or (Path(os.environ["AAYS_TERRAIN50_ARCHIVE"]) if os.environ.get("AAYS_TERRAIN50_ARCHIVE") else None)
                root = args.terrain50_root or (Path(os.environ["AAYS_TERRAIN50_ROOT"]) if os.environ.get("AAYS_TERRAIN50_ROOT") else None)
                if archive:
                    terrain_command.extend(["--terrain50-archive", str(archive)])
                elif root:
                    terrain_command.extend(["--terrain50-root", str(root)])
                terrain_stage = {"stage": "OS_TERRAIN50_PREPARATION_AND_CROSSCHECK", **_run(terrain_command, repo_root)}
                stages.append(terrain_stage)

        ea_payload = _load(ea_output) if ea_output.is_file() else {}
        metric_payload = _load(metric_output) if metric_output.is_file() else {}
        terrain_payload = _load(terrain_output) if terrain_output.is_file() else {}
        metric_success = (
            metric_payload.get("status") == "THREE_CURRENT_EA_HEIGHT_DIFFERENCES_MATCH_PRESERVED_EXACT_RESULTS"
            and metric_payload.get("row_count") == 3
        )
        numeric_success = (
            ea_payload.get("status") == "THREE_EA_DTM1M_POLYGON_SAMPLES_READY"
            and metric_success
            and terrain_payload.get("status") == "THREE_OS_TERRAIN50_CROSSCHECKS_READY"
            and terrain_payload.get("accuracy_screening_passed") is True
        )

        ea_rows = {int(row["row_no"]): row for row in ea_payload.get("samples", [])}
        metric_rows = {int(row["row_no"]): row for row in metric_payload.get("rows", [])}
        terrain_rows = {int(row["row_no"]): row for row in terrain_payload.get("crosschecks", [])}
        measured_rows: list[dict[str, Any]] = []
        if numeric_success:
            if sorted(ea_rows) != TARGET_ROWS or sorted(metric_rows) != TARGET_ROWS or sorted(terrain_rows) != TARGET_ROWS:
                raise ValueError(f"official numeric exact row sets mismatch: ea={sorted(ea_rows)} metric={sorted(metric_rows)} terrain={sorted(terrain_rows)}")
            for row_no in TARGET_ROWS:
                ea_row = ea_rows[row_no]
                metric_row = metric_rows[row_no]
                os_row = terrain_rows[row_no]
                if str(ea_row["hmlr_inspire_id"]) != str(metric_row["hmlr_inspire_id"]) or str(metric_row["hmlr_inspire_id"]) != str(os_row["hmlr_inspire_id"]):
                    raise ValueError(f"HMLR binding mismatch across numeric stages for row {row_no}")
                measured_rows.append({
                    "row_no": row_no,
                    "parcel_id": ea_row["parcel_id"],
                    "hmlr_inspire_id": ea_row["hmlr_inspire_id"],
                    "height_difference_m": metric_row["height_difference_m"],
                    "ea_height_min_m_odn": metric_row["height_min_m_odn"],
                    "ea_height_max_m_odn": metric_row["height_max_m_odn"],
                    "parcel_elevation_median_m_odn": metric_row["parcel_elevation_median_m_odn"],
                    "ea_dtm1m_q1_m_odn": ea_row["q1_m_odn"],
                    "ea_dtm1m_q3_m_odn": ea_row["q3_m_odn"],
                    "ea_valid_pixel_count": ea_row["valid_pixel_count"],
                    "os_terrain50_median_m_odn": os_row["terrain50_median_m_odn"],
                    "os_terrain50_minus_ea_median_m": os_row["terrain50_minus_ea_median_m"],
                    "height_difference_metric": "EA_DTM1M_MAX_MINUS_MIN_INSIDE_EXACT_HMLR_POLYGON",
                    "parcel_elevation_median_is_distinct_metric": True,
                    "preserved_height_difference_m": metric_row["preserved_height_difference_m"],
                    "current_minus_preserved_height_difference_m": metric_row["current_minus_preserved_height_difference_m"],
                    "result_confidence_percent": metric_row["preserved_result_confidence_percent"],
                    "primary_numeric_source": "Environment Agency LiDAR Composite DTM 1m",
                    "secondary_crosscheck_source": "OS Terrain 50",
                    "measurement_geometry": "exact HMLR INSPIRE polygon",
                    "processing_crs": "EPSG:27700",
                    "vertical_reference": "Ordnance Datum Newlyn",
                    "measurement_accuracy_score_4": "3.4/4_pending_human_crosscheck_review",
                    "final_ready": False,
                    "fake_data": False,
                })

        status = "THREE_OFFICIAL_NUMERIC_ROWS_READY_PENDING_WEB_ACCEPTANCE" if numeric_success else "BLOCKED_OFFICIAL_NUMERIC_GATE"
        payload = {
            "schema_version": 7,
            "slot_id": "height_difference_2",
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "status": status,
            "stage_order": ["THREE_EXACT_HMLR_INSPIRE_POLYGONS", "EA_DTM1M_POLYGON_SAMPLING", "CURRENT_HEIGHT_DIFFERENCE_METRIC_CONSISTENCY", "OS_DOWNLOADS_API_OR_CONFIGURED_TERRAIN50", "OS_TERRAIN50_CROSSCHECK", "CURRENT_WORKTREE_CANDIDATE_BINDING", "PORT_8012_WEB_ACCEPTANCE"],
            "stages": stages,
            "hmlr_exact_matches_path": str(args.hmlr_exact_matches),
            "ea_output_path": str(ea_output),
            "height_metric_output_path": str(metric_output),
            "preserved_metric_evidence_path": str(args.preserved_metric_evidence),
            "terrain50_output_path": str(terrain_output),
            "official_numeric_row_count": len(measured_rows),
            "measured_rows": measured_rows,
            "numeric_gate_ready": numeric_success,
            "height_metric_consistency_required": True,
            "height_metric_consistency_passed": metric_success,
            "height_difference_metric": "EA_DTM1M_MAX_MINUS_MIN_INSIDE_EXACT_HMLR_POLYGON",
            "parcel_elevation_median_is_distinct_metric": True,
            "ea_coverage_id_required": EXPECTED_EA_COVERAGE_ID,
            "ea_coverage_id_pinned": ea_payload.get("coverage_id") == EXPECTED_EA_COVERAGE_ID,
            "web_acceptance_required": True,
            "web_acceptance_passed": False,
            "current_candidate_bytes_required": True,
            "current_candidate_transport": "LOCAL_CURRENT_WORKTREE_PRE_ACCEPTANCE",
            "operation_file_path_guard_required": True,
            "example_file_path_guard_required": True,
            "web_base_autoprobe_required": True,
            "automatic_final_promotion": False,
            "human_crosscheck_review_required": True,
            "expected_web_operation_rows": args.expected_web_operation_rows,
            "source_urls": {"hmlr_inspire": "https://use-land-property-data.service.gov.uk/datasets/inspire/download", "ea_dtm1m_wcs": "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs", "os_downloads_api": "https://api.os.uk/downloads/v1/products", "os_terrain50": "https://osdatahub.os.uk/downloads/open/Terrain50"},
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 2
    except Exception as exc:
        payload = {
            "schema_version": 7,
            "slot_id": "height_difference_2",
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "status": "BLOCKED_OFFICIAL_NUMERIC_GATE_ORCHESTRATOR",
            "error": f"{type(exc).__name__}: {exc}",
            "stages": stages,
            "official_numeric_row_count": 0,
            "numeric_gate_ready": False,
            "height_metric_consistency_required": True,
            "height_metric_consistency_passed": False,
            "height_difference_metric": "EA_DTM1M_MAX_MINUS_MIN_INSIDE_EXACT_HMLR_POLYGON",
            "parcel_elevation_median_is_distinct_metric": True,
            "ea_coverage_id_required": EXPECTED_EA_COVERAGE_ID,
            "web_acceptance_required": True,
            "web_acceptance_passed": False,
            "current_candidate_bytes_required": True,
            "current_candidate_transport": "LOCAL_CURRENT_WORKTREE_PRE_ACCEPTANCE",
            "operation_file_path_guard_required": True,
            "example_file_path_guard_required": True,
            "web_base_autoprobe_required": True,
            "expected_web_operation_rows": args.expected_web_operation_rows,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 2

    _write(args.final_output, payload)
    _write(execution_output, payload)
    preacceptance_payload = _web_candidate_payload(payload, args.expected_web_operation_rows)
    _write(candidate_preacceptance_output, preacceptance_payload)
    expected_candidates_sha256 = _sha256(candidate_preacceptance_output)
    payload["preacceptance_candidates_path"] = str(candidate_preacceptance_output)
    payload["preacceptance_candidates_sha256"] = expected_candidates_sha256
    if args.web_output:
        _write(args.web_output, preacceptance_payload)
    _write(args.final_output, payload)
    _write(execution_output, payload)

    if payload.get("numeric_gate_ready") is True:
        web_command = [sys.executable, str(web_verifier), "--base-url", args.web_base_url, "--expected-operation-rows", str(args.expected_web_operation_rows), "--candidate-payload", str(candidate_preacceptance_output), "--expected-candidates-sha256", expected_candidates_sha256, "--output", str(web_acceptance_output)]
        web_stage = {"stage": "PORT_8012_WEB_ACCEPTANCE", **_run(web_command, repo_root)}
        stages.append(web_stage)
        web_payload = _load(web_acceptance_output) if web_acceptance_output.is_file() else {}
        web_passed = (
            web_stage["exit_code"] == 0
            and web_payload.get("status") == "PORT_8012_WEB_ACCEPTANCE_PASSED"
            and int(web_payload.get("visible_operation_rows", 0)) >= args.expected_web_operation_rows
            and web_payload.get("candidate_local_sha256") == expected_candidates_sha256
            and web_payload.get("candidate_payload_transport") == "LOCAL_CURRENT_WORKTREE_PRE_ACCEPTANCE"
            and web_payload.get("current_candidate_bytes_verified") is True
            and web_payload.get("current_candidate_metric_binding_verified") is True
            and web_payload.get("operation_file_path_guard_verified") is True
            and web_payload.get("example_file_path_guard_verified") is True
            and sorted(web_payload.get("candidate_rows", [])) == TARGET_ROWS
            and sorted(web_payload.get("site_measured_candidate_rows", [])) == TARGET_ROWS
        )
        payload["web_acceptance_passed"] = web_passed
        payload["web_acceptance_output_path"] = str(web_acceptance_output)
        payload["web_acceptance"] = web_payload
        if web_passed:
            payload["status"] = "THREE_OFFICIAL_NUMERIC_ROWS_AND_PORT_8012_ACCEPTANCE_READY_PENDING_REVIEW"
            code = 0
        else:
            payload["status"] = "BLOCKED_PORT_8012_WEB_ACCEPTANCE_AFTER_NUMERIC_READY"
            code = 2
        payload["stages"] = stages
        _write(args.final_output, payload)
        _write(execution_output, payload)
        if args.web_output:
            _write(args.web_output, _web_candidate_payload(payload, args.expected_web_operation_rows))

    print(json.dumps({"ok": code == 0, "status": payload["status"], "rows": payload.get("official_numeric_row_count", 0), "height_metric_consistency_passed": payload.get("height_metric_consistency_passed", False), "web_acceptance_passed": payload.get("web_acceptance_passed", False), "expected_web_operation_rows": args.expected_web_operation_rows, "preacceptance_candidates_sha256": payload.get("preacceptance_candidates_sha256")}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
