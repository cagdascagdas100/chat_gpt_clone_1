#!/usr/bin/env python3
"""No-argument same-task entrypoint for strict12 local acceptance and publish handoff.

This entrypoint reuses the exact runtime Python/PowerShell/Git identities validated
by the preflight chain, runs strict/local acceptance, freshly fetches the canonical
origin branch, captures the exact pre-publish origin HEAD, creates the seven-file
publish manifest bound to that history point, and stops at PUBLISH_PENDING. It
never creates a second task/runner and never pushes directly.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
BRANCH = "codex/aays-single-runner-v5-20260706"
EXPECTED_ROWS = list(range(61540, 61552))
ENV_PREFLIGHT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json"


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("PUBLISHER_REPO_ROOT_NOT_FOUND")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def run(command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {"command": command, "exit_code": proc.returncode, "stdout": proc.stdout[-16000:], "stderr": proc.stderr[-16000:]}


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm_executable(value: str) -> str:
    return os.path.normcase(str(Path(value).resolve()))


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo = find_repo_root(script_dir)
    current_task = load_json(repo / "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json")
    if current_task.get("task_id") != TASK_ID:
        raise ValueError("current task_id mismatch")
    if current_task.get("continuation_key") != CONTINUATION:
        raise ValueError("current continuation_key mismatch")
    if current_task.get("single_runner_only") is not True or current_task.get("new_runner") is not False:
        raise ValueError("single-runner contract mismatch")

    env_preflight_path = repo / ENV_PREFLIGHT_REL
    if not env_preflight_path.is_file():
        raise FileNotFoundError(f"runtime environment preflight missing: {env_preflight_path}")
    env_preflight = load_json(env_preflight_path)
    if int(env_preflight.get("schema_version") or 0) < 3:
        raise ValueError("runtime environment preflight schema lacks executable identity")
    if int(env_preflight.get("checks_passed") or -1) != int(env_preflight.get("checks_total") or -2):
        raise ValueError("runtime environment preflight checks incomplete")
    if env_preflight.get("bootstrap_042_executed") is not True or int(env_preflight.get("bootstrap_042_exit_code") or -1) != 0:
        raise ValueError("runtime environment preflight did not complete bootstrap 042")
    if int(env_preflight.get("numeric_values_written") or 0) != 0:
        raise ValueError("runtime environment preflight unexpectedly wrote numeric values")

    runtime_identity = env_preflight.get("runtime_identity") or {}
    validated_python = str(runtime_identity.get("python_executable") or env_preflight.get("python_executable") or "").strip()
    validated_powershell = str(runtime_identity.get("powershell_executable") or env_preflight.get("powershell_path") or "").strip()
    validated_git = str(runtime_identity.get("git_executable") or env_preflight.get("git_executable") or "").strip()
    if not validated_python or not Path(validated_python).is_file():
        raise ValueError("validated Python executable missing")
    if not validated_powershell or not Path(validated_powershell).is_file():
        raise ValueError("validated PowerShell executable missing")
    if not validated_git or not Path(validated_git).is_file():
        raise ValueError("validated Git executable missing")
    if norm_executable(validated_python) != norm_executable(sys.executable):
        raise ValueError(f"runtime Python identity drift: preflight={validated_python} current={sys.executable}")

    powershell = str(Path(validated_powershell).resolve())
    git_executable = str(Path(validated_git).resolve())
    python_executable = str(Path(sys.executable).resolve())
    strict_wrapper = script_dir / "036_run_batch131_strict12_with_local_acceptance.ps1"
    manifest_generator = script_dir / "037_prepare_batch132_publish_manifest.py"
    for path in (strict_wrapper, manifest_generator):
        if not path.is_file():
            raise FileNotFoundError(path)

    strict_result = run([
        powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(strict_wrapper),
        "-RepoRoot", str(repo), "-PythonExe", python_executable, "-PowerShellExe", powershell,
    ], repo)
    if strict_result["exit_code"] != 0:
        raise RuntimeError(f"strict/local acceptance failed: {strict_result['stderr'][-2000:]}")

    acceptance = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/029_batch131_strict12_acceptance/batch131_strict12_local_acceptance.json"
    accepted = load_json(acceptance)
    if accepted.get("local_acceptance_passed") is not True:
        raise ValueError("local acceptance did not pass")
    if [int(v) for v in (accepted.get("expected_rows") or [])] != EXPECTED_ROWS:
        raise ValueError("local acceptance row set mismatch")
    if accepted.get("remote_github_readback_required") is not True:
        raise ValueError("remote readback gate disabled")

    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    fetch_result = run([git_executable, "-C", str(repo), "fetch", "--no-tags", "origin", fetch_spec], repo)
    if fetch_result["exit_code"] != 0:
        raise RuntimeError(f"pre-publish origin fetch failed: {fetch_result['stderr'][-2000:]}")
    remote_ref = f"refs/remotes/origin/{BRANCH}"
    head_result = run([git_executable, "-C", str(repo), "rev-parse", remote_ref], repo)
    pre_publish_origin_head = head_result["stdout"].strip().lower()
    if head_result["exit_code"] != 0 or len(pre_publish_origin_head) != 40:
        raise RuntimeError("cannot resolve fresh pre-publish origin HEAD")

    publish_manifest = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/031_batch132_remote_readback/batch132_publish_manifest.json"
    manifest_result = run([
        python_executable, str(manifest_generator), "--repo-root", str(repo), "--output", str(publish_manifest),
        "--pre-publish-origin-head", pre_publish_origin_head,
    ], repo)
    if manifest_result["exit_code"] != 0:
        raise RuntimeError(f"publish manifest generation failed: {manifest_result['stderr'][-2000:]}")

    manifest = load_json(publish_manifest)
    if int(manifest.get("schema_version") or 0) < 2:
        raise ValueError("publish manifest lacks pre-publish history binding")
    if manifest.get("ready_for_serial_publisher") is not True:
        raise ValueError("publish manifest not ready")
    if manifest.get("task_id") != TASK_ID or manifest.get("continuation_key") != CONTINUATION:
        raise ValueError("publish manifest task/continuation mismatch")
    if [int(v) for v in (manifest.get("expected_rows") or [])] != EXPECTED_ROWS:
        raise ValueError("publish manifest row set mismatch")
    if len(manifest.get("files") or []) != 7:
        raise ValueError("publish manifest file count must equal 7")
    if str(manifest.get("pre_publish_origin_head") or "").lower() != pre_publish_origin_head:
        raise ValueError("publish manifest pre-publish origin HEAD mismatch")

    output = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_prepare_publish_handoff.json"
    payload = {
        "schema_version": 4,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION,
        "status": "PUBLISH_PENDING_SERIAL_PUBLISHER_REQUIRED",
        "runtime_identity_preflight": ENV_PREFLIGHT_REL,
        "runtime_python_executable": python_executable,
        "runtime_powershell_executable": powershell,
        "runtime_git_executable": git_executable,
        "runtime_identity_match_passed": True,
        "strict_local_acceptance_passed": True,
        "canonical_branch": BRANCH,
        "pre_publish_origin_fetch_refspec": fetch_spec,
        "pre_publish_origin_fetch_performed": True,
        "pre_publish_origin_head": pre_publish_origin_head,
        "expected_rows": EXPECTED_ROWS,
        "expected_verified_count": 12,
        "publish_manifest": str(publish_manifest.relative_to(repo)).replace("\\", "/"),
        "publish_file_count": 7,
        "serial_publisher_required": True,
        "child_direct_push_performed": False,
        "post_publish_entrypoint": "docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py",
        "numeric_final_acceptance": "PENDING_SERIAL_PUBLISH_AND_REMOTE_HISTORY_BOUND_READBACK",
        "new_task_created": False,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "numeric_values_changed": 0,
        "final_ready": False,
        "fake_data": False,
        "stages": {"strict_local_acceptance": strict_result, "pre_publish_origin_fetch": fetch_result, "pre_publish_origin_head": head_result, "publish_manifest": manifest_result},
    }
    write(output, payload)
    print(json.dumps({"ok": True, "status": payload["status"], "pre_publish_origin_head": pre_publish_origin_head, "python": python_executable, "powershell": powershell, "git": git_executable, "output": str(output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
