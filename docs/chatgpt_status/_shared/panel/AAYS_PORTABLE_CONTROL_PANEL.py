# -*- coding: utf-8 -*-
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

PORTABLE_ROOT = Path(__file__).resolve().parent
BASE_URL = "http://127.0.0.1:8012"
MAIN_APP_URL = f"{BASE_URL}/england_map_web/index.html"
HEALTH_URL = f"{BASE_URL}/health"
RUNNER_PANEL_URL = f"{BASE_URL}/england_map_web/runner_panel.html"
OPENAPI_URL = f"{BASE_URL}/openapi.json"
DOCS_URL = f"{BASE_URL}/docs"
SOURCES_URL = f"{BASE_URL}/sources"
MATRIX_CONTROL_URL = f"{BASE_URL}/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable"
GEOMETRY_CONTROL_URL = f"{BASE_URL}/england_map_web/geometry_review_3of4_columns_1264.html?refresh=portable"

APP_SCRIPT = PORTABLE_ROOT / "START_TERRAYIELD_PORTABLE_8012.ps1"
RUNNER_SCRIPT = PORTABLE_ROOT / "START_AAYS_STABLE_RUNNER_FROM_PANEL.ps1"
RUNNER_CMD = PORTABLE_ROOT / "RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd"
CONTROL_SYNC_SCRIPT = PORTABLE_ROOT / "SYNC_AAYS_CONTROL_SITES_TO_PORTABLE_WEB.ps1"
RUNNER_REPO = PORTABLE_ROOT / "runner_system" / "AAYS_WT" / "AAYS_RUNNER_HEALTHY_20260707"
RUNNER_STATUS = RUNNER_REPO / "docs" / "chatgpt_status" / "_shared" / "status" / "runner_bootstrap_latest.json"
RUNNER_DAEMON_STATUS = RUNNER_REPO / "docs" / "chatgpt_status" / "_shared" / "status" / "stable_runner_daemon_latest.json"
RUNNER_LOCK = RUNNER_REPO / "docs" / "chatgpt_status" / "_shared" / "locks" / "single_runner.lock"
RUNNER_HEARTBEAT = RUNNER_REPO / "docs" / "chatgpt_status" / "_shared" / "heartbeat" / "stable_runner_daemon_heartbeat_latest.json"
RUNNER_SELF_TEST = RUNNER_REPO / "docs" / "chatgpt_status" / "_shared" / "runner_outputs" / "one_click_runner_self_test_latest.json"
SLOT_BOOTSTRAP_SCRIPT = PORTABLE_ROOT / "START_AAYS_5_SLOT_COORDINATOR.ps1"
SLOT_ROOT = RUNNER_REPO / "docs" / "chatgpt_status" / "_shared" / "slots"
SLOT_MANIFEST = SLOT_ROOT / "manifest_latest.json"
SLOT_IDS = (
    ("ready_to_sell", "ReadyToSell"),
    ("gas_emissions", "Gas Emissions"),
    ("height_difference", "Height Difference"),
    ("security_public_safety", "Security"),
    ("parcel_label", "Parcel Label"),
)
V2_LAUNCHER = PORTABLE_ROOT / "RUN_AAYS_ADAPTIVE_5_WORKER.ps1"
V2_STATE_ROOT = PORTABLE_ROOT / "state"
V2_STATUS = V2_STATE_ROOT / "coordinator_status_latest.json"
V2_HEARTBEAT = V2_STATE_ROOT / "coordinator_heartbeat_latest.json"
V2_LOCK = V2_STATE_ROOT / "coordinator.lock.json"
V2_SLOT_ROOT = V2_STATE_ROOT / "slots"
LOG_DIR = PORTABLE_ROOT / "logs"
LOG_FILE = LOG_DIR / "aays_portable_control_panel.log"
POWERSHELL = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

