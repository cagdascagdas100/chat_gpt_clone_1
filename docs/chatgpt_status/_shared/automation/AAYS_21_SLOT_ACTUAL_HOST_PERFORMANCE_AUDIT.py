from __future__ import annotations

import concurrent.futures
import hashlib
import importlib.util
import json
import os
import statistics
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil


ROOT = Path(__file__).resolve().parents[7]
COORDINATOR_PATH = ROOT / "AAYS_ADAPTIVE_15_WORKER_COORDINATOR.py"
AUDIT_PATH = ROOT / "runtime" / "adaptive_v2" / "audits" / "AAYS_21_SLOT_ACTUAL_HOST_PERFORMANCE_20260720.json"
STATE_SLOTS = ROOT / "state" / "slots"
PUBLISHER_SLOTS = ROOT / "runner_system" / "adaptive_v2" / "publisher" / "docs" / "chatgpt_status" / "slots_21"
HEARTBEAT_PATH = ROOT / "state" / "coordinator_heartbeat_latest.json"
STATUS_PATH = ROOT / "state" / "coordinator_status_latest.json"
APP_URL = "http://127.0.0.1:8012/england_map_web/index.html"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def snapshot(directory: Path) -> dict[str, str]:
    if not directory.is_dir():
        return {}
    result: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            relative = str(path.relative_to(directory)).replace("\\", "/")
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def changed(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(
        name
        for name in set(before) | set(after)
        if before.get(name) != after.get(name)
    )


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def import_coordinator() -> Any:
    spec = importlib.util.spec_from_file_location("aays_coordinator_for_host_audit", COORDINATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("COORDINATOR_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    started_at = utc_now()
    started_clock = time.perf_counter()
    module = import_coordinator()
    memory_gb = module.total_memory_gb()
    logical_cpus = os.cpu_count() or 1
    profile, limits, max_workers = module.select_resource_profile(memory_gb, logical_cpus)
    resources = module.ResourceManager(limits)

    state_before = snapshot(STATE_SLOTS)
    publisher_before = snapshot(PUBLISHER_SLOTS)
    heartbeat_before = load_json(HEARTBEAT_PATH)
    status_before = load_json(STATUS_PATH)
    coordinator_pid = int(status_before.get("coordinator_pid") or status_before.get("pid") or 0)

    samples: list[dict[str, float]] = []
    monitor_stop = threading.Event()

    def monitor() -> None:
        psutil.cpu_percent(interval=None)
        while not monitor_stop.wait(0.2):
            memory = psutil.virtual_memory()
            samples.append(
                {
                    "cpu_percent": float(psutil.cpu_percent(interval=None)),
                    "memory_percent": float(memory.percent),
                    "available_memory_gb": round(memory.available / (1024**3), 3),
                }
            )

    monitor_thread = threading.Thread(target=monitor, name="aays-host-monitor", daemon=True)
    monitor_thread.start()

    light_active = 0
    light_peak = 0
    light_lock = threading.Lock()
    light_barrier = threading.Barrier(21)
    probe_bytes = (STATUS_PATH.read_bytes() if STATUS_PATH.is_file() else b"status") * 128

    def light_task(index: int) -> dict[str, Any]:
        nonlocal light_active, light_peak
        light_barrier.wait(timeout=30)
        queued_at = time.perf_counter()
        with resources.acquire(["light_read"]):
            acquired_at = time.perf_counter()
            with light_lock:
                light_active += 1
                light_peak = max(light_peak, light_active)
            digest = probe_bytes
            for _ in range(250):
                digest = hashlib.sha256(digest).digest()
            time.sleep(0.65)
            with light_lock:
                light_active -= 1
        return {
            "slot_index": index,
            "state": "PASS",
            "queue_wait_ms": round((acquired_at - queued_at) * 1000, 3),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=21) as pool:
        light_results = list(pool.map(light_task, range(1, 22)))

    def bounded_peak(resource_name: str, count: int, workload: str) -> int:
        active = 0
        peak = 0
        lock = threading.Lock()
        barrier = threading.Barrier(count)

        def task(_: int) -> None:
            nonlocal active, peak
            barrier.wait(timeout=30)
            with resources.acquire([resource_name]):
                with lock:
                    active += 1
                    peak = max(peak, active)
                if workload == "cpu":
                    block = b"AAYS" * (1024 * 1024)
                    for _iteration in range(48):
                        hashlib.sha256(block).digest()
                elif workload == "ram":
                    allocation = bytearray(32 * 1024 * 1024)
                    for offset in range(0, len(allocation), 4096):
                        allocation[offset] = 1
                    time.sleep(0.35)
                with lock:
                    active -= 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
            list(pool.map(task, range(count)))
        return peak

    cpu_peak = bounded_peak("cpu_heavy", 6, "cpu")
    ram_peak = bounded_peak("ram_heavy", 4, "ram")

    def http_probe(index: int) -> dict[str, Any]:
        target = f"{APP_URL}?aays_host_audit={index}"
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(target, timeout=5) as response:
                body = response.read(1024)
                return {
                    "ok": response.status == 200 and bool(body),
                    "status": response.status,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                    "error": None,
                }
        except Exception as exc:  # noqa: BLE001 - audit must record every network failure
            return {
                "ok": False,
                "status": None,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "error": f"{type(exc).__name__}: {exc}",
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        http_results = list(pool.map(http_probe, range(60)))

    heartbeat_deadline = time.time() + 30
    heartbeat_after = load_json(HEARTBEAT_PATH)
    while heartbeat_after.get("heartbeat_at") == heartbeat_before.get("heartbeat_at") and time.time() < heartbeat_deadline:
        time.sleep(1)
        heartbeat_after = load_json(HEARTBEAT_PATH)

    monitor_stop.set()
    monitor_thread.join(timeout=2)

    status_after = load_json(STATUS_PATH)
    state_after = snapshot(STATE_SLOTS)
    publisher_after = snapshot(PUBLISHER_SLOTS)
    state_changes = changed(state_before, state_after)
    publisher_changes = changed(publisher_before, publisher_after)
    http_latencies = [float(item["latency_ms"]) for item in http_results]
    http_failures = [item for item in http_results if not item["ok"]]
    queue_waits = [float(item["queue_wait_ms"]) for item in light_results]

    coordinator_pid_after = int(status_after.get("coordinator_pid") or status_after.get("pid") or 0)
    coordinator_state_after = status_after.get("state") or status_after.get("status")
    coordinator_stable = (
        coordinator_pid > 0
        and coordinator_pid_after == coordinator_pid
        and coordinator_state_after == "RUNNING"
        and psutil.pid_exists(coordinator_pid)
    )
    heartbeat_advanced = heartbeat_after.get("heartbeat_at") != heartbeat_before.get("heartbeat_at")

    checks = {
        "actual_host_profile_selected": profile == "balanced_16gb" and max_workers == 15,
        "all_21_logical_slot_tasks_executed": len(light_results) == 21 and all(item["state"] == "PASS" for item in light_results),
        "actual_light_read_limit_observed": light_peak == min(limits["light_read"], 21),
        "cpu_heavy_limit_observed": cpu_peak == min(limits["cpu_heavy"], 6),
        "ram_heavy_limit_observed": ram_peak == min(limits["ram_heavy"], 4),
        "http_60_of_60_ok": len(http_results) == 60 and not http_failures,
        "coordinator_pid_stable": coordinator_stable,
        "coordinator_heartbeat_advanced": heartbeat_advanced,
        "production_slot_state_untouched": not state_changes,
        "publisher_slot_contracts_untouched": not publisher_changes,
    }

    report = {
        "status": "PASS_WITH_PHYSICAL_TEST_LIMITATIONS" if all(checks.values()) else "FAIL",
        "started_at": started_at,
        "completed_at": utc_now(),
        "duration_seconds": round(time.perf_counter() - started_clock, 3),
        "portable_root": str(ROOT),
        "checks": checks,
        "actual_host": {
            "total_memory_gb": memory_gb,
            "logical_cpus": logical_cpus,
            "resource_profile": profile,
            "logical_slots": 21,
            "max_child_workers": max_workers,
            "resource_limits": limits,
        },
        "light_slot_test": {
            "tasks_executed": len(light_results),
            "max_simultaneous_running": light_peak,
            "queue_wait_ms_median": round(statistics.median(queue_waits), 3),
            "queue_wait_ms_p95": round(percentile(queue_waits, 0.95), 3),
            "results": light_results,
        },
        "bounded_workloads": {
            "cpu_heavy_peak": cpu_peak,
            "cpu_heavy_limit": limits["cpu_heavy"],
            "ram_heavy_peak": ram_peak,
            "ram_heavy_limit": limits["ram_heavy"],
        },
        "system_samples": {
            "count": len(samples),
            "cpu_percent_peak": max((sample["cpu_percent"] for sample in samples), default=0.0),
            "cpu_percent_average": round(statistics.mean((sample["cpu_percent"] for sample in samples)), 3) if samples else 0.0,
            "available_memory_gb_min": min((sample["available_memory_gb"] for sample in samples), default=0.0),
            "memory_percent_peak": max((sample["memory_percent"] for sample in samples), default=0.0),
        },
        "http_test": {
            "url": APP_URL,
            "requests": len(http_results),
            "successes": len(http_results) - len(http_failures),
            "failures": len(http_failures),
            "latency_ms_median": round(statistics.median(http_latencies), 3),
            "latency_ms_p95": round(percentile(http_latencies, 0.95), 3),
            "latency_ms_max": round(max(http_latencies), 3),
            "failure_details": http_failures,
        },
        "coordinator": {
            "pid_before": coordinator_pid,
            "pid_after": coordinator_pid_after,
            "heartbeat_before": heartbeat_before.get("heartbeat_at"),
            "heartbeat_after": heartbeat_after.get("heartbeat_at"),
            "active_workers_after": status_after.get("active_workers"),
        },
        "production_slot_state_files_changed": state_changes,
        "publisher_slot_contract_files_changed": publisher_changes,
        "actual_chatgpt_messages_sent": 0,
        "actual_business_tasks_executed": 0,
        "business_files_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "physical_reboot_sleep_disk_disconnect_tests": "NOT_RUN_WITHOUT_EXPLICIT_PERMISSION",
        "final_ready": False,
    }

    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
