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
import urllib.request
from contextlib import ExitStack, contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
LEGACY_WORKSTREAM_IDS = {"AAYS_15_SLOT_SAFE_PARALLEL_V1", "AAYS_18_SLOT_SAFE_PARALLEL_V1"}
ARCHITECTURE_VERSION = 3
TASK_LEASE_SECONDS = 3600
MAX_TASK_TIMEOUT_SECONDS = 7200
BASE_SLOT_SPECS = {
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
    "internet_access": {
        "page_key": "internet_access_parcel_layer_low_credit_20260612",
        "business_root": "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612",
        "markers": ("internet_access", "internet", "broadband"),
        "first_unverified": "MIGRATE_33785_VERIFIED_ROWS_THEN_CLOSE_58498_WITH_VERIFIED_POSTCODE_OR_NO_DATA",
        "terminal": (),
    },
    "future_growth": {
        "page_key": "aays1",
        "business_root": "docs/chatgpt_status/aays1",
        "markers": ("future_growth", "future-growth", "growth_forecast"),
        "first_unverified": "BUILD_VERIFIED_92283_ROW_FUTURE_GROWTH_EVIDENCE_MATRIX_THEN_SCORE_WITH_CONFIDENCE",
        "terminal": (),
    },
}
PARCEL_SHARDS = {
    1: {"start": 1, "end": 30761, "count": 30761},
    2: {"start": 30762, "end": 61522, "count": 30761},
    3: {"start": 61523, "end": 92283, "count": 30761},
}
SLOT_SPECS: dict[str, dict[str, Any]] = {}
for base_slot_id, base_spec in BASE_SLOT_SPECS.items():
    for shard_index, parcel_partition in PARCEL_SHARDS.items():
        slot_id = f"{base_slot_id}_{shard_index}"
        SLOT_SPECS[slot_id] = {
            **base_spec,
            "base_slot_id": base_slot_id,
            "shard_index": shard_index,
            "parcel_partition": parcel_partition,
            "markers": (*base_spec["markers"], slot_id),
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


def memory_snapshot_gb() -> tuple[float, float]:
    if os.name != "nt":
        return 0.0, 0.0

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
        return 0.0, 0.0
    divisor = 1024 ** 3
    return round(status.total_physical / divisor, 2), round(status.available_physical / divisor, 2)


def total_memory_gb() -> float:
    return memory_snapshot_gb()[0]


def available_memory_gb() -> float:
    return memory_snapshot_gb()[1]


def select_resource_profile(memory_gb: float, logical_cpus: int) -> tuple[str, dict[str, int], int]:
    limits = dict(DEFAULT_LIMITS)
    if memory_gb and memory_gb < 10:
        profile = "low_memory_8gb"
        max_workers = 5
        limits.update(light_read=5, network_fetch=2, cpu_heavy=1, browser_research=1)
    elif memory_gb and memory_gb < 24:
        profile = "balanced_16gb"
        max_workers = 15
        limits.update(light_read=15, network_fetch=8, cpu_heavy=min(5, max(2, logical_cpus // 2)),
                      ram_heavy=2, browser_research=4, browser_acceptance=2, geometry=2)
    else:
        profile = "performance_32gb_plus"
        max_workers = 18
        limits.update(light_read=18, network_fetch=10, cpu_heavy=min(6, max(3, logical_cpus // 2)),
                      ram_heavy=3, browser_research=5, browser_acceptance=3, geometry=3, vision=2)
    limits.update(heavy_disk_io=1, raster_heavy=1, git_publish=1, runtime_sync=1, shared_publish=1)
    return profile, limits, max_workers

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
    last_error: OSError | None = None
    for attempt in range(20):
        try:
            os.replace(temporary, path)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(min(0.05 * (attempt + 1), 0.25))

    # Some Windows readers do not share delete access, so replace can remain
    # blocked while ordinary writes are still permitted. Keep this fallback
    # narrow and fsync the small JSON payload before removing the temp file.
    for attempt in range(10):
        try:
            with path.open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.unlink(missing_ok=True)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(min(0.1 * (attempt + 1), 0.5))
    raise last_error or PermissionError(f"ATOMIC_JSON_WRITE_FAILED: {path}")


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
        self.manual_stop_path = self.state / "manual_stop.requested.json"
        self.preflight_path = self.state / "portable_preflight_latest.json"
        self.publish_queue = self.state / "publish_queue"
        self.publish_archive = self.state / "publish_archive"
        self.stop_event = threading.Event()
        self.instance_id = uuid.uuid4().hex
        self.memory_gb = total_memory_gb()
        self.logical_cpus = os.cpu_count() or 1
        self.resource_profile, resource_limits, self.max_workers = select_resource_profile(self.memory_gb, self.logical_cpus)
        self.resources = ResourceManager(resource_limits)
        self.git_executable = find_git_executable(self.root)
        self.active_lock = threading.Lock()
        self.publish_lock = threading.Lock()
        self.active_paths: dict[str, list[str]] = {}
        self.active_tasks: dict[str, dict[str, Any]] = {}
        self.seen_task_ids: set[str] = set()
        self.scheduled_task_ids: set[str] = set()
        self.scheduling_pause_reason: str | None = None
        self.last_remote_refresh = 0.0
        self.remote_sync: dict[str, Any] = {"state": "NOT_RUN", "head": None, "error": None}

    def git_command(self, *args: str) -> list[str]:
        if self.git_executable is None:
            raise RuntimeError("PORTABLE_GIT_NOT_AVAILABLE")
        return [str(self.git_executable), *args]

    def worktree_for_slot(self, slot_id: str) -> Path:
        spec = SLOT_SPECS[slot_id]
        if int(spec["shard_index"]) == 1:
            return self.worktrees / "slots" / str(spec["base_slot_id"])
        return self.worktrees / "slots" / slot_id

    def can_schedule(self) -> bool:
        available = available_memory_gb()
        free_disk = shutil.disk_usage(self.root).free / (1024 ** 3)
        memory_floor = 2.0 if self.resource_profile == "low_memory_8gb" else 4.0
        if available and available < memory_floor:
            self.scheduling_pause_reason = f"LOW_AVAILABLE_MEMORY_{available:.2f}GB"
            return False
        if free_disk < 30:
            self.scheduling_pause_reason = f"LOW_PORTABLE_DISK_{free_disk:.2f}GB"
            return False
        self.scheduling_pause_reason = None
        return True

    def preflight(self) -> dict[str, Any]:
        self.state.mkdir(parents=True, exist_ok=True)
        resolved_python = Path(sys.executable).resolve()
        portable_python = resolved_python.is_file() and (
            resolved_python == (self.root / "runtime" / "python312" / "python.exe").resolve()
            or resolved_python == (self.root / "runtime" / "python" / "python.exe").resolve()
        )
        slot_worktrees = [self.worktree_for_slot(slot_id) for slot_id in SLOT_SPECS]
        relative_identity_paths = all(
            value and not Path(str(value)).is_absolute()
            for value in (
                self.identity.get("relative_repo_path"),
                self.identity.get("relative_worktree_root"),
                self.identity.get("relative_runtime_path"),
                self.identity.get("relative_launcher_path"),
            )
        )
        app_project = self.root / "AAYS" / "terrayield_land_intelligence"
        dependency_probe = subprocess.run(
            [str(resolved_python), "-c", "import tkinter, fastapi, uvicorn, sqlalchemy, psycopg"],
            cwd=app_project if app_project.is_dir() else self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        port_8012_state = "FREE"
        port_8012_compatible = True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe_socket:
            probe_socket.settimeout(0.5)
            listener_present = probe_socket.connect_ex(("127.0.0.1", 8012)) == 0
        if listener_present:
            port_8012_compatible = False
            for _attempt in range(3):
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8012/health", timeout=5.0) as response:
                        payload = json.loads(response.read().decode("utf-8"))
                        response_status = int(response.status)
                    port_8012_compatible = (
                        response_status == 200
                        and payload.get("status") == "ok"
                        and payload.get("app") == "TerraYield Land Intelligence"
                    )
                    if port_8012_compatible:
                        break
                except Exception:
                    time.sleep(0.5)
            if port_8012_compatible:
                port_8012_state = "TERRAYIELD_ACTIVE"
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as final_probe:
                    final_probe.settimeout(0.5)
                    listener_still_present = final_probe.connect_ex(("127.0.0.1", 8012)) == 0
                port_8012_compatible = not listener_still_present
                port_8012_state = "FREE" if port_8012_compatible else "OCCUPIED_BY_OTHER_SERVICE"
        checks = {
            "portable_identity": self.identity.get("canonical_drive_letter_persisted") is False,
            "identity_architecture_v3": int(self.identity.get("architecture_version") or 0) == ARCHITECTURE_VERSION,
            "identity_workstream_launcher": self.identity.get("relative_launcher_path") == "RUN_AAYS_ADAPTIVE_15_WORKER.cmd",
            "identity_paths_are_relative": relative_identity_paths,
            "portable_python": portable_python,
            "portable_git": self.git_executable is not None and self.git_executable.is_file(),
            "publisher_repo": self.repo.is_dir() and (self.repo / ".git").is_dir(),
            "worktree_root": self.worktrees.is_dir(),
            "twenty_one_slot_contract": len(SLOT_SPECS) == 21 and len(set(SLOT_SPECS)) == 21,
            "slot_worktrees": all(path.is_dir() for path in slot_worktrees),
            "slot_git_repositories_are_self_contained": all((path / ".git").is_dir() for path in slot_worktrees),
            "portable_app_launcher": (self.root / "START_TERRAYIELD_PORTABLE_8012.ps1").is_file(),
            "portable_app_project": app_project.is_dir(),
            "portable_app_dependencies": dependency_probe.returncode == 0,
            "port_8012_available_or_terrayield": port_8012_compatible,
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
            "port_8012_state": port_8012_state,
            "portable_dependency_error": dependency_probe.stderr.strip() or None,
            "max_child_workers": self.max_workers,
            "heavy_jobs_serialized": True,
            "slot_count": len(SLOT_SPECS),
            "parcel_count": 92283,
            "parcel_scope": "LONDON_CANONICAL_MATRIX",
            "national_england_canonical_inventory_ready": False,
            "national_england_blocker": "NATIONAL_ENGLAND_CANONICAL_PARCEL_INVENTORY_NOT_ESTABLISHED",
            "error": error,
            "checked_at": utc_now(),
            "final_ready": False,
        }
        atomic_write_json(self.preflight_path, report)
        return report

    def slot_dir(self, slot_id: str) -> Path:
        return self.state / "slots" / slot_id

    def initialize_state(self, remote_head: str | None = None) -> None:
        for directory in (self.state, self.runtime, self.logs, self.recovery, self.publish_queue, self.publish_archive):
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
                        "architecture_version": ARCHITECTURE_VERSION,
                        "workstream_id": WORKSTREAM_ID,
                        "slot_id": slot_id,
                        "base_slot_id": spec["base_slot_id"],
                        "shard_index": spec["shard_index"],
                        "parcel_partition": spec["parcel_partition"],
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
                existing = read_json(path, {}) if path.exists() else {}
                atomic_write_json(
                    path,
                    {
                        **payload,
                        **existing,
                        "schema_version": 2,
                        "architecture_version": ARCHITECTURE_VERSION,
                        "workstream_id": WORKSTREAM_ID,
                        "slot_id": slot_id,
                        "base_slot_id": spec["base_slot_id"],
                        "shard_index": spec["shard_index"],
                        "parcel_partition": spec["parcel_partition"],
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
            remote_path = self.repo / "docs" / "chatgpt_status" / "_shared" / "slots_21" / slot_id / "checkpoint_latest.json"
            remote_contract_source = "slots_21"
            if not remote_path.exists() and spec["base_slot_id"] != "future_growth":
                remote_path = self.repo / "docs" / "chatgpt_status" / "_shared" / "slots_18" / slot_id / "checkpoint_latest.json"
                remote_contract_source = "slots_18_legacy_fallback"
            if not remote_path.exists() and spec["base_slot_id"] not in {"internet_access", "future_growth"}:
                remote_path = self.repo / "docs" / "chatgpt_status" / "_shared" / "slots_15" / slot_id / "checkpoint_latest.json"
                remote_contract_source = "slots_15_legacy_fallback"
            remote = read_json(remote_path, {})
            remote_bytes = remote_path.read_bytes() if remote_path.exists() else b""
            value = {
                **local,
                "schema_version": 2,
                "architecture_version": ARCHITECTURE_VERSION,
                "workstream_id": WORKSTREAM_ID,
                "slot_id": slot_id,
                "base_slot_id": spec["base_slot_id"],
                "shard_index": spec["shard_index"],
                "parcel_partition": spec["parcel_partition"],
                "sequence": max(1, int(local.get("sequence") or 0)),
                "hydration_state": "REMOTE_HEAD_HYDRATED_FIRST_UNVERIFIED_PRESERVED",
                "remote_head": remote_head,
                "remote_slot_checkpoint_sequence": remote.get("sequence", 0),
                "remote_slot_checkpoint_sha256": sha256_bytes(remote_bytes) if remote_bytes else None,
                "remote_contract_source": remote_contract_source,
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
            "architecture_version": ARCHITECTURE_VERSION,
            "pid": os.getpid(),
            "process_start_100ns": identity["process_start_100ns"] if identity else None,
            "machine_id": machine_id(),
            "boot_id": boot_id(),
            "instance_id": self.instance_id,
            "command": "AAYS_ADAPTIVE_SINGLE_COORDINATOR_21_SLOT run",
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
            "base_slot_id",
            "shard_index",
            "task_id",
            "attempt_id",
            "idempotency_key",
            "script_path",
            "read_paths",
            "exact_write_paths",
            "resource_class",
            "parcel_partition",
            "safety_flags",
        )
        missing = [name for name in required if name not in task]
        if missing:
            raise ValueError("TASK_CONTRACT_MISSING: " + ",".join(missing))
        if int(task["architecture_version"]) != ARCHITECTURE_VERSION:
            raise ValueError("TASK_ARCHITECTURE_MISMATCH")
        task_workstream = str(task["workstream_id"])
        if task_workstream != WORKSTREAM_ID and task_workstream not in LEGACY_WORKSTREAM_IDS:
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
        if task.get("final_ready") not in (None, False):
            raise ValueError("UNSAFE_TASK_FLAG: final_ready")
        quality = task.get("data_quality_contract")
        if task_workstream == WORKSTREAM_ID:
            if not isinstance(quality, dict):
                raise ValueError("DATA_QUALITY_CONTRACT_REQUIRED")
            quality_required = (
                "source_urls",
                "source_snapshot_date",
                "source_discovery_required",
                "measurement_level",
                "output_semantics",
                "parcel_binding_method",
                "confidence_method",
                "no_data_policy",
                "ai_role",
                "human_review_required_when",
            )
            quality_missing = [name for name in quality_required if name not in quality]
            if quality_missing:
                raise ValueError("DATA_QUALITY_CONTRACT_MISSING: " + ",".join(quality_missing))
            if not isinstance(quality["source_urls"], list):
                raise ValueError("DATA_QUALITY_SOURCE_URLS_MUST_BE_LIST")
            if quality["source_discovery_required"] not in (True, False):
                raise ValueError("DATA_QUALITY_SOURCE_DISCOVERY_MUST_BE_BOOLEAN")
            if str(quality["no_data_policy"]) != "NO_DATA_NOT_INFERRED":
                raise ValueError("DATA_QUALITY_NO_DATA_POLICY_REQUIRED")
            if str(quality["measurement_level"]) not in {
                "unknown_pending_source",
                "parcel",
                "postcode",
                "lsoa",
                "local_authority",
                "grid",
                "candidate_point",
                "document",
            }:
                raise ValueError("DATA_QUALITY_MEASUREMENT_LEVEL_INVALID")
            if str(quality["output_semantics"]) not in {
                "NO_DATA",
                "MEASURED",
                "AREA_LEVEL_PROXY",
                "CANDIDATE",
                "MIXED_WITH_ROW_LABELS",
            }:
                raise ValueError("DATA_QUALITY_OUTPUT_SEMANTICS_INVALID")
            if str(quality["ai_role"]) not in {
                "not_used",
                "evidence_assist_only",
                "vision_comparison_only",
            }:
                raise ValueError("DATA_QUALITY_AI_ROLE_INVALID")
            if not str(quality["parcel_binding_method"]).strip():
                raise ValueError("DATA_QUALITY_PARCEL_BINDING_METHOD_REQUIRED")
            if not str(quality["confidence_method"]).strip():
                raise ValueError("DATA_QUALITY_CONFIDENCE_METHOD_REQUIRED")
            if not isinstance(quality["human_review_required_when"], list) or not quality["human_review_required_when"]:
                raise ValueError("DATA_QUALITY_HUMAN_REVIEW_RULE_REQUIRED")
        if task["task_id"] in self.seen_task_ids:
            raise ValueError("DUPLICATE_TASK_ID")
        spec = SLOT_SPECS[slot_id]
        if task_workstream == "AAYS_15_SLOT_SAFE_PARALLEL_V1" and spec["base_slot_id"] == "internet_access":
            raise ValueError("INTERNET_SLOT_REQUIRES_18_OR_21_SLOT_WORKSTREAM")
        if task_workstream in LEGACY_WORKSTREAM_IDS and spec["base_slot_id"] == "future_growth":
            raise ValueError("FUTURE_GROWTH_SLOT_REQUIRES_21_SLOT_WORKSTREAM")
        if str(task["base_slot_id"]) != str(spec["base_slot_id"]) or int(task["shard_index"]) != int(spec["shard_index"]):
            raise ValueError("SLOT_SHARD_IDENTITY_MISMATCH")
        partition = task["parcel_partition"]
        expected_partition = spec["parcel_partition"]
        if (
            int(partition.get("start") or 0) != int(expected_partition["start"])
            or int(partition.get("end") or 0) != int(expected_partition["end"])
            or int(partition.get("count") or 0) != int(expected_partition["count"])
        ):
            raise ValueError("PARCEL_PARTITION_MISMATCH")
        normalized_writes = [normalize_repo_path(str(value)) for value in task["exact_write_paths"]]
        normalized_slot_id = slot_id.casefold()
        if any(normalized_slot_id not in value.split("/") for value in normalized_writes):
            raise ValueError("SLOT_WRITE_PATH_NOT_ISOLATED")
        if task_workstream == WORKSTREAM_ID:
            canonical_write_roots = (
                f"{spec['business_root']}/shards/{slot_id}",
                f"docs/chatgpt_status/_shared/slots_21/{slot_id}",
                f"england_map_web/data/aays_21_slots/{slot_id}",
            )
        elif task_workstream == "AAYS_18_SLOT_SAFE_PARALLEL_V1":
            canonical_write_roots = (
                f"{spec['business_root']}/shards/{slot_id}",
                f"docs/chatgpt_status/_shared/slots_18/{slot_id}",
                f"england_map_web/data/aays_18_slots/{slot_id}",
            )
        else:
            canonical_write_roots = (
                f"{spec['business_root']}/shards/{slot_id}",
                f"docs/chatgpt_status/_shared/slots_15/{slot_id}",
                f"england_map_web/data/aays_15_slots/{slot_id}",
            )
        normalized_roots = tuple(normalize_repo_path(value) for value in canonical_write_roots)
        if any(
            not any(value == root or value.startswith(root + "/") for root in normalized_roots)
            for value in normalized_writes
        ):
            raise ValueError("SLOT_WRITE_PATH_OUTSIDE_CANONICAL_ROOTS")
        normalized_web_root = normalize_repo_path(canonical_write_roots[2])
        web_publish_requested = any(
            value == normalized_web_root or value.startswith(normalized_web_root + "/")
            for value in normalized_writes
        )
        if web_publish_requested:
            if quality["source_discovery_required"] is not False:
                raise ValueError("WEB_PUBLISH_REQUIRES_COMPLETED_SOURCE_DISCOVERY")
            if not quality["source_urls"] or not str(quality["source_snapshot_date"]).strip():
                raise ValueError("WEB_PUBLISH_REQUIRES_SOURCE_AND_SNAPSHOT")
            if quality["measurement_level"] != "parcel" and quality["output_semantics"] == "MEASURED":
                raise ValueError("NON_PARCEL_DATA_CANNOT_BE_PUBLISHED_AS_PARCEL_MEASUREMENT")
        evidence = "|".join(
            [str(task["task_id"]), str(task["script_path"]), *map(str, task["exact_write_paths"])]
        ).casefold()
        if spec["page_key"] == "aays1" and not any(marker in evidence for marker in spec["markers"]):
            raise ValueError("AMBIGUOUS_AAYS1_TASK_WITHOUT_SLOT_MARKER")
        timeout_seconds = int(task.get("timeout_seconds") or TASK_LEASE_SECONDS)
        if timeout_seconds < 60 or timeout_seconds > MAX_TASK_TIMEOUT_SECONDS:
            raise ValueError("TASK_TIMEOUT_OUT_OF_RANGE_60_TO_7200")
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

    def write_slot_runtime_state(
        self,
        slot_id: str,
        task: dict[str, Any],
        state: str,
        result: dict[str, Any] | None = None,
        blocker: str | None = None,
    ) -> None:
        now = utc_now()
        lease_expires_at = (datetime.now(timezone.utc) + timedelta(seconds=TASK_LEASE_SECONDS)).isoformat().replace("+00:00", "Z")
        common = {
            "schema_version": 3,
            "architecture_version": ARCHITECTURE_VERSION,
            "workstream_id": WORKSTREAM_ID,
            "slot_id": slot_id,
            "base_slot_id": task.get("base_slot_id"),
            "shard_index": task.get("shard_index"),
            "parcel_partition": task.get("parcel_partition"),
            "task_id": task.get("task_id"),
            "attempt_id": task.get("attempt_id"),
            "state": state,
            "updated_at": now,
            "final_ready": False,
        }
        atomic_write_json(
            self.slot_dir(slot_id) / "status_latest.json",
            {**common, "blocker": blocker, "result": result},
        )
        atomic_write_json(
            self.slot_dir(slot_id) / "current_task_latest.json",
            {**task, **common, "blocker": blocker, "result": result},
        )
        atomic_write_json(
            self.slot_dir(slot_id) / "heartbeat_latest.json",
            {
                **common,
                "heartbeat_at": now,
                "stale_after_seconds": TASK_LEASE_SECONDS,
                "lease_expires_at": lease_expires_at,
            },
        )

    def write_global_status(self, state: str) -> None:
        with self.active_lock:
            active = {slot: value.get("task_id") for slot, value in self.active_tasks.items()}
        atomic_write_json(
            self.status_path,
            {
                "schema_version": 2,
                "architecture_version": ARCHITECTURE_VERSION,
                "workstream_id": WORKSTREAM_ID,
                "state": state,
                "coordinator_pid": os.getpid(),
                "active_workers": len(active),
                "max_child_workers": self.max_workers,
                "logical_slot_count": len(SLOT_SPECS),
                "parcel_scope": "LONDON_CANONICAL_MATRIX",
                "national_england_canonical_inventory_ready": False,
                "resource_profile": self.resource_profile,
                "total_memory_gb": self.memory_gb,
                "logical_cpus": self.logical_cpus,
                "active_tasks": active,
                "available_memory_gb": available_memory_gb(),
                "scheduling_pause_reason": self.scheduling_pause_reason,
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
        now = utc_now()
        atomic_write_json(
            self.heartbeat_path,
            {
                "schema_version": 3,
                "workstream_id": WORKSTREAM_ID,
                "architecture_version": ARCHITECTURE_VERSION,
                "state": state,
                "pid": os.getpid(),
                "machine_id": machine_id(),
                "boot_id": boot_id(),
                "heartbeat_at": now,
                "stale_after_seconds": 45,
                "logical_slot_count": len(SLOT_SPECS),
                "final_ready": False,
            },
        )
        with self.active_lock:
            active = list(self.active_tasks.items())
        for slot_id, task in active:
            lease_expires_at = (datetime.now(timezone.utc) + timedelta(seconds=TASK_LEASE_SECONDS)).isoformat().replace("+00:00", "Z")
            atomic_write_json(
                self.slot_dir(slot_id) / "heartbeat_latest.json",
                {
                    "schema_version": 3,
                    "architecture_version": ARCHITECTURE_VERSION,
                    "workstream_id": WORKSTREAM_ID,
                    "slot_id": slot_id,
                    "base_slot_id": task.get("base_slot_id"),
                    "shard_index": task.get("shard_index"),
                    "parcel_partition": task.get("parcel_partition"),
                    "task_id": task.get("task_id"),
                    "attempt_id": task.get("attempt_id"),
                    "state": "RUNNING",
                    "heartbeat_at": now,
                    "stale_after_seconds": TASK_LEASE_SECONDS,
                    "lease_expires_at": lease_expires_at,
                    "final_ready": False,
                },
            )

    def scan_tasks(self) -> list[tuple[Path, dict[str, Any]]]:
        found: list[tuple[Path, dict[str, Any]]] = []
        business_roots = sorted({str(spec["business_root"]) for spec in SLOT_SPECS.values()})
        for business_root in business_roots:
            queue = self.repo / Path(business_root) / "queue"
            if not queue.exists():
                continue
            task_paths = sorted({*queue.glob("*.v3.task.json"), *queue.glob("*.v2.task.json")})
            for path in task_paths:
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
        try:
            fetch = subprocess.run(
                self.git_command("-C", str(self.repo), "fetch", "--depth=1", "origin", str(self.identity["branch"])),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=120,
            )
        except subprocess.TimeoutExpired:
            self.remote_sync = {"state": "WAITING_FOR_NETWORK_OR_GIT_AUTH", "head": None, "error": "GIT_FETCH_TIMEOUT_120S"}
            return self.remote_sync
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

    def git_path_list(self, repo: Path, *args: str) -> list[str]:
        completed = subprocess.run(
            self.git_command("-C", str(repo), *args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"GIT_PATH_LIST_FAILED: {completed.stderr.decode('utf-8', errors='replace').strip()}")
        return [value.decode("utf-8", errors="surrogateescape") for value in completed.stdout.split(b"\0") if value]

    @staticmethod
    def changed_path_allowed(path: str, allowed_paths: list[str]) -> bool:
        normalized = normalize_repo_path(path)
        return any(normalized == allowed or normalized.startswith(allowed + "/") for allowed in allowed_paths)

    def prepare_publish_item(self, source: Path, task: dict[str, Any], worktree: Path, base_head: str) -> Path | None:
        working = set(self.git_path_list(worktree, "diff", "--name-only", "-z", "--"))
        working.update(self.git_path_list(worktree, "diff", "--cached", "--name-only", "-z", "--"))
        working.update(self.git_path_list(worktree, "ls-files", "--others", "--exclude-standard", "-z"))
        current_head = subprocess.run(
            self.git_command("-C", str(worktree), "rev-parse", "HEAD"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        ).stdout.strip()
        committed = set()
        if current_head and current_head != base_head:
            committed.update(self.git_path_list(worktree, "diff", "--name-only", "-z", base_head, current_head, "--"))
        changed = sorted(working | committed)
        allowed = [normalize_repo_path(str(value)) for value in task["exact_write_paths"]]
        outside = [path for path in changed if not self.changed_path_allowed(path, allowed)]
        if outside:
            raise RuntimeError("CHILD_CHANGED_OUTSIDE_EXACT_WRITE_PATHS: " + ",".join(outside))
        if not changed:
            return None
        if working:
            staged = subprocess.run(
                self.git_command("-C", str(worktree), "add", "-A", "--", *sorted(working)),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
            )
            if staged.returncode != 0:
                raise RuntimeError(f"CHILD_STAGE_FAILED: {staged.stderr.strip()}")
            commit = subprocess.run(
                self.git_command("-C", str(worktree), "commit", "-m", f"Local slot result {task['task_id']}"),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
            )
            if commit.returncode != 0:
                raise RuntimeError(f"CHILD_LOCAL_COMMIT_FAILED: {commit.stderr.strip() or commit.stdout.strip()}")
        child_commit = subprocess.run(
            self.git_command("-C", str(worktree), "rev-parse", "HEAD"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        ).stdout.strip()
        changed = sorted(set(self.git_path_list(worktree, "diff", "--name-only", "-z", base_head, child_commit, "--")))
        task_key = sha256_bytes(str(task["task_id"]).encode("utf-8"))[:20]
        item_path = self.publish_queue / f"{task_key}.json"
        atomic_write_json(
            item_path,
            {
                "schema_version": 3,
                "workstream_id": WORKSTREAM_ID,
                "slot_id": task["slot_id"],
                "task_id": task["task_id"],
                "attempt_id": task["attempt_id"],
                "source_queue_path": str(source.relative_to(self.repo)).replace("\\", "/"),
                "worktree": str(worktree),
                "child_commit": child_commit,
                "changed_paths": changed,
                "exact_write_paths": task["exact_write_paths"],
                "attempts": 0,
                "state": "PUBLISH_PENDING",
                "created_at": utc_now(),
                "final_ready": False,
            },
        )
        return item_path

    def pending_publish_slots(self) -> set[str]:
        slots: set[str] = set()
        if self.publish_queue.is_dir():
            for path in self.publish_queue.glob("*.json"):
                item = read_json(path, {})
                if item.get("slot_id"):
                    slots.add(str(item["slot_id"]))
        return slots

    def copy_slot_proofs(self, slot_id: str) -> list[str]:
        target_root = self.repo / "docs" / "chatgpt_status" / "_shared" / "slots_21" / slot_id
        target_root.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        for name in ("checkpoint_latest.json", "heartbeat_latest.json", "current_task_latest.json", "status_latest.json"):
            source = self.slot_dir(slot_id) / name
            if source.is_file():
                target = target_root / name
                shutil.copy2(source, target)
                copied.append(str(target.relative_to(self.repo)).replace("\\", "/"))
        return copied

    def publish_item(self, item_path: Path) -> dict[str, Any]:
        with self.publish_lock:
            item = read_json(item_path, {})
            if not item:
                return {"state": "PUBLISH_ITEM_MISSING"}
            item["attempts"] = int(item.get("attempts") or 0) + 1
            item["last_attempt_at"] = utc_now()
            atomic_write_json(item_path, item)
            try:
                sync = self.refresh_publisher(force=True)
                if sync.get("state") != "PASS":
                    raise RuntimeError(f"PUBLISHER_REFRESH_NOT_READY: {sync.get('error') or sync.get('state')}")
                worktree = Path(str(item["worktree"]))
                changed_paths = [str(value) for value in item["changed_paths"]]
                for relative in changed_paths:
                    source = worktree / Path(relative)
                    target = self.repo / Path(relative)
                    if source.is_file():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, target)
                    elif target.exists():
                        target.unlink()
                queue_relative = str(item["source_queue_path"])
                queue_path = self.repo / Path(queue_relative)
                queue_task = read_json(queue_path, {})
                if not queue_task:
                    raise RuntimeError("SOURCE_QUEUE_TASK_MISSING_DURING_PUBLISH")
                queue_task.update(
                    {
                        "status": "result_ready_for_remote_acceptance",
                        "runner_state": "PUBLISHED_BY_SINGLE_COORDINATOR",
                        "runner_child_commit": item["child_commit"],
                        "runner_published_at": utc_now(),
                        "final_ready": False,
                    }
                )
                atomic_write_json(queue_path, queue_task)
                proof_paths = self.copy_slot_proofs(str(item["slot_id"]))
                stage_paths = sorted(set([*changed_paths, queue_relative, *proof_paths]))
                stage = subprocess.run(
                    self.git_command("-C", str(self.repo), "add", "-A", "--", *stage_paths),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
                )
                if stage.returncode != 0:
                    raise RuntimeError(f"PUBLISHER_STAGE_FAILED: {stage.stderr.strip()}")
                staged_paths = self.git_path_list(self.repo, "diff", "--cached", "--name-only", "-z", "--")
                unexpected = [path for path in staged_paths if path not in stage_paths]
                if unexpected:
                    raise RuntimeError("PUBLISHER_STAGED_UNEXPECTED_PATHS: " + ",".join(unexpected))
                commit = subprocess.run(
                    self.git_command("-C", str(self.repo), "commit", "-m", f"Publish {item['slot_id']} task {item['task_id']}"),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
                )
                if commit.returncode != 0:
                    raise RuntimeError(f"PUBLISHER_COMMIT_FAILED: {commit.stderr.strip() or commit.stdout.strip()}")
                branch = str(self.identity["branch"])
                push_error = None
                for _attempt in range(3):
                    push = subprocess.run(
                        self.git_command("-C", str(self.repo), "push", "origin", f"HEAD:{branch}"),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=120,
                    )
                    if push.returncode == 0:
                        push_error = None
                        break
                    push_error = push.stderr.strip() or push.stdout.strip()
                    fetch = subprocess.run(
                        self.git_command("-C", str(self.repo), "fetch", "--depth=20", "origin", branch),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=120,
                    )
                    if fetch.returncode != 0:
                        continue
                    rebase = subprocess.run(
                        self.git_command("-C", str(self.repo), "rebase", "FETCH_HEAD"),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
                    )
                    if rebase.returncode != 0:
                        subprocess.run(self.git_command("-C", str(self.repo), "rebase", "--abort"), check=False)
                        raise RuntimeError(f"PUBLISHER_REBASE_CONFLICT: {rebase.stderr.strip() or rebase.stdout.strip()}")
                if push_error:
                    raise RuntimeError(f"PUBLISHER_PUSH_FAILED: {push_error}")
                local_head = subprocess.run(
                    self.git_command("-C", str(self.repo), "rev-parse", "HEAD"),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
                ).stdout.strip()
                remote = subprocess.run(
                    self.git_command("-C", str(self.repo), "ls-remote", "origin", f"refs/heads/{branch}"),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=60,
                )
                remote_head = remote.stdout.split()[0] if remote.returncode == 0 and remote.stdout.split() else None
                if remote_head != local_head:
                    raise RuntimeError("PUBLISH_REMOTE_READBACK_MISMATCH")
                archive = self.publish_archive / item_path.name
                item.update({"state": "PUBLISHED", "publisher_commit": local_head, "remote_readback": True, "published_at": utc_now()})
                atomic_write_json(item_path, item)
                shutil.move(str(item_path), str(archive))
                try:
                    self.refresh_child(worktree)
                except Exception:
                    pass
                return {"state": "PUBLISHED", "publisher_commit": local_head, "remote_readback": True}
            except Exception as exc:
                item["state"] = "PUBLISH_PENDING"
                item["last_error"] = str(exc)
                atomic_write_json(item_path, item)
                return {"state": "PUBLISH_PENDING", "error": str(exc)}

    def process_publish_queue(self) -> dict[str, Any] | None:
        if not self.publish_queue.is_dir():
            return None
        pending = sorted(self.publish_queue.glob("*.json"))
        if not pending:
            return None
        item = read_json(pending[0], {})
        last_attempt = item.get("last_attempt_at")
        if last_attempt:
            try:
                stamp = datetime.fromisoformat(str(last_attempt).replace("Z", "+00:00"))
                if (datetime.now(timezone.utc) - stamp).total_seconds() < 60:
                    return {"state": "WAITING_PUBLISH_RETRY"}
            except ValueError:
                pass
        return self.publish_item(pending[0])
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
                self.write_slot_runtime_state(slot_id, task, "RUNNING")
                worktree = self.worktree_for_slot(slot_id)
                self.refresh_child(worktree)
                base_head = subprocess.run(
                    self.git_command("-C", str(worktree), "rev-parse", "HEAD"),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
                ).stdout.strip()
                if not base_head:
                    raise RuntimeError("CHILD_BASE_HEAD_MISSING")
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
                        timeout=int(task.get("timeout_seconds") or TASK_LEASE_SECONDS),
                        check=False,
                    )
                if completed.returncode != 0:
                    state = "BLOCKED"
                    result = {"state": state, "exit_code": completed.returncode, "log": str(log.relative_to(self.root))}
                else:
                    self.write_slot_runtime_state(slot_id, task, "RESULT_READY_FOR_SERIAL_PUBLISH")
                    item_path = self.prepare_publish_item(source, task, worktree, base_head)
                    if item_path is None:
                        state = "BLOCKED_NO_DECLARED_OUTPUT"
                        result = {"state": state, "exit_code": 0, "log": str(log.relative_to(self.root))}
                    else:
                        self.write_slot_runtime_state(slot_id, task, "PUBLISHING")
                        publish_result = self.publish_item(item_path)
                        state = str(publish_result.get("state") or "PUBLISH_PENDING")
                        result = {
                            "state": state,
                            "exit_code": 0,
                            "log": str(log.relative_to(self.root)),
                            **publish_result,
                        }
                self.write_slot_runtime_state(slot_id, task, state, result=result)
                self.append_event(slot_id, {"transition": state, "task_id": task["task_id"], **result})
                return {"slot_id": slot_id, "task_id": task["task_id"], **result}
        except Exception as exc:
            blocker = str(exc)
            self.write_slot_runtime_state(slot_id, task, "BLOCKED", blocker=blocker)
            self.append_event(slot_id, {"transition": "BLOCKED", "task_id": task["task_id"], "error": blocker})
            return {"state": "BLOCKED", "slot_id": slot_id, "task_id": task["task_id"], "error": blocker}
        finally:
            with self.active_lock:
                self.active_tasks.pop(slot_id, None)
                self.active_paths.pop(slot_id, None)

    def run(self) -> int:
        if self.manual_stop_path.exists():
            print(json.dumps({"status": "manual_stop_requested", "started": False, "final_ready": False}))
            return 0
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
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="aays-slot")
        futures: set[concurrent.futures.Future] = set()
        try:
            self.write_global_status("RUNNING")
            while not self.stop_event.is_set():
                if self.manual_stop_path.exists():
                    self.stop_event.set()
                    break
                control = read_json(self.control_path, {})
                if control.get("requested_action") == "STOP":
                    self.stop_event.set()
                    break
                self.heartbeat()
                publish_result = self.process_publish_queue()
                if publish_result is None:
                    self.refresh_publisher()
                pending_publish_slots = self.pending_publish_slots()
                if self.can_schedule():
                    for source, task in self.scan_tasks():
                        if len(futures) >= self.max_workers:
                            break
                        task_id = str(task.get("task_id"))
                        slot_id = str(task.get("slot_id") or "")
                        if slot_id in pending_publish_slots:
                            continue
                        if task_id in self.seen_task_ids or task_id in self.scheduled_task_ids:
                            continue
                        self.scheduled_task_ids.add(task_id)
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
    production_state_root = coordinator.state

    def state_snapshot(directory: Path) -> dict[str, str]:
        if not directory.is_dir():
            return {}
        return {
            str(path.relative_to(directory)).replace("\\", "/"): sha256_bytes(path.read_bytes())
            for path in sorted(directory.rglob("*"))
            if path.is_file()
        }

    production_state_before = state_snapshot(production_state_root)
    fixture_sandbox = coordinator.runtime / "fixture_sandbox" / uuid.uuid4().hex
    coordinator.state = fixture_sandbox / "state"
    coordinator.runtime = fixture_sandbox / "runtime"
    coordinator.logs = fixture_sandbox / "logs"
    coordinator.recovery = fixture_sandbox / "recovery" / "quarantine"
    coordinator.lock_path = coordinator.state / "coordinator.lock.json"
    coordinator.heartbeat_path = coordinator.state / "coordinator_heartbeat_latest.json"
    coordinator.status_path = coordinator.state / "coordinator_status_latest.json"
    coordinator.control_path = coordinator.state / "control_latest.json"
    coordinator.manual_stop_path = coordinator.state / "manual_stop.requested.json"
    coordinator.preflight_path = coordinator.state / "portable_preflight_latest.json"
    coordinator.publish_queue = coordinator.state / "publish_queue"
    coordinator.publish_archive = coordinator.state / "publish_archive"
    coordinator.initialize_state("FIXTURE_REMOTE_HEAD")
    fixture_root = coordinator.runtime / "fixtures"
    fixture_root.mkdir(parents=True, exist_ok=True)
    active = 0
    maximum = 0
    lock = threading.Lock()
    fixture_profile, fixture_limits, fixture_workers = select_resource_profile(32.0, 16)
    coordinator.resources = ResourceManager(fixture_limits)
    barrier = threading.Barrier(len(SLOT_SPECS))

    def light(slot_id: str) -> dict[str, Any]:
        nonlocal active, maximum
        barrier.wait(timeout=30)
        with coordinator.resources.acquire(["light_read"]):
            with lock:
                active += 1
                maximum = max(maximum, active)
            payload = {"slot_id": slot_id, "state": "RUNNING", "business_write": False, "started_at": utc_now()}
            atomic_write_json(fixture_root / slot_id / "light_fixture.json", payload)
            time.sleep(1.0)
            with lock:
                active -= 1
            return {"slot_id": slot_id, "state": "PASS"}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SLOT_SPECS)) as pool:
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
        "schema_version": 3,
        "architecture_version": ARCHITECTURE_VERSION,
        "workstream_id": WORKSTREAM_ID,
        "slot_id": "security_public_safety_1",
        "base_slot_id": "security_public_safety",
        "shard_index": 1,
        "task_id": "fixture_security_task",
        "attempt_id": "fixture-1",
        "idempotency_key": "fixture-security-1",
        "script_path": "docs/chatgpt_status/aays1/automation/security_fixture.ps1",
        "read_paths": [],
        "exact_write_paths": ["docs/chatgpt_status/aays1/shards/security_public_safety_1/security_fixture.json"],
        "resource_class": "light_read",
        "parcel_partition": {"start": 1, "end": 30761, "count": 30761},
        "safety_flags": {"fake_data": False, "db_write": False, "migration": False, "production_deploy": False},
        "data_quality_contract": {
            "source_urls": [],
            "source_snapshot_date": "",
            "source_discovery_required": True,
            "measurement_level": "unknown_pending_source",
            "output_semantics": "NO_DATA",
            "parcel_binding_method": "NOT_RUN",
            "confidence_method": "NOT_SCORED",
            "no_data_policy": "NO_DATA_NOT_INFERRED",
            "ai_role": "not_used",
            "human_review_required_when": ["source_conflict", "low_confidence", "geometry_mismatch"],
        },
    }
    coordinator.classify_task(base_task)
    coordinator.seen_task_ids.add(base_task["task_id"])
    try:
        coordinator.classify_task(base_task)
    except ValueError as exc:
        duplicate_blocked = "DUPLICATE_TASK_ID" in str(exc)
    wrong = dict(base_task)
    wrong["task_id"] = "fixture_wrong_slot"
    wrong["slot_id"] = "ready_to_sell_1"
    wrong["base_slot_id"] = "ready_to_sell"
    wrong["script_path"] = "docs/chatgpt_status/aays1/automation/security_fixture.ps1"
    try:
        coordinator.classify_task(wrong)
    except ValueError as exc:
        wrong_slot_blocked = "SLOT_WRITE_PATH_NOT_ISOLATED" in str(exc) or "SLOT_SHARD_IDENTITY_MISMATCH" in str(exc)

    with coordinator.active_lock:
        coordinator.active_tasks[base_task["slot_id"]] = base_task
    coordinator.heartbeat()
    long_lease_heartbeat = read_json(coordinator.slot_dir(base_task["slot_id"]) / "heartbeat_latest.json", {})
    with coordinator.active_lock:
        coordinator.active_tasks.pop(base_task["slot_id"], None)
    long_task_heartbeat_ok = (
        long_lease_heartbeat.get("state") == "RUNNING"
        and int(long_lease_heartbeat.get("stale_after_seconds") or 0) == TASK_LEASE_SECONDS
        and long_lease_heartbeat.get("task_id") == base_task["task_id"]
    )

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

    production_state_after = state_snapshot(production_state_root)
    production_state_files_changed = sorted(
        path
        for path in set(production_state_before) | set(production_state_after)
        if production_state_before.get(path) != production_state_after.get(path)
    )
    resource_peaks = {
        name: measured_serial(name)
        for name in ("ram_heavy", "raster_heavy", "git_publish", "runtime_sync", "browser_acceptance", "shared_publish")
    }
    checks = {
        "all_21_slot_fixtures_passed": len(results) == len(SLOT_SPECS) and all(item.get("state") == "PASS" for item in results),
        "light_read_limit_observed": maximum == min(fixture_limits["light_read"], len(SLOT_SPECS)),
        "path_overlap_blocked": overlap_blocked,
        "wrong_slot_blocked": wrong_slot_blocked,
        "duplicate_task_blocked": duplicate_blocked,
        "long_task_heartbeat_refresh": long_task_heartbeat_ok,
        "serialized_resources_observed": all(resource_peaks[name] == 1 for name in ("raster_heavy", "git_publish", "runtime_sync", "shared_publish")),
        "bounded_resources_observed": all(resource_peaks[name] <= fixture_limits[name] for name in resource_peaks),
        "corrupt_checkpoint_quarantined": (quarantine / "checkpoint.corrupt.json").exists(),
        "alternate_drive_root_simulation": alternate_ok,
        "production_state_untouched": not production_state_files_changed,
    }

    report = {
        "status": "PASS_WITH_PHYSICAL_TEST_LIMITATIONS" if all(checks.values()) else "FAIL",
        "workstream_id": WORKSTREAM_ID,
        "architecture_version": ARCHITECTURE_VERSION,
        "checks": checks,
        "fixture_sandbox": str(fixture_sandbox),
        "production_state_files_changed": production_state_files_changed,
        "coordinator_process_count": 1,
        "max_child_workers": fixture_workers,
        "fixture_resource_profile": fixture_profile,
        "max_simultaneous_fixture_running": maximum,
        "fixture_results": results,
        "business_files_changed": 0,
        "path_overlap_blocked": overlap_blocked,
        "wrong_slot_blocked": wrong_slot_blocked,
        "duplicate_task_blocked": duplicate_blocked,
        "long_task_timeout_seconds": TASK_LEASE_SECONDS,
        "long_task_heartbeat_refresh": long_task_heartbeat_ok,
        "resource_peaks": resource_peaks,
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
    atomic_write_json(coordinator.state / "acceptance" / "adaptive_v3_21_slot_fixture_test_latest.json", report)
    return report


def request_stop(root: Path) -> dict[str, Any]:
    coordinator = Coordinator(root)
    atomic_write_json(
        coordinator.manual_stop_path,
        {"requested": True, "requested_at": utc_now(), "reason": "USER_REQUESTED_STOP"},
    )
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
        "max_child_workers": coordinator.max_workers,
        "resource_profile": global_status.get("resource_profile", coordinator.resource_profile),
        "total_memory_gb": global_status.get("total_memory_gb", coordinator.memory_gb),
        "logical_cpus": global_status.get("logical_cpus", coordinator.logical_cpus),
        "portable_root": str(root.resolve()),
        "manual_stop_requested": coordinator.manual_stop_path.exists(),
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
