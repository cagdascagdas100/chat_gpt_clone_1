from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_3"
SELECTABLE = {"pickup_requested", "queued", "ready", "pending", "pending_repo_queue", "queued_for_single_shared_runner"}

class StrictJsonError(ValueError):
    pass

def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def reject_constant(value: str) -> None:
    raise StrictJsonError(f"NONFINITE_JSON_CONSTANT:{value}")

def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise StrictJsonError(f"DUPLICATE_JSON_KEY:{key}")
        out[key] = value
    return out

def strict_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs, parse_constant=reject_constant)

def load_or_none(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return strict_load(path)
    except Exception:
        return None

def atomic_json(path: Path, payload: Any, backup: Path | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp = Path(tmp.name)
    if backup is not None and path.exists():
        backup.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("wb", dir=backup.parent, delete=False) as btmp:
            btmp.write(path.read_bytes())
            btmp.flush()
            os.fsync(btmp.fileno())
            btemp = Path(btmp.name)
        os.replace(btemp, backup)
    os.replace(temp, path)

def run_validator(repo: Path, manifest_path: Path, validator_path: Path, base_validator_path: Path, output_path: Path) -> tuple[bool, dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, str(validator_path), "--repo-root", str(repo), "--manifest", str(manifest_path), "--base-validator", str(base_validator_path), "--output", str(output_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=150,
        check=False,
    )
    report = load_or_none(output_path)
    if not isinstance(report, dict):
        report = {"valid": False, "error_count": 1, "errors": [f"GENERATION_VALIDATOR_REPORT_MISSING_EXIT_{completed.returncode}", completed.stderr[-2000:]]}
    return bool(completed.returncode == 0 and report.get("valid") is True), report

def disable_tasks(repo: Path, tasks: list[dict[str, Any]], current_task_id: str, reason: str) -> list[str]:
    changed: list[str] = []
    for item in tasks:
        path = repo / item["queue_path"]
        doc = load_or_none(path)
        if not isinstance(doc, dict) or doc.get("task_id") == current_task_id:
            continue
        status = str(doc.get("status", "")).strip().lower()
        if status in SELECTABLE:
            doc["status"] = "done_no_retry_needed"
            doc["disabled_at"] = now_utc()
            doc["disabled_reason"] = reason
            atomic_json(path, doc)
            changed.append(item["queue_path"])
    return changed

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--validator", required=True)
    parser.add_argument("--base-validator", required=True)
    parser.add_argument("--current-task-id", required=True)
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = strict_load(manifest_path)
    if manifest.get("slot_id") != SLOT_ID:
        raise SystemExit("MANIFEST_SLOT_MISMATCH")
    current_task_id = args.current_task_id
    recovery_tasks = manifest["recovery_tasks"]
    current_meta = next((x for x in recovery_tasks if x["task_id"] == current_task_id), None)
    if current_meta is None:
        raise SystemExit("CURRENT_RECOVERY_TASK_NOT_IN_MANIFEST")
    sequence = int(current_meta["sequence"])
    max_requeues = int(manifest["max_requeues"])
    queue_path = repo / manifest["canonical_queue_path"]
    template_path = repo / manifest["priority2_template_path"]
    state_path = repo / manifest["recovery_state_path"]
    backup_path = repo / manifest["priority2_backup_path"]
    report_path = repo / manifest["report_path"]
    website_report_path = repo / manifest["website_report_path"]
    validation_path = repo / manifest["generation_validation_path"]
    website_validation_path = repo / manifest["website_generation_validation_path"]
    completed_path = repo / manifest["runner_completed_path"]
    runner_report_path = repo / manifest["runner_report_path"]
    checkpoint_valid, validation = run_validator(repo, manifest_path, Path(args.validator).resolve(), Path(args.base_validator).resolve(), validation_path)
    atomic_json(website_validation_path, validation)
    queue = load_or_none(queue_path)
    template = strict_load(template_path)
    if template.get("slot_id") != SLOT_ID or template.get("task_id") != manifest["canonical_task_id"]:
        raise SystemExit("PRIORITY2_TEMPLATE_IDENTITY_INVALID")
    state = load_or_none(state_path)
    if not isinstance(state, dict) or state.get("slot_id") != SLOT_ID:
        state = {"schema_version": 3, "slot_id": SLOT_ID, "canonical_task_id": manifest["canonical_task_id"], "requeue_count": 0, "consumed_recovery_task_ids": [], "history": [], "fake_data": False, "final_ready": False}
    requeue_count = int(state.get("requeue_count", 0))
    consumed = [str(x) for x in state.get("consumed_recovery_task_ids", [])]
    history = list(state.get("history", []))[-19:]
    queue_status = "missing" if not isinstance(queue, dict) else str(queue.get("status", "")).strip().lower()
    automation_exit_code = None
    if runner_report_path.is_file():
        match = re.search(r"(?m)^automation_exit_code=(-?\d+)\s*$", runner_report_path.read_text(encoding="utf-8", errors="replace"))
        if match:
            automation_exit_code = int(match.group(1))
    completed = load_or_none(completed_path)
    blockers = [str(x) for x in completed.get("blockers", [])] if isinstance(completed, dict) else []
    decision = "NO_ACTION"
    retry_reason: list[str] = []
    requeued = False
    disabled: list[str] = []
    consume_current = False
    already_consumed = current_task_id in consumed
    if checkpoint_valid:
        decision = "GENERATION_BOUND_CHECKPOINT_VALID_NO_REQUEUE"
        disabled = disable_tasks(repo, recovery_tasks, current_task_id, "GENERATION_BOUND_CHECKPOINT_VALID")
        consume_current = True
    elif already_consumed:
        decision = "RECOVERY_TASK_ALREADY_CONSUMED_NO_INCREMENT"
    else:
        if queue_status == "done": retry_reason.append("QUEUE_DONE_WITHOUT_GENERATION_BOUND_CHECKPOINT")
        if queue_status == "running": retry_reason.append("QUEUE_RUNNING_ORPHANED_WHEN_RECONCILER_SELECTED")
        if queue_status == "missing": retry_reason.append("CANONICAL_QUEUE_FILE_MISSING")
        if automation_exit_code is not None and automation_exit_code != 0: retry_reason.append(f"AUTOMATION_EXIT_NONZERO_{automation_exit_code}")
        if "AUTOMATION_EXIT_NONZERO" in blockers: retry_reason.append("COMPLETED_BLOCKER_AUTOMATION_EXIT_NONZERO")
        if "RUNNER_TASK_FAILED" in blockers: retry_reason.append("COMPLETED_BLOCKER_RUNNER_TASK_FAILED")
        retry_reason = list(dict.fromkeys(retry_reason))
        if retry_reason and requeue_count < max_requeues and sequence == requeue_count + 1:
            next_count = requeue_count + 1
            restored = copy.deepcopy(template)
            restored["status"] = "pickup_requested"
            restored["retry_reconciliation_count"] = next_count
            restored["retry_requeued_at"] = now_utc()
            restored["retry_reason"] = retry_reason
            restored["last_reconciler_task_id"] = current_task_id
            restored["idempotency_key"] = f"height-difference-3-single-pass-chain-v9-generation-bound-retry-{next_count}"
            atomic_json(queue_path, restored, backup_path)
            requeue_count = next_count
            requeued = True
            decision = "CANONICAL_TASK_GENERATION_BOUND_REQUEUED"
            consume_current = True
        elif retry_reason and sequence != requeue_count + 1:
            decision = "RECOVERY_SEQUENCE_OUT_OF_ORDER_RETAIN_UNCONSUMED"
        elif retry_reason and requeue_count >= max_requeues:
            decision = "MAX_REQUEUES_EXHAUSTED"
            disabled = disable_tasks(repo, recovery_tasks, current_task_id, "MAX_REQUEUES_EXHAUSTED")
            consume_current = True
        elif queue_status in SELECTABLE:
            decision = "CANONICAL_TASK_ALREADY_SELECTABLE_RETAIN_UNCONSUMED"
        else:
            decision = "NO_RETRY_SIGNAL_RETAIN_UNCONSUMED"
    if consume_current and current_task_id not in consumed:
        consumed.append(current_task_id)
    history.append({"checked_at": now_utc(), "reconciler_task_id": current_task_id, "sequence": sequence, "decision": decision, "consumed_this_run": consume_current, "requeued": requeued, "queue_status_before": queue_status, "automation_exit_code": automation_exit_code, "retry_reason": retry_reason, "generation_bound_checkpoint_valid": checkpoint_valid, "generation_checkpoint_error_count": int(validation.get("error_count", 0))})
    state.update({"schema_version": 3, "updated_at": now_utc(), "requeue_count": requeue_count, "consumed_recovery_task_ids": consumed[-3:], "last_decision": decision, "history": history[-20:], "fake_data": False, "final_ready": False})
    atomic_json(state_path, state)
    report = {"schema_version": 3, "slot_id": SLOT_ID, "task_id": current_task_id, "canonical_task_id": manifest["canonical_task_id"], "completed_at": now_utc(), "decision": decision, "consumed_this_run": consume_current, "canonical_task_requeued": requeued, "requeue_count": requeue_count, "max_requeues": max_requeues, "recovery_sequence": sequence, "queue_status_before": queue_status, "automation_exit_code": automation_exit_code, "completed_blockers": blockers, "retry_reason": retry_reason, "generation_bound_checkpoint_valid": checkpoint_valid, "generation_checkpoint_error_count": int(validation.get("error_count", 0)), "generation_checkpoint_errors": validation.get("errors", [])[:100], "remaining_recovery_tasks_disabled": disabled, "state_path": manifest["recovery_state_path"], "canonical_queue_path": manifest["canonical_queue_path"], "output_semantics": "GENERATION_BOUND_EXACT_BLOB_RETRY_RECONCILIATION_NONFINAL", "actual_business_data_rows_written": 0, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "final_ready": False}
    atomic_json(report_path, report)
    atomic_json(website_report_path, report)
    gate_path = repo / f"docs/chatgpt_status/aays1/status/{current_task_id}_gate.json"
    atomic_json(gate_path, {"task_id": current_task_id, "source_row_gate_passed": False, "ui_token_gate_passed": False, "browser_smoke_passed": False, "post_sync_ok": False, "manual_review_required": True, "fake_data": False, "final_ready": False})
    print(f"HEIGHT_DIFFERENCE_3_RETRY_DECISION={decision}")
    print(f"HEIGHT_DIFFERENCE_3_REQUEUE_COUNT={requeue_count}")
    print(f"HEIGHT_DIFFERENCE_3_GENERATION_CHECKPOINT_VALID={str(checkpoint_valid).lower()}")
    print("FINAL_READY=false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
