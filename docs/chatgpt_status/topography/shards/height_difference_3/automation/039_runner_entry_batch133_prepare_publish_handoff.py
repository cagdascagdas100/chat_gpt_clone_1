#!/usr/bin/env python3
"""No-argument same-task entrypoint for strict12 local acceptance and publish handoff.

Batch141 requires the Batch140 fresh-heartbeat/runtime-environment receipts plus a
fresh coordinator runtime-rewire receipt. Immediately before strict measurement it
runs 046, which performs a fresh origin fetch, proves local HEAD still equals origin,
proves exactly one matching queue record exists, and binds request/current-task/queue
Git blobs plus all preflight outputs to the effective 039/040 wiring. The validated
Python/PowerShell/Git identities are then reused through strict measurement and the
serial-publisher handoff. No second task/runner is created and this script never pushes.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
BRANCH = "codex/aays-single-runner-v5-20260706"
EXPECTED_ROWS = list(range(61540, 61552))
TASK_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
HEARTBEAT_PREFLIGHT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json"
ENV_PREFLIGHT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json"
RECEIPT_VALIDATOR_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/046_validate_batch141_coordinator_rewire_receipt.py"
RECEIPT_VALIDATION_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"
PREFLIGHT_TTL_SECONDS = 900


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


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    return {"command": command, "exit_code": proc.returncode, "stdout": proc.stdout[-16000:], "stderr": proc.stderr[-16000:]}


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def norm_executable(value: str) -> str:
    return os.path.normcase(str(Path(value).resolve()))


def parse_utc(value: Any) -> datetime:
    token = str(value or "").strip()
    if not token:
        raise ValueError("missing UTC timestamp")
    if token.endswith("Z"):
        token = token[:-1] + "+00:00"
    parsed = datetime.fromisoformat(token)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo = find_repo_root(script_dir)
    current_task_path = repo / TASK_REL
    current_task = load_json(current_task_path)
    if current_task.get("task_id") != TASK_ID or current_task.get("continuation_key") != CONTINUATION:
        raise ValueError("current task identity mismatch")
    if current_task.get("single_runner_only") is not True or current_task.get("new_runner") is not False or current_task.get("parallel_runner") is not False:
        raise ValueError("single-runner contract mismatch")

    heartbeat_preflight_path = repo / HEARTBEAT_PREFLIGHT_REL
    if not heartbeat_preflight_path.is_file():
        raise FileNotFoundError(f"fresh heartbeat preflight missing: {heartbeat_preflight_path}")
    heartbeat_preflight = load_json(heartbeat_preflight_path)
    if int(heartbeat_preflight.get("schema_version") or 0) < 2:
        raise ValueError("fresh heartbeat receipt schema too old")
    if heartbeat_preflight.get("task_id") != TASK_ID or heartbeat_preflight.get("continuation_key") != CONTINUATION:
        raise ValueError("fresh heartbeat receipt task/continuation mismatch")
    if heartbeat_preflight.get("fresh_host_heartbeat_passed") is not True:
        raise ValueError("fresh host heartbeat did not pass")
    if heartbeat_preflight.get("environment_gate_044_executed") is not True or int(heartbeat_preflight.get("environment_gate_044_exit_code") or -1) != 0:
        raise ValueError("heartbeat chain did not complete environment gate 044")
    if float(heartbeat_preflight.get("global_heartbeat_age_seconds") or 1e18) > float(heartbeat_preflight.get("entry_max_global_heartbeat_age_seconds") or 0):
        raise ValueError("heartbeat receipt exceeds reserved entry freshness budget")

    env_preflight_path = repo / ENV_PREFLIGHT_REL
    if not env_preflight_path.is_file():
        raise FileNotFoundError(f"runtime environment preflight missing: {env_preflight_path}")
    env_preflight = load_json(env_preflight_path)
    if int(env_preflight.get("schema_version") or 0) < 4:
        raise ValueError("runtime environment preflight schema lacks TTL/HEAD/task binding")
    if int(env_preflight.get("checks_passed") or -1) != int(env_preflight.get("checks_total") or -2):
        raise ValueError("runtime environment preflight checks incomplete")
    if env_preflight.get("bootstrap_042_executed") is not True or int(env_preflight.get("bootstrap_042_exit_code") or -1) != 0:
        raise ValueError("runtime environment preflight did not complete bootstrap 042")
    if int(env_preflight.get("numeric_values_written") or 0) != 0 or env_preflight.get("canonical_branch") != BRANCH:
        raise ValueError("runtime environment preflight contract mismatch")

    now = datetime.now(timezone.utc)
    hb_checked = parse_utc(heartbeat_preflight.get("checked_at_utc"))
    hb_completed = parse_utc(heartbeat_preflight.get("completed_at_utc"))
    generated_at = parse_utc(env_preflight.get("generated_at_utc"))
    valid_until = parse_utc(env_preflight.get("valid_until_utc"))
    ttl_seconds = int(env_preflight.get("preflight_ttl_seconds") or 0)
    if ttl_seconds != PREFLIGHT_TTL_SECONDS:
        raise ValueError(f"runtime environment preflight TTL mismatch: {ttl_seconds}")
    if generated_at > now or now > valid_until:
        raise ValueError(f"runtime environment preflight expired or future: generated={generated_at} now={now} valid_until={valid_until}")
    if abs((valid_until - generated_at).total_seconds() - PREFLIGHT_TTL_SECONDS) > 2:
        raise ValueError("runtime environment preflight validity window mismatch")
    if not (hb_checked <= generated_at <= hb_completed):
        raise ValueError("environment preflight was not generated inside heartbeat gate execution window")

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

    local_head_result = run([git_executable, "-C", str(repo), "rev-parse", "HEAD"], repo)
    local_head = local_head_result["stdout"].strip().lower()
    if local_head_result["exit_code"] != 0 or len(local_head) != 40:
        raise RuntimeError("cannot resolve runtime local HEAD")
    if local_head != str(env_preflight.get("canonical_head") or "").lower():
        raise ValueError(f"runtime local HEAD drift: preflight={env_preflight.get('canonical_head')} current={local_head}")
    task_blob_result = run([git_executable, "-C", str(repo), "rev-parse", f"HEAD:{TASK_REL}"], repo)
    current_task_blob = task_blob_result["stdout"].strip().lower()
    if task_blob_result["exit_code"] != 0 or len(current_task_blob) != 40:
        raise RuntimeError("cannot resolve runtime current-task blob")
    if current_task_blob != str(env_preflight.get("canonical_current_task_blob_sha") or "").lower():
        raise ValueError(f"runtime current-task blob drift: preflight={env_preflight.get('canonical_current_task_blob_sha')} current={current_task_blob}")

    receipt_validator = repo / RECEIPT_VALIDATOR_REL
    if not receipt_validator.is_file():
        raise FileNotFoundError(receipt_validator)
    receipt_env = os.environ.copy()
    receipt_env["AAYS_GIT_EXE"] = git_executable
    receipt_stage = run([python_executable, str(receipt_validator)], repo, env=receipt_env)
    if receipt_stage["exit_code"] != 0:
        raise RuntimeError(f"coordinator rewire receipt validation failed: {receipt_stage['stderr'][-2400:]}")
    receipt_validation_path = repo / RECEIPT_VALIDATION_REL
    if not receipt_validation_path.is_file():
        raise FileNotFoundError(receipt_validation_path)
    receipt_validation = load_json(receipt_validation_path)
    if receipt_validation.get("status") != "COORDINATOR_REWIRE_RECEIPT_VALIDATED":
        raise ValueError("coordinator rewire receipt did not validate")
    if receipt_validation.get("task_id") != TASK_ID or receipt_validation.get("continuation_key") != CONTINUATION:
        raise ValueError("coordinator receipt validation task mismatch")
    if int(receipt_validation.get("matching_queue_record_count") or 0) != 1:
        raise ValueError("coordinator receipt duplicate queue census failed")
    if receipt_validation.get("local_head") != local_head or receipt_validation.get("fresh_origin_head") != local_head:
        raise ValueError("coordinator receipt entry fresh-origin binding drift")
    if receipt_validation.get("current_task_blob_sha") != current_task_blob:
        raise ValueError("coordinator receipt current-task blob drift")
    if receipt_validation.get("runtime_override_applied") is not True:
        raise ValueError("coordinator runtime override not proven")

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
    if int(manifest.get("schema_version") or 0) < 2 or manifest.get("ready_for_serial_publisher") is not True:
        raise ValueError("publish manifest history/readiness contract mismatch")
    if manifest.get("task_id") != TASK_ID or manifest.get("continuation_key") != CONTINUATION:
        raise ValueError("publish manifest task/continuation mismatch")
    if [int(v) for v in (manifest.get("expected_rows") or [])] != EXPECTED_ROWS or len(manifest.get("files") or []) != 7:
        raise ValueError("publish manifest row/file set mismatch")
    if str(manifest.get("pre_publish_origin_head") or "").lower() != pre_publish_origin_head:
        raise ValueError("publish manifest pre-publish origin HEAD mismatch")

    output = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_prepare_publish_handoff.json"
    payload = {
        "schema_version": 6,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION,
        "status": "PUBLISH_PENDING_SERIAL_PUBLISHER_REQUIRED",
        "fresh_heartbeat_preflight": HEARTBEAT_PREFLIGHT_REL,
        "fresh_host_heartbeat_passed": True,
        "runtime_identity_preflight": ENV_PREFLIGHT_REL,
        "runtime_preflight_generated_at_utc": env_preflight.get("generated_at_utc"),
        "runtime_preflight_valid_until_utc": env_preflight.get("valid_until_utc"),
        "runtime_preflight_ttl_seconds": PREFLIGHT_TTL_SECONDS,
        "runtime_preflight_head": local_head,
        "runtime_preflight_current_task_blob_sha": current_task_blob,
        "coordinator_rewire_receipt_validation": RECEIPT_VALIDATION_REL,
        "coordinator_rewire_receipt_validated": True,
        "coordinator_receipt_binding_key_sha256": receipt_validation.get("binding_key_sha256"),
        "coordinator_receipt_matching_queue_record_count": 1,
        "runtime_entry_fresh_origin_head": receipt_validation.get("fresh_origin_head"),
        "runtime_python_executable": python_executable,
        "runtime_powershell_executable": powershell,
        "runtime_git_executable": git_executable,
        "runtime_identity_match_passed": True,
        "runtime_preflight_freshness_and_head_binding_passed": True,
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
        "stages": {
            "coordinator_rewire_receipt_validation": receipt_stage,
            "strict_local_acceptance": strict_result,
            "pre_publish_origin_fetch": fetch_result,
            "pre_publish_origin_head": head_result,
            "publish_manifest": manifest_result,
        },
    }
    write(output, payload)
    print(json.dumps({"ok": True, "status": payload["status"], "entry_fresh_origin_head": receipt_validation.get("fresh_origin_head"), "pre_publish_origin_head": pre_publish_origin_head, "coordinator_binding_key": receipt_validation.get("binding_key_sha256"), "python": python_executable, "powershell": powershell, "git": git_executable, "output": str(output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
