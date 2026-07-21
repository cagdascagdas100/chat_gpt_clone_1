#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
SLOT_ID = "height_difference_2"
IDEMPOTENCY_KEY = "height-difference-2-canonical-export-official-sampling-v3"


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runtime-recovery", type=Path, required=True)
    p.add_argument("--bridge-task", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)

    checks: dict[str, Any] = {}
    code = 2
    try:
        recovery = _read(args.runtime_recovery)
        task = _read(args.bridge_task)
        if recovery.get("status") != "SAME_TASK_RUNTIME_READY_RECEIPT_WRITTEN":
            raise ValueError("runtime recovery receipt status incomplete")
        if recovery.get("task_id") != TASK_ID or recovery.get("slot_id") != SLOT_ID:
            raise ValueError("runtime recovery identity mismatch")
        if not recovery.get("runtime_receipt_written") or not recovery.get("ready_for_claim"):
            raise ValueError("runtime recovery ready receipt missing")
        if recovery.get("bridge_task_sha256") != _sha256(args.bridge_task):
            raise ValueError("bridge task hash mismatch")
        if task.get("task_id") != TASK_ID or task.get("slot_id") != SLOT_ID:
            raise ValueError("bridge task identity mismatch")
        if task.get("idempotency_key") != IDEMPOTENCY_KEY:
            raise ValueError("bridge task idempotency mismatch")
        if not task.get("runtime_recovery_applied") or not task.get("ready_for_claim") or not task.get("claimable"):
            raise ValueError("bridge task runtime-ready flags missing")
        if task.get("runtime_recovery_contract") != "branch_aware_same_task_existing_bridge_v1":
            raise ValueError("bridge task recovery contract mismatch")
        forbidden = ("new_runner", "parallel_runner", "new_task_created", "fake_data", "db_write", "migration", "production_deploy", "final_ready")
        if any(bool(recovery.get(k)) or bool(task.get(k)) for k in forbidden):
            raise ValueError("runtime receipt safety flag mismatch")
        markers = recovery.get("markers_after") or {}
        pending = markers.get("pending") or []
        if str(args.bridge_task) not in pending:
            raise ValueError("bridge pending marker missing")
        checks = {
            "task_id": TASK_ID,
            "slot_id": SLOT_ID,
            "bridge_task_sha256": _sha256(args.bridge_task),
            "pending_marker_count": len(pending),
            "ready_for_claim": True,
            "same_idempotent_task_only": True,
            "new_runner": False,
            "new_task_created": False,
        }
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": TASK_ID,
            "status": "SAME_TASK_RUNTIME_RECEIPT_VERIFIED",
            "checks": checks,
            "claim_observed": False,
            "process_started": False,
            "new_runner": False,
            "parallel_runner": False,
            "new_task_created": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 0
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": TASK_ID,
            "status": "BLOCKED_SAME_TASK_RUNTIME_RECEIPT_VERIFICATION",
            "error": f"{type(exc).__name__}: {exc}",
            "checks": checks,
            "claim_observed": False,
            "process_started": False,
            "new_runner": False,
            "parallel_runner": False,
            "new_task_created": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"]}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
