#!/usr/bin/env python3
"""Keep the portable AAYS coordinator alive until the user explicitly stops it."""
from __future__ import annotations

import argparse
import ctypes
import json
import msvcrt
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CREATE_NO_WINDOW = 0x08000000
CHECK_INTERVAL_SECONDS = 10
STALE_SECONDS = 60
STALE_POLLS_BEFORE_RESTART = 3
ES_SYSTEM_REQUIRED = 0x00000001
ES_CONTINUOUS = 0x80000000


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


class KeepAlive:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.python = self.root / "runtime" / "python312" / "python.exe"
        self.coordinator = self.root / "AAYS_ADAPTIVE_15_WORKER_COORDINATOR.py"
        self.launcher = self.root / "RUN_AAYS_ADAPTIVE_15_WORKER.ps1"
        self.state = self.root / "state"
        self.heartbeat = self.state / "runner_keepalive_watchdog_latest.json"
        self.lock_path = self.state / "runner_keepalive_watchdog.lock"
        self.stop_path = self.state / "runner_keepalive_watchdog.stop.requested"
        self.manual_stop = self.state / "manual_stop.requested.json"
        self.log_path = self.root / "logs" / "adaptive_v3" / "runner_keepalive_watchdog.log"
        for required in (self.python, self.coordinator, self.launcher):
            if not required.is_file():
                raise FileNotFoundError(required)

    def log(self, message: str) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if self.log_path.exists() and self.log_path.stat().st_size > 5_000_000:
            rotated = self.log_path.with_suffix(".previous.log")
            try:
                os.replace(self.log_path, rotated)
            except OSError:
                pass
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{utc_now()} {message}\n")

    def block_idle_system_sleep(self, enabled: bool) -> None:
        flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED if enabled else ES_CONTINUOUS
        if not ctypes.windll.kernel32.SetThreadExecutionState(flags):
            raise ctypes.WinError()
        self.log(f"idle system sleep block enabled={enabled}")

    def coordinator_status(self) -> dict[str, Any]:
        completed = subprocess.run(
            [str(self.python), str(self.coordinator), "status", "--root", str(self.root)],
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            creationflags=CREATE_NO_WINDOW,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"STATUS_FAILED_{completed.returncode}: {completed.stderr.strip()}")
        return json.loads(completed.stdout)

    def launch(self, action: str) -> tuple[bool, str]:
        # Do not block the watchdog for the launcher's full preflight/stop
        # window. Start it detached and keep monitoring every ten seconds; the
        # coordinator has its own single-instance lock and reports the result.
        process = subprocess.Popen(
            [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(self.launcher), "-Action", action,
            ],
            cwd=self.root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )
        output = f"launcher_pid={process.pid}"
        self.log(f"launcher action={action} dispatched {output}")
        return True, output

    def snapshot(self, state: str, status: dict[str, Any], **extra: Any) -> dict[str, Any]:
        heartbeat_at = parse_time(status.get("heartbeat_at"))
        age = None
        if heartbeat_at is not None:
            age = max(0.0, (datetime.now(timezone.utc) - heartbeat_at).total_seconds())
        return {
            "schema_version": 1,
            "state": state,
            "watchdog_pid": os.getpid(),
            "coordinator_pid": status.get("pid"),
            "coordinator_pid_alive": bool(status.get("pid_alive")),
            "coordinator_heartbeat_at": status.get("heartbeat_at"),
            "coordinator_heartbeat_age_seconds": None if age is None else round(age, 1),
            "manual_stop_requested": self.manual_stop.exists(),
            "logical_slot_count": 22,
            "physical_worker_upper_limit": 15,
            "idle_system_sleep_blocked": True,
            "updated_at": utc_now(),
            "final_ready": False,
            **extra,
        }

    def check_only(self) -> int:
        try:
            status = self.coordinator_status()
            payload = self.snapshot("CHECK", status)
        except Exception as exc:
            payload = {"state": "CHECK_ERROR", "error": f"{type(exc).__name__}: {exc}", "updated_at": utc_now()}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["state"] == "CHECK" else 2

    def run(self) -> int:
        self.state.mkdir(parents=True, exist_ok=True)
        lock_handle = self.lock_path.open("a+b")
        if self.lock_path.stat().st_size == 0:
            lock_handle.write(b"0")
            lock_handle.flush()
        lock_handle.seek(0)
        try:
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            print(json.dumps({"status": "already_running", "second_watchdog_blocked": True}))
            return 0

        self.stop_path.unlink(missing_ok=True)
        self.block_idle_system_sleep(True)
        self.log(f"watchdog started pid={os.getpid()} root={self.root}")
        stale_polls = 0
        backoff_until = 0.0
        last_error: str | None = None
        try:
            while not self.stop_path.exists():
                try:
                    status = self.coordinator_status()
                    alive = bool(status.get("pid_alive"))
                    heartbeat_at = parse_time(status.get("heartbeat_at"))
                    age = float("inf") if heartbeat_at is None else max(
                        0.0, (datetime.now(timezone.utc) - heartbeat_at).total_seconds()
                    )
                    lock_created_at = parse_time(status.get("lock_created_at"))
                    startup_age = float("inf") if lock_created_at is None else max(
                        0.0, (datetime.now(timezone.utc) - lock_created_at).total_seconds()
                    )
                    heartbeat_matches_lock = (
                        status.get("heartbeat_pid") is not None
                        and status.get("heartbeat_pid") == status.get("pid")
                    )
                    if self.manual_stop.exists():
                        stale_polls = 0
                        payload = self.snapshot("PAUSED_BY_USER", status, last_error=last_error)
                    elif alive and not heartbeat_matches_lock and startup_age <= 180:
                        # A new coordinator has acquired the lock but has not
                        # replaced the previous process's heartbeat yet. Give
                        # initialization a bounded grace window instead of
                        # immediately dispatching a false Restart.
                        stale_polls = 0
                        payload = self.snapshot(
                            "COORDINATOR_STARTUP_GRACE",
                            status,
                            startup_age_seconds=round(startup_age, 1),
                        )
                    elif alive and age <= STALE_SECONDS:
                        stale_polls = 0
                        last_error = None
                        payload = self.snapshot("MONITORING_HEALTHY", status)
                    elif time.monotonic() < backoff_until:
                        payload = self.snapshot("RESTART_BACKOFF", status, last_error=last_error)
                    elif not alive:
                        ok, output = self.launch("Start")
                        last_error = None if ok else output[-2000:]
                        backoff_until = time.monotonic() + (5 if ok else 30)
                        payload = self.snapshot("START_REQUESTED" if ok else "START_FAILED", status, last_error=last_error)
                    else:
                        stale_polls += 1
                        if stale_polls >= STALE_POLLS_BEFORE_RESTART:
                            ok, output = self.launch("Restart")
                            last_error = None if ok else output[-2000:]
                            backoff_until = time.monotonic() + (10 if ok else 60)
                            stale_polls = 0
                            payload = self.snapshot("STALE_RESTART_REQUESTED" if ok else "STALE_RESTART_FAILED", status, last_error=last_error)
                        else:
                            payload = self.snapshot("STALE_CONFIRMING", status, stale_poll=stale_polls)
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                    payload = {
                        "schema_version": 1,
                        "state": "WATCHDOG_ERROR",
                        "watchdog_pid": os.getpid(),
                        "error": last_error,
                        "updated_at": utc_now(),
                        "final_ready": False,
                    }
                    self.log(last_error)
                atomic_json(self.heartbeat, payload)
                time.sleep(CHECK_INTERVAL_SECONDS)
            self.log("watchdog stop requested by user")
            try:
                status = self.coordinator_status()
            except Exception:
                status = {}
            atomic_json(self.heartbeat, self.snapshot("STOPPED_BY_USER", status))
            return 0
        finally:
            try:
                self.block_idle_system_sleep(False)
            except OSError as exc:
                self.log(f"sleep block release warning: {exc}")
            try:
                lock_handle.seek(0)
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
            lock_handle.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    keepalive = KeepAlive(args.root)
    return keepalive.check_only() if args.check else keepalive.run()


if __name__ == "__main__":
    raise SystemExit(main())
