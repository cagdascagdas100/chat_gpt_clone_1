#!/usr/bin/env python3
"""Validate the bound coordinator receipt and atomically publish validation evidence."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
ATTEMPT_ID = "height-difference-3-20260721-011"
IDEMPOTENCY = "height_difference_3:canonical_security_stream:hmlr_ea_terrain50:v1"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
BRANCH = "codex/aays-single-runner-v5-20260706"
RUN039 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py"
POST040 = "docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py"
REQUEST_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json"
TASK_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
QUEUE_REL = "docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json"
QUEUE_ROOT = "docs/chatgpt_status/topography/queue"
RECEIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"
VALIDATION_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"
RECEIPT_TTL_SECONDS = 600
PREFLIGHT_OUTPUTS = {
    "043": "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/039_batch136_exact_head_preflight/exact_branch_head_and_dependency_preflight_runtime.json",
    "045": "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json",
    "044": "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json",
    "042": "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/037_batch135_fresh_origin_wiring_qa/fresh_origin_wiring_preflight_runtime.json",
    "041": "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/035_batch134_coordinator_wiring_qa/coordinator_wiring_request_validation.json",
}


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


def bind(parts: list[str]) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def git_executable() -> str:
    token = str(os.environ.get("AAYS_GIT_EXE") or "git").strip()
    found = shutil.which(token)
    if found:
        return str(Path(found).resolve())
    candidate = Path(token)
    if candidate.is_file():
        return str(candidate.resolve())
    raise RuntimeError("GIT_EXECUTABLE_NOT_FOUND")


def git(executable: str, repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run([executable, "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if check and proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr[-1200:]}")
    return proc.stdout.strip()


def blob(executable: str, repo: Path, ref: str, rel: str) -> str:
    value = git(executable, repo, "rev-parse", f"{ref}:{rel}").lower()
    if len(value) != 40:
        raise ValueError(f"bad blob: {rel}: {value}")
    return value


def hits(raw: str) -> list[str]:
    result: set[str] = set()
    for line in raw.splitlines():
        token = line.strip()
        if token.startswith("HEAD:"):
            token = token[5:]
        if token:
            result.add(token)
    return sorted(result)


def main() -> int:
    repo = root(Path(__file__).resolve())
    executable = git_executable()
    receipt_path = repo / RECEIPT_REL
    if not receipt_path.is_file():
        raise FileNotFoundError(receipt_path)
    receipt = load(receipt_path)
    receipt_sha = sha256(receipt_path)
    task = load(repo / TASK_REL)
    request = load(repo / REQUEST_REL)
    queue = load(repo / QUEUE_REL)
    checks: list[dict[str, Any]] = []

    def need(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            raise RuntimeError(f"COORDINATOR_RECEIPT_FAILED:{name}:{detail}")

    need("receipt_schema", int(receipt.get("schema_version") or 0) >= 4)
    need("receipt_atomic", receipt.get("atomic_output_materialization") is True)
    need("receipt_identity", receipt.get("task_id") == TASK_ID and receipt.get("attempt_id") == ATTEMPT_ID and receipt.get("idempotency_key") == IDEMPOTENCY and receipt.get("continuation_key") == CONTINUATION)
    need("task_identity", task.get("task_id") == TASK_ID and task.get("attempt_id") == ATTEMPT_ID and task.get("idempotency_key") == IDEMPOTENCY and task.get("continuation_key") == CONTINUATION)
    need("request_identity", request.get("task_id") == TASK_ID and request.get("attempt_id") == ATTEMPT_ID and request.get("idempotency_key") == IDEMPOTENCY and request.get("continuation_key") == CONTINUATION)
    need("queue_identity", queue.get("task_id") == TASK_ID and queue.get("attempt_id") == ATTEMPT_ID and queue.get("idempotency_key") == IDEMPOTENCY)

    action_id = str(receipt.get("coordinator_action_id") or "").strip()
    nonce = str(receipt.get("receipt_nonce") or "").strip()
    need("action_id", len(action_id) >= 8)
    need("nonce", len(nonce) == 32)
    need("runtime_override", receipt.get("runtime_override_applied") is True)
    need("direct_entrypoints", receipt.get("effective_runtime_script") == RUN039 and receipt.get("effective_post_publish_script") == POST040 and receipt.get("direct_entrypoint_control_plane_seal_required") is True)

    now = datetime.now(timezone.utc)
    age = (now - parse_utc(receipt.get("receipt_created_at_utc"))).total_seconds()
    need("ttl", -2 <= age <= RECEIPT_TTL_SECONDS, age)

    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    git(executable, repo, "fetch", "--no-tags", "origin", fetch_spec)
    local_head = git(executable, repo, "rev-parse", "HEAD").lower()
    remote_head = git(executable, repo, "rev-parse", f"refs/remotes/origin/{BRANCH}").lower()
    need("fresh_origin", len(local_head) == 40 and local_head == remote_head)
    need("head_binding", receipt.get("local_head") == local_head and receipt.get("fresh_origin_head") == remote_head)

    request_blob = blob(executable, repo, "HEAD", REQUEST_REL)
    task_blob = blob(executable, repo, "HEAD", TASK_REL)
    queue_blob = blob(executable, repo, "HEAD", QUEUE_REL)
    need("request_blob", receipt.get("request_blob_sha") == request_blob)
    need("task_blob", receipt.get("current_task_blob_sha") == task_blob)
    need("queue_blob", receipt.get("source_queue_blob_sha") == queue_blob)

    combined = sorted(
        set(hits(git(executable, repo, "grep", "-l", "-F", TASK_ID, "HEAD", "--", QUEUE_ROOT, check=False)))
        & set(hits(git(executable, repo, "grep", "-l", "-F", ATTEMPT_ID, "HEAD", "--", QUEUE_ROOT, check=False)))
        & set(hits(git(executable, repo, "grep", "-l", "-F", IDEMPOTENCY, "HEAD", "--", QUEUE_ROOT, check=False)))
    )
    need("single_queue", combined == [QUEUE_REL], combined)

    saved = receipt.get("preflight_output_sha256") or {}
    actual: dict[str, str] = {}
    for key, rel in PREFLIGHT_OUTPUTS.items():
        path = repo / rel
        need(f"preflight_{key}_exists", path.is_file())
        value = load(path)
        need(f"preflight_{key}_slot", value.get("slot_id") == "height_difference_3")
        need(f"preflight_{key}_atomic", value.get("atomic_output_materialization") is True)
        actual[key] = sha256(path)
        need(f"preflight_{key}_sha", saved.get(key) == actual[key])

    binding_key = bind([
        TASK_ID,
        ATTEMPT_ID,
        IDEMPOTENCY,
        CONTINUATION,
        request_blob,
        task_blob,
        queue_blob,
        local_head,
        *(actual[key] for key in ("043", "045", "044", "042", "041")),
        RUN039,
        POST040,
        action_id,
        nonce,
    ])
    need("binding", receipt.get("binding_key_sha256") == binding_key)

    result = {
        "schema_version": 5,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "idempotency_key": IDEMPOTENCY,
        "continuation_key": CONTINUATION,
        "status": "COORDINATOR_REWIRE_RECEIPT_VALIDATED",
        "validated_at_utc": now.isoformat().replace("+00:00", "Z"),
        "receipt_age_seconds": age,
        "receipt_ttl_seconds": RECEIPT_TTL_SECONDS,
        "receipt_sha256": receipt_sha,
        "receipt_nonce": nonce,
        "coordinator_action_id": action_id,
        "local_head": local_head,
        "fresh_origin_head": remote_head,
        "request_blob_sha": request_blob,
        "current_task_blob_sha": task_blob,
        "source_queue_blob_sha": queue_blob,
        "matching_queue_record_count": 1,
        "matching_queue_records": combined,
        "preflight_output_sha256": actual,
        "binding_key_sha256": binding_key,
        "effective_runtime_script": RUN039,
        "effective_post_publish_script": POST040,
        "direct_entrypoint_control_plane_seal_required": True,
        "runtime_override_applied": True,
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "atomic_output_materialization": True,
        "new_task_created": False,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_mutated_by_slot": False,
        "numeric_values_written": 0,
        "final_ready": False,
        "fake_data": False,
    }
    output = repo / VALIDATION_REL
    atomic_json(output, result)
    print(json.dumps({
        "ok": True,
        "status": result["status"],
        "receipt_sha256": receipt_sha,
        "binding_key": binding_key,
        "output": str(output),
    }))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=__import__("sys").stderr)
        raise
