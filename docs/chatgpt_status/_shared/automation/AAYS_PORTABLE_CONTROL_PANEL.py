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
APP_START_ARGS = ["-NoBrowser"]
if not APP_SCRIPT.is_file():
    APP_SCRIPT = PORTABLE_ROOT / "AAYS_TERRAYIELD_PORTABLE_BASE.ps1"
    APP_START_ARGS = ["-Mode", "Local", "-ApiPort", "8012", "-NoBrowser"]
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
    ("ready_to_sell_1", "ReadyToSell 1"),
    ("ready_to_sell_2", "ReadyToSell 2"),
    ("ready_to_sell_3", "ReadyToSell 3"),
    ("gas_emissions_1", "Gas Emissions 1"),
    ("gas_emissions_2", "Gas Emissions 2"),
    ("gas_emissions_3", "Gas Emissions 3"),
    ("height_difference_1", "Height Difference 1"),
    ("height_difference_2", "Height Difference 2"),
    ("height_difference_3", "Height Difference 3"),
    ("security_public_safety_1", "Security 1"),
    ("security_public_safety_2", "Security 2"),
    ("security_public_safety_3", "Security 3"),
    ("parcel_label_1", "Parcel Label 1"),
    ("parcel_label_2", "Parcel Label 2"),
    ("parcel_label_3", "Parcel Label 3"),
    ("internet_access_1", "Internet Access 1"),
    ("internet_access_2", "Internet Access 2"),
    ("internet_access_3", "Internet Access 3"),
    ("future_growth_1", "Future Growth 1"),
    ("future_growth_2", "Future Growth 2"),
    ("future_growth_3", "Future Growth 3"),
)
V2_LAUNCHER = PORTABLE_ROOT / "RUN_AAYS_ADAPTIVE_21_SLOT.ps1"
if not V2_LAUNCHER.is_file():
    V2_LAUNCHER = PORTABLE_ROOT / "RUN_AAYS_ADAPTIVE_15_WORKER.ps1"
KEEPALIVE_LAUNCHER = PORTABLE_ROOT / "START_AAYS_RUNNER_KEEPALIVE.ps1"
V2_STATE_ROOT = PORTABLE_ROOT / "state"
V2_STATUS = V2_STATE_ROOT / "coordinator_status_latest.json"
V2_HEARTBEAT = V2_STATE_ROOT / "coordinator_heartbeat_latest.json"
V2_LOCK = V2_STATE_ROOT / "coordinator.lock.json"
V2_PREFLIGHT = V2_STATE_ROOT / "portable_preflight_latest.json"
REMOTE_CHECK_SCRIPT = PORTABLE_ROOT / "CHECK_AAYS_REMOTE_ACCESS.ps1"
REMOTE_GUIDE = PORTABLE_ROOT / "AAYS_REMOTE_ACCESS_SETUP_TR.md"
REMOTE_STATUS = V2_STATE_ROOT / "remote_access_preflight_latest.json"
V2_SLOT_ROOT = V2_STATE_ROOT / "slots"
V2_RECOVERY_ROOT = V2_STATE_ROOT / "recovery"
PUBLISHER_REPO = PORTABLE_ROOT / "runner_system" / "adaptive_v2" / "publisher"
PUBLISHER_SHARED = PUBLISHER_REPO / "docs" / "chatgpt_status" / "_shared"
CONTINUE_TEST_STATUS = PUBLISHER_SHARED / "status" / "AAYS_21_PAGE_CONTINUE_DRY_RUN_latest.json"
AI_PHOTO_TEST_STATUS = PUBLISHER_SHARED / "status" / "AAYS_AI_PHOTO_EVIDENCE_AUDIT_latest.json"
BROWSER_TEST_STATUS = PUBLISHER_SHARED / "status" / "AAYS_18_SLOT_AI_BROWSER_SMOKE_latest.json"
DATA_QUALITY_TEST_STATUS = PUBLISHER_SHARED / "status" / "AAYS_18_SLOT_DATA_QUALITY_RECHECK_latest.json"
COMBINED_TEST_STATUS = PUBLISHER_SHARED / "status" / "AAYS_21_PAGE_CONTINUE_AND_AI_PHOTO_TEST_latest.json"
if not COMBINED_TEST_STATUS.is_file():
    COMBINED_TEST_STATUS = PUBLISHER_SHARED / "status" / "AAYS_18_PAGE_CONTINUE_AND_AI_PHOTO_TEST_latest.json"
