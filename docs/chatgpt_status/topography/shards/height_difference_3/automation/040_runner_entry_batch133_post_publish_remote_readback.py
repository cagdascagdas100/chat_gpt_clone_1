#!/usr/bin/env python3
"""Post-publish readback with sealed preflight inputs and atomic final acceptance."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
EXPECTED_ROWS = list(range(61540, 61552))
RECEIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"
VALIDATION_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"
ACCEPTANCE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/029_batch131_strict12_acceptance/batch131_strict12_local_acceptance.json"
MANIFEST_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/031_batch132_remote_readback/batch132_publish_manifest.json"
REMOTE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/031_batch132_remote_readback/batch132_origin_remote_readback.json"
HEARTBEAT_PREFLIGHT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json"
ENV_PREFLIGHT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json"
HANDOFF_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_prepare_publish_handoff.json"
FINAL_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_post_publish_remote_acceptance.json"


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


def run(command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-16000:],
        "stderr": proc.stderr[-16000:],
    }


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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo = root(script_dir)
    task = load(repo / "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json")
    if task.get("task_id") != TASK_ID or task.get("continuation_key") != CONTINUATION:
        raise ValueError("current task/continuation mismatch")

    handoff_path = repo / HANDOFF_REL
    handoff = load(handoff_path)
    handoff_sha = sha256(handoff_path)
    if int(handoff.get("schema_version") or 0) < 9 or handoff.get("status") != "PUBLISH_PENDING_SERIAL_PUBLISHER_REQUIRED" or [int(value) for value in handoff.get("expected_rows") or []] != EXPECTED_ROWS:
        raise ValueError("pre-publish handoff seal/schema mismatch")
    if handoff.get("runtime_identity_match_passed") is not True or handoff.get("fresh_host_heartbeat_passed") is not True or handoff.get("runtime_preflight_freshness_and_head_binding_passed") is not True or handoff.get("control_plane_receipt_validation_seal_passed") is not True or handoff.get("data_plane_acceptance_manifest_seal_passed") is not True:
        raise ValueError("pre-publish runtime/control/data-plane gates missing")
    if handoff.get("post_strict_runtime_preflight_ttl_recheck_passed") is not True or handoff.get("post_strict_receipt_ttl_recheck_passed") is not True or handoff.get("handoff_atomic_materialization") is not True:
        raise ValueError("post-strict freshness/atomic handoff gates missing")

    receipt = repo / RECEIPT_REL
    validation = repo / VALIDATION_REL
    acceptance = repo / ACCEPTANCE_REL
    manifest = repo / MANIFEST_REL
    heartbeat_preflight = repo / HEARTBEAT_PREFLIGHT_REL
    environment_preflight = repo / ENV_PREFLIGHT_REL
    for path in (receipt, validation, acceptance, manifest, heartbeat_preflight, environment_preflight):
        if not path.is_file():
            raise FileNotFoundError(path)

    expected = {
        "receipt": str(handoff.get("coordinator_receipt_sha256") or ""),
        "validation": str(handoff.get("coordinator_receipt_validation_sha256") or ""),
        "acceptance": str(handoff.get("strict_local_acceptance_sha256") or ""),
        "manifest": str(handoff.get("publish_manifest_sha256") or ""),
        "heartbeat": str(handoff.get("heartbeat_preflight_sha256") or ""),
        "environment": str(handoff.get("runtime_environment_preflight_sha256") or ""),
    }
    if any(len(value) != 64 for value in expected.values()):
        raise ValueError("handoff byte seal missing")
    before = {
        "receipt": sha256(receipt),
        "validation": sha256(validation),
        "acceptance": sha256(acceptance),
        "manifest": sha256(manifest),
        "heartbeat": sha256(heartbeat_preflight),
        "environment": sha256(environment_preflight),
    }
    if before != expected:
        raise RuntimeError(f"CONTROL_DATA_OR_PREFLIGHT_SEAL_CHANGED_BEFORE_REMOTE_READBACK:{before}:{expected}")

    validation_payload = load(validation)
    manifest_payload = load(manifest)
    if validation_payload.get("receipt_sha256") != expected["receipt"] or validation_payload.get("binding_key_sha256") != handoff.get("coordinator_receipt_binding_key_sha256") or validation_payload.get("coordinator_action_id") != handoff.get("coordinator_action_id") or validation_payload.get("receipt_nonce") != handoff.get("coordinator_receipt_nonce") or validation_payload.get("atomic_output_materialization") is not True:
        raise ValueError("handoff/validation seal identity mismatch")
    if manifest_payload.get("task_id") != TASK_ID or manifest_payload.get("continuation_key") != CONTINUATION or [int(value) for value in manifest_payload.get("expected_rows") or []] != EXPECTED_ROWS or len(manifest_payload.get("files") or []) != 7:
        raise ValueError("handoff/manifest identity mismatch")

    pre_publish_origin_head = str(handoff.get("pre_publish_origin_head") or "").strip().lower()
    if len(pre_publish_origin_head) != 40 or handoff.get("pre_publish_origin_fetch_performed") is not True or str(manifest_payload.get("pre_publish_origin_head") or "").strip().lower() != pre_publish_origin_head:
        raise ValueError("pre-publish origin proof missing")

    python_executable = str(handoff.get("runtime_python_executable") or "").strip()
    powershell_executable = str(handoff.get("runtime_powershell_executable") or "").strip()
    git_executable = str(handoff.get("runtime_git_executable") or "").strip()
    for executable, name in ((python_executable, "Python"), (powershell_executable, "PowerShell"), (git_executable, "Git")):
        if not executable or not Path(executable).is_file():
            raise ValueError(f"handoff runtime {name} missing")
    if norm(python_executable) != norm(sys.executable):
        raise ValueError("post-publish Python identity drift")
    powershell_executable = str(Path(powershell_executable).resolve())
    git_executable = str(Path(git_executable).resolve())

    verifier = script_dir / "038_verify_batch132_origin_remote_readback.ps1"
    if not verifier.is_file():
        raise FileNotFoundError(verifier)
    readback_result = run([
        powershell_executable,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(verifier),
        "-RepoRoot",
        str(repo),
        "-GitExe",
        git_executable,
    ], repo)
    if readback_result["exit_code"] != 0:
        raise RuntimeError(f"origin remote readback failed: {readback_result['stderr'][-2000:]}")

    after = {
        "receipt": sha256(receipt),
        "validation": sha256(validation),
        "acceptance": sha256(acceptance),
        "manifest": sha256(manifest),
        "heartbeat": sha256(heartbeat_preflight),
        "environment": sha256(environment_preflight),
    }
    if after != expected:
        raise RuntimeError(f"CONTROL_DATA_OR_PREFLIGHT_SEAL_CHANGED_DURING_REMOTE_READBACK:{after}:{expected}")
    if sha256(handoff_path) != handoff_sha:
        raise RuntimeError("HANDOFF_CHANGED_DURING_REMOTE_READBACK")

    remote_path = repo / REMOTE_REL
    if not remote_path.is_file():
        raise FileNotFoundError(remote_path)
    remote_sha = sha256(remote_path)
    remote = load(remote_path)
    if int(remote.get("schema_version") or 0) < 3 or remote.get("task_id") != TASK_ID or remote.get("continuation_key") != CONTINUATION or [int(value) for value in remote.get("expected_rows") or []] != EXPECTED_ROWS or str(remote.get("pre_publish_origin_head") or "").strip().lower() != pre_publish_origin_head:
        raise ValueError("remote readback identity/history mismatch")
    if remote.get("pre_publish_head_is_ancestor_of_remote_head") is not True or remote.get("remote_history_binding_passed") is not True or remote.get("remote_history_and_commit_delta_binding_passed") is not True:
        raise ValueError("remote history binding failed")

    materialization_commit = str(remote.get("first_full_blob_materialization_commit") or "").strip().lower()
    history_mode = str(remote.get("history_mode") or "")
    delta_mode = str(remote.get("materialization_commit_delta_gate_mode") or "")
    publisher_candidate = remote.get("publisher_commit_candidate")
    if len(materialization_commit) != 40 or remote.get("materialization_commit_is_ancestor_of_remote_head") is not True:
        raise ValueError("materialization commit invalid")
    if history_mode == "FIRST_FULL_BLOB_MATERIALIZATION_COMMIT_FOUND":
        if remote.get("materialization_commit_changes_all_manifest_paths") is not True or str(publisher_candidate or "").strip().lower() != materialization_commit or delta_mode != "ALL_SEVEN_MANIFEST_PATHS_CHANGED_IN_MATERIALIZATION_COMMIT":
            raise ValueError("materialization delta gate failed")
    elif history_mode == "ALREADY_PRESENT_AT_PREPUBLISH_HEAD_NO_REPLAY_REQUIRED":
        if delta_mode != "ALREADY_PRESENT_NO_REPLAY_DELTA_NOT_REQUIRED":
            raise ValueError("no-replay delta mode mismatch")
    else:
        raise ValueError(f"unknown remote history mode: {history_mode}")
    if remote.get("all_remote_blobs_match") is not True or int(remote.get("file_count") or 0) != 7 or remote.get("remote_tracking_ref_freshly_updated") is not True or remote.get("numeric_publish_acceptance_for_12_rows") is not True:
        raise ValueError("remote blob/numeric acceptance failed")
    if sha256(remote_path) != remote_sha or sha256(handoff_path) != handoff_sha or {
        "receipt": sha256(receipt),
        "validation": sha256(validation),
        "acceptance": sha256(acceptance),
        "manifest": sha256(manifest),
        "heartbeat": sha256(heartbeat_preflight),
        "environment": sha256(environment_preflight),
    } != expected:
        raise RuntimeError("REMOTE_READBACK_OR_SEALED_INPUT_CHANGED_BEFORE_FINAL_ACCEPTANCE")

    final_path = repo / FINAL_REL
    payload = {
        "schema_version": 7,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION,
        "status": "REMOTE_HISTORY_CONTROL_DATA_AND_PREFLIGHT_SEAL_ACCEPTED_12_ROWS",
        "runtime_python_executable": str(Path(sys.executable).resolve()),
        "runtime_powershell_executable": powershell_executable,
        "runtime_git_executable": git_executable,
        "runtime_identity_match_passed": True,
        "fresh_host_heartbeat_passed": True,
        "runtime_preflight_freshness_and_head_binding_passed": True,
        "post_strict_runtime_preflight_ttl_recheck_passed": True,
        "post_strict_receipt_ttl_recheck_passed": True,
        "control_plane_receipt_validation_seal_passed": True,
        "data_plane_acceptance_manifest_seal_passed": True,
        "preflight_evidence_seal_passed": True,
        "handoff_sha256": handoff_sha,
        "heartbeat_preflight_sha256": expected["heartbeat"],
        "runtime_environment_preflight_sha256": expected["environment"],
        "coordinator_receipt_sha256": expected["receipt"],
        "coordinator_receipt_validation_sha256": expected["validation"],
        "strict_local_acceptance_sha256": expected["acceptance"],
        "publish_manifest_sha256": expected["manifest"],
        "remote_readback_sha256": remote_sha,
        "coordinator_receipt_binding_key_sha256": handoff.get("coordinator_receipt_binding_key_sha256"),
        "coordinator_action_id": handoff.get("coordinator_action_id"),
        "coordinator_receipt_nonce": handoff.get("coordinator_receipt_nonce"),
        "pre_publish_origin_head": pre_publish_origin_head,
        "remote_head": remote.get("remote_head"),
        "history_mode": history_mode,
        "first_full_blob_materialization_commit": materialization_commit,
        "materialization_commit_delta_gate_mode": delta_mode,
        "materialization_commit_changes_all_manifest_paths": remote.get("materialization_commit_changes_all_manifest_paths"),
        "publisher_commit_candidate": publisher_candidate,
        "remote_history_binding_passed": True,
        "remote_history_and_commit_delta_binding_passed": True,
        "expected_rows": EXPECTED_ROWS,
        "verified_count": 12,
        "remote_file_count": 7,
        "all_remote_blobs_match": True,
        "numeric_publish_acceptance_for_12_rows": True,
        "sealed_inputs_unchanged_before_and_after_remote_readback": True,
        "remote_readback_byte_identity_preserved_through_acceptance": True,
        "final_acceptance_atomic_materialization": True,
        "child_direct_push_performed": False,
        "numeric_values_changed": 0,
        "new_task_created": False,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "overall_product_final_ready": False,
        "final_ready": False,
        "fake_data": False,
        "remote_readback_stage": readback_result,
    }
    atomic_json(final_path, payload)
    print(json.dumps({
        "ok": True,
        "status": payload["status"],
        "pre_publish_origin_head": pre_publish_origin_head,
        "materialization_commit": materialization_commit,
        "manifest_sha256": expected["manifest"],
        "remote_readback_sha256": remote_sha,
        "output": str(final_path),
    }))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
