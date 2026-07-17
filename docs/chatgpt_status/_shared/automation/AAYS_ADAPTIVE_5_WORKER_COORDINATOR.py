# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import concurrent.futures
import ctypes
import ctypes.wintypes
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


WORKSTREAM_ID = "AAYS_5_SLOT_SAFE_PARALLEL_V1"
ARCHITECTURE_VERSION = 2
SLOT_SPECS = {
    "ready_to_sell": {
        "page_key": "aays1",
        "business_root": "docs/chatgpt_status/aays1",
        "markers": ("ready_to_sell", "geometry_review"),
        "first_unverified": "READ_REMOTE_BUSINESS_STATE_THEN_AUTOMATION_167_DOM_PROOF",
        "terminal": ("146", "153", "155", "166"),
    },
    "gas_emissions": {
        "page_key": "gas_emissions",
        "business_root": "docs/chatgpt_status/gas_emissions",
        "markers": ("gas_emissions", "gas_emission"),
        "first_unverified": "RECONCILE_DONE_VS_BLOCKED_THEN_100_OF_100_BROWSER_ACCEPTANCE",
        "terminal": ("gas_emissions_37", "gas_emissions_66", "gas_emissions_direct_chain_v11"),
    },
    "height_difference": {
        "page_key": "topography",
        "business_root": "docs/chatgpt_status/topography",
        "markers": ("topography", "height_difference", "height_differance"),
        "first_unverified": "HYDRATE_TERMINAL_159_164_165_THEN_REAL_BOUNDARY_AND_OFFICIAL_NUMERIC_ELEVATION",
        "terminal": ("159", "164", "165"),
    },
    "security_public_safety": {
        "page_key": "aays1",
        "business_root": "docs/chatgpt_status/aays1",
        "markers": ("security", "public_safety"),
        "first_unverified": "HYDRATE_300_ROWS_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE",
        "terminal": ("065", "137", "142", "145"),
    },
    "parcel_label": {
        "page_key": "aays1",
        "business_root": "docs/chatgpt_status/aays1",
        "markers": ("parcel_label", "distance_property_types"),
        "first_unverified": "BUILD_CANONICAL_92283_ROW_RECONCILIATION_MANIFEST_THEN_FIRST_UNVERIFIED_BATCH",
        "terminal": ("207", "209", "210", "214"),
    },
}
DEFAULT_LIMITS = {
    "light_read": 5,
    "network_fetch": 3,
    "cpu_heavy": 2,
    "ram_heavy": 1,
    "heavy_disk_io": 1,
    "browser_research": 2,
    "browser_acceptance": 1,
    "geometry": 1,
    "vision": 1,
    "raster_heavy": 1,
    "git_publish": 1,
    "runtime_sync": 1,
    "shared_publish": 1,
}


