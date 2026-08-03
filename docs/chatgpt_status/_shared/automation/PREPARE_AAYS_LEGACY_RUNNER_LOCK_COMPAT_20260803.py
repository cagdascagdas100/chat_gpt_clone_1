#!/usr/bin/env python3
"""Fail-closed compatibility guard for legacy AAYS single-runner lock records."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from typing import Any

EXPECTED_RUNNER_PREFIX = "RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON"


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def read_json(path: pathlib.Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def write_json_atomic(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.tmp.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def parse_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except ValueError:
        return None


def heartbeat_age_seconds(heartbeat: dict[str, Any] | None, now: dt.datetime) -> float:
    observed = parse_time((heartbeat or {}).get("heartbeat_at"))
    return float("inf") if observed is None else max(0.0, (now - observed).total_seconds())


def classify_legacy_lock(
    lock: dict[str, Any] | None,
    *,
    process_alive: bool,
    command_line: str,
    expected_repo_root: str,
    expected_branch: str,
    heartbeat_age: float,
    stale_minutes: int,
) -> dict[str, Any]:
    if not lock or lock.get("pid") is None:
        return {"action": "no_lock", "verified": False, "reason": "lock_missing_or_invalid"}

    if lock.get("process_start_time") or lock.get("lock_scope"):
        return {"action": "not_legacy", "verified": False, "reason": "new_schema_lock"}

    if not process_alive:
        return {"action": "remove_dead_legacy_lock", "verified": False, "reason": "legacy_pid_not_alive"}

    expected_repo = os.path.normcase(os.path.normpath(expected_repo_root))
    lock_repo = os.path.normcase(os.path.normpath(str(lock.get("repo_root") or "")))
    repo_matches = bool(lock_repo) and lock_repo == expected_repo
    branch_matches = str(lock.get("branch") or "") == expected_branch
    runner_matches = str(lock.get("runner") or "").startswith(EXPECTED_RUNNER_PREFIX)
    command_matches = (
        bool(command_line.strip())
        and EXPECTED_RUNNER_PREFIX.lower() in command_line.lower()
        and expected_repo_root.lower() in command_line.lower()
    )
    verified = repo_matches and branch_matches and runner_matches and command_matches
    if not verified:
        return {
            "action": "fail_closed",
            "verified": False,
            "reason": "legacy_live_lock_identity_unverified",
        }

    threshold = max(1, stale_minutes) * 60
    if heartbeat_age == float("inf") or heartbeat_age > threshold:
        return {
            "action": "stop_verified_stale_legacy_daemon",
            "verified": True,
            "reason": "legacy_identity_verified_heartbeat_stale",
        }
    return {
        "action": "migrate_verified_fresh_legacy_lock",
        "verified": True,
        "reason": "legacy_identity_verified_heartbeat_fresh",
    }


def resolve_repo_root(requested: str) -> pathlib.Path:
    candidates = [
        requested,
        str(pathlib.Path(__file__).resolve().parents[4]),
        r"F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = pathlib.Path(candidate).resolve()
        if (path / "docs" / "chatgpt_status" / "_shared").is_dir():
            if str(path).lower().startswith("c:\\"):
                raise RuntimeError(f"BLOCKED_C_DRIVE_NOT_CANONICAL={path}")
            return path
    raise RuntimeError("AAYS_REPO_ROOT_NOT_FOUND")


def get_process_info(pid: int) -> dict[str, Any] | None:
    if os.name != "nt":
        raise RuntimeError("WINDOWS_PROCESS_INSPECTION_REQUIRED")
    script = (
        f'$p=Get-CimInstance Win32_Process -Filter "ProcessId={pid}" -ErrorAction SilentlyContinue;'
        "if($null -eq $p){exit 3};"
        f"$g=Get-Process -Id {pid} -ErrorAction Stop;"
        "[pscustomobject]@{process_id=$p.ProcessId;command_line=[string]$p.CommandLine;"
        "start_time=$g.StartTime.ToUniversalTime().ToString('o')}|ConvertTo-Json -Compress"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if result.returncode == 3:
        return None
    if result.returncode != 0:
        raise RuntimeError(f"PROCESS_INSPECTION_FAILED:{result.stderr.strip()}")
    value = json.loads(result.stdout)
    return value if isinstance(value, dict) else None


def stop_process_tree(pid: int) -> None:
    result = subprocess.run(
        ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0 and get_process_info(pid) is not None:
        raise RuntimeError(f"LEGACY_STALE_RUNNER_TREE_STOP_FAILED:{result.stdout.strip()}:{result.stderr.strip()}")
    if get_process_info(pid) is not None:
        raise RuntimeError(f"LEGACY_STALE_RUNNER_TREE_STILL_ALIVE={pid}")


def self_test() -> None:
    repo = r"F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
    branch = "codex/aays-single-runner-v5-20260706"
    lock = {
        "pid": 10108,
        "runner": "RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707",
        "repo_root": repo,
        "branch": branch,
        "started_at": "2026-07-09T21:25:46Z",
    }
    command = f"powershell.exe -File X:\\RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1 -RepoRoot {repo}"
    cases = [
        (True, command, 999999.0, "stop_verified_stale_legacy_daemon"),
        (True, command, 10.0, "migrate_verified_fresh_legacy_lock"),
        (True, "powershell.exe -File unrelated.ps1", 999999.0, "fail_closed"),
        (False, "", 999999.0, "remove_dead_legacy_lock"),
    ]
    for alive, cmd, age, expected in cases:
        actual = classify_legacy_lock(
            lock,
            process_alive=alive,
            command_line=cmd,
            expected_repo_root=repo,
            expected_branch=branch,
            heartbeat_age=age,
            stale_minutes=15,
        )
        if actual["action"] != expected:
            raise AssertionError(f"{expected}!={actual}")
    print(json.dumps({"self_test": "PASS", "cases": len(cases)}, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--main-branch", default="codex/aays-single-runner-v5-20260706")
    parser.add_argument("--stale-minutes", type=int, default=15)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    repo = resolve_repo_root(args.repo_root)
    shared = repo / "docs" / "chatgpt_status" / "_shared"
    lock_path = shared / "locks" / "single_runner.lock"
    heartbeat = read_json(shared / "heartbeat" / "stable_runner_daemon_heartbeat_latest.json")
    lock = read_json(lock_path)
    if not lock or lock.get("pid") is None:
        print(json.dumps({"state": "NO_LOCK", "changed": False}))
        return 0

    pid = int(lock["pid"])
    process = get_process_info(pid)
    age = heartbeat_age_seconds(heartbeat, utc_now())
    decision = classify_legacy_lock(
        lock,
        process_alive=process is not None,
        command_line=str((process or {}).get("command_line") or ""),
        expected_repo_root=str(repo),
        expected_branch=args.main_branch,
        heartbeat_age=age,
        stale_minutes=args.stale_minutes,
    )
    action = decision["action"]
    if action in {"no_lock", "not_legacy"}:
        print(json.dumps({"state": action.upper(), "changed": False}))
        return 0
    if action == "remove_dead_legacy_lock":
        lock_path.unlink(missing_ok=True)
    elif action == "fail_closed":
        raise RuntimeError(f"BLOCKED_LEGACY_LIVE_LOCK_OWNER_IDENTITY_UNVERIFIED_PID={pid}")
    elif action == "stop_verified_stale_legacy_daemon":
        stop_process_tree(pid)
        lock_path.unlink(missing_ok=True)
    elif action == "migrate_verified_fresh_legacy_lock":
        lock["process_start_time"] = process["start_time"]
        lock["lock_scope"] = "single_shared_runner_daemon"
        lock["supervisor_pid"] = pid
        lock["updated_at"] = utc_now().isoformat()
        lock.setdefault("instance_id", f"legacy-migrated-{pid}")
        write_json_atomic(lock_path, lock)
    else:
        raise RuntimeError(f"UNEXPECTED_LEGACY_LOCK_ACTION={action}")

    print(json.dumps({"state": action.upper(), "pid": pid, "changed": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"{type(exc).__name__}:{exc}", file=sys.stderr)
        raise SystemExit(1)
