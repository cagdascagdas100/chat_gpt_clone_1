#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
ATTEMPT_ID = "height-difference-2-20260721-019"
EXPECTED_BRANCH = "codex/aays-single-runner-v5-20260706"
EXPECTED_WEB_ROWS = 305


def read_text(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8-sig")


def read_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads(read_text(root, rel))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()

    root_cmd = read_text(root, "RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd")
    hotfix = read_text(root, "docs/chatgpt_status/_shared/automation/RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.cmd")
    devam = read_text(root, "devam.ps1")
    launcher = read_text(root, "docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1")
    daemon = read_text(root, "docs/chatgpt_status/_shared/automation/RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1")
    restart = read_text(root, "docs/chatgpt_status/topography/shards/height_difference_2/automation/026_restart_existing_canonical_f_runner_if_stale.ps1")
    carrier = read_text(root, "docs/chatgpt_status/topography/shards/height_difference_2/automation/025_height_difference_2_shared_runner_carrier.ps1")
    numeric = read_text(root, "docs/chatgpt_status/topography/shards/height_difference_2/automation/014_run_official_numeric_gate.py")
    queue = read_json(root, "docs/chatgpt_status/aays1/queue/0000_001_height_difference_2_canonical_export_official_sampling_20260720.task.json")
    control = read_json(root, "docs/chatgpt_status/_shared/control/request_queue_refresh.json")
    request = read_json(root, "docs/chatgpt_status/_shared/status/reboot_runner_start_request_20260721_height_difference_2_001.json")

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("root_cmd_calls_actual_hotfix", "RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.cmd" in root_cmd, "Root cmd must call the actual hotfix.")
    check("root_cmd_pins_f_repo", "F:\\TerraYield_AAYS_Portable\\runner_system\\AAYS_WT\\AAYS_RUNNER_HEALTHY_20260707" in root_cmd, "Canonical F repo root must be explicit.")
    check("root_cmd_pins_branch", EXPECTED_BRANCH in root_cmd, "Canonical branch must be explicit.")
    check("hotfix_old_loop_removed", ":RUNNER_LOOP" not in hotfix, "Legacy infinite polling loop must be absent.")
    check("hotfix_max_tasks_eight_removed", "-MaxTasks 8" not in hotfix and "max_sequential_queue_tasks=8" not in hotfix, "Eight-task scan mode must be absent.")
    check("hotfix_calls_devam_once", 'powershell -NoProfile -ExecutionPolicy Bypass -File "devam.ps1"' in hotfix, "Hotfix must delegate once to repo devam.")
    check("hotfix_branch_guard", "BLOCKED_CANONICAL_BRANCH_MISMATCH" in hotfix and EXPECTED_BRANCH in hotfix, "Hotfix must fail closed on branch mismatch.")
    check("devam_explicit_repo_root", "-RepoRoot $repoRoot" in devam, "Devam must pass the resolved F repo root.")
    check("devam_explicit_work_root", "-WorkRoot $workRoot" in devam, "Devam must pass the derived F work root.")
    check("devam_max_tasks_one", "-MaxTasks 1" in devam, "Devam must limit each scan to one task.")
    check("launcher_blocks_c_repo", "BLOCKED_C_DRIVE_NOT_CANONICAL" in launcher, "Shared launcher must block C-drive repo roots.")
    check("launcher_blocks_c_work_root", "BLOCKED_C_WORK_ROOT_NOT_CANONICAL" in launcher, "Shared launcher must block C-drive work roots.")
    check("launcher_defaults_max_tasks_one", "[int]$MaxTasks = 1" in launcher, "Shared launcher default must be one task.")
    check("launcher_uses_persistent_daemon", "RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1" in launcher, "Shared launcher must use the persistent daemon.")
    check("daemon_runs_single_worker_contract", '"-MaxTasks","$MaxTasks"' in daemon and "Start-TrackedPowerShell" in daemon, "Persistent daemon must pass the configured one-task limit to one worker.")
    check("restart_attempt_019", ATTEMPT_ID in restart, "Restart receipt must be tied to attempt 019.")
    check("restart_recognises_actual_hotfix", "RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709" in restart, "Restart helper must recognise the actual hotfix process.")
    check("restart_requires_persistent_daemon", "Get-PersistentDaemons" in restart and "EXISTING_CANONICAL_PERSISTENT_DAEMON_RESTARTED" in restart, "Restart success must require one persistent daemon.")
    check("restart_blocks_multiple_daemons", "BLOCKED_MULTIPLE_PERSISTENT_DAEMONS_AFTER_START" in restart and "BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES" in restart, "Multiple or ambiguous processes must fail closed.")
    check("carrier_attempt_019", ATTEMPT_ID in carrier, "Carrier attempt must match the queue attempt.")
    check("carrier_web_floor_305", "$expectedWebRows = 305" in carrier and "AAYS_HEIGHT_DIFFERENCE_2_EXPECTED_WEB_ROWS" in carrier, "Carrier must pass the 305-row web floor.")
    check("numeric_gate_web_floor_305", '"305"' in numeric and "expected_web_operation_rows" in numeric, "Numeric gate must default and report the 305-row floor.")
    check("queue_identity_and_daemon_contract", queue.get("task_id") == TASK_ID and queue.get("attempt_id") == ATTEMPT_ID and queue.get("runner_contract", {}).get("persistent_daemon_required") is True and queue.get("runner_contract", {}).get("max_tasks_per_scan") == 1 and queue.get("expected_web_operation_rows") == EXPECTED_WEB_ROWS, "Queue must preserve identity and require one persistent daemon with 305 web rows.")
    check("control_and_restart_request_match", control.get("task_id") == TASK_ID and control.get("attempt_id") == ATTEMPT_ID and control.get("persistent_daemon_required") is True and control.get("max_tasks") == 1 and request.get("task_id") == TASK_ID and request.get("attempt_id") == ATTEMPT_ID and request.get("persistent_daemon_required") is True, "Control and restart request must match attempt 019 and the persistent-daemon contract.")

    passed = sum(1 for item in checks if item["passed"])
    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "product_rows_promoted": 0,
        "fixture_or_static_contract_only": True,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": passed == len(checks), "passed": passed, "total": len(checks)}))
    return 0 if passed == len(checks) else 2


if __name__ == "__main__":
    raise SystemExit(main())
