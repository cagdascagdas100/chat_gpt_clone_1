#!/usr/bin/env python3
"""Fail-closed static verifier for the existing canonical F shared-runner entry chain."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

CANONICAL_PREFIX = "F:\\TerraYield_AAYS_Portable\\runner_system\\AAYS_WT\\"
EXPECTED_BRANCH = "codex/aays-single-runner-v5-20260706"


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def verify(devam: str, launcher: str, restart: str, daemon: str) -> list[Check]:
    checks: list[Check] = []

    def add(name: str, condition: bool, detail: str = "") -> None:
        checks.append(Check(name, bool(condition), detail))

    add("devam_canonical_prefix", CANONICAL_PREFIX in devam)
    add("devam_passes_repo_root", "-RepoRoot $repoRoot" in devam)
    add("devam_passes_work_root", "-WorkRoot $workRoot" in devam)
    add("devam_pins_branch", EXPECTED_BRANCH in devam and "-MainBranch $expectedBranch" in devam)
    add("devam_max_tasks_one", "-MaxTasks 1" in devam)
    add("devam_no_panel", "-NoPanel" in devam)

    add("launcher_no_c_default_repo", '[string]$RepoRoot = ""' in launcher and "C:\\AAYS_WT\\AAYS_REPAIR" not in launcher)
    add("launcher_no_c_default_work", '[string]$WorkRoot = ""' in launcher and "C:\\AAYS_WT\\AAYS_STABLE" not in launcher)
    add("launcher_local_repo_candidate", "$localRepo = Join-Path $PSScriptRoot" in launcher)
    add("launcher_blocks_c_repo", "BLOCKED_C_DRIVE_NOT_CANONICAL" in launcher)
    add("launcher_blocks_c_work", "BLOCKED_C_WORK_ROOT_NOT_CANONICAL" in launcher)
    add("launcher_derives_workroot", "Join-Path (Split-Path -Parent $repoRoot) 'AAYS_STABLE_RUNNER_WORKTREES'" in launcher)
    add("launcher_default_max_tasks_one", "[int]$MaxTasks = 1" in launcher)
    add("launcher_records_workroot", "work_root = $WorkRoot" in launcher)

    add("restart_attempt_018", "height-difference-2-20260721-018" in restart)
    add("restart_blocks_multiple_before", "BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES" in restart)
    add("restart_preserves_single", "CANONICAL_RUNNER_ALREADY_ACTIVE_NO_NEW_PROCESS" in restart)
    add("restart_repo_entry_fallback", "repo_devam_fallback" in restart and "$repoEntry = Join-Path $repoRoot 'devam.ps1'" in restart)
    add("restart_blocks_multiple_after", "BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES_AFTER_START" in restart)

    add("daemon_f_defaults", CANONICAL_PREFIX in daemon and "C_DRIVE_NOT_CANONICAL" in daemon)
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--devam", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--restart", type=Path, required=True)
    parser.add_argument("--daemon", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    paths = (args.devam, args.launcher, args.restart, args.daemon)
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        payload = {
            "status": "BLOCKED_CANONICAL_F_LAUNCHER_CHAIN_FILE_MISSING",
            "missing": missing,
            "passed": 0,
            "total": 20,
            "final_ready": False,
            "fake_data": False,
        }
        code = 2
    else:
        texts = [path.read_text(encoding="utf-8-sig") for path in paths]
        checks = verify(*texts)
        passed = sum(check.ok for check in checks)
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": "CANONICAL_F_LAUNCHER_CHAIN_20_OF_20_PASS" if passed == len(checks) else "BLOCKED_CANONICAL_F_LAUNCHER_CHAIN_CONTRACT",
            "passed": passed,
            "total": len(checks),
            "checks": [asdict(check) for check in checks],
            "new_runner_architecture_created": False,
            "parallel_runner_allowed": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 0 if passed == len(checks) else 2

    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
