from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from AAYS_21_SLOT_RECOVERY_SUPERVISOR import SlotRecoverySupervisor


SLOTS = {
    f"{base}_{index}"
    for base in (
        "ready_to_sell", "gas_emissions", "height_difference",
        "security_public_safety", "parcel_label", "internet_access", "future_growth",
    )
    for index in (1, 2, 3)
}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(git_executable: Path, repo: Path, *args: str) -> None:
    completed = subprocess.run(
        [str(git_executable), "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())


def main() -> int:
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: fixture.py GIT_EXE [TEMP_ROOT]")
    git_executable = Path(sys.argv[1]).resolve()
    temporary_root = Path(sys.argv[2]).resolve() if len(sys.argv) == 3 else None
    if temporary_root is not None:
        temporary_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="aays_recovery_fixture_",
        dir=str(temporary_root) if temporary_root is not None else None,
    ) as temporary:
        root = Path(temporary)
        repo = root / "publisher"
        worktree_root = root / "worktrees"
        repo.mkdir()
        git(git_executable, repo, "init")
        git(git_executable, repo, "config", "user.name", "AAYS Fixture")
        git(git_executable, repo, "config", "user.email", "fixture@local.invalid")
        (repo / "marker.txt").write_text("fixture\n", encoding="utf-8")
        (repo / "docs").mkdir()
        (repo / "docs" / "example.py").write_text("print('fixture')\n", encoding="utf-8")
        git(git_executable, repo, "add", "marker.txt", "docs/example.py")
        git(git_executable, repo, "commit", "-m", "fixture")

        slot = "security_public_safety_2"
        worktree = worktree_root / slot
        worktree_root.mkdir()
        git(git_executable, repo, "worktree", "add", "--detach", str(worktree), "HEAD")
        state_slot = root / "state" / "slots" / slot
        old = datetime.now(timezone.utc) - timedelta(minutes=10)
        write_json(state_slot / "status_latest.json", {
            "slot_id": slot,
            "state": "BLOCKED",
            "task_id": "old-task",
            "attempt_id": "old-attempt",
            "blocker": "Unable to create index.lock; another git process seems to be running",
            "updated_at": old.isoformat().replace("+00:00", "Z"),
        })
        write_json(state_slot / "heartbeat_latest.json", {
            "state": "BLOCKED",
            "heartbeat_at": old.isoformat().replace("+00:00", "Z"),
            "stale_after_seconds": 45,
        })
        git_dir_line = (worktree / ".git").read_text(encoding="utf-8").splitlines()[0]
        git_dir = Path(git_dir_line.split(":", 1)[1].strip())
        if not git_dir.is_absolute():
            git_dir = (worktree / git_dir).resolve()
        lock = git_dir / "index.lock"
        lock.write_bytes(b"")
        os.utime(lock, (time.time() - 120, time.time() - 120))

        source = root / "queue" / "new.task.json"
        write_json(source, {"status": "queued"})
        os.utime(source, (time.time() + 2, time.time() + 2))
        task = {
            "slot_id": slot,
            "task_id": "new-continuation-task",
            "attempt_id": "new-continuation-attempt",
            "idempotency_key": "new-continuation-key",
        }
        supervisor = SlotRecoverySupervisor(
            root, repo, lambda _slot: worktree, git_executable, SLOTS,
        )
        supervisor.wait_seconds = 0
        first = supervisor.gate(source, task)
        second = supervisor.gate(source, task)
        lock_removed = not lock.exists()

        proactive_slot = "ready_to_sell_2"
        proactive_state = root / "state" / "slots" / proactive_slot
        write_json(proactive_state / "status_latest.json", {
            "slot_id": proactive_slot,
            "state": "BLOCKED",
            "blocker": "CHILD_REMOTE_CHECKOUT_TIMEOUT_300S",
            "updated_at": old.isoformat().replace("+00:00", "Z"),
        })
        write_json(proactive_state / "heartbeat_latest.json", {})
        proactive_source = root / "queue" / "proactive-old.task.json"
        write_json(proactive_source, {"status": "queued"})
        os.utime(proactive_source, (time.time() - 1200, time.time() - 1200))
        proactive_task = {
            "slot_id": proactive_slot,
            "task_id": "old-task-proactive-recovery",
            "attempt_id": "old-attempt-proactive-recovery",
            "idempotency_key": "old-key-proactive-recovery",
        }
        proactive_supervisor = SlotRecoverySupervisor(
            root, repo, lambda _slot: worktree, git_executable, SLOTS,
        )
        proactive_supervisor.wait_seconds = 0
        proactive_first = proactive_supervisor.gate(proactive_source, proactive_task)
        proactive_second = proactive_supervisor.gate(proactive_source, proactive_task)

        (worktree / "marker.txt").write_text("preserved dirty progress\n", encoding="utf-8")
        isolated_slot = "height_difference_1"
        isolated_state = root / "state" / "slots" / isolated_slot
        write_json(isolated_state / "status_latest.json", {
            "slot_id": isolated_slot,
            "state": "BLOCKED",
            "blocker": "CHILD_REMOTE_CHECKOUT_TIMEOUT_300S",
            "updated_at": old.isoformat().replace("+00:00", "Z"),
        })
        write_json(isolated_state / "heartbeat_latest.json", {})
        isolated_source = root / "queue" / "dirty-old.task.json"
        write_json(isolated_source, {"status": "queued"})
        os.utime(isolated_source, (time.time() - 1200, time.time() - 1200))
        isolated_task = {
            "slot_id": isolated_slot,
            "task_id": "dirty-task-isolated-recovery",
            "attempt_id": "dirty-attempt-isolated-recovery",
            "idempotency_key": "dirty-key-isolated-recovery",
            "script_path": "docs/example.py",
            "read_paths": ["docs"],
            "exact_write_paths": ["docs/output"],
        }
        isolated_supervisor = SlotRecoverySupervisor(
            root, repo, lambda _slot: worktree, git_executable, SLOTS,
        )
        isolated_supervisor.wait_seconds = 0
        isolated_first = isolated_supervisor.gate(isolated_source, isolated_task)
        isolated_second = isolated_supervisor.gate(isolated_source, isolated_task)
        isolated_plan = json.loads(
            (root / "state" / "recovery" / "slots" / isolated_slot / "latest.json").read_text(encoding="utf-8")
        )
        isolated_path = Path(str(isolated_second["task"].get("isolated_recovery_worktree") or ""))
        original_dirty_preserved = (worktree / "marker.txt").read_text(encoding="utf-8") == "preserved dirty progress\n"

        data_slot = "future_growth_2"
        data_state = root / "state" / "slots" / data_slot
        write_json(data_state / "status_latest.json", {
            "slot_id": data_slot,
            "state": "BLOCKED",
            "blocker": "VERIFIED_FUTURE_GROWTH_ROW_EXPORT_NOT_STARTED",
            "updated_at": old.isoformat().replace("+00:00", "Z"),
        })
        write_json(data_state / "heartbeat_latest.json", {})
        data_source = root / "queue" / "future.task.json"
        write_json(data_source, {"status": "queued"})
        os.utime(data_source, (time.time() + 2, time.time() + 2))
        data_task = {
            "slot_id": data_slot,
            "task_id": "future-new-continuation",
            "attempt_id": "future-new-attempt",
            "idempotency_key": "future-new-key",
        }
        data_supervisor = SlotRecoverySupervisor(
            root, repo, lambda _slot: worktree, git_executable, SLOTS,
        )
        data_supervisor.wait_seconds = 0
        data_first = data_supervisor.gate(data_source, data_task)
        data_second = data_supervisor.gate(data_source, data_task)
        time.sleep(0.02)
        write_json(data_state / "status_latest.json", {
            "slot_id": data_slot,
            "state": "BLOCKED_NO_DECLARED_OUTPUT",
            "task_id": data_task["task_id"],
            "blocker": "BLOCKED_NO_DECLARED_OUTPUT",
            "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        })
        data_third = data_supervisor.gate(data_source, data_task)

        report = {
            "status": "PASS" if (
                len(SLOTS) == 21
                and first["decision"] == "WAIT"
                and second["decision"] == "ALLOW"
                and lock_removed
                and proactive_first["decision"] == "WAIT"
                and proactive_second["decision"] == "ALLOW"
                and isolated_first["decision"] == "WAIT"
                and isolated_second["decision"] == "ALLOW"
                and isolated_path.is_dir()
                and original_dirty_preserved
                and data_first["decision"] == "WAIT"
                and data_second["decision"] == "ALLOW"
                and data_second["task"].get("source_discovery_policy")
                    == "LOCAL_FILES_THEN_FREE_PUBLIC_NO_AUTH"
                and data_second["task"].get("forbid_user_source_request") is True
                and data_second["task"].get("forbid_email_or_account_sources") is True
                and data_second["task"].get("continue_after_no_data") is True
                and data_third["decision"] == "NO_DATA_CONTINUE"
            ) else "FAIL",
            "logical_slot_count": len(SLOTS),
            "first_decision": first,
            "second_decision": second,
            "orphan_lock_removed": lock_removed,
            "proactive_first_decision": proactive_first,
            "proactive_second_decision": proactive_second,
            "isolated_first_decision": isolated_first,
            "isolated_second_decision": isolated_second,
            "isolated_plan": isolated_plan,
            "isolated_worktree_created": isolated_path.is_dir(),
            "original_dirty_progress_preserved": original_dirty_preserved,
            "data_first_decision": data_first,
            "data_second_decision": data_second,
            "data_third_decision": data_third,
            "fake_data_written": False,
            "destructive_reset_used": False,
        }
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
