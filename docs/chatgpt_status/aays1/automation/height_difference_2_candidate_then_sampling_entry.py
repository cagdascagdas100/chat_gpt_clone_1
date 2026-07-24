from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
EXPECTED_BRANCH = "codex/aays-single-runner-v5-20260706"
EXPECTED_PAGE_KEY = "aays1"

def _repo_root() -> Path:
    configured = os.environ.get("AAYS_REPO_ROOT", "").strip()
    return Path(configured).resolve() if configured else Path.cwd().resolve()

def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def _run(command: list[str], cwd: Path, stage: str) -> dict[str, Any]:
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "stage": stage,
        "command": command,
        "exit_code": process.returncode,
        "stdout": process.stdout[-8000:],
        "stderr": process.stderr[-8000:],
    }

def _run_candidate_extraction(repo_root: Path) -> dict[str, Any]:
    script = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/automation/007_extract_three_canonical_candidates.py"
    source = repo_root / "england_map_web/data/program_layer_matrix/topography.geojson"
    output = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs/005_canonical_candidate_seeds_latest.json"
    web_output = repo_root / "england_map_web/data/aays_21_slots/height_difference_2/candidate_seeds_latest.json"
    if not script.is_file():
        return {"stage": "CANONICAL_CANDIDATE_SEED_EXTRACTION", "exit_code": 2, "status": "BLOCKED_CANDIDATE_EXTRACTOR_SCRIPT_MISSING"}
    result = _run([
        sys.executable, str(script), "--source", str(source), "--output", str(output), "--web-output", str(web_output)
    ], repo_root, "CANONICAL_CANDIDATE_SEED_EXTRACTION")
    result.update({"script": str(script), "source": str(source), "output": str(output), "web_output": str(web_output)})
    if output.is_file():
        try:
            payload = json.loads(output.read_text(encoding="utf-8"))
            result["candidate_status"] = payload.get("status")
            result["candidate_seed_count"] = payload.get("candidate_seed_count", 0)
            result["source_sha256"] = payload.get("source_sha256")
        except Exception as exc:
            result["candidate_output_read_error"] = f"{type(exc).__name__}: {exc}"
    return result

def _run_hmlr_polygon_preparation(repo_root: Path) -> dict[str, Any]:
    script = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/automation/011_prepare_three_hmlr_polygons.py"
    seed_manifest = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs/005_canonical_candidate_seeds_latest.json"
    output_dir = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs/007_hmlr_polygon_preparation_latest"
    if not script.is_file():
        return {"stage": "HMLR_EXACT_POLYGON_PREPARATION", "exit_code": 2, "status": "BLOCKED_HMLR_ORCHESTRATOR_MISSING"}
    result = _run([
        sys.executable, str(script), "--seed-manifest", str(seed_manifest), "--output-dir", str(output_dir)
    ], repo_root, "HMLR_EXACT_POLYGON_PREPARATION")
    execution = output_dir / "hmlr_polygon_preparation_execution.json"
    exact_matches = output_dir / "hmlr_exact_matches.json"
    starter = output_dir / "starter_manifest.json"
    result.update({
        "script": str(script), "seed_manifest": str(seed_manifest), "output_dir": str(output_dir),
        "execution": str(execution), "starter_manifest": str(starter), "hmlr_exact_matches": str(exact_matches),
    })
    if execution.is_file():
        try:
            payload = json.loads(execution.read_text(encoding="utf-8"))
            result["hmlr_status"] = payload.get("status")
            result["hmlr_source_manifest"] = payload.get("hmlr_source_manifest")
        except Exception as exc:
            result["hmlr_output_read_error"] = f"{type(exc).__name__}: {exc}"
    return result

