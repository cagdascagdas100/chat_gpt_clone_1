#!/usr/bin/env python3
"""Fail-closed portable validator for the same-task coordinator wiring request."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
ATTEMPT = "height-difference-3-20260721-011"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
BRANCH = "codex/aays-single-runner-v5-20260706"
LEGACY = "docs/chatgpt_status/topography/shards/height_difference_3/automation/023_runner_entry_canonical_api_measurement.py"
RUN039 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py"
POST040 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py"
P037 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/037_prepare_batch132_publish_manifest.py"
READ038 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/038_verify_batch132_origin_remote_readback.ps1"
REQUEST = "docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json"
TASK = "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
QUEUE = "docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json"
QUEUE_ROOT = "docs/chatgpt_status/topography/queue"
OWNER = "docs/chatgpt_status/_shared/slots_21/height_difference_3/ownership_latest.json"
V041 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/041_validate_batch134_coordinator_wiring_request.py"
B042 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/042_run_batch135_fresh_origin_wiring_preflight.py"
H043 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/043_run_batch136_exact_branch_head_and_dependency_preflight.py"
E044 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/044_run_batch137_runtime_environment_preflight.py"
H045 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/045_run_batch140_fresh_runner_heartbeat_gate.py"
V046 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/046_validate_batch141_coordinator_rewire_receipt.py"
G047 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/047_generate_batch142_coordinator_rewire_receipt.py"
S036 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/036_run_batch131_strict12_with_local_acceptance.ps1"
S033 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/033_run_batch130_prepare12_strict_measurement_chain.ps1"
S032 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/032_run_batch129_range_extract_and_prepare12.ps1"
R076 = "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/076_batch138_runtime_executable_identity_resume.json"
R077 = "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/077_batch139_remote_history_binding_resume.json"
R078 = "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/078_batch140_fresh_heartbeat_ttl_and_commit_delta_resume.json"
R079 = "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/079_batch141_coordinator_receipt_duplicate_census_and_entry_origin_resume.json"
R080 = "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/080_batch142_deterministic_receipt_generator_and_seal_resume.json"
ENVOUT = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json"
HBOUT = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json"
RECEIPT = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"
RECEIPTVAL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"
SLOTHB = "docs/chatgpt_status/_shared/slots_21/height_difference_3/heartbeat_latest.json"
GLOBALHB = "docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json"
EXPECTED_ROWS = list(range(61540, 61552))
NREAD = 57
NOUT = 22


def root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs/chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def resolve_git() -> str:
    token = str(os.environ.get("AAYS_GIT_EXE") or "git").strip()
    found = shutil.which(token)
    if found:
        return str(Path(found).resolve())
    candidate = Path(token)
    if candidate.is_file():
        return str(candidate.resolve())
    raise RuntimeError("GIT_EXECUTABLE_NOT_FOUND")


def git(executable: str, repo: Path, *args: str) -> str:
    proc = subprocess.run([executable, "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr[-1200:]}")
    return proc.stdout.strip()


def blob(executable: str, repo: Path, ref: str, rel: str) -> str:
    value = git(executable, repo, "rev-parse", f"{ref}:{rel}").lower()
    if len(value) != 40:
        raise ValueError(f"bad blob: {ref}:{rel}:{value}")
    return value


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


def main() -> int:
    repo = root(Path(__file__).resolve())
    git_exe = resolve_git()
    request = load(repo / REQUEST)
    task = load(repo / TASK)
    queue = load(repo / QUEUE)
    owner = load(repo / OWNER)
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            raise ValueError(f"wiring validation failed: {name}: {detail}")

    check("schema13", int(request.get("schema_version") or 0) >= 13)
    check("identity", request.get("task_id") == TASK_ID and request.get("attempt_id") == ATTEMPT and request.get("continuation_key") == CONTINUATION)
    check("no_duplicate", request.get("new_task_forbidden") is True and request.get("duplicate_task_forbidden") is True and request.get("new_runner_forbidden") is True and request.get("parallel_runner_forbidden") is True)
    check("task_identity", task.get("task_id") == TASK_ID and task.get("attempt_id") == ATTEMPT and task.get("continuation_key") == CONTINUATION)
    check("task_entrypoints", task.get("script_path") == RUN039 and task.get("post_publish_script_path") == POST040)
    check("single_runner", task.get("single_runner_only") is True and task.get("new_runner") is False and task.get("parallel_runner") is False)

    reads = list(task.get("read_paths") or [])
    outputs = list(task.get("expected_outputs") or [])
    check("task_57_reads", len(reads) == NREAD, len(reads))
    check("task_22_outputs", len(outputs) == NOUT, len(outputs))
    check("unique_paths", len(set(reads)) == len(reads) and len(set(outputs)) == len(outputs))
    check("resume080_readable", R080 in reads)
    check("generator_validator_readable", G047 in reads and V046 in reads)
    check("queue_root_readable", QUEUE_ROOT in reads)
    check("generated_receipts_are_outputs", HBOUT in outputs and ENVOUT in outputs and RECEIPT in outputs and RECEIPTVAL in outputs and RECEIPT not in reads and RECEIPTVAL not in reads)

    check("queue_identity", queue.get("task_id") == TASK_ID and queue.get("attempt_id") == ATTEMPT)
    check("queue_single_runner", queue.get("single_runner_only") is True and queue.get("new_runner") is False and queue.get("parallel_runner") is False)
    check("queue_script_known", queue.get("script_path") in {LEGACY, RUN039}, queue.get("script_path"))

    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    git(git_exe, repo, "fetch", "--no-tags", "origin", fetch_spec)
    remote = git(git_exe, repo, "rev-parse", f"refs/remotes/origin/{BRANCH}")
    local = git(git_exe, repo, "rev-parse", "HEAD")
    check("heads", len(remote) == 40 and local == remote, {"local": local, "remote": remote})

    preconditions = request.get("preconditions") or {}
    check("scope_contract", int(preconditions.get("canonical_current_task_read_path_count_required") or 0) == NREAD and int(preconditions.get("canonical_current_task_expected_output_count_required") or 0) == NOUT)
    check("freshness_contract", preconditions.get("fresh_runner_heartbeat_gate_required") is True and int(preconditions.get("runtime_environment_preflight_ttl_seconds") or 0) == 900 and preconditions.get("runtime_preflight_head_task_blob_binding_required") is True and preconditions.get("post_strict_runtime_preflight_recheck_required") is True and preconditions.get("post_strict_receipt_ttl_recheck_required") is True)
    check("atomic_contract", preconditions.get("atomic_preflight_outputs_required") is True and preconditions.get("atomic_receipt_output_required") is True and preconditions.get("atomic_receipt_validation_output_required") is True and preconditions.get("atomic_handoff_output_required") is True and preconditions.get("atomic_final_acceptance_output_required") is True)
    check("receipt_preconditions", preconditions.get("deterministic_coordinator_receipt_generator_required") is True and preconditions.get("coordinator_rewire_receipt_required") is True and int(preconditions.get("coordinator_rewire_receipt_ttl_seconds") or 0) == 600 and preconditions.get("coordinator_receipt_nonce_required") is True and preconditions.get("coordinator_action_id_required") is True and preconditions.get("receipt_sha256_seal_required") is True and preconditions.get("control_plane_receipt_validation_byte_seal_required") is True)
    check("data_plane_preconditions", preconditions.get("data_plane_acceptance_manifest_byte_seal_required") is True and preconditions.get("remote_readback_byte_seal_required") is True and preconditions.get("preflight_evidence_byte_seal_required") is True)
    check("history_preconditions", preconditions.get("fresh_pre_publish_origin_head_required") is True and preconditions.get("remote_history_binding_required") is True and preconditions.get("materialization_commit_all_manifest_paths_changed_required") is True)

    task_blob = blob(git_exe, repo, remote, TASK)
    queue_blob = blob(git_exe, repo, remote, QUEUE)
    check("task_pin", task_blob == str(preconditions.get("canonical_current_task_expected_blob_sha") or "").lower(), task_blob)
    check("queue_pin", queue_blob == str(preconditions.get("legacy_queue_expected_blob_sha") or "").lower(), queue_blob)
    check("local_task_remote", blob(git_exe, repo, "HEAD", TASK) == task_blob)
    check("local_queue_remote", blob(git_exe, repo, "HEAD", QUEUE) == queue_blob)

    paths = [REQUEST, TASK, QUEUE, P037, RUN039, POST040, READ038, V041, B042, H043, E044, H045, V046, G047, S036, S033, S032, R076, R077, R078, R079, R080]
    remote_blobs: dict[str, str] = {}
    parity_rows: list[dict[str, Any]] = []
    for rel in paths:
        local_blob = blob(git_exe, repo, "HEAD", rel)
        remote_blob = blob(git_exe, repo, remote, rel)
        check(f"parity:{rel}", local_blob == remote_blob, {"local": local_blob, "remote": remote_blob})
        remote_blobs[rel] = remote_blob
        parity_rows.append({"path": rel, "local_head_blob": local_blob, "remote_blob": remote_blob})
    check("critical_clean", git(git_exe, repo, "status", "--porcelain", "--untracked-files=no", "--", *paths) == "")

    validator_chain = request.get("validator_chain") or {}
    identity_chain = request.get("runtime_identity_chain") or {}
    history_chain = request.get("remote_history_chain") or {}
    freshness_chain = request.get("freshness_chain") or {}
    receipt_chain = request.get("coordinator_receipt_chain") or {}
    control_seal = request.get("control_plane_seal_chain") or {}
    data_seal = request.get("data_plane_seal_chain") or {}
    override = request.get("coordinator_runtime_override") or {}
    pins = [
        ("043", validator_chain.get("exact_branch_head_gate_expected_blob_sha"), H043),
        ("045", freshness_chain.get("fresh_heartbeat_gate_expected_blob_sha"), H045),
        ("044", validator_chain.get("runtime_environment_gate_expected_blob_sha"), E044),
        ("042", validator_chain.get("fresh_origin_bootstrap_expected_blob_sha"), B042),
        ("041", validator_chain.get("same_task_validator_expected_blob_sha"), V041),
        ("046", receipt_chain.get("coordinator_receipt_validator_expected_blob_sha"), V046),
        ("047", receipt_chain.get("coordinator_receipt_generator_expected_blob_sha"), G047),
        ("039", override.get("runtime_script_expected_blob_sha"), RUN039),
        ("040", override.get("post_publish_script_expected_blob_sha"), POST040),
        ("037", history_chain.get("publish_manifest_037_expected_blob_sha"), P037),
        ("038", history_chain.get("remote_readback_038_expected_blob_sha"), READ038),
        ("036", identity_chain.get("strict036_expected_blob_sha"), S036),
        ("033", identity_chain.get("strict033_expected_blob_sha"), S033),
        ("032", identity_chain.get("strict032_expected_blob_sha"), S032),
        ("076", identity_chain.get("resume_076_expected_blob_sha"), R076),
        ("077", history_chain.get("resume_077_expected_blob_sha"), R077),
        ("078", freshness_chain.get("resume_078_expected_blob_sha"), R078),
        ("079", receipt_chain.get("resume_079_expected_blob_sha"), R079),
        ("080", receipt_chain.get("resume_080_expected_blob_sha"), R080),
    ]
    for name, expected, rel in pins:
        check(f"pin_{name}", str(expected or "").lower() == remote_blobs[rel], {"pin": expected, "remote": remote_blobs[rel]})

    check("receipt_binding", receipt_chain.get("receipt_generator") == G047 and receipt_chain.get("receipt_validator") == V046 and int(receipt_chain.get("receipt_ttl_seconds") or 0) == 600 and receipt_chain.get("queue_census_basis") == ["task_id", "attempt_id", "idempotency_key"] and receipt_chain.get("coordinator_action_id_required") is True and receipt_chain.get("random_receipt_nonce_required") is True and receipt_chain.get("receipt_binding_includes_action_id_and_nonce") is True and receipt_chain.get("validator_emits_receipt_sha256") is True and receipt_chain.get("direct_entrypoint_control_plane_seal_required") is True and receipt_chain.get("atomic_receipt_materialization_required") is True and receipt_chain.get("atomic_validation_materialization_required") is True)
    check("control_plane_seal", control_seal.get("039_receipt_sha256_before_and_after_046_equal") is True and control_seal.get("039_receipt_sha256_unchanged_during_strict") is True and control_seal.get("039_validation_sha256_unchanged_during_strict") is True and control_seal.get("039_receipt_and_validation_sha256_unchanged_before_handoff") is True and control_seal.get("039_post_strict_receipt_ttl_recheck_required") is True and control_seal.get("040_requires_receipt_and_validation_sha256_before_remote_readback") is True and control_seal.get("040_rechecks_receipt_and_validation_sha256_after_remote_readback") is True and control_seal.get("numeric_acceptance_fails_closed_on_control_plane_seal_drift") is True)
    check("data_plane_seal", data_seal.get("039_hashes_strict_local_acceptance") is True and data_seal.get("039_hashes_publish_manifest") is True and data_seal.get("039_rechecks_acceptance_and_manifest_before_handoff") is True and data_seal.get("039_rechecks_preflight_evidence_before_handoff") is True and data_seal.get("handoff_carries_strict_local_acceptance_sha256") is True and data_seal.get("handoff_carries_publish_manifest_sha256") is True and data_seal.get("handoff_carries_preflight_sha256") is True and data_seal.get("handoff_atomic_materialization_required") is True and data_seal.get("040_requires_acceptance_manifest_and_preflight_sha256_before_remote_readback") is True and data_seal.get("040_rechecks_acceptance_manifest_and_preflight_sha256_after_remote_readback") is True and data_seal.get("040_hashes_remote_readback_json") is True and data_seal.get("040_rechecks_remote_readback_sha256_before_final_acceptance") is True and data_seal.get("final_acceptance_carries_remote_readback_sha256") is True and data_seal.get("final_acceptance_atomic_materialization_required") is True and data_seal.get("numeric_acceptance_fails_closed_on_data_plane_seal_drift") is True)
    check("identity_propagation", identity_chain.get("python_executable_propagates_044_039_036_033_032_and_040") is True and identity_chain.get("powershell_executable_propagates_044_039_036_033_032_and_040") is True and identity_chain.get("git_executable_propagates_043_045_044_042_041_047_046_039_handoff_040_038") is True)
    check("history_binding", history_chain.get("runtime_039_captures_fresh_pre_publish_origin_head") is True and history_chain.get("manifest_binds_pre_publish_origin_head") is True and history_chain.get("materialization_commit_must_change_all_seven_manifest_paths") is True and history_chain.get("post_publish_040_requires_remote_history_and_commit_delta_binding") is True)
    check("override", override.get("use_existing_queue_record") is True and override.get("do_not_create_new_queue_record") is True and override.get("runtime_script_path") == RUN039 and override.get("post_publish_script_path") == POST040 and override.get("runtime_arguments") == [] and override.get("post_publish_arguments") == [])
    check("rows", [int(value) for value in request.get("expected_rows") or []] == EXPECTED_ROWS)

    owner_state = str(owner.get("state") or "")
    owner_id = owner.get("owner_page_session_id")
    check("owner_safe", owner_state == "UNCLAIMED", {"state": owner_state, "owner": owner_id})

    output = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/035_batch134_coordinator_wiring_qa/coordinator_wiring_request_validation.json"
    payload = {
        "schema_version": 14,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION,
        "status": "ALREADY_ALIGNED" if queue.get("script_path") == RUN039 else "SAFE_FOR_COORDINATOR_RUNTIME_REWIRE_AFTER_ATOMIC_TTL_AND_SEAL_GATES",
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "fresh_remote_head": remote,
        "critical_blob_parity": parity_rows,
        "expected_read_path_count": NREAD,
        "expected_output_count": NOUT,
        "portable_git_executable": git_exe,
        "portable_git_contract_passed": True,
        "direct_control_plane_receipt_validation_seal_pinned": True,
        "publish_manifest_remote_readback_and_preflight_byte_seals_pinned": True,
        "post_strict_runtime_and_receipt_ttl_rechecks_pinned": True,
        "atomic_preflight_receipt_validation_handoff_and_final_outputs_pinned": True,
        "fresh_host_heartbeat_still_required": True,
        "coordinator_action_performed": False,
        "legacy_queue_mutated": False,
        "new_task_created": False,
        "new_runner_created": False,
        "numeric_values_written": 0,
        "expected_rows": EXPECTED_ROWS,
        "atomic_output_materialization": True,
        "final_ready": False,
        "fake_data": False,
    }
    atomic_json(output, payload)
    print(json.dumps({"ok": True, "checks": len(checks), "output": str(output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=__import__("sys").stderr)
        raise
