#!/usr/bin/env python3
"""Generate a deterministic, evidence-bound coordinator runtime-rewire receipt.

This helper is called by the existing coordinator only after it has applied the
same-task runtime override. It does not mutate queue state, start a runner,
publish, or write numeric parcel values. All repository evidence is recomputed
locally from fresh canonical origin plus the five preflight outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import subprocess
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
PREFLIGHT_OUTPUTS = {
    "043": "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/039_batch136_exact_head_preflight/exact_branch_head_and_dependency_preflight_runtime.json",
    "045": "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json",
    "044": "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json",
    "042": "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/037_batch135_fresh_origin_wiring_qa/fresh_origin_wiring_preflight_runtime.json",
    "041": "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/035_batch134_coordinator_wiring_qa/coordinator_wiring_request_validation.json",
}


def root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object:{path}")
    return value


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def binding_key(parts: list[str]) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def resolve_git() -> str:
    token = str(os.environ.get("AAYS_GIT_EXE") or "git").strip()
    found = shutil.which(token)
    if found:
        return str(Path(found).resolve())
    candidate = Path(token)
    if candidate.is_file():
        return str(candidate.resolve())
    raise RuntimeError(f"GIT_EXECUTABLE_NOT_FOUND:{token}")


def run_git(git: str, repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run([git, "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:{proc.stderr[-1600:]}")
    return proc.stdout.strip()


def git_blob(git: str, repo: Path, ref: str, rel: str) -> str:
    value = run_git(git, repo, "rev-parse", f"{ref}:{rel}").lower()
    if len(value) != 40:
        raise ValueError(f"invalid Git blob:{ref}:{rel}:{value}")
    return value


def normalize_hits(raw: str) -> list[str]:
    hits: set[str] = set()
    for line in raw.splitlines():
        token = line.strip()
        if token.startswith("HEAD:"):
            token = token[5:]
        if token:
            hits.add(token)
    return sorted(hits)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coordinator-action-id", required=True)
    parser.add_argument("--effective-runtime-script", required=True)
    parser.add_argument("--effective-post-publish-script", required=True)
    parser.add_argument("--runtime-override-applied", action="store_true")
    args = parser.parse_args()

    if not args.runtime_override_applied:
        raise ValueError("coordinator must explicitly attest runtime override applied")
    if args.effective_runtime_script != RUN039 or args.effective_post_publish_script != POST040:
        raise ValueError("effective coordinator entrypoint mismatch")
    action_id = args.coordinator_action_id.strip()
    if len(action_id) < 8:
        raise ValueError("coordinator action id too short")

    repo = root(Path(__file__).resolve())
    git = resolve_git()
    request = load_json(repo / REQUEST_REL)
    task = load_json(repo / TASK_REL)
    queue = load_json(repo / QUEUE_REL)
    if request.get("task_id") != TASK_ID or request.get("attempt_id") != ATTEMPT_ID or request.get("idempotency_key") != IDEMPOTENCY or request.get("continuation_key") != CONTINUATION:
        raise ValueError("request identity mismatch")
    if task.get("task_id") != TASK_ID or task.get("attempt_id") != ATTEMPT_ID or task.get("idempotency_key") != IDEMPOTENCY or task.get("continuation_key") != CONTINUATION:
        raise ValueError("current task identity mismatch")
    if queue.get("task_id") != TASK_ID or queue.get("attempt_id") != ATTEMPT_ID or queue.get("idempotency_key") != IDEMPOTENCY:
        raise ValueError("legacy queue stable identity mismatch")

    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    run_git(git, repo, "fetch", "--no-tags", "origin", fetch_spec)
    local_head = run_git(git, repo, "rev-parse", "HEAD").lower()
    remote_head = run_git(git, repo, "rev-parse", f"refs/remotes/origin/{BRANCH}").lower()
    if len(local_head) != 40 or local_head != remote_head:
        raise RuntimeError(f"LOCAL_HEAD_NOT_FRESH_ORIGIN:{local_head}:{remote_head}")

    request_blob = git_blob(git, repo, "HEAD", REQUEST_REL)
    task_blob = git_blob(git, repo, "HEAD", TASK_REL)
    queue_blob = git_blob(git, repo, "HEAD", QUEUE_REL)

    task_hits = normalize_hits(run_git(git, repo, "grep", "-l", "-F", TASK_ID, "HEAD", "--", QUEUE_ROOT, check=False))
    attempt_hits = normalize_hits(run_git(git, repo, "grep", "-l", "-F", ATTEMPT_ID, "HEAD", "--", QUEUE_ROOT, check=False))
    idem_hits = normalize_hits(run_git(git, repo, "grep", "-l", "-F", IDEMPOTENCY, "HEAD", "--", QUEUE_ROOT, check=False))
    combined = sorted(set(task_hits).intersection(attempt_hits).intersection(idem_hits))
    if combined != [QUEUE_REL]:
        raise RuntimeError(f"DUPLICATE_OR_MISSING_QUEUE_RECORD:{combined}")

    hashes: dict[str, str] = {}
    for key, rel in PREFLIGHT_OUTPUTS.items():
        path = repo / rel
        if not path.is_file():
            raise FileNotFoundError(path)
        payload = load_json(path)
        if payload.get("slot_id") != "height_difference_3":
            raise ValueError(f"preflight slot mismatch:{key}")
        if payload.get("task_id") is not None and payload.get("task_id") != TASK_ID:
            raise ValueError(f"preflight task mismatch:{key}")
        if payload.get("continuation_key") is not None and payload.get("continuation_key") != CONTINUATION:
            raise ValueError(f"preflight continuation mismatch:{key}")
        hashes[key] = sha256_file(path)

    nonce = secrets.token_hex(16)
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    binding = binding_key([
        TASK_ID, ATTEMPT_ID, IDEMPOTENCY, CONTINUATION,
        request_blob, task_blob, queue_blob, local_head,
        *(hashes[k] for k in ("043", "045", "044", "042", "041")),
        RUN039, POST040, action_id, nonce,
    ])
    payload = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "status": "COORDINATOR_RUNTIME_REWIRE_RECEIPT",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "idempotency_key": IDEMPOTENCY,
        "continuation_key": CONTINUATION,
        "receipt_created_at_utc": created,
        "coordinator_action_id": action_id,
        "receipt_nonce": nonce,
        "local_head": local_head,
        "fresh_origin_head": remote_head,
        "fresh_origin_fetch_refspec": fetch_spec,
        "request_blob_sha": request_blob,
        "current_task_blob_sha": task_blob,
        "source_queue_blob_sha": queue_blob,
        "queue_census_basis": ["task_id", "attempt_id", "idempotency_key"],
        "matching_queue_record_count": 1,
        "matching_queue_records": combined,
        "preflight_output_sha256": hashes,
        "binding_key_sha256": binding,
        "runtime_override_applied": True,
        "effective_runtime_script": RUN039,
        "effective_post_publish_script": POST040,
        "coordinator_only": True,
        "new_queue_record_created": False,
        "new_task_created": False,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_mutated_by_slot": False,
        "numeric_values_written": 0,
        "final_ready": False,
        "fake_data": False,
    }
    output = repo / RECEIPT_REL
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": payload["status"], "action_id": action_id, "queue_records": 1, "head": local_head, "receipt_nonce": nonce, "binding_key": binding, "output": str(output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
