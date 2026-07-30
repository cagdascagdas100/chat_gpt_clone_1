#!/usr/bin/env python3
"""Same-task Strict12 entrypoint with fresh TTL, contract-drift checks and atomic handoff."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
BRANCH = "codex/aays-single-runner-v5-20260706"
EXPECTED_ROWS = list(range(61540, 61552))
PREFLIGHT_TTL_SECONDS = 900
RECEIPT_TTL_SECONDS = 600
TASK_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
HEARTBEAT_PREFLIGHT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json"
ENV_PREFLIGHT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json"
RECEIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"
RECEIPT_VALIDATOR_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/046_validate_batch141_coordinator_rewire_receipt.py"
RECEIPT_VALIDATION_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"
ACCEPTANCE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/029_batch131_strict12_acceptance/batch131_strict12_local_acceptance.json"
MANIFEST_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/031_batch132_remote_readback/batch132_publish_manifest.json"
HANDOFF_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_prepare_publish_handoff.json"


def root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs/chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("PUBLISHER_REPO_ROOT_NOT_FOUND")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    return {"command": command, "exit_code": proc.returncode, "stdout": proc.stdout[-16000:], "stderr": proc.stderr[-16000:]}


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}_", suffix=".json.tmp", dir=path.parent)
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def norm(value: str) -> str:
    return os.path.normcase(str(Path(value).resolve()))


def parse_utc(value: Any) -> datetime:
    token = str(value or "").strip()
    if not token:
        raise ValueError("missing timestamp")
    if token.endswith("Z"):
        token = token[:-1] + "+00:00"
    parsed = datetime.fromisoformat(token)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_fresh_window(now: datetime, generated: datetime, valid_until: datetime) -> None:
    if generated > now or now > valid_until:
        raise RuntimeError("RUNTIME_PREFLIGHT_EXPIRED_OR_FUTURE")
    if abs((valid_until - generated).total_seconds() - PREFLIGHT_TTL_SECONDS) > 2:
        raise RuntimeError("RUNTIME_PREFLIGHT_TTL_WINDOW_MISMATCH")


def receipt_age_seconds(receipt: dict[str, Any], now: datetime) -> float:
    return (now - parse_utc(receipt.get("receipt_created_at_utc"))).total_seconds()


def git_output(executable: str, repo: Path, *args: str) -> str:
    result = run([executable, "-C", str(repo), *args], repo)
    if result["exit_code"] != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result['stderr'][-2000:]}")
    return result["stdout"].strip()


def git_blob(executable: str, repo: Path, ref: str, rel: str) -> str:
    value = git_output(executable, repo, "rev-parse", f"{ref}:{rel}").lower()
    if len(value) != 40:
        raise RuntimeError(f"BAD_GIT_BLOB:{ref}:{rel}:{value}")
    return value


def contract_paths(task: dict[str, Any]) -> list[str]:
    reads = [str(value) for value in task.get("read_paths") or []]
    if len(reads) != 57 or len(set(reads)) != 57:
        raise ValueError("runtime contract read-path count/uniqueness mismatch")
    paths = [value for value in reads if not value.endswith("/height_difference_3") and value != "docs/chatgpt_status/topography/queue"]
    if TASK_REL not in paths:
        paths.append(TASK_REL)
    paths = sorted(set(paths))
    if len(paths) != 54:
        raise ValueError(f"runtime contract exact-file count mismatch:{len(paths)}")
    return paths


def blob_map(executable: str, repo: Path, ref: str, paths: list[str]) -> dict[str, str]:
    return {rel: git_blob(executable, repo, ref, rel) for rel in paths}


def blob_map_digest(values: dict[str, str]) -> str:
    encoded = json.dumps(values, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo = root(script_dir)
    task_path = repo / TASK_REL
    task = load(task_path)
    if task.get("task_id") != TASK_ID or task.get("continuation_key") != CONTINUATION:
        raise ValueError("current task identity mismatch")
    if task.get("single_runner_only") is not True or task.get("new_runner") is not False or task.get("parallel_runner") is not False:
        raise ValueError("single-runner contract mismatch")

    heartbeat_path = repo / HEARTBEAT_PREFLIGHT_REL
    environment_path = repo / ENV_PREFLIGHT_REL
    receipt_path = repo / RECEIPT_REL
    validation_path = repo / RECEIPT_VALIDATION_REL
    heartbeat = load(heartbeat_path)
    environment = load(environment_path)
    if int(heartbeat.get("schema_version") or 0) < 4 or heartbeat.get("task_id") != TASK_ID or heartbeat.get("continuation_key") != CONTINUATION or heartbeat.get("fresh_host_heartbeat_passed") is not True:
        raise ValueError("fresh heartbeat receipt mismatch")
    if heartbeat.get("environment_gate_044_executed") is not True or int(heartbeat.get("environment_gate_044_exit_code") or -1) != 0:
        raise ValueError("heartbeat chain did not complete 044")
    if float(heartbeat.get("global_heartbeat_age_seconds") or 1e18) > float(heartbeat.get("global_heartbeat_entry_max_age_seconds") or 0):
        raise ValueError("heartbeat receipt exceeds reserved freshness budget")
    if int(environment.get("schema_version") or 0) < 5 or int(environment.get("checks_passed") or -1) != int(environment.get("checks_total") or -2) or environment.get("bootstrap_042_executed") is not True or int(environment.get("bootstrap_042_exit_code") or -1) != 0 or int(environment.get("numeric_values_written") or 0) != 0 or environment.get("canonical_branch") != BRANCH:
        raise ValueError("runtime environment preflight mismatch")
    if environment.get("pyproj_network_restored") is not True or environment.get("atomic_output_materialization") is not True:
        raise ValueError("runtime environment restoration/atomic contract missing")

    entry_now = datetime.now(timezone.utc)
    heartbeat_checked = parse_utc(heartbeat.get("checked_at_utc"))
    heartbeat_completed = parse_utc(heartbeat.get("completed_at_utc"))
    generated = parse_utc(environment.get("generated_at_utc"))
    valid_until = parse_utc(environment.get("valid_until_utc"))
    ttl = int(environment.get("preflight_ttl_seconds") or 0)
    if ttl != PREFLIGHT_TTL_SECONDS or not (heartbeat_checked <= generated <= heartbeat_completed):
        raise ValueError("runtime preflight TTL/window binding mismatch")
    require_fresh_window(entry_now, generated, valid_until)

    runtime_identity = environment.get("runtime_identity") or {}
    python_executable = str(runtime_identity.get("python_executable") or environment.get("python_executable") or "").strip()
    powershell_executable = str(runtime_identity.get("powershell_executable") or environment.get("powershell_path") or "").strip()
    git_executable = str(runtime_identity.get("git_executable") or environment.get("git_executable") or "").strip()
    for executable, name in ((python_executable, "Python"), (powershell_executable, "PowerShell"), (git_executable, "Git")):
        if not executable or not Path(executable).is_file():
            raise ValueError(f"validated {name} executable missing")
    if norm(python_executable) != norm(sys.executable):
        raise ValueError("runtime Python identity drift")
    python_executable = str(Path(sys.executable).resolve())
    powershell_executable = str(Path(powershell_executable).resolve())
    git_executable = str(Path(git_executable).resolve())

    local_head = git_output(git_executable, repo, "rev-parse", "HEAD").lower()
    task_blob = git_blob(git_executable, repo, "HEAD", TASK_REL)
    if local_head != str(environment.get("canonical_head") or "").lower():
        raise ValueError("runtime local HEAD drift")
    if task_blob != str(environment.get("canonical_current_task_blob_sha") or "").lower():
        raise ValueError("runtime current-task blob drift")
    if task_path.read_bytes() != git_output(git_executable, repo, "show", f"HEAD:{TASK_REL}").encode("utf-8"):
        raise RuntimeError("CURRENT_TASK_WORKTREE_HEAD_CONTENT_DRIFT")

    runtime_contract_paths = contract_paths(task)
    dirty = git_output(git_executable, repo, "status", "--porcelain", "--untracked-files=no", "--", *runtime_contract_paths)
    if dirty:
        raise RuntimeError(f"RUNTIME_CONTRACT_WORKTREE_DIRTY:{dirty[-2000:]}")
    head_contract_blobs = blob_map(git_executable, repo, "HEAD", runtime_contract_paths)
    runtime_contract_digest = blob_map_digest(head_contract_blobs)

    validator_path = repo / RECEIPT_VALIDATOR_REL
    if not validator_path.is_file() or not receipt_path.is_file():
        raise FileNotFoundError("receipt validator/receipt missing")
    heartbeat_sha_before = sha256(heartbeat_path)
    environment_sha_before = sha256(environment_path)
    receipt_sha_before = sha256(receipt_path)
    validator_env = os.environ.copy()
    validator_env["AAYS_GIT_EXE"] = git_executable
    validation_result = run([python_executable, str(validator_path)], repo, validator_env)
    if validation_result["exit_code"] != 0:
        raise RuntimeError(f"coordinator receipt validation failed: {validation_result['stderr'][-2400:]}")
    if not validation_path.is_file():
        raise FileNotFoundError(validation_path)
    validation = load(validation_path)
    receipt_sha_validated = sha256(receipt_path)
    validation_sha_validated = sha256(validation_path)
    if receipt_sha_before != receipt_sha_validated or validation.get("receipt_sha256") != receipt_sha_validated:
        raise RuntimeError("COORDINATOR_RECEIPT_CHANGED_AROUND_046")
    if validation.get("atomic_output_materialization") is not True:
        raise ValueError("coordinator validation output is not atomic")
    if validation.get("status") != "COORDINATOR_REWIRE_RECEIPT_VALIDATED" or validation.get("task_id") != TASK_ID or validation.get("continuation_key") != CONTINUATION or int(validation.get("matching_queue_record_count") or 0) != 1 or validation.get("local_head") != local_head or validation.get("fresh_origin_head") != local_head or validation.get("current_task_blob_sha") != task_blob or validation.get("runtime_override_applied") is not True:
        raise ValueError("coordinator receipt validation contract mismatch")

    strict_script = script_dir / "036_run_batch131_strict12_with_local_acceptance.ps1"
    manifest_generator = script_dir / "037_prepare_batch132_publish_manifest.py"
    if not strict_script.is_file() or not manifest_generator.is_file():
        raise FileNotFoundError("strict/manifest script missing")
    strict_result = run([powershell_executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(strict_script), "-RepoRoot", str(repo), "-PythonExe", python_executable, "-PowerShellExe", powershell_executable], repo)
    if strict_result["exit_code"] != 0:
        raise RuntimeError(f"strict/local acceptance failed: {strict_result['stderr'][-2000:]}")
    if sha256(receipt_path) != receipt_sha_validated or sha256(validation_path) != validation_sha_validated:
        raise RuntimeError("CONTROL_PLANE_RECEIPT_OR_VALIDATION_CHANGED_DURING_STRICT")
    if sha256(heartbeat_path) != heartbeat_sha_before or sha256(environment_path) != environment_sha_before:
        raise RuntimeError("PREFLIGHT_EVIDENCE_CHANGED_DURING_STRICT")

    acceptance_path = repo / ACCEPTANCE_REL
    acceptance = load(acceptance_path)
    acceptance_sha = sha256(acceptance_path)
    if acceptance.get("local_acceptance_passed") is not True or [int(value) for value in acceptance.get("expected_rows") or []] != EXPECTED_ROWS or acceptance.get("remote_github_readback_required") is not True:
        raise ValueError("local acceptance mismatch")

    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    fetch_result = run([git_executable, "-C", str(repo), "fetch", "--no-tags", "origin", fetch_spec], repo)
    if fetch_result["exit_code"] != 0:
        raise RuntimeError(f"pre-publish origin fetch failed: {fetch_result['stderr'][-2000:]}")
    pre_publish_origin_head = git_output(git_executable, repo, "rev-parse", f"refs/remotes/origin/{BRANCH}").lower()
    remote_contract_blobs = blob_map(git_executable, repo, pre_publish_origin_head, runtime_contract_paths)
    drifted = [rel for rel in runtime_contract_paths if remote_contract_blobs[rel] != head_contract_blobs[rel]]
    if drifted:
        raise RuntimeError(f"REMOTE_RUNTIME_CONTRACT_DRIFT_BEFORE_HANDOFF:{drifted}")
    if git_blob(git_executable, repo, pre_publish_origin_head, TASK_REL) != task_blob:
        raise RuntimeError("REMOTE_CURRENT_TASK_BLOB_DRIFT_BEFORE_HANDOFF")
    if blob_map_digest(remote_contract_blobs) != runtime_contract_digest:
        raise RuntimeError("REMOTE_RUNTIME_CONTRACT_MAP_DIGEST_DRIFT")
    dirty_after = git_output(git_executable, repo, "status", "--porcelain", "--untracked-files=no", "--", *runtime_contract_paths)
    if dirty_after:
        raise RuntimeError(f"RUNTIME_CONTRACT_WORKTREE_DIRTY_AFTER_STRICT:{dirty_after[-2000:]}")

    manifest_path = repo / MANIFEST_REL
    manifest_result = run([python_executable, str(manifest_generator), "--repo-root", str(repo), "--output", str(manifest_path), "--pre-publish-origin-head", pre_publish_origin_head], repo)
    if manifest_result["exit_code"] != 0:
        raise RuntimeError(f"publish manifest generation failed: {manifest_result['stderr'][-2000:]}")
    manifest = load(manifest_path)
    manifest_sha = sha256(manifest_path)
    if int(manifest.get("schema_version") or 0) < 2 or manifest.get("ready_for_serial_publisher") is not True or manifest.get("task_id") != TASK_ID or manifest.get("continuation_key") != CONTINUATION or [int(value) for value in manifest.get("expected_rows") or []] != EXPECTED_ROWS or len(manifest.get("files") or []) != 7 or str(manifest.get("pre_publish_origin_head") or "").lower() != pre_publish_origin_head:
        raise ValueError("publish manifest mismatch")

    post_strict_now = datetime.now(timezone.utc)
    require_fresh_window(post_strict_now, generated, valid_until)
    receipt = load(receipt_path)
    post_strict_receipt_age = receipt_age_seconds(receipt, post_strict_now)
    if not (-2 <= post_strict_receipt_age <= RECEIPT_TTL_SECONDS):
        raise RuntimeError(f"COORDINATOR_RECEIPT_EXPIRED_AFTER_STRICT:{post_strict_receipt_age}")
    if sha256(receipt_path) != receipt_sha_validated or sha256(validation_path) != validation_sha_validated:
        raise RuntimeError("CONTROL_PLANE_RECEIPT_OR_VALIDATION_CHANGED_BEFORE_HANDOFF")
    if sha256(acceptance_path) != acceptance_sha or sha256(manifest_path) != manifest_sha:
        raise RuntimeError("DATA_PLANE_ACCEPTANCE_OR_MANIFEST_CHANGED_BEFORE_HANDOFF")
    if sha256(heartbeat_path) != heartbeat_sha_before or sha256(environment_path) != environment_sha_before:
        raise RuntimeError("PREFLIGHT_EVIDENCE_CHANGED_BEFORE_HANDOFF")

    handoff_path = repo / HANDOFF_REL
    payload = {
        "schema_version": 10,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION,
        "status": "PUBLISH_PENDING_SERIAL_PUBLISHER_REQUIRED",
        "fresh_heartbeat_preflight": HEARTBEAT_PREFLIGHT_REL,
        "heartbeat_preflight_sha256": heartbeat_sha_before,
        "fresh_host_heartbeat_passed": True,
        "runtime_identity_preflight": ENV_PREFLIGHT_REL,
        "runtime_environment_preflight_sha256": environment_sha_before,
        "runtime_preflight_generated_at_utc": environment.get("generated_at_utc"),
        "runtime_preflight_valid_until_utc": environment.get("valid_until_utc"),
        "runtime_preflight_ttl_seconds": PREFLIGHT_TTL_SECONDS,
        "runtime_preflight_head": local_head,
        "runtime_preflight_current_task_blob_sha": task_blob,
        "runtime_contract_path_count": len(runtime_contract_paths),
        "runtime_contract_paths": runtime_contract_paths,
        "runtime_contract_blob_sha1": head_contract_blobs,
        "runtime_contract_blob_map_sha256": runtime_contract_digest,
        "runtime_contract_worktree_clean_passed": True,
        "runtime_contract_remote_blob_parity_passed": True,
        "current_task_worktree_head_blob_match_passed": True,
        "current_task_remote_blob_parity_passed": True,
        "post_strict_runtime_preflight_ttl_recheck_passed": True,
        "post_strict_runtime_preflight_checked_at_utc": post_strict_now.isoformat().replace("+00:00", "Z"),
        "coordinator_rewire_receipt": RECEIPT_REL,
        "coordinator_rewire_receipt_validation": RECEIPT_VALIDATION_REL,
        "coordinator_rewire_receipt_validated": True,
        "coordinator_receipt_sha256": receipt_sha_validated,
        "coordinator_receipt_validation_sha256": validation_sha_validated,
        "coordinator_receipt_binding_key_sha256": validation.get("binding_key_sha256"),
        "coordinator_action_id": validation.get("coordinator_action_id"),
        "coordinator_receipt_nonce": validation.get("receipt_nonce"),
        "coordinator_receipt_matching_queue_record_count": 1,
        "coordinator_receipt_ttl_seconds": RECEIPT_TTL_SECONDS,
        "post_strict_receipt_ttl_recheck_passed": True,
        "post_strict_receipt_age_seconds": post_strict_receipt_age,
        "control_plane_receipt_validation_seal_passed": True,
        "strict_local_acceptance_sha256": acceptance_sha,
        "publish_manifest_sha256": manifest_sha,
        "data_plane_acceptance_manifest_seal_passed": True,
        "runtime_entry_fresh_origin_head": validation.get("fresh_origin_head"),
        "runtime_python_executable": python_executable,
        "runtime_powershell_executable": powershell_executable,
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
        "publish_manifest": MANIFEST_REL,
        "publish_file_count": 7,
        "serial_publisher_required": True,
        "child_direct_push_performed": False,
        "post_publish_entrypoint": "docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py",
        "handoff_atomic_materialization": True,
        "numeric_final_acceptance": "PENDING_SERIAL_PUBLISH_REMOTE_HISTORY_CONTROL_PLANE_DATA_PLANE_AND_RUNTIME_CONTRACT_SEAL_READBACK",
        "new_task_created": False,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "numeric_values_changed": 0,
        "final_ready": False,
        "fake_data": False,
        "stages": {"coordinator_rewire_receipt_validation": validation_result, "strict_local_acceptance": strict_result, "pre_publish_origin_fetch": fetch_result, "publish_manifest": manifest_result},
    }
    atomic_json(handoff_path, payload)
    print(json.dumps({"ok": True, "status": payload["status"], "pre_publish_origin_head": pre_publish_origin_head, "runtime_contract_blob_map_sha256": runtime_contract_digest, "receipt_sha256": receipt_sha_validated, "validation_sha256": validation_sha_validated, "acceptance_sha256": acceptance_sha, "manifest_sha256": manifest_sha, "post_strict_receipt_age_seconds": post_strict_receipt_age, "output": str(handoff_path)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