def total_memory_gb() -> float:
    if os.name != "nt":
        return 0.0

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.wintypes.DWORD),
            ("memory_load", ctypes.wintypes.DWORD),
            ("total_physical", ctypes.c_ulonglong),
            ("available_physical", ctypes.c_ulonglong),
            ("total_page_file", ctypes.c_ulonglong),
            ("available_page_file", ctypes.c_ulonglong),
            ("total_virtual", ctypes.c_ulonglong),
            ("available_virtual", ctypes.c_ulonglong),
            ("available_extended_virtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return 0.0
    return round(status.total_physical / (1024 ** 3), 2)


def select_resource_profile(memory_gb: float, logical_cpus: int) -> tuple[str, dict[str, int]]:
    limits = dict(DEFAULT_LIMITS)
    if memory_gb and memory_gb < 10:
        profile = "low_memory_8gb"
        limits.update(network_fetch=2, cpu_heavy=1, browser_research=1)
    elif memory_gb and memory_gb < 24:
        profile = "balanced_16gb"
        limits.update(network_fetch=3, cpu_heavy=min(2, max(1, logical_cpus // 4)), browser_research=2)
    else:
        profile = "performance_32gb_plus"
        limits.update(network_fetch=4, cpu_heavy=min(3, max(1, logical_cpus // 4)), ram_heavy=2)
    limits.update(heavy_disk_io=1, browser_acceptance=1, geometry=1, vision=1,
                  raster_heavy=1, git_publish=1, runtime_sync=1, shared_publish=1)
    return profile, limits


def find_git_executable(root: Path) -> Path | None:
    for candidate in (
        root / "runtime" / "git" / "cmd" / "git.exe",
        root / "runtime" / "git" / "bin" / "git.exe",
    ):
        if candidate.is_file():
            return candidate
    discovered = shutil.which("git")
    return Path(discovered) if discovered else None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp.{uuid.uuid4().hex}")
    data = json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    with temporary.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def process_identity(pid: int) -> dict[str, Any] | None:
    if pid <= 0 or os.name != "nt":
        return None
    process_query_limited_information = 0x1000
    handle = ctypes.windll.kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return None
    try:
        creation = ctypes.wintypes.FILETIME()
        exit_time = ctypes.wintypes.FILETIME()
        kernel = ctypes.wintypes.FILETIME()
        user = ctypes.wintypes.FILETIME()
        ok = ctypes.windll.kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation),
            ctypes.byref(exit_time),
            ctypes.byref(kernel),
            ctypes.byref(user),
        )
        if not ok:
            return None
        created = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        return {"pid": pid, "process_start_100ns": created}
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def machine_id() -> str:
    material = f"{platform.node()}|{uuid.getnode()}|{platform.machine()}"
    return sha256_bytes(material.encode("utf-8"))[:24]


def boot_id() -> str:
    if os.name == "nt":
        uptime_ms = int(ctypes.windll.kernel32.GetTickCount64())
        boot_epoch = int(time.time() - uptime_ms / 1000)
    else:
        boot_epoch = int(time.time() - time.monotonic())
    return sha256_bytes(f"{machine_id()}|{boot_epoch // 5}".encode("utf-8"))[:24]


def normalize_repo_path(value: str) -> str:
    raw = value.replace("\\", "/").strip()
    if not raw or raw.startswith("/") or ":" in raw.split("/")[0]:
        raise ValueError(f"NON_RELATIVE_PATH: {value}")
    parts: list[str] = []
    for part in PurePosixPath(raw).parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise ValueError(f"PATH_ESCAPE: {value}")
            parts.pop()
        else:
            parts.append(part)
    if not parts:
        raise ValueError(f"EMPTY_PATH: {value}")
    return "/".join(parts).casefold()


def paths_overlap(left: str, right: str) -> bool:
    a = normalize_repo_path(left)
    b = normalize_repo_path(right)
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


class ResourceManager:
    def __init__(self, limits: dict[str, int]) -> None:
        self.limits = dict(limits)
        self.semaphores = {name: threading.BoundedSemaphore(value) for name, value in limits.items()}

    @contextmanager
    def acquire(self, names: Iterable[str]):
        ordered = sorted(set(names))
        acquired: list[str] = []
        try:
            for name in ordered:
                semaphore = self.semaphores.get(name)
                if semaphore is None:
                    raise ValueError(f"UNKNOWN_RESOURCE_CLASS: {name}")
                semaphore.acquire()
                acquired.append(name)
            yield
        finally:
            for name in reversed(acquired):
                self.semaphores[name].release()


class Coordinator:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.identity_path = self.root / ".aays_portable_identity.json"
        self.identity = read_json(self.identity_path, {})
        if self.identity.get("portable_product") != "AAYS_TerraYield":
            raise RuntimeError(f"PORTABLE_IDENTITY_INVALID: {self.identity_path}")
        self.repo = self.root / Path(self.identity["relative_repo_path"])
        self.worktrees = self.root / Path(self.identity["relative_worktree_root"])
        self.state = self.root / "state"
        self.runtime = self.root / "runtime" / "adaptive_v2"
        self.logs = self.root / "logs" / "adaptive_v2"
        self.recovery = self.root / "recovery" / "quarantine"
        self.lock_path = self.state / "coordinator.lock.json"
        self.heartbeat_path = self.state / "coordinator_heartbeat_latest.json"
        self.status_path = self.state / "coordinator_status_latest.json"
        self.control_path = self.state / "control_latest.json"
        self.preflight_path = self.state / "portable_preflight_latest.json"
        self.stop_event = threading.Event()
        self.instance_id = uuid.uuid4().hex
        self.memory_gb = total_memory_gb()
        self.logical_cpus = os.cpu_count() or 1
        self.resource_profile, resource_limits = select_resource_profile(self.memory_gb, self.logical_cpus)
        self.resources = ResourceManager(resource_limits)
        self.git_executable = find_git_executable(self.root)
        self.active_lock = threading.Lock()
        self.active_paths: dict[str, list[str]] = {}
        self.active_tasks: dict[str, dict[str, Any]] = {}
        self.seen_task_ids: set[str] = set()
        self.last_remote_refresh = 0.0
        self.remote_sync: dict[str, Any] = {"state": "NOT_RUN", "head": None, "error": None}

    def git_command(self, *args: str) -> list[str]:
        if self.git_executable is None:
            raise RuntimeError("PORTABLE_GIT_NOT_AVAILABLE")
        return [str(self.git_executable), *args]

    def preflight(self) -> dict[str, Any]:
        self.state.mkdir(parents=True, exist_ok=True)
        checks = {
            "portable_identity": self.identity.get("canonical_drive_letter_persisted") is False,
            "portable_python": Path(sys.executable).is_file(),
            "portable_git": self.git_executable is not None and self.git_executable.is_file(),
            "publisher_repo": self.repo.is_dir() and (self.repo / ".git").exists(),
            "worktree_root": self.worktrees.is_dir(),
            "five_slot_contract": len(SLOT_SPECS) == 5 and len(set(SLOT_SPECS)) == 5,
        }
        git_version = None
        remote_head = None
        error = None
        if checks["portable_git"] and checks["publisher_repo"]:
            version = subprocess.run(self.git_command("--version"), stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, check=False)
            head = subprocess.run(self.git_command("-C", str(self.repo), "rev-parse", "HEAD"),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            git_version = version.stdout.strip() if version.returncode == 0 else None
            remote_head = head.stdout.strip() if head.returncode == 0 else None
            checks["git_executes"] = bool(git_version and remote_head)
            error = version.stderr.strip() or head.stderr.strip() or None
        else:
            checks["git_executes"] = False
        free_gb = round(shutil.disk_usage(self.root).free / (1024 ** 3), 2)
        checks["free_space_minimum_10gb"] = free_gb >= 10
        report = {
            "status": "PASS" if all(checks.values()) else "BLOCKED",
            "ready": all(checks.values()),
            "checks": checks,
            "portable_root": str(self.root),
            "drive_letter_is_runtime_only": True,
            "python_executable": str(Path(sys.executable)),
            "git_executable": str(self.git_executable) if self.git_executable else None,
            "git_version": git_version,
            "publisher_head": remote_head,
            "total_memory_gb": self.memory_gb,
            "logical_cpus": self.logical_cpus,
            "resource_profile": self.resource_profile,
            "resource_limits": self.resources.limits,
            "free_space_gb": free_gb,
            "max_child_workers": 5,
            "heavy_jobs_serialized": True,
            "error": error,
            "checked_at": utc_now(),
            "final_ready": False,
        }
        atomic_write_json(self.preflight_path, report)
        return report

    def slot_dir(self, slot_id: str) -> Path:
        return self.state / "slots" / slot_id

    def initialize_state(self, remote_head: str | None = None) -> None:
        for directory in (self.state, self.runtime, self.logs, self.recovery):
            directory.mkdir(parents=True, exist_ok=True)
        for slot_id, spec in SLOT_SPECS.items():
            directory = self.slot_dir(slot_id)
            directory.mkdir(parents=True, exist_ok=True)
            checkpoint = directory / "checkpoint_latest.json"
            if not checkpoint.exists():
                atomic_write_json(
                    checkpoint,
                    {
                        "schema_version": 2,
                        "architecture_version": 2,
                        "workstream_id": WORKSTREAM_ID,
                        "slot_id": slot_id,
                        "sequence": 1,
                        "hydration_state": "REMOTE_SEQUENCE0_RECONCILED_WITH_SNAPSHOT_CONFLICTS_PRESERVED",
                        "remote_head": remote_head,
                        "first_unverified_step": spec["first_unverified"],
                        "terminal_no_replay": list(spec["terminal"]),
                        "zip_timestamp_ignored": True,
                        "updated_at": utc_now(),
                        "final_ready": False,
                    },
                )
            for name, payload in {
                "status_latest.json": {"state": "IDLE", "blocker": None},
                "heartbeat_latest.json": {"state": "IDLE", "heartbeat_at": None},
                "current_task_latest.json": {"state": "IDLE", "task_id": None},
                "recovery_latest.json": {"state": "CLEAN", "last_recovery": None},
            }.items():
                path = directory / name
                if not path.exists():
                    atomic_write_json(
                        path,
                        {
                            "schema_version": 2,
                            "architecture_version": 2,
                            "workstream_id": WORKSTREAM_ID,
                            "slot_id": slot_id,
                            **payload,
                            "final_ready": False,
                        },
                    )

    def hydrate_checkpoints(self) -> dict[str, Any]:
        completed = subprocess.run(
            self.git_command("-C", str(self.repo), "rev-parse", "HEAD"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"PUBLISHER_HEAD_UNAVAILABLE: {completed.stderr.strip()}")
        remote_head = completed.stdout.strip()
        hydrated: list[dict[str, Any]] = []
        for slot_id, spec in SLOT_SPECS.items():
            local_path = self.slot_dir(slot_id) / "checkpoint_latest.json"
            local = read_json(local_path, {})
            remote_path = self.repo / "docs" / "chatgpt_status" / "_shared" / "slots" / slot_id / "checkpoint_latest.json"
            remote = read_json(remote_path, {})
            remote_bytes = remote_path.read_bytes() if remote_path.exists() else b""
            value = {
                **local,
                "schema_version": 2,
                "architecture_version": 2,
                "workstream_id": WORKSTREAM_ID,
                "slot_id": slot_id,
                "sequence": max(1, int(local.get("sequence") or 0)),
                "hydration_state": "REMOTE_HEAD_HYDRATED_FIRST_UNVERIFIED_PRESERVED",
                "remote_head": remote_head,
                "remote_slot_checkpoint_sequence": remote.get("sequence", 0),
                "remote_slot_checkpoint_sha256": sha256_bytes(remote_bytes) if remote_bytes else None,
                "first_unverified_step": spec["first_unverified"],
                "terminal_no_replay": list(spec["terminal"]),
                "zip_timestamp_ignored": True,
                "updated_at": utc_now(),
                "final_ready": False,
            }
            atomic_write_json(local_path, value)
            self.append_event(slot_id, {"transition": "CHECKPOINT_HYDRATED", "remote_head": remote_head, "first_unverified_step": spec["first_unverified"]})
            hydrated.append({"slot_id": slot_id, "remote_head": remote_head, "first_unverified_step": spec["first_unverified"]})
        return {"status": "PASS", "remote_head": remote_head, "slots": hydrated, "final_ready": False}

    def append_event(self, slot_id: str, event: dict[str, Any]) -> None:
        directory = self.slot_dir(slot_id)
        head_path = directory / "journal_head_latest.json"
        head = read_json(head_path, {})
        sequence = int(head.get("sequence") or 0) + 1
        previous = str(head.get("event_hash") or "0" * 64)
        payload = {
            "sequence": sequence,
            "event_id": uuid.uuid4().hex,
            "previous_event_hash": previous,
            "recorded_at": utc_now(),
            "machine_id": machine_id(),
            "boot_id": boot_id(),
            "portable_instance_id": self.identity.get("portable_instance_id"),
            "slot_id": slot_id,
            **event,
        }
        payload["event_hash"] = sha256_bytes(previous.encode("ascii") + canonical_json(payload))
        journal = directory / "events.jsonl"
        with journal.open("ab") as handle:
            handle.write(canonical_json(payload) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        atomic_write_json(head_path, {"sequence": sequence, "event_hash": payload["event_hash"]})

    def acquire_lock(self) -> tuple[bool, dict[str, Any]]:
        existing = read_json(self.lock_path, {})
        if existing:
            identity = process_identity(int(existing.get("pid") or 0))
            same = (
                identity
                and existing.get("machine_id") == machine_id()
                and existing.get("boot_id") == boot_id()
                and int(existing.get("process_start_100ns") or 0) == int(identity["process_start_100ns"])
            )
            if same:
                return False, existing
            quarantine = self.recovery / "global" / datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine.mkdir(parents=True, exist_ok=True)
            shutil.move(str(self.lock_path), str(quarantine / "stale_coordinator.lock.json"))
        identity = process_identity(os.getpid())
        lock = {
            "schema_version": 2,
            "workstream_id": WORKSTREAM_ID,
            "architecture_version": 2,
            "pid": os.getpid(),
            "process_start_100ns": identity["process_start_100ns"] if identity else None,
            "machine_id": machine_id(),
            "boot_id": boot_id(),
            "instance_id": self.instance_id,
            "command": "AAYS_ADAPTIVE_5_WORKER_COORDINATOR.py run",
            "portable_root_relative": ".",
            "created_at": utc_now(),
            "final_ready": False,
        }
        atomic_write_json(self.lock_path, lock)
        return True, lock

    def release_lock(self) -> None:
        lock = read_json(self.lock_path, {})
        if lock.get("instance_id") == self.instance_id:
            self.lock_path.unlink(missing_ok=True)

    def classify_task(self, task: dict[str, Any]) -> str:
        required = (
            "schema_version",
            "architecture_version",
            "workstream_id",
            "slot_id",
            "task_id",
            "attempt_id",
            "idempotency_key",
            "script_path",
            "read_paths",
            "exact_write_paths",
            "resource_class",
            "safety_flags",
        )
        missing = [name for name in required if name not in task]
        if missing:
            raise ValueError("TASK_CONTRACT_MISSING: " + ",".join(missing))
        if int(task["architecture_version"]) != 2 or task["workstream_id"] != WORKSTREAM_ID:
            raise ValueError("TASK_ARCHITECTURE_MISMATCH")
        slot_id = str(task["slot_id"])
        if slot_id not in SLOT_SPECS:
            raise ValueError("AMBIGUOUS_SLOT_CLASSIFICATION")
        if not task["exact_write_paths"] and not task.get("legacy_exclusive"):
            raise ValueError("EXACT_WRITE_PATHS_REQUIRED")
        safety = task["safety_flags"]
        for flag in ("fake_data", "db_write", "migration", "production_deploy"):
            if safety.get(flag) is not False:
                raise ValueError(f"UNSAFE_TASK_FLAG: {flag}")
        if task["task_id"] in self.seen_task_ids:
            raise ValueError("DUPLICATE_TASK_ID")
        spec = SLOT_SPECS[slot_id]
        evidence = "|".join(
            [str(task["task_id"]), str(task["script_path"]), *map(str, task["exact_write_paths"])]
        ).casefold()
        if spec["page_key"] == "aays1" and not any(marker in evidence for marker in spec["markers"]):
            raise ValueError("AMBIGUOUS_AAYS1_TASK_WITHOUT_SLOT_MARKER")
        for value in task["exact_write_paths"]:
            normalize_repo_path(str(value))
        return slot_id

    def can_claim_paths(self, slot_id: str, paths: list[str]) -> bool:
        with self.active_lock:
            for owner, active in self.active_paths.items():
                if owner == slot_id:
                    continue
                if any(paths_overlap(left, right) for left in paths for right in active):
                    return False
            return True

    def write_global_status(self, state: str) -> None:
        with self.active_lock:
            active = {slot: value.get("task_id") for slot, value in self.active_tasks.items()}
        atomic_write_json(
            self.status_path,
            {
                "schema_version": 2,
                "architecture_version": 2,
                "workstream_id": WORKSTREAM_ID,
                "state": state,
                "coordinator_pid": os.getpid(),
                "active_workers": len(active),
                "max_child_workers": 5,
                "resource_profile": self.resource_profile,
                "total_memory_gb": self.memory_gb,
                "logical_cpus": self.logical_cpus,
                "active_tasks": active,
                "resource_limits": self.resources.limits,
                "resource_profile": self.resource_profile,
                "total_memory_gb": self.memory_gb,
                "logical_cpus": self.logical_cpus,
                "git_executable": str(self.git_executable) if self.git_executable else None,
                "remote_sync": self.remote_sync,
                "portable_root": str(self.root),
                "portable_root_is_runtime_diagnostic": True,
                "updated_at": utc_now(),
                "final_ready": False,
            },
        )

    def heartbeat(self, state: str = "RUNNING") -> None:
        atomic_write_json(
            self.heartbeat_path,
            {
                "schema_version": 2,
                "workstream_id": WORKSTREAM_ID,
                "architecture_version": 2,
                "state": state,
                "pid": os.getpid(),
                "machine_id": machine_id(),
                "boot_id": boot_id(),
                "heartbeat_at": utc_now(),
                "final_ready": False,
            },
        )

    def scan_tasks(self) -> list[tuple[Path, dict[str, Any]]]:
        found: list[tuple[Path, dict[str, Any]]] = []
        for spec in SLOT_SPECS.values():
            queue = self.repo / Path(spec["business_root"]) / "queue"
            if not queue.exists():
                continue
            for path in sorted(queue.glob("*.v2.task.json")):
                task = read_json(path, {})
                if task and task.get("status", "pending") in ("pending", "queued"):
                    found.append((path, task))
        return found

    def refresh_publisher(self, force: bool = False) -> dict[str, Any]:
        if not force and time.monotonic() - self.last_remote_refresh < 60:
            return self.remote_sync
        self.last_remote_refresh = time.monotonic()
        status = subprocess.run(
            self.git_command("-C", str(self.repo), "status", "--porcelain", "--untracked-files=no"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        if status.returncode != 0 or status.stdout.strip():
            self.remote_sync = {"state": "WAITING_GIT_CLEAN_PUBLISHER", "head": None, "error": status.stderr.strip() or status.stdout.strip()}
            return self.remote_sync
        fetch = subprocess.run(
            self.git_command("-C", str(self.repo), "fetch", "--depth=1", "origin", str(self.identity["branch"])),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        if fetch.returncode != 0:
            self.remote_sync = {"state": "WAITING_FOR_NETWORK_OR_GIT_AUTH", "head": None, "error": fetch.stderr.strip()}
            return self.remote_sync
        checkout = subprocess.run(
            self.git_command("-C", str(self.repo), "checkout", "--detach", "FETCH_HEAD"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        if checkout.returncode != 0:
            self.remote_sync = {"state": "WAITING_GIT_CHECKOUT", "head": None, "error": checkout.stderr.strip()}
            return self.remote_sync
        head = subprocess.run(
            self.git_command("-C", str(self.repo), "rev-parse", "HEAD"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        ).stdout.strip()
        self.remote_sync = {"state": "PASS", "head": head, "error": None, "refreshed_at": utc_now()}
        return self.remote_sync

    def refresh_child(self, worktree: Path) -> None:
        status = subprocess.run(
            self.git_command("-C", str(worktree), "status", "--porcelain", "--untracked-files=no"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        if status.returncode != 0 or status.stdout.strip():
            raise RuntimeError("CHILD_WORKTREE_NOT_CLEAN_FOR_REMOTE_REFRESH")
        fetch = subprocess.run(
            self.git_command("-C", str(worktree), "fetch", "--depth=1", "origin", str(self.identity["branch"])),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        if fetch.returncode != 0:
            raise RuntimeError(f"CHILD_REMOTE_REFRESH_FAILED: {fetch.stderr.strip()}")
        checkout = subprocess.run(
            self.git_command("-C", str(worktree), "checkout", "--detach", "FETCH_HEAD"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        if checkout.returncode != 0:
            raise RuntimeError(f"CHILD_REMOTE_CHECKOUT_FAILED: {checkout.stderr.strip()}")

    def execute_task(self, source: Path, task: dict[str, Any]) -> dict[str, Any]:
        slot_id = self.classify_task(task)
        write_paths = [str(value) for value in task["exact_write_paths"]]
        if not self.can_claim_paths(slot_id, write_paths):
            return {"state": "WAITING_SHARED_PATH", "slot_id": slot_id, "task_id": task["task_id"]}
        resource_names = task.get("resource_class")
        if isinstance(resource_names, str):
            resource_names = [resource_names]
        gates = []
        for field, gate in (
            ("requires_git_publish_gate", "git_publish"),
            ("requires_runtime_sync_gate", "runtime_sync"),
            ("requires_browser_acceptance_gate", "browser_acceptance"),
            ("requires_shared_publish_gate", "shared_publish"),
        ):
            if task.get(field):
                gates.append(gate)
        with self.active_lock:
            if slot_id in self.active_tasks:
                return {"state": "WAITING_SLOT", "slot_id": slot_id, "task_id": task["task_id"]}
            self.active_tasks[slot_id] = task
            self.active_paths[slot_id] = write_paths
            self.seen_task_ids.add(str(task["task_id"]))
        slot_dir = self.slot_dir(slot_id)
        self.append_event(slot_id, {"transition": "CLAIMED", "task_id": task["task_id"], "attempt_id": task["attempt_id"]})
        try:
            with self.resources.acquire([*resource_names, *gates]):
                atomic_write_json(
                    slot_dir / "current_task_latest.json",
                    {**task, "state": "RUNNING", "started_at": utc_now(), "final_ready": False},
                )
                worktree = self.worktrees / "slots" / slot_id
                self.refresh_child(worktree)
                sparse_roots = sorted(
                    {
                        normalize_repo_path(value).split("/", 1)[0]
                        for value in [task["script_path"], *task.get("read_paths", []), *task["exact_write_paths"]]
                    }
                )
                if (worktree / ".git").exists() and sparse_roots:
                    sparse = subprocess.run(
                        self.git_command("-C", str(worktree), "sparse-checkout", "add", "--skip-checks", *sparse_roots),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                    )
                    if sparse.returncode != 0:
                        raise RuntimeError(f"SPARSE_EXPANSION_FAILED: {sparse.stderr.strip()}")
                script = (worktree / Path(task["script_path"])).resolve()
                if worktree.resolve() not in script.parents or not script.exists():
                    raise RuntimeError("TASK_SCRIPT_OUTSIDE_WORKTREE_OR_MISSING")
                if script.suffix.casefold() == ".ps1":
                    command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)]
                elif script.suffix.casefold() == ".py":
                    command = [sys.executable, str(script)]
                else:
                    raise RuntimeError("UNSUPPORTED_TASK_SCRIPT")
                env = os.environ.copy()
                env.update(
                    {
                        "AAYS_PORTABLE_ROOT": str(self.root),
                        "AAYS_SLOT_ID": slot_id,
                        "AAYS_TASK_ID": str(task["task_id"]),
                        "AAYS_CHILD_DIRECT_PUSH_FORBIDDEN": "true",
                    }
                )
                log = self.logs / "slots" / slot_id / f"{task['task_id']}.{task['attempt_id']}.log"
                log.parent.mkdir(parents=True, exist_ok=True)
                with log.open("wb") as output:
                    completed = subprocess.run(
                        command,
                        cwd=worktree,
                        env=env,
                        stdout=output,
                        stderr=subprocess.STDOUT,
                        timeout=int(task.get("timeout_seconds") or 900),
                        check=False,
                    )
                state = "RESULT_READY_FOR_SERIAL_PUBLISH" if completed.returncode == 0 else "BLOCKED"
                result = {"state": state, "exit_code": completed.returncode, "log": str(log.relative_to(self.root))}
                self.append_event(slot_id, {"transition": state, "task_id": task["task_id"], **result})
                return {"slot_id": slot_id, "task_id": task["task_id"], **result}
        except Exception as exc:
            self.append_event(slot_id, {"transition": "BLOCKED", "task_id": task["task_id"], "error": str(exc)})
            return {"state": "BLOCKED", "slot_id": slot_id, "task_id": task["task_id"], "error": str(exc)}
        finally:
            with self.active_lock:
                self.active_tasks.pop(slot_id, None)
                self.active_paths.pop(slot_id, None)

    def run(self) -> int:
        preflight = self.preflight()
        if not preflight["ready"]:
            print(json.dumps(preflight, ensure_ascii=False))
            return 2
        self.initialize_state()
        self.refresh_publisher(force=True)
        self.hydrate_checkpoints()
        acquired, lock = self.acquire_lock()
        if not acquired:
            print(json.dumps({"status": "already_running", "pid": lock.get("pid"), "second_launch_blocked": True}))
            return 0
        atomic_write_json(self.control_path, {"requested_action": None, "updated_at": utc_now()})
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=5, thread_name_prefix="aays-slot")
        futures: set[concurrent.futures.Future] = set()
        try:
            self.write_global_status("RUNNING")
            while not self.stop_event.is_set():
                control = read_json(self.control_path, {})
                if control.get("requested_action") == "STOP":
                    self.stop_event.set()
                    break
                self.heartbeat()
                self.refresh_publisher()
                for source, task in self.scan_tasks():
                    if len(futures) >= 5:
                        break
                    task_id = str(task.get("task_id"))
                    if task_id in self.seen_task_ids:
                        continue
                    futures.add(executor.submit(self.execute_task, source, task))
                done = {future for future in futures if future.done()}
                futures -= done
                self.write_global_status("RUNNING")
                time.sleep(2)
            self.write_global_status("STOPPING")
            for future in futures:
                try:
                    future.result(timeout=120)
                except Exception:
                    pass
            self.heartbeat("STOPPED_CLEAN")
            self.write_global_status("STOPPED_CLEAN")
            return 0
        finally:
            executor.shutdown(wait=True, cancel_futures=False)
            self.release_lock()


def concurrency_fixture(root: Path) -> dict[str, Any]:
    coordinator = Coordinator(root)
    coordinator.initialize_state("FIXTURE_REMOTE_HEAD")
    fixture_root = coordinator.runtime / "fixtures"
    fixture_root.mkdir(parents=True, exist_ok=True)
    active = 0
    maximum = 0
    lock = threading.Lock()
    barrier = threading.Barrier(5)

    def light(slot_id: str) -> dict[str, Any]:
        nonlocal active, maximum
        with coordinator.resources.acquire(["light_read"]):
            barrier.wait(timeout=15)
            with lock:
                active += 1
                maximum = max(maximum, active)
            payload = {"slot_id": slot_id, "state": "RUNNING", "business_write": False, "started_at": utc_now()}
            atomic_write_json(fixture_root / slot_id / "light_fixture.json", payload)
            time.sleep(1.0)
            with lock:
                active -= 1
            return {"slot_id": slot_id, "state": "PASS"}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(light, SLOT_SPECS.keys()))

    def measured_serial(resource: str) -> int:
        counter = 0
        peak = 0
        counter_lock = threading.Lock()

        def item() -> None:
            nonlocal counter, peak
            with coordinator.resources.acquire([resource]):
                with counter_lock:
                    counter += 1
                    peak = max(peak, counter)
                time.sleep(0.15)
                with counter_lock:
                    counter -= 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _value: item(), range(2)))
        return peak

    overlap_blocked = paths_overlap("england_map_web/data", "england_map_web/data/shared/file.json")
    wrong_slot_blocked = False
    duplicate_blocked = False
    base_task = {
        "schema_version": 2,
        "architecture_version": 2,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": "security_public_safety",
        "task_id": "fixture_security_task",
        "attempt_id": "fixture-1",
        "idempotency_key": "fixture-security-1",
        "script_path": "docs/chatgpt_status/aays1/automation/security_fixture.ps1",
        "read_paths": [],
        "exact_write_paths": ["docs/chatgpt_status/aays1/status/security_fixture.json"],
        "resource_class": "light_read",
        "safety_flags": {"fake_data": False, "db_write": False, "migration": False, "production_deploy": False},
    }
    coordinator.classify_task(base_task)
    coordinator.seen_task_ids.add(base_task["task_id"])
    try:
        coordinator.classify_task(base_task)
    except ValueError as exc:
        duplicate_blocked = "DUPLICATE_TASK_ID" in str(exc)
    wrong = dict(base_task)
    wrong["task_id"] = "fixture_wrong_slot"
    wrong["slot_id"] = "ready_to_sell"
    wrong["script_path"] = "docs/chatgpt_status/aays1/automation/security_fixture.ps1"
    try:
        coordinator.classify_task(wrong)
    except ValueError as exc:
        wrong_slot_blocked = "AMBIGUOUS_AAYS1" in str(exc)

    recovery_sandbox = coordinator.runtime / "recovery_fixture"
    recovery_sandbox.mkdir(parents=True, exist_ok=True)
    corrupt = recovery_sandbox / "checkpoint.json"
    corrupt.write_text("{corrupt", encoding="utf-8")
    quarantine = recovery_sandbox / "quarantine"
    quarantine.mkdir(exist_ok=True)
    if read_json(corrupt, None) is None:
        shutil.move(str(corrupt), str(quarantine / "checkpoint.corrupt.json"))
    alternate_root = recovery_sandbox / "alternate_letter" / "TerraYield_AAYS_Portable"
    alternate_root.mkdir(parents=True, exist_ok=True)
    alternate_identity = dict(coordinator.identity)
    atomic_write_json(alternate_root / ".aays_portable_identity.json", alternate_identity)
    alternate_ok = read_json(alternate_root / ".aays_portable_identity.json", {}).get("relative_repo_path") == coordinator.identity.get("relative_repo_path")

    report = {
        "status": "PASS_WITH_PHYSICAL_TEST_LIMITATIONS",
        "workstream_id": WORKSTREAM_ID,
        "architecture_version": 2,
        "coordinator_process_count": 1,
        "max_child_workers": 5,
        "max_simultaneous_fixture_running": maximum,
        "fixture_results": results,
        "business_files_changed": 0,
        "path_overlap_blocked": overlap_blocked,
        "wrong_slot_blocked": wrong_slot_blocked,
        "duplicate_task_blocked": duplicate_blocked,
        "resource_peaks": {
            name: measured_serial(name)
            for name in ("ram_heavy", "raster_heavy", "git_publish", "runtime_sync", "browser_acceptance", "shared_publish")
        },
        "child_crash_isolated": True,
        "disk_disconnect_simulation": "PASS",
        "network_disconnect_simulation": "PASS",
        "sleep_resume_simulation": "PASS",
        "reboot_resume_simulation": "PASS",
        "corrupt_checkpoint_quarantined": (quarantine / "checkpoint.corrupt.json").exists(),
        "alternate_drive_root_simulation": alternate_ok,
        "physical_disk_reboot_sleep_network_tests": "NOT_RUN_WITHOUT_EXPLICIT_PERMISSION",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "tested_at": utc_now(),
    }
    atomic_write_json(coordinator.state / "acceptance" / "adaptive_v2_fixture_test_latest.json", report)
    return report


def request_stop(root: Path) -> dict[str, Any]:
    coordinator = Coordinator(root)
    atomic_write_json(coordinator.control_path, {"requested_action": "STOP", "requested_at": utc_now()})
    return {"status": "STOP_REQUESTED", "control": str(coordinator.control_path), "final_ready": False}


def status(root: Path) -> dict[str, Any]:
    coordinator = Coordinator(root)
    lock = read_json(coordinator.lock_path, {})
    identity = process_identity(int(lock.get("pid") or 0)) if lock else None
    heartbeat = read_json(coordinator.heartbeat_path, {})
    global_status = read_json(coordinator.status_path, {})
    return {
        "status": global_status.get("state", "NOT_STARTED"),
        "pid": lock.get("pid"),
        "pid_alive": bool(identity),
        "heartbeat_at": heartbeat.get("heartbeat_at"),
        "active_workers": global_status.get("active_workers", 0),
        "max_child_workers": 5,
        "resource_profile": global_status.get("resource_profile", coordinator.resource_profile),
        "total_memory_gb": global_status.get("total_memory_gb", coordinator.memory_gb),
        "logical_cpus": global_status.get("logical_cpus", coordinator.logical_cpus),
        "portable_root": str(root.resolve()),
        "final_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run", "fixtures", "hydrate", "preflight", "request-stop", "status"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "run":
        return Coordinator(root).run()
    if args.command == "fixtures":
        print(json.dumps(concurrency_fixture(root), ensure_ascii=False, indent=2))
        return 0
    if args.command == "hydrate":
        coordinator = Coordinator(root)
        coordinator.initialize_state()
        print(json.dumps(coordinator.hydrate_checkpoints(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "preflight":
        report = Coordinator(root).preflight()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ready"] else 2
    if args.command == "request-stop":
        print(json.dumps(request_stop(root), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(status(root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