REMOTE_SLOT_ROOT = PUBLISHER_SHARED / "slots_21"
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
            code = int(getattr(response, "status", 0))
            body = response.read().decode("utf-8", errors="replace")
            if code != 200:
                return False, f"HTTP {code}"
            if url == HEALTH_URL:
                payload = json.loads(body)
                valid = payload.get("status") == "ok" and payload.get("app") == "TerraYield Land Intelligence"
                return valid, "HTTP 200 TerraYield" if valid else "HTTP 200 fakat TerraYield sağlık yanıtı değil"
            return True, "HTTP 200"
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
        self.geometry("1100x1030")
        self.minsize(900, 760)
        self.configure(bg="#f4f6f8")
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.status_var = tk.StringVar(value="Hazır")
        self.app_var = tk.StringVar(value="App: kontrol edilmedi")
        self.runner_var = tk.StringVar(value="Runner: kontrol edilmedi")
        self.path_var = tk.StringVar(value=f"Portable root: {PORTABLE_ROOT}")
        self.safe_remove_var = tk.StringVar(value="Güvenli disk çıkarma: kontrol edilmedi")
        self.machine_var = tk.StringVar(value="Bilgisayar profili: ön kontrol yapılmadı")
        self.remote_var = tk.StringVar(value="Uzaktan erişim: kontrol edilmedi")
        self.data_scope_var = tk.StringVar(value="Veri kapsamı: kontrol edilmedi")
        self.continue_test_var = tk.StringVar(value="21 sayfa devam testi: kontrol edilmedi")
        self.layer_test_var = tk.StringVar(value="Katman testi: kontrol edilmedi")
        self.ai_test_var = tk.StringVar(value="AI fotoğraf testi: kontrol edilmedi")
        self.browser_test_var = tk.StringVar(value="Tarayıcı testi: kontrol edilmedi")
        self.test_blocker_var = tk.StringVar(value="Test blockerları: kontrol edilmedi")
        self.slot_vars = {
            slot_id: tk.StringVar(value=f"{label}: kontrol edilmedi")
            for slot_id, label in SLOT_IDS
        }
        self.wrap_labels: list[ttk.Label] = []
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

        viewport = ttk.Frame(self)
        viewport.pack(fill="both", expand=True)
        self.scroll_canvas = tk.Canvas(viewport, background="#f4f6f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(viewport, orient="vertical", command=self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        root = ttk.Frame(self.scroll_canvas, padding=16)
        self.scroll_window = self.scroll_canvas.create_window((0, 0), window=root, anchor="nw")
        root.bind("<Configure>", lambda _event: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))
        self.scroll_canvas.bind("<Configure>", self._resize_scroll_content)
        self.bind_all("<MouseWheel>", self._on_mousewheel)

        ttk.Label(root, text="AAYS TerraYield Portable Kontrol Paneli", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Sabit ana URL: http://127.0.0.1:8012/england_map_web/index.html", style="Body.TLabel").pack(anchor="w", pady=(4, 12))

        actions = ttk.LabelFrame(root, text="Başlat ve Aç", padding=12)
        actions.pack(fill="x")
        grid = ttk.Frame(actions)
        grid.pack(fill="x")
        buttons = [
            ("Uygulama + 21 Slot Başlat", self.start_all),
            ("Yeni PC Ön Kontrol", self.run_preflight),
            ("Uygulamayı Aç", self.start_app_and_open),
            ("Uygulamayı Başlat", self.start_app_only),
            ("21 Slot Runner Başlat", self.start_runner),
            ("Runner'ı Durdur", self.stop_runner),
            ("Runner'ı Yeniden Başlat", self.restart_runner),
            ("Uzaktan Erişim Kontrol", self.check_remote_access),
            ("Uzaktan Erişim Rehberi", self.open_remote_guide),
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
        for index, (variable, style) in enumerate((
            (self.app_var, "Status.TLabel"),
            (self.runner_var, "Status.TLabel"),
            (self.path_var, "Body.TLabel"),
            (self.machine_var, "Body.TLabel"),
            (self.remote_var, "Body.TLabel"),
            (self.data_scope_var, "Body.TLabel"),
            (self.safe_remove_var, "Body.TLabel"),
            (self.status_var, "Body.TLabel"),
        )):
            label = ttk.Label(status, textvariable=variable, style=style, justify="left")
            label.pack(fill="x", anchor="w", pady=(0 if index == 0 else 6, 0))
            self.wrap_labels.append(label)

        tests = ttk.LabelFrame(root, text="Son 21 Slot + AI/Fotoğraf Testleri", padding=12)
        tests.pack(fill="x", pady=(12, 0))
        for variable in (
            self.continue_test_var,
            self.layer_test_var,
            self.ai_test_var,
            self.browser_test_var,
            self.test_blocker_var,
        ):
            label = ttk.Label(tests, textvariable=variable, style="Body.TLabel", justify="left")
            label.pack(fill="x", anchor="w", pady=2)
            self.wrap_labels.append(label)

        slots = ttk.LabelFrame(root, text="21 Slot Canlı Durumu", padding=12)
        slots.pack(fill="x", pady=(12, 0))
        for slot_id, _label in SLOT_IDS:
            label = ttk.Label(
                slots,
                textvariable=self.slot_vars[slot_id],
                style="Body.TLabel",
                justify="left",
            )
            label.pack(fill="x", anchor="w", pady=3)
            self.wrap_labels.append(label)

        text_box = ttk.LabelFrame(root, text="Not", padding=12)
        text_box.pack(fill="x", pady=(12, 0))
        note = (
            "Bu panel taşınabilir diskteki kendi kökünden çalışır. Bu bilgisayardaki masaüstü kısayolu yalnızca bu paneli açar. "
            "Başka bir Windows bilgisayarda diski takınca AAYS_PORTABLE_CONTROL_PANEL.cmd dosyasını taşınabilir kökten çalıştırın. Önce Yeni PC Ön Kontrol, sonra Uygulama + 21 Slot Başlat düğmesini kullanın. "
            "Uygulama URL'si sabittir: 127.0.0.1:8012. 21 Slot Runner Başlat düğmesi tek koordinatörü çalıştırır; RAM'e göre sınırlı sayıda görevi aynı anda yürütür ve ikinci koordinatör açmaz."
        )
        note_label = ttk.Label(text_box, text=note, style="Body.TLabel", justify="left")
        note_label.pack(fill="x", anchor="w")
        self.wrap_labels.append(note_label)

    def _resize_scroll_content(self, event: tk.Event) -> None:
        self.scroll_canvas.itemconfigure(self.scroll_window, width=event.width)
        wraplength = max(640, int(event.width) - 90)
        for label in self.wrap_labels:
            label.configure(wraplength=wraplength)

    def _on_mousewheel(self, event: tk.Event) -> None:
        delta = int(-event.delta / 120) if event.delta else 0
        if delta:
            self.scroll_canvas.yview_scroll(delta, "units")

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
    def check_remote_access(self) -> None:
        self.set_status("Chrome Remote Desktop, Tailscale ve 8012 erişimi kontrol ediliyor")
        process = self.run_powershell(REMOTE_CHECK_SCRIPT, [])
        if process is not None:
            threading.Thread(target=self._wait_for_runner_action, args=(process, "uzaktan erişim kontrolü tamamlandı"), daemon=True).start()

    def open_remote_guide(self) -> None:
        if REMOTE_GUIDE.exists():
            os.startfile(str(REMOTE_GUIDE))
            self.set_status("Uzaktan erişim rehberi açıldı")
        else:
            self.set_status(f"Eksik rehber: {REMOTE_GUIDE}")

    def start_all(self) -> None:
        self.set_status("Uygulama ve tek koordinatör içindeki 21 slot başlatılıyor")
        self.run_powershell(APP_SCRIPT, list(APP_START_ARGS))
        launcher = KEEPALIVE_LAUNCHER if KEEPALIVE_LAUNCHER.is_file() else V2_LAUNCHER
        args = [] if launcher == KEEPALIVE_LAUNCHER else ["-Action", "Start"]
        process = self.run_powershell(launcher, args)
        threading.Thread(target=self._wait_for_app, args=(True,), daemon=True).start()
        if process is not None:
            threading.Thread(target=self._wait_for_runner_action, args=(process, "başlatıldı"), daemon=True).start()

    def run_preflight(self) -> None:
        self.set_status("Yeni bilgisayar için Python, Git, repo, disk ve kaynak kontrolü yapılıyor")
        process = self.run_powershell(V2_LAUNCHER, ["-Action", "Preflight"])
        if process is not None:
            threading.Thread(target=self._wait_for_runner_action, args=(process, "ön kontrolden geçti"), daemon=True).start()

    def start_app_only(self) -> None:
        self.set_status("Uygulama 8012 baslatiliyor")
        self.run_powershell(APP_SCRIPT, list(APP_START_ARGS))
        threading.Thread(target=self._wait_for_app, args=(False,), daemon=True).start()

    def start_app_and_open(self) -> None:
        self.set_status("Uygulama 8012 baslatiliyor ve ana link acilacak")
        self.run_powershell(APP_SCRIPT, list(APP_START_ARGS))
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
        launcher = KEEPALIVE_LAUNCHER if KEEPALIVE_LAUNCHER.is_file() else V2_LAUNCHER
        args = [] if launcher == KEEPALIVE_LAUNCHER else ["-Action", "Start"]
        process = self.run_powershell(launcher, args)
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
        remote_status = read_json(REMOTE_SLOT_ROOT / slot_id / "status_latest.json")
        recovery = read_json(V2_RECOVERY_ROOT / "slots" / slot_id / "latest.json")
        valid = (
            status.get("workstream_id") == "AAYS_21_SLOT_SAFE_PARALLEL_V1"
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
            "heartbeat_age": age,
            "partition": checkpoint.get("parcel_partition") or status.get("parcel_partition") or {},
            "blocker": status.get("blocker") or current.get("blocker") or remote_status.get("blocker"),
            "recovery_state": recovery.get("state"),
            "recovery_reason": recovery.get("repair_reason") or recovery.get("blocker"),
            "recovery_wait_until": recovery.get("wait_until"),
        }

    def refresh_slot_status(self) -> None:
        for slot_id, label in SLOT_IDS:
            info = self.read_slot_info(slot_id)
            if not info["valid"]:
                text = f"{label} [{slot_id}]: HAZIR DEĞİL - slot dosyaları eksik veya kimlik uyuşmuyor"
            else:
                owner = info["owner"] or "sahipsiz"
                task = info["task"] or "-"
                partition = info.get("partition") or {}
                start = int(partition.get("start") or 0)
                end = int(partition.get("end") or 0)
                partition_text = (
                    f"{start:,}-{end:,}".replace(",", ".") if start and end else "bilinmiyor"
                )
                age = info.get("heartbeat_age")
                if task != "-":
                    heartbeat_text = f"{int(age)} sn" if info.get("heartbeat_live") and age is not None else "STALE/YOK"
                else:
                    heartbeat_text = "aktif görev yok"
                raw_state = str(info["state"])
                recovery_state = str(info.get("recovery_state") or "")
                display_state = raw_state
                if raw_state.upper().startswith("BLOCKED"):
                    if recovery_state == "RECOVERY_WAITING":
                        display_state = "KURTARILIYOR (eski kayıt BLOCKED)"
                    elif recovery_state == "RECOVERY_SUCCEEDED":
                        display_state = "GÜVENLİ YENİDEN DENEMEDE (eski kayıt BLOCKED)"
                    elif recovery_state == "RECOVERY_PARKED":
                        display_state = "GERÇEK KAYNAK/ELLE MÜDAHALE BEKLİYOR"
                    else:
                        display_state = "PROAKTİF KURTARMA TARAMASI BEKLİYOR"
                text = (
                    f"{label} [{slot_id}]: {display_state} | aralık {partition_text} | "
                    f"owner {owner} | görev {task} | heartbeat {heartbeat_text} | "
                    f"sıradaki {info['step']} | blocker {info.get('blocker') or 'yok'} | "
                    f"otomatik kurtarma {info.get('recovery_state') or 'tetik bekliyor'}"
                )
            self.slot_vars[slot_id].set(text)

    def refresh_test_status(self) -> None:
        combined = read_json(COMBINED_TEST_STATUS)
        continue_test = read_json(CONTINUE_TEST_STATUS)
        layer_test = read_json(DATA_QUALITY_TEST_STATUS)
        ai_test = read_json(AI_PHOTO_TEST_STATUS)
        browser_test = read_json(BROWSER_TEST_STATUS)

        if continue_test:
            self.continue_test_var.set(
                f"21 sayfa devam testi: {continue_test.get('status', 'bilinmiyor')} - "
                f"doğru slot {continue_test.get('valid_continue_contracts', 0)}/21 - "
                f"yanlış slot engeli {continue_test.get('wrong_slot_blocked_count', 0)}/21 - "
                f"business yazımı {continue_test.get('business_files_written', 0)}"
            )
        else:
            self.continue_test_var.set("21 sayfa devam testi: kanıt dosyası bulunamadı")

        topics = layer_test.get("topics", {}) if layer_test else {}
        layer_text = (
            f"Katman bütünlüğü: {layer_test.get('status', 'kanıt yok') if layer_test else 'kanıt yok'} - "
            f"distance {topics.get('distance-property-types', {}).get('actual_feature_count', 0)} - "
            f"topography {topics.get('topography', {}).get('actual_feature_count', 0):,} - "
            f"gas {topics.get('gas-emissions', {}).get('actual_feature_count', 0):,} - "
            f"security {topics.get('security', {}).get('actual_feature_count', 0):,} - "
            f"internet {topics.get('internet', {}).get('actual_feature_count', 0):,}"
        )
        self.layer_test_var.set(layer_text.replace(",", "."))

        if ai_test:
            self.ai_test_var.set(
                f"AI fotoğraf kanıtı: {ai_test.get('status', 'bilinmiyor')} - "
                f"geometri {ai_test.get('geometry_features', 0)} - sonuç {ai_test.get('result_rows', 0)}/"
                f"{ai_test.get('rows_total_declared', 0)} - fotoğraf decode "
                f"{ai_test.get('photo_files_decoded', 0)}/{ai_test.get('unique_photo_files_referenced', 0)} - "
                f"poligon {ai_test.get('unique_polygon_files_referenced', 0)} - "
                f"manifest {ai_test.get('parsed_manifest_files', 0)} - visual skor "
                f"{ai_test.get('visual_match_score_rows', 0)}"
            )
        else:
            self.ai_test_var.set("AI fotoğraf kanıtı: kanıt dosyası bulunamadı")

        checks = browser_test.get("checks", {}) if browser_test else {}
        browser_pass = sum(value is True for value in checks.values())
        self.browser_test_var.set(
            f"Tarayıcı testi: {browser_test.get('status', 'kanıt yok') if browser_test else 'kanıt yok'} - "
            f"kontrol {browser_pass}/{len(checks)} - load "
            f"{browser_test.get('dom', {}).get('loadState', 'bilinmiyor') if browser_test else 'bilinmiyor'} - "
            f"mod {browser_test.get('dom', {}).get('loadMode', 'bilinmiyor') if browser_test else 'bilinmiyor'} - "
            f"foto linki {'AÇILIYOR' if checks.get('firstPhotoHttpImage') else 'SORUNLU'} - WEBP image/webp"
        )

        blockers = combined.get("blockers", []) if combined else []
        self.test_blocker_var.set(
            "Gerçek kalanlar: " + (" | ".join(map(str, blockers)) if blockers else "blocker yok")
        )

    def read_runner_info(self) -> dict:
        v2_status = read_json(V2_STATUS)
        v2_heartbeat = read_json(V2_HEARTBEAT)
        v2_lock = read_json(V2_LOCK)
        if v2_status or v2_lock:
            recovery_summary = v2_status.get("automatic_recovery") or read_json(
                V2_RECOVERY_ROOT / "summary_latest.json"
            )
            recovery_states = recovery_summary.get("slot_states", {}) if recovery_summary else {}
            recovery_waiting = sum(
                1 for value in recovery_states.values()
                if str(value.get("state") or "").upper() == "RECOVERY_WAITING"
            )
            recovery_succeeded = sum(
                1 for value in recovery_states.values()
                if str(value.get("state") or "").upper() == "RECOVERY_SUCCEEDED"
            )
            recovery_parked = sum(
                1 for value in recovery_states.values()
                if str(value.get("state") or "").upper() == "RECOVERY_PARKED"
            )
            remote_recent_count = 0
            remote_waiting_count = 0
            remote_blocked_count = 0
            remote_ages = []
            for slot_id, _label in SLOT_IDS:
                remote_status = read_json(REMOTE_SLOT_ROOT / slot_id / "status_latest.json")
                if not remote_status:
                    continue
                remote_age = utc_age_seconds(remote_status.get("updated_at"))
                if remote_age is not None:
                    remote_ages.append(remote_age)
                if remote_age is not None and remote_age <= 900:
                    remote_recent_count += 1
                remote_state = str(remote_status.get("state") or "").casefold()
                if any(word in remote_state for word in ("pending", "queued", "claim", "ready_for_claim")):
                    remote_waiting_count += 1
                if "blocked" in remote_state or bool(remote_status.get("blocker")):
                    remote_blocked_count += 1
            runner_pid = v2_lock.get("pid") or v2_status.get("coordinator_pid")
            pid_values = [
                int(value)
                for value in (
                    v2_lock.get("pid"),
                    v2_status.get("coordinator_pid"),
                    v2_heartbeat.get("pid"),
                )
                if value is not None
            ]
            aligned = bool(pid_values) and len(set(pid_values)) == 1
            heartbeat_age = utc_age_seconds(v2_heartbeat.get("heartbeat_at"))
            alive = pid_alive(runner_pid)
            fresh = heartbeat_age is not None and heartbeat_age <= 45
            return {
                "status": "HEALTHY" if alive and fresh and aligned else ("STALE" if alive else "FAILED"),
                "pid": runner_pid,
                "pid_alive": alive,
                "ready": alive and fresh and aligned,
                "pid_aligned": aligned,
                "heartbeat_fresh": fresh,
                "heartbeat_age": heartbeat_age,
                "queue_scan_count": int(v2_status.get("queue_scan_count") or 0),
                "queue_ready_count": int(v2_status.get("queue_ready_count") or 0),
                "publish_pending_count": int(v2_status.get("publish_pending_count") or 0),
                "blocked_slot_count": int(v2_status.get("blocked_slot_count") or 0),
                "remote_recent_count": remote_recent_count,
                "remote_waiting_count": remote_waiting_count,
                "remote_blocked_count": remote_blocked_count,
                "remote_latest_age": min(remote_ages) if remote_ages else None,
                "current_task_id": ", ".join(v2_status.get("active_tasks", {}).values()) or None,
                "active_workers": int(v2_status.get("active_workers") or 0),
                "max_child_workers": int(v2_status.get("max_child_workers") or 15),
                "available_worker_capacity": int(
                    v2_status.get("available_worker_capacity") or v2_status.get("max_child_workers") or 15
                ),
                "logical_slot_count": int(v2_status.get("logical_slot_count") or 21),
                "coordinator_state": v2_status.get("state", "NOT_STARTED"),
                "consecutive_failures": 0,
                "scheduling_pause_reason": v2_status.get("scheduling_pause_reason"),
                "adaptive_capacity_reason": v2_status.get("adaptive_capacity_reason"),
                "remote_sync_state": v2_status.get("remote_sync", {}).get("state", "BILINMIYOR"),
                "remote_sync_error": v2_status.get("remote_sync", {}).get("error"),
                "blocker": v2_status.get("scheduling_pause_reason"),
                "recovery_waiting": recovery_waiting,
                "recovery_succeeded": recovery_succeeded,
                "recovery_parked": recovery_parked,
                "recovery_worker_count": int(v2_status.get("recovery_worker_count") or 0),
                "recovery_pending_count": int(v2_status.get("recovery_pending_count") or 0),
                "recovery_latest": recovery_summary.get("latest_decision", {}) if recovery_summary else {},
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
        preflight = read_json(V2_PREFLIGHT)
        if preflight:
            self.machine_var.set(
                f"Bilgisayar profili: {preflight.get('resource_profile', 'bilinmiyor')} - "
                f"RAM {preflight.get('total_memory_gb', '?')} GB - CPU {preflight.get('logical_cpus', '?')} izlek - "
                f"{preflight.get('slot_count', 21)} mantıksal slot / aynı anda en fazla {preflight.get('max_child_workers', '?')} - "
                f"Git {'HAZIR' if preflight.get('checks', {}).get('git_executes') else 'EKSIK'}"
            )
            national_ready = bool(preflight.get("national_england_canonical_inventory_ready"))
            self.data_scope_var.set(
                f"Veri kapsamı: 92.283 kayıt = Londra kanonik matrisi; tüm İngiltere kanonik envanteri "
                f"{'HAZIR' if national_ready else 'HAZIR DEĞİL'} - internet eşleşen 33.785 / NO_DATA veya eksik 58.498"
            )
        remote = read_json(REMOTE_STATUS)
        if remote:
            self.remote_var.set(
                f"Uzaktan erişim: {remote.get('status', 'bilinmiyor')} - "
                f"Chrome {'HAZIR' if remote.get('chrome_remote_desktop_running') else 'KURULUM GEREKLI'} - "
                f"Tailscale {'HAZIR' if remote.get('tailscale_backend_state') == 'Running' else 'KURULUM/GIRIS GEREKLI'}"
            )
        info = self.read_runner_info()
        if info.get("ready"):
            age = int(info.get("heartbeat_age") or 0)
            active_workers = int(info.get("active_workers", 0))
            ready_tasks = int(info.get("queue_ready_count", 0))
            worker_explanation = (
                "GERÇEK GÖREV ÇALIŞIYOR"
                if active_workers
                else ("hazır görev bekliyor" if ready_tasks else "runner açık, yürütülebilir görev yok")
            )
            remote_age = info.get("remote_latest_age")
            remote_age_text = f"{int(remote_age // 60)} dk" if remote_age is not None else "yok"
            self.runner_var.set(
                f"Runner ana süreci: HEALTHY - PID {info.get('pid')} - heartbeat {age} sn. "
                f"Çalışan gerçek görev işçisi: {active_workers}/"
                f"{info.get('available_worker_capacity', info.get('max_child_workers', 15))} "
                f"(donanım üst sınırı {info.get('max_child_workers', 15)}); durum: {worker_explanation}. "
                f"Mantıksal slot: {info.get('logical_slot_count', 21)}. "
                f"Yerel kuyruk: hazır {ready_tasks}, taranan {info.get('queue_scan_count')}. "
                f"ChatGPT/GitHub çıktısı: son 15 dk güncel {info.get('remote_recent_count', 0)}/21; "
                f"en yeni uzak kayıt yaşı {remote_age_text}; eski bekleme kaydı {info.get('remote_waiting_count', 0)}. "
                f"Yayın bekleyen {info.get('publish_pending_count', 0)}; bloklu slot {info.get('blocked_slot_count', 0)}. "
                f"Otomatik kurtarma: bekleyen {info.get('recovery_waiting', 0)}, "
                f"aktif bakım işçisi {info.get('recovery_worker_count', 0)}, "
                f"bakım kuyruğu {info.get('recovery_pending_count', 0)}, "
                f"düzeltilen {info.get('recovery_succeeded', 0)}, "
                f"gerçek veri/elle müdahale bekleyen {info.get('recovery_parked', 0)}. "
                f"Git eşitleme: {info.get('remote_sync_state', 'BILINMIYOR')}. "
                f"Aktif görev: {info.get('current_task_id') or '-'}. "
                f"Kaynak: {info.get('scheduling_pause_reason') or info.get('adaptive_capacity_reason') or 'tam kapasite'}"
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
        self.refresh_test_status()
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
