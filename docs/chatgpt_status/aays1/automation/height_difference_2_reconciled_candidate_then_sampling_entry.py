#!/usr/bin/env python3
"""Attempt-020 reconciled Point -> HMLR -> official numeric entrypoint."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
ATTEMPT_ID = "height-difference-2-20260721-020"
EXPECTED_BRANCH = "codex/aays-single-runner-v5-20260706"
EXPECTED_PAGE_KEY = "aays1"
TARGET_ROWS = [30762, 46142, 61522]


def _repo_root() -> Path:
    configured = os.environ.get("AAYS_REPO_ROOT", "").strip()
    return Path(configured).resolve() if configured else Path.cwd().resolve()


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _run(command: list[str], cwd: Path, stage: str, timeout_seconds: int) -> dict[str, Any]:
    try:
        process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout_seconds)
        return {
            "stage": stage,
            "command": command,
            "exit_code": process.returncode,
            "timed_out": False,
            "stdout": process.stdout[-12000:],
            "stderr": process.stderr[-12000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "stage": stage,
            "command": command,
            "exit_code": 124,
            "timed_out": True,
            "stdout": (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-12000:] if isinstance(exc.stderr, str) else "",
        }


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    branch = os.environ.get("AAYS_TARGET_BRANCH", "").strip()
    page_key = os.environ.get("AAYS_PAGE_KEY", "").strip()
    task_id = os.environ.get("AAYS_TASK_ID", "").strip()
    attempt_id = os.environ.get("AAYS_ATTEMPT_ID", "").strip()
    if branch and branch != EXPECTED_BRANCH:
        raise RuntimeError("HEIGHT_DIFFERENCE_2_WRONG_BRANCH")
    if page_key and page_key != EXPECTED_PAGE_KEY:
        raise RuntimeError("HEIGHT_DIFFERENCE_2_WRONG_PAGE_KEY")
    if task_id and task_id != TASK_ID:
        raise RuntimeError("HEIGHT_DIFFERENCE_2_WRONG_TASK")
    if attempt_id and attempt_id != ATTEMPT_ID:
        raise RuntimeError("HEIGHT_DIFFERENCE_2_WRONG_ATTEMPT")

    repo_root = _repo_root()
    automation = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/automation"
    runner_outputs = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs"
    web_root = repo_root / "england_map_web/data/aays_21_slots/height_difference_2"

    extractor = automation / "043_extract_reconciled_exact_candidates.py"
    hmlr_recovery = automation / "043_prepare_hmlr_sources_and_match.py"
    numeric_gate = automation / "014_run_official_numeric_gate.py"
    source = repo_root / "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
    point_evidence = web_root / "canonical_points_runtime_032.json"
    hmlr_evidence = web_root / "hmlr_exact_polygons_runtime_034_v2.json"
    seed_output = runner_outputs / "005_canonical_candidate_seeds_latest.json"
    seed_web_output = web_root / "candidate_seeds_latest.json"
    hmlr_output_dir = runner_outputs / "007_hmlr_polygon_preparation_latest"
    hmlr_exact = hmlr_output_dir / "hmlr_exact_matches.json"
    numeric_output_dir = runner_outputs / "008_official_numeric_gate_latest"
    final_output = runner_outputs / "003_height_difference_2_canonical_export_official_sampling_latest.json"
    web_output = web_root / "candidates_latest.json"
    summary_output = runner_outputs / "006_candidate_seed_and_sampling_entrypoint_latest.json"

    required = [extractor, hmlr_recovery, numeric_gate, source, point_evidence, hmlr_evidence]
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        payload = {
            "schema_version": 4,
            "slot_id": "height_difference_2",
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "status": "BLOCKED_RECONCILED_ENTRYPOINT_INPUT_MISSING",
            "missing": missing,
            "target_rows": TARGET_ROWS,
            "official_numeric_row_count": 0,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        _write(summary_output, payload)
        return 2

    stages: list[dict[str, Any]] = []
    candidate_stage = _run([
        sys.executable,
        str(extractor),
        "--source", str(source),
        "--point-evidence", str(point_evidence),
        "--hmlr-evidence", str(hmlr_evidence),
        "--output", str(seed_output),
        "--web-output", str(seed_web_output),
    ], repo_root, "RECONCILED_EXACT_CANDIDATE_SEED_EXTRACTION", 1800)
    stages.append(candidate_stage)
    candidate_payload = _load(seed_output) if seed_output.is_file() else {}

    if candidate_stage["exit_code"] != 0 or candidate_payload.get("candidate_seed_count") != 3:
        hmlr_stage = {"stage": "FRESH_HMLR_GML_REVALIDATION", "exit_code": 2, "status": "SKIPPED_RECONCILED_CANDIDATE_GATE_FAILED"}
        numeric_stage = {"stage": "OFFICIAL_NUMERIC_GATE", "exit_code": 2, "status": "SKIPPED_RECONCILED_CANDIDATE_GATE_FAILED"}
    else:
        hmlr_stage = _run([
            sys.executable,
            str(hmlr_recovery),
            "--seed-manifest", str(seed_output),
            "--output-dir", str(hmlr_output_dir),
            "--timeout", "300",
            "--matcher-timeout", "1800",
        ], repo_root, "FRESH_HMLR_GML_REVALIDATION", 3600)
        hmlr_payload = _load(hmlr_output_dir / "hmlr_polygon_preparation_execution.json") if (hmlr_output_dir / "hmlr_polygon_preparation_execution.json").is_file() else {}
        if hmlr_stage["exit_code"] != 0 or hmlr_payload.get("matched_candidate_count") != 3:
            numeric_stage = {"stage": "OFFICIAL_NUMERIC_GATE", "exit_code": 2, "status": "SKIPPED_FRESH_HMLR_GATE_FAILED"}
        else:
            command = [
                sys.executable,
                str(numeric_gate),
                "--repo-root", str(repo_root),
                "--hmlr-exact-matches", str(hmlr_exact),
                "--output-dir", str(numeric_output_dir),
                "--final-output", str(final_output),
                "--web-output", str(web_output),
                "--expected-web-operation-rows", os.environ.get("AAYS_HEIGHT_DIFFERENCE_2_EXPECTED_WEB_ROWS", "1036"),
            ]
            if os.environ.get("AAYS_EA_DTM1M_COVERAGE_ID"):
                command.extend(["--coverage-id", os.environ["AAYS_EA_DTM1M_COVERAGE_ID"]])
            numeric_stage = _run(command, repo_root, "OFFICIAL_NUMERIC_GATE", 3600)

    stages.extend([hmlr_stage, numeric_stage])
    numeric_payload = _load(final_output) if final_output.is_file() else {}
    success = (
        candidate_stage["exit_code"] == 0
        and hmlr_stage.get("exit_code") == 0
        and numeric_stage.get("exit_code") == 0
        and candidate_payload.get("candidate_seed_count") == 3
        and numeric_payload.get("official_numeric_row_count") == 3
    )
    payload = {
        "schema_version": 4,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "task_version": "6.2-fhost-safe-ffonly-terrain50-webfloor",
        "status": "THREE_SOURCE_OFFICIAL_NUMERIC_GATE_EXECUTED" if success else "BLOCKED_FAIL_CLOSED_RECONCILED_STAGE_GATE",
        "target_rows": TARGET_ROWS,
        "stage_order": [
            "RECONCILED_EXACT_CANDIDATE_SEED_EXTRACTION",
            "FRESH_HMLR_GML_REVALIDATION",
            "OFFICIAL_NUMERIC_GATE",
        ],
        "stages": stages,
        "candidate_seed_count": candidate_payload.get("candidate_seed_count", 0),
        "official_numeric_row_count": numeric_payload.get("official_numeric_row_count", 0),
        "fresh_official_hmlr_revalidation_required": True,
        "nearest_row_fallback_used": False,
        "nearest_polygon_fill_used": False,
        "automatic_final_promotion": False,
        "single_shared_runner_only": True,
        "new_runner": False,
        "parallel_runner": False,
        "actual_business_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    _write(summary_output, payload)
    return 0 if success else next((int(stage.get("exit_code", 2)) for stage in stages if int(stage.get("exit_code", 2)) != 0), 2)


if __name__ == "__main__":
    raise SystemExit(main())