URLS = [
    ("Ana uygulama", MAIN_APP_URL),
    ("Health", HEALTH_URL),
    ("Runner panel", RUNNER_PANEL_URL),
    ("OpenAPI", OPENAPI_URL),
    ("API docs", DOCS_URL),
    ("Sources", SOURCES_URL),
    ("Parsel Katman Matrisi", MATRIX_CONTROL_URL),
    ("Geometri 3/4 Kontrol", GEOMETRY_CONTROL_URL),
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_http_ok(url: str, timeout: float = 2.5) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            code = getattr(response, "status", 0)
            return 200 <= int(code) < 500, f"HTTP {code}"
    except Exception as exc:
        return False, str(exc)


def pid_alive(pid: object) -> bool:
    try:
        pid_int = int(pid)
    except Exception:
        return False
    if pid_int <= 0:
        return False
    if os.name != "nt":
        return False
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid_int)
    if handle:
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    return False


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
    except Exception:
        return {}


def utc_age_seconds(value: object) -> float | None:
    try:
        stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - stamp.astimezone(timezone.utc)).total_seconds())
    except Exception:
        return None


class AaysPanel(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AAYS TerraYield Portable Panel - Sabit 8012")
        self.geometry("900x790")
        self.minsize(840, 720)
        self.configure(bg="#f4f6f8")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.status_var = tk.StringVar(value="Hazır")
        self.app_var = tk.StringVar(value="App: kontrol edilmedi")
        self.runner_var = tk.StringVar(value="Runner: kontrol edilmedi")
        self.path_var = tk.StringVar(value=f"Portable root: {PORTABLE_ROOT}")
        self.safe_remove_var = tk.StringVar(value="Güvenli disk çıkarma: kontrol edilmedi")
        self.slot_vars = {
            slot_id: tk.StringVar(value=f"{label}: kontrol edilmedi")
            for slot_id, label in SLOT_IDS
        }
        self.last_control_sync = 0.0
        self._build_ui()
        self.refresh_status()
        self.after(20000, self._auto_refresh)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", padding=8)
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), background="#f4f6f8")
        style.configure("Body.TLabel", font=("Segoe UI", 10), background="#f4f6f8")
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"), background="#f4f6f8")

        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="AAYS TerraYield Portable Kontrol Paneli", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Sabit ana URL: http://127.0.0.1:8012/england_map_web/index.html", style="Body.TLabel").pack(anchor="w", pady=(4, 12))

        actions = ttk.LabelFrame(root, text="Başlat ve Aç", padding=12)
        actions.pack(fill="x")
        grid = ttk.Frame(actions)
        grid.pack(fill="x")
        buttons = [
            ("Uygulamayı Başlat", self.start_app_only),
            ("Uygulamayı Aç", self.start_app_and_open),
            ("Tek Runner Başlat", self.start_runner),
            ("Runner'ı Durdur", self.stop_runner),
            ("Runner'ı Yeniden Başlat", self.restart_runner),
            ("Durumu Yenile", self.refresh_status),
        ]
        for idx, (label, command) in enumerate(buttons):
            ttk.Button(grid, text=label, command=command).grid(row=idx // 3, column=idx % 3, padx=4, pady=4, sticky="ew")
            grid.columnconfigure(idx % 3, weight=1)

        links = ttk.LabelFrame(root, text="Sabit Linkler", padding=12)
        links.pack(fill="x", pady=(12, 0))
        for row, (label, url) in enumerate(URLS):
            ttk.Button(links, text=label, command=lambda l=label, u=url: self.open_url(l, u)).grid(row=row // 3, column=row % 3, padx=4, pady=4, sticky="ew")
        for idx in range(3):
            links.columnconfigure(idx, weight=1)

        status = ttk.LabelFrame(root, text="Durum", padding=12)
        status.pack(fill="x", pady=(12, 0))
        ttk.Label(status, textvariable=self.app_var, style="Status.TLabel").pack(anchor="w")
        ttk.Label(status, textvariable=self.runner_var, style="Status.TLabel").pack(anchor="w", pady=(6, 0))
        ttk.Label(status, textvariable=self.path_var, style="Body.TLabel").pack(anchor="w", pady=(6, 0))
        ttk.Label(status, textvariable=self.safe_remove_var, style="Body.TLabel").pack(anchor="w", pady=(6, 0))
        ttk.Label(status, textvariable=self.status_var, style="Body.TLabel").pack(anchor="w", pady=(6, 0))

        slots = ttk.LabelFrame(root, text="5 Slot Durumu", padding=12)
        slots.pack(fill="x", pady=(12, 0))
        for slot_id, _label in SLOT_IDS:
            ttk.Label(slots, textvariable=self.slot_vars[slot_id], style="Body.TLabel").pack(anchor="w", pady=2)

        text_box = ttk.LabelFrame(root, text="Not", padding=12)
        text_box.pack(fill="both", expand=True, pady=(12, 0))
        note = (
            "Bu panel taşınabilir diskteki kendi kökünden çalışır. Bu bilgisayardaki masaüstü kısayolu yalnızca bu paneli açar. "
            "Başka bir Windows bilgisayarda diski takınca AAYS_PORTABLE_CONTROL_PANEL.cmd dosyasını taşınabilir kökten çalıştırın. "
            "Uygulama URL'si sabittir: 127.0.0.1:8012. Tek Runner Başlat düğmesi gerçek runner recovery ve GitHub smoke testini çalıştırır; sağlıklı runner varsa ikinci runner açmaz."
        )
        ttk.Label(text_box, text=note, style="Body.TLabel", wraplength=700, justify="left").pack(anchor="w")

    def log(self, message: str) -> None:
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(f"[{now_text()}] {message}\n")

    def run_powershell(self, script: Path, args: list[str] | None = None) -> subprocess.Popen | None:
        if not script.exists():
            self.set_status(f"Eksik script: {script}")
            return None
        args = args or []
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_handle = LOG_FILE.open("a", encoding="utf-8")
        cmd = [str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(script), *args]
        self.log("RUN " + " ".join(cmd))
        return subprocess.Popen(cmd, cwd=str(PORTABLE_ROOT), stdout=log_handle, stderr=subprocess.STDOUT, creationflags=CREATE_NO_WINDOW)

    def set_status(self, text: str) -> None:
        self.status_var.set(f"{now_text()} - {text}")
        self.log(text)



    def sync_control_sites_if_due(self, force: bool = False) -> None:
        now = time.time()
        if force or now - self.last_control_sync > 60:
            self.last_control_sync = now
            self.run_powershell(CONTROL_SYNC_SCRIPT, [])
    def open_url(self, label: str, url: str) -> None:
        if url in (MATRIX_CONTROL_URL, GEOMETRY_CONTROL_URL):
            self.set_status(f"Kontrol sitesi yenileniyor: {label}")
            self.sync_control_sites_if_due(force=True)
        webbrowser.open(url)
    def start_app_only(self) -> None:
        self.set_status("Uygulama 8012 baslatiliyor")
        self.run_powershell(APP_SCRIPT, ["-NoBrowser"])
        threading.Thread(target=self._wait_for_app, args=(False,), daemon=True).start()

    def start_app_and_open(self) -> None:
        self.set_status("Uygulama 8012 baslatiliyor ve ana link acilacak")
        self.run_powershell(APP_SCRIPT, ["-NoBrowser"])
        threading.Thread(target=self._wait_for_app, args=(True,), daemon=True).start()

    def _wait_for_app(self, open_after: bool) -> None:
        deadline = time.time() + 150
        last_msg = ""
        while time.time() < deadline:
            ok, msg = is_http_ok(HEALTH_URL, timeout=3)
            last_msg = msg
            if ok:
                self.after(0, lambda: self.app_var.set(f"App: AKTIF - {HEALTH_URL}"))
                self.after(0, lambda: self.set_status("Uygulama aktif"))
                if open_after:
                    webbrowser.open(MAIN_APP_URL)
                return
            time.sleep(3)
        self.after(0, lambda: self.app_var.set(f"App: KAPALI veya gec aciliyor - {last_msg}"))
        self.after(0, lambda: self.set_status("Uygulama 150 sn icinde saglikli yanit vermedi"))
        if open_after:
            webbrowser.open(MAIN_APP_URL)

    def start_runner(self) -> None:
        self.set_status("Tek runner recovery ve gerçek smoke testi başlatılıyor")
        process = self.run_powershell(V2_LAUNCHER, ["-Action", "Start"])
        if process is not None:
            threading.Thread(target=self._wait_for_runner_action, args=(process, "başlatıldı"), daemon=True).start()

    def stop_runner(self) -> None:
        self.set_status("Coordinator güvenli durdurma ve checkpoint flush başlatılıyor")
        process = self.run_powershell(V2_LAUNCHER, ["-Action", "Stop"])
        if process is not None:
            threading.Thread(target=self._wait_for_runner_action, args=(process, "durduruldu"), daemon=True).start()

    def restart_runner(self) -> None:
        self.set_status("Coordinator checkpointten yeniden başlatılıyor")
        process = self.run_powershell(V2_LAUNCHER, ["-Action", "Restart"])
        if process is not None:
            threading.Thread(target=self._wait_for_runner_action, args=(process, "yeniden başlatıldı"), daemon=True).start()

    def _wait_for_runner_action(self, process: subprocess.Popen, success_text: str) -> None:
        try:
            exit_code = process.wait(timeout=150)
        except subprocess.TimeoutExpired:
            self.after(0, lambda: self.set_status("Runner işlemi zaman aşımına uğradı; logu kontrol edin"))
            return
        if exit_code == 0:
            self.after(0, lambda: self.set_status(f"Coordinator {success_text}"))
        else:
            self.after(0, lambda: self.set_status(f"Runner işlemi başarısız (exit {exit_code})"))
        self.after(1000, self.refresh_status)

    def read_slot_info(self, slot_id: str) -> dict:
        status = read_json(V2_SLOT_ROOT / slot_id / "status_latest.json")
        heartbeat = read_json(V2_SLOT_ROOT / slot_id / "heartbeat_latest.json")
        checkpoint = read_json(V2_SLOT_ROOT / slot_id / "checkpoint_latest.json")
        current = read_json(V2_SLOT_ROOT / slot_id / "current_task_latest.json")
        valid = (
            status.get("workstream_id") == "AAYS_5_SLOT_SAFE_PARALLEL_V1"
            and status.get("slot_id") == slot_id
            and checkpoint.get("slot_id") == slot_id
        )
        age = utc_age_seconds(heartbeat.get("heartbeat_at"))
        live = age is not None and age <= int(heartbeat.get("stale_after_seconds") or 900)
        return {
            "valid": valid,
            "state": status.get("state", "missing"),
            "owner": current.get("attempt_id"),
            "task": current.get("task_id"),
            "step": checkpoint.get("first_unverified_step", "missing"),
            "heartbeat_live": live,
        }

    def refresh_slot_status(self) -> None:
        for slot_id, label in SLOT_IDS:
            info = self.read_slot_info(slot_id)
            if not info["valid"]:
                text = f"{label}: HAZIR DEGIL - slot dosyalari eksik veya kimlik uyusmuyor"
            else:
                owner = info["owner"] or "sahipsiz"
                task = info["task"] or "-"
                text = (
                    f"{label}: {info['state']} | owner {owner} | task {task} | "
                    f"next {info['step']}"
                )
            self.slot_vars[slot_id].set(text)

    def read_runner_info(self) -> dict:
        v2_status = read_json(V2_STATUS)
        v2_heartbeat = read_json(V2_HEARTBEAT)
        v2_lock = read_json(V2_LOCK)
        if v2_status or v2_lock:
            runner_pid = v2_lock.get("pid") or v2_status.get("coordinator_pid")
            heartbeat_age = utc_age_seconds(v2_heartbeat.get("heartbeat_at"))
            alive = pid_alive(runner_pid)
            fresh = heartbeat_age is not None and heartbeat_age <= 45
            return {
                "status": "HEALTHY" if alive and fresh else ("STALE" if alive else "FAILED"),
                "pid": runner_pid,
                "pid_alive": alive,
                "ready": alive and fresh,
                "heartbeat_age": heartbeat_age,
                "queue_scan_count": 0,
                "queue_ready_count": 0,
                "current_task_id": ", ".join(v2_status.get("active_tasks", {}).values()) or None,
                "active_workers": int(v2_status.get("active_workers") or 0),
                "max_child_workers": 5,
                "coordinator_state": v2_status.get("state", "NOT_STARTED"),
                "consecutive_failures": 0,
                "blocker": None,
            }
        bootstrap = read_json(RUNNER_STATUS)
        daemon = read_json(RUNNER_DAEMON_STATUS)
        lock = read_json(RUNNER_LOCK)
        heartbeat = read_json(RUNNER_HEARTBEAT)
        smoke = read_json(RUNNER_SELF_TEST)
        pid = lock.get("pid") or bootstrap.get("runner_pid")
        heartbeat_pid = heartbeat.get("daemon_pid")
        bootstrap_pid = bootstrap.get("runner_pid")
        age = utc_age_seconds(heartbeat.get("heartbeat_at"))
        alive = pid_alive(pid)
        aligned = bool(pid and int(pid) == int(heartbeat_pid or -1) == int(bootstrap_pid or -2))
        fresh = age is not None and age <= 180
        queue_age = utc_age_seconds(heartbeat.get("last_queue_scan_at"))
        queue_fresh = queue_age is not None and queue_age <= 900
        current_task_id = heartbeat.get("current_task_id")
        failures = int(heartbeat.get("consecutive_failures") or daemon.get("consecutive_failures") or 0)
        queue_active = queue_fresh or bool(current_task_id)
        healthy = alive and aligned and fresh and queue_active and failures == 0
        if healthy:
            status = "HEALTHY"
        elif alive and aligned and fresh:
            status = "DEGRADED"
        elif alive:
            status = "STALE"
        else:
            status = "FAILED"
        return {
            "status": status,
            "pid": pid,
            "pid_alive": alive,
            "ready": healthy,
            "pid_aligned": aligned,
            "heartbeat_fresh": fresh,
            "heartbeat_age": age,
            "queue_scan_fresh": queue_fresh,
            "queue_scan_age": queue_age,
            "queue_scan_count": heartbeat.get("last_queue_scan_count", 0),
            "queue_ready_count": heartbeat.get("last_queue_ready_count", 0),
            "current_task_id": current_task_id,
            "last_pickup_task_id": heartbeat.get("last_pickup_task_id"),
            "consecutive_failures": failures,
            "task_blocker_count": heartbeat.get("task_blocker_count", 0),
            "smoke_status": smoke.get("status", "not_run"),
            "smoke_push": smoke.get("git_push_status", "not_run"),
            "remote_readback": bool(smoke.get("remote_readback_ok")),
            "blocker": bootstrap.get("blocker"),
        }

    def refresh_status(self) -> None:
        ok, msg = is_http_ok(HEALTH_URL, timeout=2.5)
        if ok:
            self.app_var.set(f"App: AKTIF - {HEALTH_URL}")
        else:
            self.app_var.set(f"App: KAPALI - {msg}")
        info = self.read_runner_info()
        if info.get("ready"):
            age = int(info.get("heartbeat_age") or 0)
            self.runner_var.set(
                f"Runner: HEALTHY - PID {info.get('pid')} - heartbeat {age} sn - "
                f"workers {info.get('active_workers', 0)}/{info.get('max_child_workers', 5)} - "
                f"queue {info.get('queue_ready_count')}/{info.get('queue_scan_count')} - "
                f"aktif görev {info.get('current_task_id') or '-'}"
            )
        elif info.get("status") == "DEGRADED":
            self.runner_var.set(
                f"Runner: DEGRADED - PID {info.get('pid')} - hata {info.get('consecutive_failures')} - "
                f"queue yaşı {int(info.get('queue_scan_age') or 0)} sn - "
                f"aktif görev {info.get('current_task_id') or '-'}"
            )
        elif info.get("pid"):
            self.runner_var.set(
                f"Runner: STALE - PID {info.get('pid')} - PID eşleşmesi {info.get('pid_aligned')} - "
                f"heartbeat güncel {info.get('heartbeat_fresh')} - blocker {info.get('blocker') or 'health_mismatch'}"
            )
        else:
            self.runner_var.set(f"Runner: FAILED/KAPALI - {info.get('blocker') or info.get('status')}")
        if info.get("coordinator_state") == "STOPPED_CLEAN" and not info.get("pid_alive"):
            self.safe_remove_var.set("Güvenli disk çıkarma: EVET")
        else:
            self.safe_remove_var.set("Güvenli disk çıkarma: HAYIR - önce Runner'ı Durdur")
        self.refresh_slot_status()
        self.set_status("Durum yenilendi")

    def _auto_refresh(self) -> None:
        self.refresh_status()
        self.after(20000, self._auto_refresh)


def main() -> None:
    try:
        app = AaysPanel()
        app.mainloop()
    except Exception as exc:
        messagebox.showerror("AAYS panel hata", str(exc))
        raise


if __name__ == "__main__":
    main()