def _run_official_numeric_gate(repo_root: Path) -> dict[str, Any]:
    script = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/automation/014_run_official_numeric_gate.py"
    hmlr = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs/007_hmlr_polygon_preparation_latest/hmlr_exact_matches.json"
    output_dir = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs/008_official_numeric_gate_latest"
    final_output = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs/003_height_difference_2_canonical_export_official_sampling_latest.json"
    web_output = repo_root / "england_map_web/data/aays_21_slots/height_difference_2/candidates_latest.json"
    if not script.is_file():
        return {"stage": "OFFICIAL_NUMERIC_GATE", "exit_code": 2, "status": "BLOCKED_NUMERIC_ORCHESTRATOR_MISSING"}
    command = [
        sys.executable, str(script), "--repo-root", str(repo_root), "--hmlr-exact-matches", str(hmlr),
        "--output-dir", str(output_dir), "--final-output", str(final_output), "--web-output", str(web_output),
    ]
    if os.environ.get("AAYS_EA_DTM1M_COVERAGE_ID"):
        command.extend(["--coverage-id", os.environ["AAYS_EA_DTM1M_COVERAGE_ID"]])
    result = _run(command, repo_root, "OFFICIAL_NUMERIC_GATE")
    result.update({
        "script": str(script), "hmlr_exact_matches": str(hmlr), "output_dir": str(output_dir),
        "final_output": str(final_output), "web_output": str(web_output),
    })
    if final_output.is_file():
        try:
            payload = json.loads(final_output.read_text(encoding="utf-8"))
            result["numeric_status"] = payload.get("status")
            result["official_numeric_row_count"] = payload.get("official_numeric_row_count", 0)
        except Exception as exc:
            result["numeric_output_read_error"] = f"{type(exc).__name__}: {exc}"
    return result

def main() -> int:
    branch = os.environ.get("AAYS_TARGET_BRANCH", "").strip()
    if branch and branch != EXPECTED_BRANCH:
        raise RuntimeError("HEIGHT_DIFFERENCE_2_WRONG_BRANCH")
    page_key = os.environ.get("AAYS_PAGE_KEY", "").strip()
    if page_key and page_key != EXPECTED_PAGE_KEY:
        raise RuntimeError("HEIGHT_DIFFERENCE_2_WRONG_PAGE_KEY")

    repo_root = _repo_root()
    stages: list[dict[str, Any]] = []
    candidate_result = _run_candidate_extraction(repo_root)
    stages.append(candidate_result)

    if candidate_result.get("exit_code") != 0:
        hmlr_result = {"stage": "HMLR_EXACT_POLYGON_PREPARATION", "exit_code": 2, "status": "SKIPPED_CANDIDATE_GATE_FAILED"}
        numeric_result = {"stage": "OFFICIAL_NUMERIC_GATE", "exit_code": 2, "status": "SKIPPED_CANDIDATE_GATE_FAILED"}
    else:
        hmlr_result = _run_hmlr_polygon_preparation(repo_root)
        if hmlr_result.get("exit_code") != 0:
            numeric_result = {"stage": "OFFICIAL_NUMERIC_GATE", "exit_code": 2, "status": "SKIPPED_HMLR_EXACT_POLYGON_GATE_FAILED"}
        else:
            numeric_result = _run_official_numeric_gate(repo_root)

    stages.extend([hmlr_result, numeric_result])
    all_codes = [int(stage.get("exit_code", 2)) for stage in stages]
    success = all(code == 0 for code in all_codes)
    summary = {
        "schema_version": 3,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "stage_order": [
            "CANONICAL_CANDIDATE_SEED_EXTRACTION",
            "HMLR_EXACT_POLYGON_PREPARATION",
            "OFFICIAL_NUMERIC_GATE",
        ],
        "stages": stages,
        "candidate_seed_count": candidate_result.get("candidate_seed_count", 0),
        "candidate_extraction_exit_code": candidate_result.get("exit_code", 2),
        "hmlr_polygon_exit_code": hmlr_result.get("exit_code", 2),
        "numeric_gate_exit_code": numeric_result.get("exit_code", 2),
        "official_numeric_row_count": numeric_result.get("official_numeric_row_count", 0),
        "status": "THREE_SOURCE_OFFICIAL_NUMERIC_GATE_EXECUTED" if success else "BLOCKED_FAIL_CLOSED_STAGE_GATE",
        "numeric_started_without_three_exact_hmlr_polygons": False,
        "automatic_final_promotion": False,
        "single_shared_runner_only": True,
        "new_runner": False,
        "parallel_runner": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    summary_path = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs/006_candidate_seed_and_sampling_entrypoint_latest.json"
    _write_json(summary_path, summary)
    return 0 if success else next((code for code in all_codes if code != 0), 2)

if __name__ == "__main__":
    raise SystemExit(main())
