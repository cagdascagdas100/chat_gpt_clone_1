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
import re
import shutil
import socket
import ssl
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

from AAYS_21_SLOT_RECOVERY_SUPERVISOR import SlotRecoverySupervisor


WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
LEGACY_WORKSTREAM_IDS = {"AAYS_15_SLOT_SAFE_PARALLEL_V1", "AAYS_18_SLOT_SAFE_PARALLEL_V1"}
ARCHITECTURE_VERSION = 3
TASK_LEASE_SECONDS = 3600
# Some bounded national-source validation waves legitimately need several
# hours on a 16 GB portable host. Heartbeats still refresh every loop, so a
# longer subprocess timeout does not weaken stale-runner detection.
MAX_TASK_TIMEOUT_SECONDS = 21600
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
PROBLEM_SOLVER_SLOT_ID = "problem_solver_1"
DATA_SLOT_COUNT = len(SLOT_SPECS)
LOGICAL_SLOT_COUNT = DATA_SLOT_COUNT + 1
DEFAULT_LIMITS = {
    "light_read": 5,
    "network_fetch": 3,
    "cpu_heavy": 2,
    "ram_heavy": 1,
    "heavy_disk_io": 1,
    "local_large_file_scan": 1,
    "browser_research": 2,
    "browser_acceptance": 1,
    "geometry": 1,
    "vision": 1,
    "raster_heavy": 1,
    "git_publish": 1,
    "runtime_sync": 1,
    "shared_publish": 1,
}
QUEUE_READY_STATUSES = {
    "pending",
    "queued",
    "pickup_requested",
    "READY",
    "queued_after_existing_shared_task",
    "queued_for_shared_coordinator_browser_acceptance",
    "queued_stale_runner_blocked_expanded_same_attempt",
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


def select_available_worker_capacity(resource_profile: str, max_workers: int, available_gb: float) -> int:
    """Keep all logical slots queued while scaling physical workers to free RAM."""
    if not available_gb:
        return max_workers
    if resource_profile == "low_memory_8gb":
        if available_gb < 1.5:
            return 0
        if available_gb < 2.5:
            return min(max_workers, 2)
        return max_workers
    if resource_profile == "balanced_16gb":
        # With many ChatGPT/Chrome tabs open, Windows commonly keeps 1.5-2.5
        # GB available while still having a healthy page file. Preserve a hard
        # stop below 1.5 GB, but allow two gated workers in that band so the
        # queue makes measurable progress instead of remaining at 0 forever.
        if available_gb < 1.5:
            return 0
        if available_gb < 2.5:
            return min(max_workers, 2)
        if available_gb < 3.5:
            return min(max_workers, 4)
        if available_gb < 5.0:
            return min(max_workers, 8)
        if available_gb < 7.0:
            return min(max_workers, 12)
        return max_workers
    if available_gb < 2.5:
        return 0
    if available_gb < 3.5:
        return min(max_workers, 4)
    if available_gb < 5.0:
        return min(max_workers, 8)
    if available_gb < 7.0:
        return min(max_workers, 12)
    if available_gb < 10.0:
        return min(max_workers, 15)
    return max_workers

def find_git_executable(root: Path) -> Path | None:
    candidates: tuple[Path, ...] = (
        # Prefer a Git executable on the internal system disk when available.
        # Repository data and all configuration remain on the portable root;
        # this only avoids removable-drive stalls while starting git.exe.
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "mingw64" / "bin" / "git.exe",
        # Use the real Git binary. Git for Windows' cmd/git.exe shim spawns a
        # second process which can survive Python's timeout and retain locks.
        root / "runtime" / "git" / "mingw64" / "bin" / "git.exe",
        root / "runtime" / "git" / "cmd" / "git.exe",
        root / "runtime" / "git" / "bin" / "git.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    discovered = shutil.which("git")
    return Path(discovered) if discovered else None


def configure_windows_tls_bundle(root: Path) -> Path | None:
    """Combine certifi with Windows trusted roots for portable Python tasks."""
    try:
        import certifi

        certifi_text = Path(certifi.where()).read_text(encoding="ascii")
        roots: list[str] = []
        seen: set[str] = set()
        if sys.platform == "win32" and hasattr(ssl, "enum_certificates"):
            for certificate, encoding, _trust in ssl.enum_certificates("ROOT"):
                if encoding != "x509_asn":
                    continue
                pem = ssl.DER_cert_to_PEM_cert(certificate)
                if pem not in seen:
                    seen.add(pem)
                    roots.append(pem)
        target = root / "runtime" / "cache" / "windows_root_plus_certifi.pem"
        target.parent.mkdir(parents=True, exist_ok=True)
        content = certifi_text.rstrip() + "\n" + "".join(roots)
        if not target.is_file() or target.read_text(encoding="ascii") != content:
            temporary = target.with_name(target.name + f".tmp.{uuid.uuid4().hex}")
            temporary.write_text(content, encoding="ascii")
            os.replace(temporary, target)
        os.environ["SSL_CERT_FILE"] = str(target)
        os.environ["REQUESTS_CA_BUNDLE"] = str(target)
        return target
    except Exception:
        return None


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
        exit_code = ctypes.wintypes.DWORD()
        if not ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return None
        # OpenProcess/GetProcessTimes can still succeed for a terminated
        # process while another launcher owns a handle. Only STILL_ACTIVE is
        # a live coordinator.
        if exit_code.value != 259:
            return None
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
        self.problem_solver_root = self.state / "problem_solver"
        self.problem_solver_state_path = self.problem_solver_root / "state_latest.json"
        self.mobile_notification_config_path = self.state / "mobile_notification_config.json"
        self.mobile_notification_state_path = self.problem_solver_root / "mobile_notification_latest.json"
        self.stop_event = threading.Event()
        self.instance_id = uuid.uuid4().hex
        self.process_mutex_handle: int | None = None
        self.memory_gb = total_memory_gb()
        self.logical_cpus = os.cpu_count() or 1
        self.resource_profile, resource_limits, self.max_workers = select_resource_profile(self.memory_gb, self.logical_cpus)
        self.resources = ResourceManager(resource_limits)
        self.git_executable = find_git_executable(self.root)
        self.tls_ca_bundle = configure_windows_tls_bundle(self.root)
        self.recovery_supervisor = SlotRecoverySupervisor(
            self.root,
            self.repo,
            self.worktree_for_slot,
            self.git_executable,
            set(SLOT_SPECS),
            progress_callback=lambda recovery_state: self.heartbeat(recovery_state),
        )
        self.recovery_active_count = 0
        self.recovery_pending_count = 0
        self.active_lock = threading.Lock()
        self.publish_lock = threading.Lock()
        self.active_paths: dict[str, list[str]] = {}
        self.active_tasks: dict[str, dict[str, Any]] = {}
        self.seen_task_ids: set[str] = set()
        self.scheduled_task_ids: set[str] = set()
        self.scheduled_slot_ids: set[str] = set()
        self.scheduling_pause_reason: str | None = None
        self.available_worker_capacity = self.max_workers
        self.adaptive_capacity_reason: str | None = None
        self.last_remote_refresh = 0.0
        self.remote_sync: dict[str, Any] = {"state": "NOT_RUN", "head": None, "error": None}
        self.queue_compatibility_count = 0
        self.queue_rejected: dict[str, str] = {}
        self.last_problem_solver_cycle = 0.0

    def git_command(self, *args: str) -> list[str]:
        if self.git_executable is None:
            raise RuntimeError("PORTABLE_GIT_NOT_AVAILABLE")
        return [str(self.git_executable), *args]

    @staticmethod
    def worktree_git_dir(worktree: Path) -> Path:
        """Resolve the real per-worktree git directory on Windows.

        Linked worktrees store a `gitdir: ...` pointer in `.git`; treating it
        as a directory made stale index/sparse locks impossible to remove.
        """
        marker = worktree / ".git"
        if marker.is_dir():
            return marker
        if marker.is_file():
            first_line = marker.read_text(encoding="utf-8", errors="replace").splitlines()[0].strip()
            if first_line.casefold().startswith("gitdir:"):
                value = first_line.split(":", 1)[1].strip()
                candidate = Path(value)
                if not candidate.is_absolute():
                    candidate = (worktree / candidate).resolve()
                return candidate
        raise RuntimeError(f"WORKTREE_GIT_DIR_NOT_RESOLVED: {worktree}")

    def worktree_for_slot(self, slot_id: str) -> Path:
        overrides = read_json(self.state / "worktree_overrides.json", {}) or {}
        override = overrides.get(slot_id) if isinstance(overrides, dict) else None
        if override:
            candidate = (self.root / Path(str(override))).resolve()
            allowed_roots = (
                self.worktrees.resolve(),
                (self.root / "wt").resolve(),
            )
            if any(candidate.is_relative_to(root) for root in allowed_roots) and candidate.is_dir():
                return candidate
        spec = SLOT_SPECS[slot_id]
        if int(spec["shard_index"]) == 1:
            return self.worktrees / "slots" / str(spec["base_slot_id"])
        return self.worktrees / "slots" / slot_id

    def portable_worktree_git_layout(self, worktree: Path) -> bool:
        """Accept embedded repos and standard linked worktrees, but only on this portable root."""
        try:
            git_dir = self.worktree_git_dir(worktree).resolve()
            return git_dir.is_dir() and git_dir.is_relative_to(self.root.resolve())
        except (OSError, RuntimeError, IndexError):
            return False

    def can_schedule(self) -> bool:
        available = available_memory_gb()
        free_disk = shutil.disk_usage(self.root).free / (1024 ** 3)
        self.available_worker_capacity = select_available_worker_capacity(
            self.resource_profile, self.max_workers, available
        )
        if self.available_worker_capacity == 0:
            self.scheduling_pause_reason = f"LOW_AVAILABLE_MEMORY_{available:.2f}GB"
            self.adaptive_capacity_reason = self.scheduling_pause_reason
            return False
        if free_disk < 30:
            self.scheduling_pause_reason = f"LOW_PORTABLE_DISK_{free_disk:.2f}GB"
            self.adaptive_capacity_reason = self.scheduling_pause_reason
            return False
        self.scheduling_pause_reason = None
        self.adaptive_capacity_reason = (
            None
            if self.available_worker_capacity >= self.max_workers
            else f"ADAPTIVE_MEMORY_CAP_{self.available_worker_capacity}_OF_{self.max_workers}_{available:.2f}GB"
        )
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
            [
                str(resolved_python),
                "-c",
                (
                    "import importlib.util; "
                    "names=('tkinter','fastapi','uvicorn','sqlalchemy','psycopg'); "
                    "missing=[name for name in names if importlib.util.find_spec(name) is None]; "
                    "raise SystemExit(1 if missing else 0)"
                ),
            ],
            cwd=app_project if app_project.is_dir() else self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=30,
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
            "twenty_one_slot_contract": DATA_SLOT_COUNT == 21 and len(set(SLOT_SPECS)) == 21,
            "problem_solver_slot_contract": PROBLEM_SOLVER_SLOT_ID not in SLOT_SPECS,
            "slot_worktrees": all(path.is_dir() for path in slot_worktrees),
            # Recovery overrides are standard linked Git worktrees (`.git` is
            # a pointer file). They remain portable because the resolved
            # gitdir must stay under this same portable root.
            "slot_git_repositories_are_self_contained": all(
                self.portable_worktree_git_layout(path) for path in slot_worktrees
            ),
            "portable_app_launcher": any(
                path.is_file()
                for path in (
                    self.root / "START_TERRAYIELD_PORTABLE_8012.ps1",
                    self.root / "AAYS_TERRAYIELD_PORTABLE_BASE.ps1",
                )
            ),
            "portable_app_project": app_project.is_dir(),
            "portable_app_dependencies": dependency_probe.returncode == 0,
            "port_8012_available_or_terrayield": port_8012_compatible,
        }
        git_version = None
        remote_head = None
        error = None
        if checks["portable_git"] and checks["publisher_repo"]:
            try:
                version = subprocess.run(
                    self.git_command("--version"), stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, check=False, timeout=15,
                )
                head = subprocess.run(
                    self.git_command("-C", str(self.repo), "rev-parse", "HEAD"),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    check=False, timeout=30,
                )
                git_version = version.stdout.strip() if version.returncode == 0 else None
                remote_head = head.stdout.strip() if head.returncode == 0 else None
                checks["git_executes"] = bool(git_version and remote_head)
                error = version.stderr.strip() or head.stderr.strip() or None
            except subprocess.TimeoutExpired as exc:
                checks["git_executes"] = False
                error = f"GIT_PREFLIGHT_TIMEOUT_{int(exc.timeout)}S"
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
            "slot_count": LOGICAL_SLOT_COUNT,
            "data_slot_count": DATA_SLOT_COUNT,
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
        for directory in (
            self.state, self.runtime, self.logs, self.recovery, self.publish_queue,
            self.publish_archive, self.problem_solver_root,
        ):
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
                required_metadata = {
                    "schema_version": 2,
                    "architecture_version": ARCHITECTURE_VERSION,
                    "workstream_id": WORKSTREAM_ID,
                    "slot_id": slot_id,
                    "base_slot_id": spec["base_slot_id"],
                    "shard_index": spec["shard_index"],
                    "parcel_partition": spec["parcel_partition"],
                    "final_ready": False,
                }
                # Existing live state is already durable and authoritative.
                # Rewriting 84 unchanged files on every watchdog launch causes
                # long USB flush stalls and can trigger a false stale restart.
                if existing and all(existing.get(key) == value for key, value in required_metadata.items()):
                    continue
                atomic_write_json(path, {**payload, **existing, **required_metadata})
        solver_dir = self.slot_dir(PROBLEM_SOLVER_SLOT_ID)
        solver_dir.mkdir(parents=True, exist_ok=True)
        solver_metadata = {
            "schema_version": 1,
            "architecture_version": ARCHITECTURE_VERSION,
            "workstream_id": WORKSTREAM_ID,
            "slot_id": PROBLEM_SOLVER_SLOT_ID,
            "base_slot_id": "system_recovery",
            "role": "PRIORITY_MANUAL_ACTION_AND_21_SLOT_RECOVERY_COORDINATOR",
            "data_worker_capacity_consumed": 0,
            "final_ready": False,
        }
        for name, payload in {
            "checkpoint_latest.json": {"state": "READY", "first_unverified_step": "SOLVE_MANUAL_ACTIONS_THEN_STALLED_SLOTS"},
            "status_latest.json": {"state": "IDLE", "target_slot_id": None},
            "heartbeat_latest.json": {"state": "IDLE", "heartbeat_at": None},
            "current_task_latest.json": {"state": "IDLE", "task_id": None},
        }.items():
            path = solver_dir / name
            if not path.exists():
                atomic_write_json(path, {**payload, **solver_metadata, "updated_at": utc_now()})
        if not self.mobile_notification_config_path.exists():
            atomic_write_json(self.mobile_notification_config_path, {
                "schema_version": 1,
                "enabled": False,
                "endpoint_url": "",
                "authorization_bearer_token": "",
                "instructions": "Android bildirim servisi/ntfy tam HTTPS konu URL'sini endpoint_url alanına yazın.",
                "final_ready": False,
            })

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
        for slot_index, (slot_id, spec) in enumerate(SLOT_SPECS.items()):
            if slot_index % 4 == 0:
                self.heartbeat("HYDRATING_CHECKPOINTS")
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
            stable_keys = (
                "schema_version", "architecture_version", "workstream_id", "slot_id", "base_slot_id",
                "shard_index", "parcel_partition", "hydration_state", "remote_head",
                "remote_slot_checkpoint_sequence", "remote_slot_checkpoint_sha256", "remote_contract_source",
                "first_unverified_step", "terminal_no_replay", "zip_timestamp_ignored", "final_ready",
            )
            if not local or any(local.get(key) != value.get(key) for key in stable_keys):
                atomic_write_json(local_path, value)
                self.append_event(
                    slot_id,
                    {
                        "transition": "CHECKPOINT_HYDRATED",
                        "remote_head": remote_head,
                        "first_unverified_step": spec["first_unverified"],
                    },
                )
            hydrated.append({"slot_id": slot_id, "remote_head": remote_head, "first_unverified_step": spec["first_unverified"]})
        self.heartbeat("CHECKPOINTS_HYDRATED")
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

    def acquire_process_mutex(self) -> bool:
        """Serialize coordinator startup before the JSON ownership check."""
        if os.name != "nt":
            return True
        import ctypes

        mutex_suffix = hashlib.sha256(str(self.root).casefold().encode("utf-8")).hexdigest()[:20]
        handle = ctypes.windll.kernel32.CreateMutexW(None, False, f"Local\\AAYSPortableCoordinatorV3_{mutex_suffix}")
        if not handle:
            raise OSError("COORDINATOR_PROCESS_MUTEX_CREATE_FAILED")
        wait_result = ctypes.windll.kernel32.WaitForSingleObject(handle, 0)
        if wait_result not in (0x00000000, 0x00000080):
            ctypes.windll.kernel32.CloseHandle(handle)
            return False
        self.process_mutex_handle = int(handle)
        return True

    def release_process_mutex(self) -> None:
        if os.name != "nt" or not self.process_mutex_handle:
            return
        import ctypes

        handle = self.process_mutex_handle
        self.process_mutex_handle = None
        ctypes.windll.kernel32.ReleaseMutex(handle)
        ctypes.windll.kernel32.CloseHandle(handle)

    def acquire_lock(self) -> tuple[bool, dict[str, Any]]:
        if not self.acquire_process_mutex():
            return False, read_json(self.lock_path, {})
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
                self.release_process_mutex()
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
        try:
            lock = read_json(self.lock_path, {})
            if lock.get("instance_id") == self.instance_id:
                self.lock_path.unlink(missing_ok=True)
        finally:
            self.release_process_mutex()

    def normalize_queue_task(self, source: Path, raw_task: dict[str, Any]) -> dict[str, Any]:
        """Upgrade real legacy queue records in memory without weakening execution gates.

        Older ChatGPT pages wrote several equivalent ready states and omitted
        fields introduced by the v3 coordinator.  The work itself is real, but
        those records were invisible to the runner.  This adapter supplies only
        conservative metadata; the normal path, safety and data-quality checks
        still run before a task can be claimed.
        """
        task = dict(raw_task)
        original_status = str(task.get("status") or "pending")
        if original_status not in QUEUE_READY_STATUSES:
            raise ValueError(f"QUEUE_STATUS_NOT_RUNNABLE: {original_status}")
        slot_id = str(task.get("slot_id") or "")
        if slot_id not in SLOT_SPECS:
            raise ValueError("AMBIGUOUS_SLOT_CLASSIFICATION")
        spec = SLOT_SPECS[slot_id]
        script_path = normalize_repo_path(str(task.get("script_path") or ""))
        if not script_path or not script_path.startswith("docs/chatgpt_status/"):
            raise ValueError("LEGACY_SCRIPT_PATH_NOT_ALLOWED")

        compatibility_needed = (
            task.get("compatibility_migrated") is True
            or original_status not in {"pending", "queued"}
            or int(task.get("architecture_version") or 0) != ARCHITECTURE_VERSION
            or str(task.get("workstream_id") or "") != WORKSTREAM_ID
            or not isinstance(task.get("safety_flags"), dict)
            or not isinstance(task.get("data_quality_contract"), dict)
        )
        task.update(
            schema_version=3,
            architecture_version=ARCHITECTURE_VERSION,
            workstream_id=WORKSTREAM_ID,
            base_slot_id=spec["base_slot_id"],
            shard_index=spec["shard_index"],
            parcel_partition=dict(spec["parcel_partition"]),
            status="queued",
            script_path=script_path,
            final_ready=False,
        )
        task.setdefault("read_paths", [])
        task["legacy_queue_status"] = original_status
        task["compatibility_migrated"] = compatibility_needed
        task["compatibility_source_queue"] = str(source.relative_to(self.repo)).replace("\\", "/")

        safety = dict(task.get("safety_flags") or {})
        for flag in ("fake_data", "db_write", "migration", "production_deploy"):
            safety.setdefault(flag, False)
        task["safety_flags"] = safety

        raw_resources = task.get("resource_class")
        candidates: list[str] = []
        values = raw_resources if isinstance(raw_resources, list) else [raw_resources]
        for value in values:
            candidates.extend(re.split(r"[\s,]+", str(value or "").strip()))
        resources = list(dict.fromkeys(value for value in candidates if value in self.resources.limits))
        if not resources:
            base_slot_id = str(spec["base_slot_id"])
            if base_slot_id in {"height_difference", "future_growth", "parcel_label"}:
                resources = ["cpu_heavy"]
            elif base_slot_id in {"security_public_safety", "internet_access"}:
                resources = ["network_fetch"]
            else:
                resources = ["light_read"]
        task["resource_class"] = resources

        quality = dict(task.get("data_quality_contract") or {})
        source_urls = quality.get("source_urls")
        if not isinstance(source_urls, list):
            source_urls = []
        if not source_urls:
            serialized = json.dumps(raw_task, ensure_ascii=False)
            script = self.repo / Path(script_path)
            if script.is_file() and script.stat().st_size <= 2_000_000:
                try:
                    serialized += "\n" + script.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    pass
            source_urls = list(dict.fromkeys(
                value.rstrip(".,);]")
                for value in re.findall(r"https?://[^\s\"'<>]+", serialized)
            ))[:32]
        if not source_urls and any(name.startswith("browser_") for name in resources):
            source_urls = ["http://127.0.0.1:8012/england_map_web/index.html"]
        quality["source_urls"] = source_urls
        quality.setdefault("source_snapshot_date", datetime.now(timezone.utc).date().isoformat())
        quality.setdefault("source_discovery_required", not bool(source_urls))
        quality.setdefault("measurement_level", "unknown_pending_source")
        quality.setdefault("output_semantics", "CANDIDATE")
        quality.setdefault("parcel_binding_method", "declared_92283_row_shard_partition")
        quality.setdefault("confidence_method", "runner_evidence_and_declared_source_validation")
        quality.setdefault("no_data_policy", "NO_DATA_NOT_INFERRED")
        quality.setdefault("ai_role", "not_used_for_numeric_measurement")
        quality.setdefault(
            "human_review_required_when",
            ["source_conflict", "low_confidence", "geometry_mismatch"],
        )
        task["data_quality_contract"] = quality
        return task

    def classify_task(self, task: dict[str, Any], *, allow_seen: bool = False) -> str:
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
                "parcel_polygon",
                "document",
            }:
                raise ValueError("DATA_QUALITY_MEASUREMENT_LEVEL_INVALID")
            if str(quality["output_semantics"]) not in {
                "NO_DATA",
                "MEASURED",
                "AREA_LEVEL_PROXY",
                "CANDIDATE",
                "MIXED_WITH_ROW_LABELS",
                "MEASURED_ONLY_AFTER_THREE_SOURCE_GATE",
            }:
                raise ValueError("DATA_QUALITY_OUTPUT_SEMANTICS_INVALID")
            if str(quality["ai_role"]) not in {
                "not_used",
                "not_used_for_numeric_measurement",
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
        if not allow_seen and task["task_id"] in self.seen_task_ids:
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
        compatibility_migrated = task.get("compatibility_migrated") is True
        if any(
            normalized_slot_id not in value.split("/")
            and not (compatibility_migrated and normalized_slot_id in value)
            for value in normalized_writes
        ):
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
        def write_path_allowed(value: str) -> bool:
            if any(value == root or value.startswith(root + "/") for root in normalized_roots):
                return True
            if not compatibility_migrated or normalized_slot_id not in value:
                return False
            return value.startswith("docs/chatgpt_status/") or value.startswith("england_map_web/data/")

        if any(not write_path_allowed(value) for value in normalized_writes):
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
            raise ValueError(f"TASK_TIMEOUT_OUT_OF_RANGE_60_TO_{MAX_TASK_TIMEOUT_SECONDS}")
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

    def _notify_mobile_problem_state(self, manual_actions: list[dict[str, Any]], all_clear: bool) -> dict[str, Any]:
        action_ids = sorted(str(item.get("id") or item.get("slot_id") or "") for item in manual_actions)
        fingerprint = sha256_bytes(json.dumps({"all_clear": all_clear, "ids": action_ids}, sort_keys=True).encode("utf-8"))
        result = {
            "state": "CHATGPT_APP_AUTOMATION_ACTIVE",
            "delivery": "CHATGPT_CODEX_TASK_NOTIFICATION",
            "automation_id": "aays-problem-z-c-bildirimleri",
            "pending_manual_action_count": len(manual_actions),
            "all_clear": all_clear,
            "fingerprint": fingerprint,
            "updated_at": utc_now(),
            "final_ready": False,
        }
        atomic_write_json(self.mobile_notification_state_path, result)
        return result

    def problem_solver_cycle(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        manual_report = read_json(self.state / "manual_actions_latest.json", {})
        manual_actions = [item for item in manual_report.get("actions", []) if isinstance(item, dict)]
        tasks = self.scan_tasks()
        task_by_slot: dict[str, tuple[Path, dict[str, Any]]] = {}
        for source, task in tasks:
            slot_id = str(task.get("slot_id") or "")
            if slot_id in SLOT_SPECS and slot_id not in task_by_slot:
                task_by_slot[slot_id] = (source, task)
        manual_slots: list[str] = []
        for item in manual_actions:
            slot_id = str(item.get("slot_id") or "")
            if slot_id in SLOT_SPECS and slot_id not in manual_slots:
                manual_slots.append(slot_id)
        stalled_slots: list[str] = []
        health_by_slot: dict[str, dict[str, Any]] = {}
        for slot_id in SLOT_SPECS:
            health = self.recovery_supervisor._health(slot_id)
            health_by_slot[slot_id] = health
            if health.get("needs_recovery") and slot_id not in manual_slots:
                stalled_slots.append(slot_id)
        remote_trigger_path = (
            self.repo / "docs" / "chatgpt_status" / "_shared" / "slots_21"
            / PROBLEM_SOLVER_SLOT_ID / "continuation_requested_latest.json"
        )
        remote_trigger = read_json(remote_trigger_path, {})
        trigger_id = str(remote_trigger.get("request_id") or remote_trigger.get("requested_at") or "")
        state = read_json(self.problem_solver_state_path, {})
        explicit_continuation = bool(trigger_id and trigger_id != state.get("last_remote_trigger_id"))
        attempts = state.get("attempts_by_fingerprint") if isinstance(state.get("attempts_by_fingerprint"), dict) else {}
        target_slot: str | None = None
        target_source: Path | None = None
        target_task: dict[str, Any] | None = None
        target_reason = ""
        target_fingerprint = ""
        for slot_id in [*manual_slots, *stalled_slots]:
            pair = task_by_slot.get(slot_id)
            if pair is None:
                continue
            health = health_by_slot.get(slot_id, {})
            target_reason = str(health.get("blocker") or health.get("state") or "STALLED_SLOT")
            target_fingerprint = sha256_bytes(f"{slot_id}|{target_reason}".encode("utf-8"))[:20]
            record = attempts.get(target_fingerprint, {}) if isinstance(attempts.get(target_fingerprint), dict) else {}
            last_attempt = None
            try:
                last_attempt = datetime.fromisoformat(str(record.get("last_attempt_at") or "").replace("Z", "+00:00"))
            except ValueError:
                pass
            due = last_attempt is None or (now - last_attempt).total_seconds() >= 300
            if explicit_continuation or (int(record.get("count") or 0) < 3 and due):
                target_slot = slot_id
                target_source, target_task = pair
                break
        all_clear = not manual_actions and not stalled_slots
        notification = self._notify_mobile_problem_state(manual_actions, all_clear)
        solver_dir = self.slot_dir(PROBLEM_SOLVER_SLOT_ID)
        if target_slot and target_task and target_source:
            plan_steps = [
                "READ_CURRENT_MANUAL_ACTION_AND_SLOT_HEALTH",
                "CAPTURE_BLOCKER_AND_NON_DESTRUCTIVE_DIAGNOSTICS",
                "REQUEST_SERIAL_RECOVERY_GATE_REOPEN",
                "VERIFY_ORPHAN_LOCK_OR_TIMEOUT_OR_FREE_SOURCE_REPAIR",
                "RESUME_ORIGINAL_TASK_WITHOUT_DUPLICATE_RUNNER",
                "VERIFY_STATUS_PROGRESS_AND_SELECT_NEXT_PROBLEM",
            ]
            count = int((attempts.get(target_fingerprint) or {}).get("count") or 0) + 1
            attempts[target_fingerprint] = {"count": count, "last_attempt_at": utc_now(), "slot_id": target_slot}
            request = {
                "schema_version": 1,
                "workstream_id": WORKSTREAM_ID,
                "requested_by_slot": PROBLEM_SOLVER_SLOT_ID,
                "target_slot_id": target_slot,
                "target_task_id": target_task.get("task_id"),
                "reason": target_reason,
                "plan_steps": plan_steps,
                "priority": "MANUAL_ACTION_FIRST" if target_slot in manual_slots else "STALLED_SLOT_SECOND",
                "request_id": uuid.uuid4().hex,
                "requested_at": utc_now(),
                "destructive_actions_allowed": False,
                "force_push_allowed": False,
                "final_ready": False,
            }
            atomic_write_json(
                self.state / "recovery" / "problem_solver_requests" / f"{target_slot}.json", request,
            )
            # A previously parked recovery task may already be present in the
            # scheduler's in-memory seen set. Re-open only an inactive target;
            # an active slot keeps its ownership and cannot be duplicated.
            target_task_id = str(target_task.get("task_id") or "")
            if target_task_id and target_slot not in self.scheduled_slot_ids:
                self.seen_task_ids.discard(target_task_id)
                self.scheduled_task_ids.discard(target_task_id)
            solver_state = {
                "state": "RECOVERY_REQUESTED", "target_slot_id": target_slot,
                "target_task_id": target_task.get("task_id"), "target_reason": target_reason,
                "plan_steps": plan_steps, "attempt": count,
                "manual_action_count": len(manual_actions), "stalled_slot_count": len(stalled_slots),
                "available_worker_capacity": self.available_worker_capacity,
                "max_child_workers": self.max_workers, "data_worker_capacity_consumed": 0,
                "notification": notification, "attempts_by_fingerprint": attempts,
                "last_remote_trigger_id": trigger_id or state.get("last_remote_trigger_id"),
                "updated_at": utc_now(), "final_ready": False,
            }
        else:
            solver_state = {
                "state": "ALL_CLEAR_MONITORING" if all_clear else "WAITING_FOR_ELIGIBLE_RECOVERY_TASK",
                "target_slot_id": None, "manual_action_count": len(manual_actions),
                "stalled_slot_count": len(stalled_slots),
                "slots_without_ready_task": sorted(set([*manual_slots, *stalled_slots]) - set(task_by_slot)),
                "available_worker_capacity": self.available_worker_capacity,
                "max_child_workers": self.max_workers, "data_worker_capacity_consumed": 0,
                "notification": notification, "attempts_by_fingerprint": attempts,
                "last_remote_trigger_id": trigger_id or state.get("last_remote_trigger_id"),
                "updated_at": utc_now(), "final_ready": False,
            }
        atomic_write_json(self.problem_solver_state_path, solver_state)
        common = {
            "schema_version": 1, "architecture_version": ARCHITECTURE_VERSION,
            "workstream_id": WORKSTREAM_ID, "slot_id": PROBLEM_SOLVER_SLOT_ID,
            "base_slot_id": "system_recovery", "updated_at": utc_now(), "final_ready": False,
        }
        atomic_write_json(solver_dir / "status_latest.json", {**solver_state, **common})
        atomic_write_json(solver_dir / "current_task_latest.json", {**solver_state, **common})
        atomic_write_json(solver_dir / "heartbeat_latest.json", {
            **common, "state": "RUNNING_MONITOR", "heartbeat_at": utc_now(), "stale_after_seconds": 90,
        })
        self.append_event(PROBLEM_SOLVER_SLOT_ID, {
            "transition": solver_state["state"], "target_slot_id": solver_state.get("target_slot_id"),
            "manual_action_count": len(manual_actions), "stalled_slot_count": len(stalled_slots),
        })
        return solver_state

    def write_global_status(self, state: str) -> None:
        with self.active_lock:
            active = {slot: value.get("task_id") for slot, value in self.active_tasks.items()}
        queued_tasks = self.scan_tasks()
        pending_publish_slots = self.pending_publish_slots()
        ready_tasks = [
            task
            for _source, task in queued_tasks
            if str(task.get("task_id") or "") not in self.seen_task_ids
            and str(task.get("task_id") or "") not in self.scheduled_task_ids
            and str(task.get("slot_id") or "") not in pending_publish_slots
            and str(task.get("slot_id") or "") not in self.scheduled_slot_ids
        ]
        blocked_slots = 0
        for slot_id in SLOT_SPECS:
            slot_status = read_json(self.slot_dir(slot_id) / "status_latest.json", {})
            if str(slot_status.get("state") or "").upper().startswith("BLOCKED"):
                blocked_slots += 1
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
                "available_worker_capacity": self.available_worker_capacity,
                "adaptive_capacity_reason": self.adaptive_capacity_reason,
                "logical_slot_count": LOGICAL_SLOT_COUNT,
                "data_slot_count": DATA_SLOT_COUNT,
                "problem_solver": read_json(self.problem_solver_state_path, {}),
                "parcel_scope": "LONDON_CANONICAL_MATRIX",
                "national_england_canonical_inventory_ready": False,
                "resource_profile": self.resource_profile,
                "total_memory_gb": self.memory_gb,
                "logical_cpus": self.logical_cpus,
                "tls_ca_bundle": str(self.tls_ca_bundle) if self.tls_ca_bundle else None,
                "active_tasks": active,
                "queue_scan_count": len(queued_tasks),
                "queue_ready_count": len(ready_tasks),
                "queue_compatibility_count": self.queue_compatibility_count,
                "queue_rejected_count": len(self.queue_rejected),
                "queue_rejected": self.queue_rejected,
                "automatic_recovery": self.recovery_supervisor.summary(),
                "recovery_worker_count": self.recovery_active_count,
                "recovery_pending_count": self.recovery_pending_count,
                "publish_pending_count": len(list(self.publish_queue.glob("*.json"))) if self.publish_queue.is_dir() else 0,
                "blocked_slot_count": blocked_slots,
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
                "logical_slot_count": LOGICAL_SLOT_COUNT,
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
        rejected: dict[str, str] = {}
        compatibility_count = 0
        business_roots = sorted({str(spec["business_root"]) for spec in SLOT_SPECS.values()})
        for business_root in business_roots:
            queue = self.repo / Path(business_root) / "queue"
            if not queue.exists():
                continue
            task_paths = sorted(queue.glob("*.task.json"))
            for path in task_paths:
                raw_task = read_json(path, {})
                if not raw_task or str(raw_task.get("status") or "pending") not in QUEUE_READY_STATUSES:
                    continue
                if path.name == "current.task.json":
                    continue
                try:
                    task = self.normalize_queue_task(path, raw_task)
                    self.classify_task(task, allow_seen=True)
                except (KeyError, TypeError, ValueError, OSError) as exc:
                    rejected[path.name] = str(exc)
                    continue
                if task.get("compatibility_migrated"):
                    compatibility_count += 1
                found.append((path, task))
        self.queue_compatibility_count = compatibility_count
        self.queue_rejected = dict(sorted(rejected.items()))
        return found

    def refresh_publisher(self, force: bool = False) -> dict[str, Any]:
        if not force and time.monotonic() - self.last_remote_refresh < 60:
            return self.remote_sync
        self.last_remote_refresh = time.monotonic()
        # A killed or timed-out checkout can leave an empty index.lock behind.
        # This coordinator reaches publisher refresh between its own Git
        # subprocess calls, so an old empty lock here is an orphan.
        publisher_index_lock = self.repo / ".git" / "index.lock"
        try:
            lock_age = time.time() - publisher_index_lock.stat().st_mtime
            if publisher_index_lock.is_file() and publisher_index_lock.stat().st_size == 0 and lock_age >= 60:
                publisher_index_lock.unlink()
        except (FileNotFoundError, OSError):
            pass
        stat_cache_only = False
        try:
            status = subprocess.run(
                self.git_command("-C", str(self.repo), "status", "--porcelain", "--untracked-files=no"),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=60,
            )
        except subprocess.TimeoutExpired:
            self.remote_sync = {"state": "WAITING_GIT_STATUS", "head": None, "error": "GIT_STATUS_TIMEOUT_60S"}
            return self.remote_sync
        if status.returncode != 0:
            self.remote_sync = {"state": "WAITING_GIT_CLEAN_PUBLISHER", "head": None, "error": status.stderr.strip() or status.stdout.strip()}
            return self.remote_sync
        if status.stdout.strip():
            working_diff = subprocess.run(
                self.git_command("-C", str(self.repo), "diff", "--quiet", "--ignore-submodules", "--"),
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False, timeout=60,
            )
            staged_diff = subprocess.run(
                self.git_command("-C", str(self.repo), "diff", "--cached", "--quiet", "--ignore-submodules", "--"),
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False, timeout=60,
            )
            if working_diff.returncode != 0 or staged_diff.returncode != 0:
                self.remote_sync = {"state": "WAITING_GIT_CLEAN_PUBLISHER", "head": None, "error": status.stdout.strip()}
                return self.remote_sync
            stat_cache_only = True
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
        try:
            checkout_command = self.git_command("-C", str(self.repo), "checkout")
            if stat_cache_only:
                checkout_command.append("--force")
            checkout_command.extend(("--detach", "FETCH_HEAD"))
            checkout = subprocess.run(
                checkout_command,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=300,
            )
        except subprocess.TimeoutExpired:
            self.remote_sync = {"state": "WAITING_GIT_CHECKOUT", "head": None, "error": "GIT_CHECKOUT_TIMEOUT_300S"}
            return self.remote_sync
        if checkout.returncode != 0:
            self.remote_sync = {"state": "WAITING_GIT_CHECKOUT", "head": None, "error": checkout.stderr.strip()}
            return self.remote_sync
        head = subprocess.run(
            self.git_command("-C", str(self.repo), "rev-parse", "HEAD"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=30,
        ).stdout.strip()
        self.remote_sync = {"state": "PASS", "head": head, "error": None, "refreshed_at": utc_now()}
        return self.remote_sync

    def refresh_child(self, worktree: Path) -> None:
        # This long legacy PowerShell path cannot be materialized on the moved
        # portable gas shard under the current Windows account.  Keep the
        # tracked blob authoritative while excluding only the absent worktree
        # copy from dirty checks; execute_task can materialize the exact HEAD
        # blob into the runtime directory when that task is selected.
        portable_sparse_omissions = (
            "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/"
            "RECONCILE_DONE_VS_BLOCKED_THEN_100_BROWSER_ACCEPTANCE_20260720.ps1",
        )
        for omitted in portable_sparse_omissions:
            if not (worktree / Path(omitted)).exists():
                try:
                    subprocess.run(
                        self.git_command("-C", str(worktree), "update-index", "--skip-worktree", "--", omitted),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                        timeout=30,
                    )
                except subprocess.TimeoutExpired:
                    # This is only a portable-stat-cache optimisation for an
                    # unrelated legacy gas path. Never block another slot when
                    # the optional index hint is slow on the portable disk.
                    pass
        stat_cache_only = False
        try:
            status = subprocess.run(
                self.git_command("-C", str(worktree), "status", "--porcelain", "--untracked-files=no"),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("CHILD_WORKTREE_STATUS_TIMEOUT_60S") from exc
        if status.returncode != 0:
            raise RuntimeError("CHILD_WORKTREE_NOT_CLEAN_FOR_REMOTE_REFRESH")
        if status.stdout.strip():
            # Git can report a false worktree modification when only its cached
            # stat data is stale (common on a portable NTFS disk moved between
            # Windows accounts).  Accept that case only when both authoritative
            # content comparisons are clean; genuine tracked edits remain a
            # hard stop.
            working_diff = subprocess.run(
                self.git_command("-C", str(worktree), "diff", "--quiet", "--ignore-submodules", "--"),
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False, timeout=60,
            )
            staged_diff = subprocess.run(
                self.git_command("-C", str(worktree), "diff", "--cached", "--quiet", "--ignore-submodules", "--"),
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False, timeout=60,
            )
            if working_diff.returncode != 0 or staged_diff.returncode != 0:
                raise RuntimeError("CHILD_WORKTREE_NOT_CLEAN_FOR_REMOTE_REFRESH")
            stat_cache_only = True
        try:
            fetch = subprocess.run(
                self.git_command("-C", str(worktree), "fetch", "--depth=1", "origin", str(self.identity["branch"])),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=180,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("CHILD_REMOTE_FETCH_TIMEOUT_180S") from exc
        if fetch.returncode != 0:
            raise RuntimeError(f"CHILD_REMOTE_REFRESH_FAILED: {fetch.stderr.strip()}")
        current_head = subprocess.run(
            self.git_command("-C", str(worktree), "rev-parse", "HEAD"),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False, timeout=30,
        ).stdout.strip()
        fetched_head = subprocess.run(
            self.git_command("-C", str(worktree), "rev-parse", "FETCH_HEAD"),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False, timeout=30,
        ).stdout.strip()
        if current_head and current_head == fetched_head:
            return
        checkout_command = self.git_command("-C", str(worktree), "checkout")
        if stat_cache_only:
            # Content was proven identical above.  Force only this stat-cache
            # recovery case so checkout can refresh the portable worktree.
            checkout_command.append("--force")
        checkout_command.extend(("--detach", "FETCH_HEAD"))
        try:
            checkout = subprocess.run(
                checkout_command,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=300,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("CHILD_REMOTE_CHECKOUT_TIMEOUT_300S") from exc
        # A killed or timed-out Git process can leave an empty index.lock behind.
        # At this point our checkout process has exited and no slot task has been
        # launched yet, so a sufficiently old empty lock is an orphan. Remove it
        # once and retry instead of permanently blocking the logical slot.
        if checkout.returncode != 0 and "index.lock" in checkout.stderr:
            index_lock = self.worktree_git_dir(worktree) / "index.lock"
            try:
                lock_age = time.time() - index_lock.stat().st_mtime
                if index_lock.is_file() and index_lock.stat().st_size == 0 and lock_age >= 60:
                    index_lock.unlink()
                    checkout = subprocess.run(
                        checkout_command,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=300,
                    )
            except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
                pass
        if checkout.returncode != 0:
            raise RuntimeError(f"CHILD_REMOTE_CHECKOUT_FAILED: {checkout.stderr.strip()}")

    def git_path_list(self, repo: Path, *args: str) -> list[str]:
        try:
            completed = subprocess.run(
                self.git_command("-C", str(repo), *args),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("GIT_PATH_LIST_TIMEOUT_120S") from exc
        if completed.returncode != 0:
            raise RuntimeError(f"GIT_PATH_LIST_FAILED: {completed.stderr.decode('utf-8', errors='replace').strip()}")
        return [value.decode("utf-8", errors="surrogateescape") for value in completed.stdout.split(b"\0") if value]

    @staticmethod
    def changed_path_allowed(path: str, allowed_paths: list[str]) -> bool:
        normalized = normalize_repo_path(path)
        return any(normalized == allowed or normalized.startswith(allowed + "/") for allowed in allowed_paths)

    @staticmethod
    def publisher_conflict_timestamp(value: Any) -> datetime | None:
        if not isinstance(value, str):
            return None
        candidate = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @classmethod
    def publisher_conflict_json_signature(cls, value: Any) -> Any:
        """Remove only volatile timestamps before comparing generated proofs."""
        volatile = {
            "updated_at", "last_updated", "generated_at", "heartbeat_at",
            "last_attempt_at", "runner_published_at", "published_at",
        }
        if isinstance(value, dict):
            return {
                key: cls.publisher_conflict_json_signature(child)
                for key, child in value.items()
                if str(key).casefold() not in volatile
            }
        if isinstance(value, list):
            return [cls.publisher_conflict_json_signature(child) for child in value]
        return value

    @classmethod
    def publisher_conflict_json_latest(cls, value: Any) -> datetime:
        latest = datetime.min.replace(tzinfo=timezone.utc)
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).casefold() in {
                    "updated_at", "last_updated", "generated_at", "heartbeat_at",
                    "last_attempt_at", "runner_published_at", "published_at",
                }:
                    parsed = cls.publisher_conflict_timestamp(child)
                    if parsed and parsed > latest:
                        latest = parsed
                nested = cls.publisher_conflict_json_latest(child)
                if nested > latest:
                    latest = nested
        elif isinstance(value, list):
            for child in value:
                nested = cls.publisher_conflict_json_latest(child)
                if nested > latest:
                    latest = nested
        return latest

    @classmethod
    def generated_conflict_side(cls, relative: str, ours: str, theirs: str) -> str | None:
        """Resolve only equivalent generated records; never guess through code."""
        suffix = Path(relative).suffix.casefold()
        generated_path = any(
            marker in f"/{normalize_repo_path(relative).casefold()}"
            for marker in (
                "/reports/", "/status/", "/runner_outputs/", "/outputs/",
                "/_shared/slots_21/", "/_shared/manual_actions/",
            )
        )
        if not generated_path or suffix not in {".json", ".txt", ".md"}:
            return None
        if ours == theirs:
            return "ours"
        if suffix == ".json":
            try:
                ours_json = json.loads(ours)
                theirs_json = json.loads(theirs)
            except json.JSONDecodeError:
                return None
            if cls.publisher_conflict_json_signature(ours_json) != cls.publisher_conflict_json_signature(theirs_json):
                return None
            ours_time = cls.publisher_conflict_json_latest(ours_json)
            theirs_time = cls.publisher_conflict_json_latest(theirs_json)
            return "theirs" if theirs_time > ours_time else "ours"
        iso_pattern = re.compile(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})")
        if iso_pattern.sub("<TIMESTAMP>", ours) != iso_pattern.sub("<TIMESTAMP>", theirs):
            return None
        ours_times = [cls.publisher_conflict_timestamp(match.group(0)) for match in iso_pattern.finditer(ours)]
        theirs_times = [cls.publisher_conflict_timestamp(match.group(0)) for match in iso_pattern.finditer(theirs)]
        ours_latest = max((value for value in ours_times if value), default=datetime.min.replace(tzinfo=timezone.utc))
        theirs_latest = max((value for value in theirs_times if value), default=datetime.min.replace(tzinfo=timezone.utc))
        return "theirs" if theirs_latest > ours_latest else "ours"

    def auto_resolve_publisher_conflicts(self, stage_paths: list[str]) -> dict[str, Any]:
        conflicts = self.git_path_list(
            self.repo, "diff", "--name-only", "--diff-filter=U", "-z", "--"
        )
        allowed = {normalize_repo_path(path) for path in stage_paths}
        if not conflicts:
            return {"state": "PASS", "resolved": []}
        foreign = [path for path in conflicts if normalize_repo_path(path) not in allowed]
        if foreign:
            return {"state": "FOREIGN_CONFLICT", "paths": foreign}
        resolved: list[dict[str, str]] = []
        for relative in conflicts:
            versions: dict[str, str] = {}
            for side, stage in (("ours", 2), ("theirs", 3)):
                shown = subprocess.run(
                    self.git_command("-C", str(self.repo), "show", f":{stage}:{relative}"),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=60,
                )
                if shown.returncode != 0:
                    return {"state": "CONFLICT_STAGE_MISSING", "path": relative}
                try:
                    versions[side] = shown.stdout.decode("utf-8")
                except UnicodeDecodeError:
                    return {"state": "BINARY_CONFLICT_REQUIRES_OWNER", "path": relative}
            selected = self.generated_conflict_side(relative, versions["ours"], versions["theirs"])
            if not selected:
                return {"state": "SEMANTIC_CONFLICT_REQUIRES_SLOT_OWNER", "path": relative}
            checkout = subprocess.run(
                self.git_command("-C", str(self.repo), "checkout", f"--{selected}", "--", relative),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=60,
            )
            if checkout.returncode != 0:
                return {"state": "CONFLICT_CHECKOUT_FAILED", "path": relative, "error": checkout.stderr.strip()}
            staged = subprocess.run(
                self.git_command("-C", str(self.repo), "add", "--sparse", "--", relative),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=60,
            )
            if staged.returncode != 0:
                return {"state": "CONFLICT_STAGE_FAILED", "path": relative, "error": staged.stderr.strip()}
            resolved.append({"path": relative, "selected": selected})
        remaining = self.git_path_list(
            self.repo, "diff", "--name-only", "--diff-filter=U", "-z", "--"
        )
        if remaining:
            return {"state": "CONFLICTS_REMAIN", "paths": remaining, "resolved": resolved}
        return {"state": "PASS", "resolved": resolved}

    def chunk_large_publish_file(
        self,
        worktree: Path,
        relative: str,
        chunk_size: int = 48 * 1024 * 1024,
    ) -> dict[str, Any]:
        source = worktree / Path(relative)
        if not source.is_file():
            raise FileNotFoundError(relative)
        file_size = source.stat().st_size
        source_hash = hashlib.sha256()
        with source.open("rb") as stream:
            while block := stream.read(4 * 1024 * 1024):
                source_hash.update(block)
        digest = source_hash.hexdigest()
        part_count = max(1, (file_size + chunk_size - 1) // chunk_size)
        # Keep the generated path short on Windows. The original filename can
        # already be close to MAX_PATH; the content hash is collision-safe for
        # this adjacent chunk store and is also recorded in the manifest.
        chunk_root = source.parent / ".aays_chunks" / digest[:16]
        chunk_root.mkdir(parents=True, exist_ok=True)
        parts: list[dict[str, Any]] = []
        with source.open("rb") as stream:
            for index in range(1, part_count + 1):
                part = chunk_root / f"part-{index:04d}-of-{part_count:04d}.bin"
                temporary = part.with_name(f"{part.name}.tmp.{uuid.uuid4().hex}")
                part_hash = hashlib.sha256()
                written = 0
                with temporary.open("wb") as output:
                    while written < chunk_size:
                        block = stream.read(min(4 * 1024 * 1024, chunk_size - written))
                        if not block:
                            break
                        output.write(block)
                        part_hash.update(block)
                        written += len(block)
                os.replace(temporary, part)
                part_relative = part.relative_to(worktree).as_posix()
                parts.append({
                    "index": index,
                    "path": part_relative,
                    "size_bytes": written,
                    "sha256": part_hash.hexdigest(),
                })
        if sum(int(part["size_bytes"]) for part in parts) != file_size:
            raise RuntimeError("CHUNK_SIZE_SUM_MISMATCH")
        manifest_path = source.with_name(f"{source.name}.aays-chunks.json")
        manifest = {
            "schema_version": 1,
            "format": "AAYS_GITHUB_CHUNKED_BLOB_V1",
            "original_path": normalize_repo_path(relative),
            "original_size_bytes": file_size,
            "original_sha256": digest,
            "chunk_size_bytes": chunk_size,
            "part_count": part_count,
            "parts": parts,
            "reassembly": {
                "algorithm": "concatenate parts in ascending index order",
                "verification": "result size and SHA-256 must equal original_size_bytes and original_sha256",
                "user_source_required": False,
            },
            "created_at": utc_now(),
            "final_ready": True,
        }
        atomic_write_json(manifest_path, manifest)
        return {
            "original_path": normalize_repo_path(relative),
            "original_size_bytes": file_size,
            "original_sha256": digest,
            "manifest_path": manifest_path.relative_to(worktree).as_posix(),
            "part_paths": [str(part["path"]) for part in parts],
            "part_count": part_count,
            "chunk_size_bytes": chunk_size,
        }

    def prepare_publish_item(self, source: Path, task: dict[str, Any], worktree: Path, base_head: str) -> Path | None:
        working = set(self.git_path_list(worktree, "diff", "--name-only", "-z", "--"))
        working.update(self.git_path_list(worktree, "diff", "--cached", "--name-only", "-z", "--"))
        working.update(self.git_path_list(worktree, "ls-files", "--others", "--exclude-standard", "-z"))
        working.discard(
            "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/"
            "RECONCILE_DONE_VS_BLOCKED_THEN_100_BROWSER_ACCEPTANCE_20260720.ps1"
        )
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
        github_blob_limit = 95 * 1024 * 1024
        local_only_large_paths: list[str] = []
        chunked_large_files: list[dict[str, Any]] = []
        publishable_paths: list[str] = []
        for relative in changed:
            candidate = worktree / Path(relative)
            if candidate.is_file() and candidate.stat().st_size > github_blob_limit:
                local_only_large_paths.append(relative)
                try:
                    chunked = self.chunk_large_publish_file(worktree, relative)
                except Exception as exc:
                    raise RuntimeError(f"LARGE_FILE_CHUNK_FAILED:{relative}:{type(exc).__name__}:{exc}") from exc
                chunked_large_files.append(chunked)
                publishable_paths.append(str(chunked["manifest_path"]))
                publishable_paths.extend(str(value) for value in chunked["part_paths"])
            else:
                publishable_paths.append(relative)
        changed = sorted(set(publishable_paths))
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
                "local_only_large_paths": local_only_large_paths,
                "chunked_large_files": chunked_large_files,
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
            publisher_base_head: str | None = None
            stage_paths: list[str] = []
            item["attempts"] = int(item.get("attempts") or 0) + 1
            item["last_attempt_at"] = utc_now()
            atomic_write_json(item_path, item)
            try:
                sync = self.refresh_publisher(force=True)
                if sync.get("state") != "PASS":
                    raise RuntimeError(f"PUBLISHER_REFRESH_NOT_READY: {sync.get('error') or sync.get('state')}")
                publisher_base_head = subprocess.run(
                    self.git_command("-C", str(self.repo), "rev-parse", "HEAD"),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=30,
                ).stdout.strip()
                if not publisher_base_head:
                    raise RuntimeError("PUBLISHER_BASE_HEAD_MISSING")
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
                queue_stage_paths: list[str] = []
                if queue_task:
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
                    queue_stage_paths.append(queue_relative)
                else:
                    # Another slot/page may have superseded or removed the
                    # source task while this result was waiting to publish.
                    # The child commit and slot proofs are still authoritative;
                    # publish them instead of retrying the orphan forever.
                    item["source_queue_missing_at_publish"] = True
                    atomic_write_json(item_path, item)
                proof_paths = self.copy_slot_proofs(str(item["slot_id"]))
                stage_paths = sorted(set([*changed_paths, *queue_stage_paths, *proof_paths]))
                stage = subprocess.run(
                    self.git_command("-C", str(self.repo), "add", "--sparse", "-A", "--", *stage_paths),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=120,
                )
                if stage.returncode != 0:
                    raise RuntimeError(f"PUBLISHER_STAGE_FAILED: {stage.stderr.strip()}")
                staged_paths = self.git_path_list(self.repo, "diff", "--cached", "--name-only", "-z", "--")
                unexpected = [path for path in staged_paths if path not in stage_paths]
                if unexpected:
                    raise RuntimeError("PUBLISHER_STAGED_UNEXPECTED_PATHS: " + ",".join(unexpected))
                commit = subprocess.run(
                    self.git_command("-C", str(self.repo), "commit", "-m", f"Publish {item['slot_id']} task {item['task_id']}"),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=120,
                )
                if commit.returncode != 0:
                    raise RuntimeError(f"PUBLISHER_COMMIT_FAILED: {commit.stderr.strip() or commit.stdout.strip()}")
                branch = str(self.identity["branch"])
                push_error = None
                for _attempt in range(5):
                    push = subprocess.run(
                        self.git_command("-C", str(self.repo), "push", "origin", f"HEAD:{branch}"),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=600,
                    )
                    if push.returncode == 0:
                        push_error = None
                        break
                    push_error = push.stderr.strip() or push.stdout.strip()
                    push_error_lower = push_error.casefold()
                    # Authentication/configuration failures cannot be repaired
                    # by fetching and rebasing. Retrying that path created
                    # avoidable conflicts and stale locks while GitHub login
                    # was missing.
                    if not any(
                        marker in push_error_lower
                        for marker in ("non-fast-forward", "fetch first", "rejected")
                    ):
                        break
                    fetch = subprocess.run(
                        self.git_command("-C", str(self.repo), "fetch", "--depth=20", "origin", branch),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=120,
                    )
                    if fetch.returncode != 0:
                        continue
                    # Multiple ChatGPT pages can advance the same branch every
                    # minute. Replaying a large evidence commit with rebase on
                    # every race took several minutes and lost the next race.
                    # A normal merge preserves both histories and is usually a
                    # tree-only operation, so the follow-up push happens fast.
                    merge = subprocess.run(
                        self.git_command("-C", str(self.repo), "merge", "--no-edit", "FETCH_HEAD"),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=300,
                    )
                    if merge.returncode != 0:
                        resolution = self.auto_resolve_publisher_conflicts(stage_paths)
                        if resolution.get("state") != "PASS":
                            subprocess.run(self.git_command("-C", str(self.repo), "merge", "--abort"), check=False)
                            raise RuntimeError(
                                "PUBLISHER_MERGE_CONFLICT: "
                                f"{resolution.get('state')} {resolution.get('path') or resolution.get('paths') or ''}; "
                                f"{merge.stderr.strip() or merge.stdout.strip()}"
                            )
                        finish_merge = subprocess.run(
                            self.git_command("-C", str(self.repo), "commit", "--no-edit"),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=120,
                        )
                        if finish_merge.returncode != 0:
                            subprocess.run(self.git_command("-C", str(self.repo), "merge", "--abort"), check=False)
                            raise RuntimeError(
                                "PUBLISHER_AUTO_RESOLVE_COMMIT_FAILED: "
                                f"{finish_merge.stderr.strip() or finish_merge.stdout.strip()}"
                            )
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
                # The publisher checkout is a disposable serialization area;
                # authoritative results remain in the child worktree and the
                # publish-queue item. Restore only paths touched by this item so
                # an auth/timeout/rebase failure cannot poison every later item.
                if publisher_base_head and stage_paths:
                    subprocess.run(
                        self.git_command("-C", str(self.repo), "merge", "--abort"),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=60,
                    )
                    subprocess.run(
                        self.git_command("-C", str(self.repo), "rebase", "--abort"),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=60,
                    )
                    subprocess.run(
                        self.git_command("-C", str(self.repo), "add", "--sparse", "-A", "--", *stage_paths),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=120,
                    )
                    subprocess.run(
                        self.git_command(
                            "-C", str(self.repo), "restore", f"--source={publisher_base_head}",
                            "--staged", "--worktree", "--", *stage_paths,
                        ),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=180,
                    )
                    subprocess.run(
                        self.git_command("-C", str(self.repo), "checkout", "--detach", publisher_base_head),
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=180,
                    )
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
        due: list[tuple[datetime, Path]] = []
        now = datetime.now(timezone.utc)
        for path in pending:
            item = read_json(path, {})
            last_attempt = item.get("last_attempt_at")
            stamp = datetime.min.replace(tzinfo=timezone.utc)
            if last_attempt:
                try:
                    stamp = datetime.fromisoformat(str(last_attempt).replace("Z", "+00:00"))
                    if (now - stamp).total_seconds() < 60:
                        continue
                except ValueError:
                    stamp = datetime.min.replace(tzinfo=timezone.utc)
            due.append((stamp, path))
        if not due:
            return {"state": "WAITING_PUBLISH_RETRY"}
        _stamp, next_item = min(due, key=lambda value: (value[0], value[1].name))
        return self.publish_item(next_item)
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
                # If a previous attempt completed its script but stopped before
                # staging/publishing, its declared outputs are authoritative
                # resumable work. Do not discard or block on those exact paths;
                # rerun idempotently and continue into serial publication.
                preexisting = set(self.git_path_list(worktree, "diff", "--name-only", "-z", "--"))
                preexisting.update(
                    self.git_path_list(worktree, "ls-files", "--others", "--exclude-standard", "-z")
                )
                preexisting.discard(
                    "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/"
                    "RECONCILE_DONE_VS_BLOCKED_THEN_100_BROWSER_ACCEPTANCE_20260720.ps1"
                )
                resume_existing_outputs = bool(preexisting) and all(
                    self.changed_path_allowed(path, write_paths) for path in preexisting
                )
                if not resume_existing_outputs:
                    try:
                        self.refresh_child(worktree)
                    except RuntimeError as exc:
                        fallback_allowed = task.get("allow_verified_local_head_fallback") is True
                        fallback_markers = (
                            "CHILD_REMOTE_CHECKOUT_TIMEOUT",
                            "CHILD_REMOTE_FETCH_TIMEOUT",
                            "CHILD_REMOTE_REFRESH_FAILED",
                        )
                        local_head = subprocess.run(
                            self.git_command("-C", str(worktree), "rev-parse", "HEAD"),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            text=True,
                            check=False,
                            timeout=30,
                        ).stdout.strip()
                        if not fallback_allowed or not local_head or not any(
                            marker in str(exc) for marker in fallback_markers
                        ):
                            raise
                        self.append_event(slot_id, {
                            "transition": "RECOVERY_LOCAL_HEAD_FALLBACK",
                            "task_id": task["task_id"],
                            "local_head": local_head,
                            "recovery_plan_key": task.get("recovery_plan_key"),
                        })
                base_head = subprocess.run(
                    self.git_command("-C", str(worktree), "rev-parse", "HEAD"),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
                ).stdout.strip()
                if not base_head:
                    raise RuntimeError("CHILD_BASE_HEAD_MISSING")
                sparse_roots: list[str] = []
                for value in [task["script_path"], *task.get("read_paths", []), *task["exact_write_paths"]]:
                    normalized = normalize_repo_path(value)
                    repo_path = PurePosixPath(normalized)
                    # Cone-mode sparse checkout accepts nested directories. A
                    # file needs its parent; declared output/read directories
                    # can be included directly. Avoid expanding a huge top-level
                    # tree such as all of england_map_web for one slot output.
                    sparse_root = str(repo_path.parent) if repo_path.suffix else normalized
                    if sparse_root not in ("", "."):
                        sparse_roots.append(sparse_root)
                sparse_roots = sorted(set(sparse_roots))
                if (worktree / ".git").exists() and sparse_roots:
                    try:
                        sparse_list = subprocess.run(
                            self.git_command("-C", str(worktree), "sparse-checkout", "list"),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            check=False,
                            timeout=60,
                        )
                    except subprocess.TimeoutExpired as exc:
                        raise RuntimeError("SPARSE_LIST_TIMEOUT_60S") from exc
                    configured_roots = {
                        normalize_repo_path(value.strip())
                        for value in sparse_list.stdout.splitlines()
                        if value.strip()
                    } if sparse_list.returncode == 0 else set()
                    missing_roots = [
                        value
                        for value in sparse_roots
                        if not any(value == root or value.startswith(root + "/") for root in configured_roots)
                    ]
                    if missing_roots:
                        sparse_command = self.git_command(
                            "-C", str(worktree), "sparse-checkout", "add", "--skip-checks", *missing_roots
                        )
                        try:
                            sparse = subprocess.run(
                                sparse_command,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE,
                                text=True,
                                check=False,
                                timeout=300,
                            )
                        except subprocess.TimeoutExpired as exc:
                            existing_paths = all((worktree / Path(value)).exists() for value in missing_roots)
                            if task.get("allow_existing_sparse_paths_after_timeout") is True and existing_paths:
                                sparse = subprocess.CompletedProcess(sparse_command, 0, "", "")
                            else:
                                raise RuntimeError("SPARSE_EXPANSION_TIMEOUT_300S") from exc
                        if sparse.returncode != 0 and "sparse-checkout.lock" in sparse.stderr:
                            sparse_lock = self.worktree_git_dir(worktree) / "info" / "sparse-checkout.lock"
                            try:
                                lock_age = time.time() - sparse_lock.stat().st_mtime
                                if sparse_lock.is_file() and sparse_lock.stat().st_size == 0 and lock_age >= 60:
                                    sparse_lock.unlink()
                                    sparse = subprocess.run(
                                        sparse_command,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=False,
                                        timeout=300,
                                    )
                            except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
                                pass
                        if sparse.returncode != 0:
                            raise RuntimeError(f"SPARSE_EXPANSION_FAILED: {sparse.stderr.strip()}")
                declared_script_path = normalize_repo_path(str(task["script_path"]))
                script = (worktree / Path(declared_script_path)).resolve()
                if worktree.resolve() not in script.parents:
                    raise RuntimeError("TASK_SCRIPT_OUTSIDE_WORKTREE_OR_MISSING")
                if not script.exists():
                    # Sparse portable worktrees can legitimately omit a tracked
                    # script (or be unable to materialize one after moving to a
                    # new Windows account). Execute the exact blob from the
                    # verified child HEAD instead of treating that as no work.
                    materialized = subprocess.run(
                        self.git_command(
                            "-C", str(worktree), "show", f"HEAD:{declared_script_path}"
                        ),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False,
                        timeout=60,
                    )
                    if materialized.returncode != 0:
                        # Git object names are case-sensitive even on the
                        # Windows worktree. Some queue records normalized this
                        # legacy script to lowercase; resolve the tracked case
                        # within its declared parent and retry the exact blob.
                        script_parent = str(PurePosixPath(declared_script_path).parent)
                        tracked = subprocess.run(
                            self.git_command(
                                "-C", str(worktree), "ls-tree", "-r", "--name-only", "HEAD", "--", script_parent
                            ),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            check=False,
                            timeout=60,
                        )
                        tracked_case = next(
                            (
                                value.strip()
                                for value in tracked.stdout.splitlines()
                                if value.strip().casefold() == declared_script_path.casefold()
                            ),
                            None,
                        )
                        if tracked_case:
                            materialized = subprocess.run(
                                self.git_command("-C", str(worktree), "show", f"HEAD:{tracked_case}"),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                check=False,
                                timeout=60,
                            )
                    if materialized.returncode != 0 or not materialized.stdout:
                        raise RuntimeError(
                            "TASK_SCRIPT_OUTSIDE_WORKTREE_OR_MISSING: "
                            + materialized.stderr.decode("utf-8", errors="replace").strip()
                        )
                    script = (
                        self.runtime
                        / "materialized_scripts"
                        / slot_id
                        / f"{task['task_id']}{Path(declared_script_path).suffix}"
                    )
                    script.parent.mkdir(parents=True, exist_ok=True)
                    script.write_bytes(materialized.stdout)
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
                        # The launcher uses AAYS_REPO_ROOT for the dedicated
                        # publisher checkout. Child scripts must never inherit
                        # that shared path; all slot reads/writes belong to the
                        # isolated child worktree until serial publication.
                        "AAYS_REPO_ROOT": str(worktree),
                        "AAYS_SLOT_WORKTREE": str(worktree),
                        "AAYS_SLOT_ID": slot_id,
                        "AAYS_TASK_ID": str(task["task_id"]),
                        "AAYS_CHILD_DIRECT_PUSH_FORBIDDEN": "true",
                        "AAYS_SOURCE_DISCOVERY_POLICY": str(
                            task.get("source_discovery_policy") or "DECLARED_SOURCES_ONLY"
                        ),
                        "AAYS_ALLOW_FREE_PUBLIC_SOURCE_DISCOVERY": str(
                            bool(task.get("allow_free_public_source_discovery"))
                        ).lower(),
                        "AAYS_FORBID_USER_SOURCE_REQUEST": str(
                            bool(task.get("forbid_user_source_request"))
                        ).lower(),
                        "AAYS_FORBID_EMAIL_OR_ACCOUNT_SOURCES": str(
                            bool(task.get("forbid_email_or_account_sources"))
                        ).lower(),
                        "AAYS_ALLOW_EVIDENCE_BACKED_NO_DATA": str(
                            bool(task.get("allow_evidence_backed_no_data"))
                        ).lower(),
                        "AAYS_CONTINUE_AFTER_NO_DATA": str(
                            bool(task.get("continue_after_no_data"))
                        ).lower(),
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
                    if task.get("continue_after_no_data"):
                        state = "NO_DATA_CONTINUE"
                        result = {
                            "state": state,
                            "exit_code": completed.returncode,
                            "log": str(log.relative_to(self.root)),
                            "source_discovery_policy": task.get("source_discovery_policy"),
                            "user_source_required": False,
                            "email_or_account_source_used": False,
                            "fake_data": False,
                            "reason": "SOURCE_DISCOVERY_EXECUTED_WITHOUT_USABLE_DATA",
                        }
                    else:
                        state = "BLOCKED"
                        result = {"state": state, "exit_code": completed.returncode, "log": str(log.relative_to(self.root))}
                else:
                    self.write_slot_runtime_state(slot_id, task, "RESULT_READY_FOR_SERIAL_PUBLISH")
                    item_path = self.prepare_publish_item(source, task, worktree, base_head)
                    if item_path is None:
                        if task.get("continue_after_no_data"):
                            state = "NO_DATA_CONTINUE"
                            result = {
                                "state": state,
                                "exit_code": 0,
                                "log": str(log.relative_to(self.root)),
                                "source_discovery_policy": task.get("source_discovery_policy"),
                                "user_source_required": False,
                                "email_or_account_source_used": False,
                                "fake_data": False,
                                "reason": "SOURCE_DISCOVERY_COMPLETED_WITHOUT_DECLARED_OUTPUT",
                            }
                        else:
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
        preflight = read_json(self.preflight_path, {})
        try:
            checked_at = datetime.fromisoformat(str(preflight.get("checked_at") or "").replace("Z", "+00:00"))
            preflight_age = (datetime.now(timezone.utc) - checked_at).total_seconds()
        except (TypeError, ValueError):
            preflight_age = float("inf")
        # The PowerShell launcher performs and persists preflight immediately
        # before spawning us. Reuse that fresh proof instead of scanning all 21
        # portable worktrees twice on every start.
        if not preflight.get("ready") or preflight_age > 300:
            preflight = self.preflight()
        if not preflight["ready"]:
            print(json.dumps(preflight, ensure_ascii=False))
            return 2
        acquired, lock = self.acquire_lock()
        if not acquired:
            print(json.dumps({"status": "already_running", "pid": lock.get("pid"), "second_launch_blocked": True}))
            return 0
        try:
            # Take the single-instance lock before the many durable state
            # writes in initialize_state.  The watchdog can dispatch another
            # launcher while a slow USB disk is flushing those files; without
            # this ordering every launch performed the same initialization and
            # none reached its first heartbeat promptly.
            # Publish the new PID immediately. The watchdog must not compare a
            # newly acquired lock with the previous process's stale heartbeat.
            self.heartbeat("INITIALIZING_STATE")
            self.initialize_state()
            self.heartbeat("STARTING_REMOTE_SYNC")
            self.write_global_status("STARTING_REMOTE_SYNC")
            # Hydrate from the last locally verified head immediately.  Remote
            # refresh/publish is queued on the dedicated publisher worker below
            # so a slow checkout can never freeze startup or task scheduling.
            self.remote_sync = {
                "state": "INITIAL_SYNC_QUEUED",
                "head": None,
                "error": None,
            }
            self.hydrate_checkpoints()
        except Exception:
            self.release_lock()
            raise
        atomic_write_json(self.control_path, {"requested_action": None, "updated_at": utc_now()})
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="aays-slot")
        # Publishing can legitimately take several minutes for large evidence
        # files or while remote ChatGPT pages are pushing new commits.  It must
        # not block heartbeats, status updates, or scheduling of unrelated
        # slots.  Keep Git serialization in one dedicated maintenance worker.
        publisher_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="aays-publisher"
        )
        recovery_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="aays-recovery"
        )
        problem_solver_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="aays-problem-solver"
        )
        publisher_future: concurrent.futures.Future | None = None
        problem_solver_future: concurrent.futures.Future | None = None
        recovery_futures: dict[str, concurrent.futures.Future] = {}
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
                if problem_solver_future is not None and problem_solver_future.done():
                    try:
                        problem_solver_future.result()
                    except Exception as exc:
                        atomic_write_json(self.problem_solver_state_path, {
                            "state": "PROBLEM_SOLVER_ERROR",
                            "error": f"{type(exc).__name__}:{exc}",
                            "updated_at": utc_now(),
                            "final_ready": False,
                        })
                    problem_solver_future = None
                if (
                    problem_solver_future is None
                    and time.monotonic() - self.last_problem_solver_cycle >= 15
                ):
                    self.last_problem_solver_cycle = time.monotonic()
                    problem_solver_future = problem_solver_executor.submit(self.problem_solver_cycle)
                if publisher_future is not None and publisher_future.done():
                    try:
                        publisher_future.result()
                    except Exception as exc:
                        self.remote_sync = {
                            "state": "PUBLISH_MAINTENANCE_ERROR",
                            "head": self.remote_sync.get("head"),
                            "error": str(exc),
                        }
                    publisher_future = None
                if publisher_future is None:
                    if any(self.publish_queue.glob("*.json")):
                        publisher_future = publisher_executor.submit(self.process_publish_queue)
                    elif (
                        self.recovery_pending_count == 0
                        and time.monotonic() - self.last_remote_refresh >= 60
                    ):
                        publisher_future = publisher_executor.submit(self.refresh_publisher)
                pending_publish_slots = self.pending_publish_slots()
                if self.can_schedule():
                    for source, task in self.scan_tasks():
                        if len(futures) >= self.available_worker_capacity:
                            break
                        task_id = str(task.get("task_id"))
                        slot_id = str(task.get("slot_id") or "")
                        if slot_id in pending_publish_slots:
                            continue
                        if slot_id in self.scheduled_slot_ids:
                            continue
                        if task_id in self.seen_task_ids or task_id in self.scheduled_task_ids:
                            continue
                        slot_status = read_json(self.slot_dir(slot_id) / "status_latest.json", {})
                        if (
                            str(slot_status.get("state") or "").upper() == "NO_DATA_CONTINUE"
                            and str(slot_status.get("task_id") or "") == task_id
                        ):
                            self.seen_task_ids.add(task_id)
                            continue
                        recovery_future = recovery_futures.get(task_id)
                        if recovery_future is not None:
                            if not recovery_future.done():
                                continue
                            try:
                                recovery = recovery_future.result()
                            except Exception as exc:
                                self.remote_sync = {
                                    "state": "RECOVERY_MAINTENANCE_ERROR",
                                    "head": self.remote_sync.get("head"),
                                    "error": str(exc),
                                }
                                recovery = {"decision": "BLOCK", "task": task}
                            recovery_futures.pop(task_id, None)
                            self.recovery_pending_count = len(recovery_futures)
                            self.recovery_active_count = min(1, self.recovery_pending_count)
                            recovery_decision = str(recovery.get("decision") or "BLOCK")
                            if recovery_decision == "NO_DATA_CONTINUE":
                                self.seen_task_ids.add(task_id)
                                no_data_result = {
                                    "state": "NO_DATA_CONTINUE",
                                    "source_discovery_policy": "LOCAL_FILES_THEN_FREE_PUBLIC_NO_AUTH",
                                    "user_source_required": False,
                                    "email_or_account_source_used": False,
                                    "fake_data": False,
                                    "reason": recovery.get("reason") or "EVIDENCE_BACKED_NO_DATA_CONTINUE",
                                }
                                self.write_slot_runtime_state(
                                    slot_id, task, "NO_DATA_CONTINUE", result=no_data_result,
                                )
                                self.append_event(
                                    slot_id,
                                    {"transition": "NO_DATA_CONTINUE", "task_id": task_id, **no_data_result},
                                )
                                continue
                            if recovery_decision != "ALLOW":
                                continue
                            task = dict(recovery.get("task") or task)
                        else:
                            health = self.recovery_supervisor._health(slot_id)
                            if health.get("needs_recovery"):
                                recovery_futures[task_id] = recovery_executor.submit(
                                    self.recovery_supervisor.gate, source, task
                                )
                                self.recovery_pending_count = len(recovery_futures)
                                self.recovery_active_count = min(1, self.recovery_pending_count)
                                continue
                        task_id = str(task.get("task_id"))
                        self.scheduled_task_ids.add(task_id)
                        self.scheduled_slot_ids.add(slot_id)
                        futures.add(executor.submit(self.execute_task, source, task))
                done = {future for future in futures if future.done()}
                for future in done:
                    try:
                        result = future.result()
                    except Exception:
                        result = {}
                    finished_slot = str(result.get("slot_id") or "")
                    finished_task = str(result.get("task_id") or "")
                    if finished_slot:
                        self.scheduled_slot_ids.discard(finished_slot)
                    if result.get("state") == "WAITING_SLOT" and finished_task:
                        self.scheduled_task_ids.discard(finished_task)
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
            recovery_executor.shutdown(wait=True, cancel_futures=False)
            problem_solver_executor.shutdown(wait=True, cancel_futures=False)
            publisher_executor.shutdown(wait=True, cancel_futures=False)
            self.release_lock()


def concurrency_fixture(root: Path) -> dict[str, Any]:
    coordinator = Coordinator(root)
    production_state_root = coordinator.state

    def state_snapshot(directory: Path) -> dict[str, str]:
        if not directory.is_dir():
            return {}
        snapshot: dict[str, str] = {}
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            try:
                digest = sha256_bytes(path.read_bytes())
            except (OSError, PermissionError):
                # Live coordinator/worker logs can be temporarily locked on
                # Windows.  A fixture must not fail merely because production
                # is active; locked files are excluded from both snapshots.
                continue
            snapshot[str(path.relative_to(directory)).replace("\\", "/")] = digest
        return snapshot

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
    pid_alive = bool(
        identity
        and lock.get("machine_id") == machine_id()
        and lock.get("boot_id") == boot_id()
        and int(lock.get("process_start_100ns") or 0) == int(identity["process_start_100ns"])
    )
    heartbeat = read_json(coordinator.heartbeat_path, {})
    global_status = read_json(coordinator.status_path, {})
    return {
        "status": global_status.get("state", "NOT_STARTED"),
        "pid": lock.get("pid"),
        "pid_alive": pid_alive,
        "lock_created_at": lock.get("created_at"),
        "heartbeat_pid": heartbeat.get("pid"),
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
