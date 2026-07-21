from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import subprocess
import sys

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
EXPECTED_BRANCH = "codex/aays-single-runner-v5-20260706"
EXPECTED_PAGE_KEY = "aays1"


def _repo_root() -> Path:
    configured = os.environ.get("AAYS_REPO_ROOT", "").strip()
    return Path(configured).resolve() if configured else Path.cwd().resolve()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run_candidate_extraction(repo_root: Path) -> dict[str, object]:
    script = repo_root / "docs" / "chatgpt_status" / "topography" / "shards" / "height_difference_2" / "automation" / "007_extract_three_canonical_candidates.py"
    source = repo_root / "england_map_web" / "data" / "program_layer_matrix" / "topography.geojson"
    output = repo_root / "docs" / "chatgpt_status" / "topography" / "shards" / "height_difference_2" / "runner_outputs" / "005_canonical_candidate_seeds_latest.json"
    web_output = repo_root / "england_map_web" / "data" / "aays_21_slots" / "height_difference_2" / "candidate_seeds_latest.json"
    result: dict[str, object] = {
        "stage": "CANONICAL_CANDIDATE_SEED_EXTRACTION",
        "script": str(script),
        "source": str(source),
        "output": str(output),
        "web_output": str(web_output),
    }
    if not script.is_file():
        result.update({"exit_code": 2, "status": "BLOCKED_CANDIDATE_EXTRACTOR_SCRIPT_MISSING"})
        return result
    command = [
        sys.executable,
        str(script),
        "--source",
        str(source),
        "--output",
        str(output),
        "--web-output",
        str(web_output),
    ]
    process = subprocess.run(command, cwd=repo_root, text=True, capture_output=True, check=False)
    result.update(
        {
            "command": command,
            "exit_code": process.returncode,
            "stdout": process.stdout[-8000:],
            "stderr": process.stderr[-8000:],
            "status": "CANDIDATE_EXTRACTION_EXECUTED",
        }
    )
    if output.is_file():
        try:
            payload = json.loads(output.read_text(encoding="utf-8"))
            result["candidate_status"] = payload.get("status")
            result["candidate_seed_count"] = payload.get("candidate_seed_count", 0)
            result["source_sha256"] = payload.get("source_sha256")
        except Exception as exc:
            result["candidate_output_read_error"] = f"{type(exc).__name__}: {exc}"
    return result


def _run_existing_entrypoint(repo_root: Path) -> tuple[int, dict[str, object]]:
    existing = repo_root / "docs" / "chatgpt_status" / "aays1" / "automation" / "height_difference_2_official_sampling_entry.py"
    result: dict[str, object] = {
        "stage": "EXPANDED_DISCOVERY_AND_OFFICIAL_SAMPLING",
        "existing_entrypoint": str(existing),
    }
    if not existing.is_file():
        result.update({"exit_code": 2, "status": "BLOCKED_EXISTING_ENTRYPOINT_MISSING"})
        return 2, result
    exit_code = 0
    try:
        runpy.run_path(str(existing), run_name="__main__")
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    except Exception as exc:
        exit_code = 2
        result["error"] = f"{type(exc).__name__}: {exc}"
    result.update({"exit_code": exit_code, "status": "EXISTING_ENTRYPOINT_EXECUTED"})
    return exit_code, result


def main() -> int:
    branch = os.environ.get("AAYS_TARGET_BRANCH", "").strip()
    if branch and branch != EXPECTED_BRANCH:
        raise RuntimeError("HEIGHT_DIFFERENCE_2_WRONG_BRANCH")
    page_key = os.environ.get("AAYS_PAGE_KEY", "").strip()
    if page_key and page_key != EXPECTED_PAGE_KEY:
        raise RuntimeError("HEIGHT_DIFFERENCE_2_WRONG_PAGE_KEY")
    repo_root = _repo_root()
    candidate_result = _run_candidate_extraction(repo_root)
    os.environ["AAYS_HEIGHT_DIFFERENCE_2_CANDIDATE_SEED_OUTPUT"] = str(
        repo_root / "docs" / "chatgpt_status" / "topography" / "shards" / "height_difference_2" / "runner_outputs" / "005_canonical_candidate_seeds_latest.json"
    )
    sampling_code, sampling_result = _run_existing_entrypoint(repo_root)
    summary = {
        "schema_version": 1,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "stages": [candidate_result, sampling_result],
        "candidate_seed_count": candidate_result.get("candidate_seed_count", 0),
        "candidate_extraction_exit_code": candidate_result.get("exit_code", 2),
        "sampling_exit_code": sampling_code,
        "status": "CANDIDATE_SEEDS_AND_SAMPLING_EXECUTED" if candidate_result.get("exit_code") == 0 and sampling_code == 0 else "BLOCKED_CANDIDATE_OR_SAMPLING_STAGE",
        "official_polygon_measurements_written_by_wrapper": 0,
        "single_shared_runner_only": True,
        "new_runner": False,
        "parallel_runner": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    summary_path = repo_root / "docs" / "chatgpt_status" / "topography" / "shards" / "height_difference_2" / "runner_outputs" / "006_candidate_seed_and_sampling_entrypoint_latest.json"
    _write_json(summary_path, summary)
    return sampling_code if sampling_code != 0 else int(candidate_result.get("exit_code", 2))


if __name__ == "__main__":
    raise SystemExit(main())
