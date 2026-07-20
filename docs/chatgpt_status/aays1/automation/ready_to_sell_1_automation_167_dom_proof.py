from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SLOT_ID = "ready_to_sell_1"
TASK_STEP = "READ_REMOTE_BUSINESS_STATE_THEN_AUTOMATION_167_DOM_PROOF"
ROOT = Path(__file__).resolve().parents[4]
BUSINESS_ROOT = ROOT / "docs" / "chatgpt_status" / "aays1"
SLOT_ROOT = BUSINESS_ROOT / "shards" / SLOT_ID
TARGET_HTML = ROOT / "england_map_web" / "geometry_review_3of4_1264_live.html"
TARGET_JS = ROOT / "england_map_web" / "geometry_review_3of4_1264_live.js"
GEOMETRY_STATUS = BUSINESS_ROOT / "geometry_review_3of4" / "all_1264_status.txt"
REPORT_JSON = SLOT_ROOT / "reports" / "001_ready_to_sell_1_automation_167_dom_proof_20260720.json"
REPORT_MD = SLOT_ROOT / "reports" / "001_ready_to_sell_1_automation_167_dom_proof_20260720.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str | None:
    return sha256_bytes(path.read_bytes()) if path.is_file() else None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_business_state() -> dict[str, Any]:
    terminal_ids = ("146", "153", "155", "166")
    files: list[dict[str, Any]] = []
    for folder_name in ("status", "reports", "queue", "current-task"):
        folder = BUSINESS_ROOT / folder_name
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            name = path.name.casefold()
            if not any(token in name for token in terminal_ids) and not any(
                marker in name for marker in ("ready_to_sell", "geometry_review", "automation_167")
            ):
                continue
            relative = str(path.relative_to(ROOT)).replace("\\", "/")
            files.append(
                {
                    "path": relative,
                    "bytes": path.stat().st_size,
                    "sha256": file_sha256(path),
                }
            )
            if len(files) >= 250:
                break
    geometry_status_text = read_text(GEOMETRY_STATUS)
    return {
        "terminal_no_replay": list(terminal_ids),
        "matched_business_files": files,
        "matched_business_file_count": len(files),
        "geometry_status_path": str(GEOMETRY_STATUS.relative_to(ROOT)).replace("\\", "/"),
        "geometry_status_present": GEOMETRY_STATUS.is_file(),
        "geometry_status_sha256": file_sha256(GEOMETRY_STATUS),
        "processed_rows_1264": bool(re.search(r"(?m)^PROCESSED_ROWS=1264\s*$", geometry_status_text)),
        "real_geometry_confirmed": bool(re.search(r"(?m)^REAL_GEOMETRY_CONFIRMED=true\s*$", geometry_status_text, re.I)),
        "business_final_ready_false": bool(re.search(r"(?m)^FINAL_READY=false\s*$", geometry_status_text, re.I)),
    }


class CaptureHandler(SimpleHTTPRequestHandler):
    events: list[dict[str, Any]] = []

    def log_message(self, format_string: str, *args: Any) -> None:
        message = format_string % args
        status_match = re.search(r'"(?:GET|HEAD) ([^ ]+) HTTP/[^\"]+" (\d+)', message)
        self.events.append(
            {
                "message": message,
                "path": status_match.group(1) if status_match else None,
                "status": int(status_match.group(2)) if status_match else None,
            }
        )


def browser_candidates() -> list[str]:
    candidates: list[str] = []
    for name in ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    if os.name == "nt":
        roots = [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")]
        relatives = [
            Path("Microsoft/Edge/Application/msedge.exe"),
            Path("Google/Chrome/Application/chrome.exe"),
            Path("Chromium/Application/chrome.exe"),
        ]
        for root in roots:
            if not root:
                continue
            for relative in relatives:
                candidate = Path(root) / relative
                if candidate.is_file():
                    candidates.append(str(candidate))
    return list(dict.fromkeys(candidates))


def http_get(url: str) -> dict[str, Any]:
    try:
        request = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "AAYS-ready-to-sell-167/1.0"})
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read()
            return {
                "status": int(response.status),
                "bytes": len(body),
                "sha256": sha256_bytes(body),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return {
            "status": int(exc.code),
            "bytes": len(body),
            "sha256": sha256_bytes(body),
            "error": f"HTTPError: {exc}",
        }
    except Exception as exc:
        return {"status": None, "bytes": 0, "sha256": None, "error": f"{type(exc).__name__}: {exc}"}


def browser_probe(url: str) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for binary in browser_candidates():
        with tempfile.TemporaryDirectory(prefix="aays_ready_to_sell_167_") as profile:
            command = [
                binary,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--enable-logging=stderr",
                "--log-level=0",
                "--window-size=1440,1200",
                "--virtual-time-budget=15000",
                f"--user-data-dir={profile}",
                "--dump-dom",
                url,
            ]
            try:
                completed = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=60,
                    check=False,
                )
                dom = completed.stdout or ""
                stderr = completed.stderr or ""
                attempt = {
                    "browser_binary": binary,
                    "exit_code": completed.returncode,
                    "dom_bytes": len(dom.encode("utf-8")),
                    "stderr_tail": stderr[-4000:] if stderr else None,
                }
                attempts.append(attempt)
                if completed.returncode == 0 and dom:
                    return {
                        "engine": "chromium_cli",
                        "browser_binary": binary,
                        "exit_code": 0,
                        "dom": dom,
                        "dom_sha256": sha256_bytes(dom.encode("utf-8")),
                        "stderr": stderr,
                        "attempts": attempts,
                        "error": None,
                    }
            except Exception as exc:
                attempts.append({"browser_binary": binary, "error": f"{type(exc).__name__}: {exc}"})
    return {
        "engine": None,
        "browser_binary": None,
        "exit_code": None,
        "dom": "",
        "dom_sha256": None,
        "stderr": None,
        "attempts": attempts,
        "error": "BROWSER_EXECUTABLE_OR_WORKING_HEADLESS_SESSION_NOT_AVAILABLE",
    }


def run_dom_acceptance() -> dict[str, Any]:
    CaptureHandler.events = []
    handler = partial(CaptureHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = int(server.server_port)
    html_relative = str(TARGET_HTML.relative_to(ROOT)).replace("\\", "/")
    js_relative = str(TARGET_JS.relative_to(ROOT)).replace("\\", "/")
    html_url = f"http://127.0.0.1:{port}/{html_relative}"
    js_url = f"http://127.0.0.1:{port}/{js_relative}"
    try:
        html_http = http_get(html_url)
        js_http = http_get(js_url)
        browser = browser_probe(html_url)
        time.sleep(0.5)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    dom = str(browser.get("dom") or "")
    rendered_rows = max(0, len(re.findall(r"<tr(?:\s|>)", dom, re.I)) - 1)
    loading_text_present = "1264 GeoJSON yükleniyor..." in dom
    server_404_paths = [event.get("path") for event in CaptureHandler.events if event.get("status") == 404]
    return {
        "target_html": html_relative,
        "target_javascript": js_relative,
        "html_exists": TARGET_HTML.is_file(),
        "javascript_exists": TARGET_JS.is_file(),
        "html_sha256": file_sha256(TARGET_HTML),
        "javascript_sha256": file_sha256(TARGET_JS),
        "html_http": html_http,
        "javascript_http": js_http,
        "browser": {key: value for key, value in browser.items() if key != "dom"},
        "dom_bytes": len(dom.encode("utf-8")),
        "dom_sha256": browser.get("dom_sha256"),
        "rendered_body_rows": rendered_rows,
        "loading_text_present_after_browser": loading_text_present,
        "server_events": CaptureHandler.events,
        "server_404_paths": server_404_paths,
    }


def determine_status(business: dict[str, Any], acceptance: dict[str, Any]) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if not business["geometry_status_present"]:
        blockers.append("REMOTE_BUSINESS_GEOMETRY_STATUS_MISSING")
    if not business["processed_rows_1264"] or not business["real_geometry_confirmed"]:
        blockers.append("REMOTE_BUSINESS_STATE_DOES_NOT_CONFIRM_1264_REAL_GEOMETRY")
    if not acceptance["html_exists"]:
        blockers.append("AUTOMATION_167_TARGET_HTML_MISSING")
    if not acceptance["javascript_exists"]:
        blockers.append("MISSING_GEOMETRY_REVIEW_1264_LIVE_JAVASCRIPT")
    if acceptance["html_http"].get("status") != 200:
        blockers.append("AUTOMATION_167_TARGET_HTML_HTTP_NOT_200")
    if acceptance["javascript_http"].get("status") != 200:
        blockers.append("AUTOMATION_167_JAVASCRIPT_HTTP_NOT_200")
    browser = acceptance["browser"]
    if browser.get("exit_code") != 0:
        blockers.append("AUTOMATION_167_BROWSER_SESSION_NOT_ACCEPTED")
    if acceptance["loading_text_present_after_browser"]:
        blockers.append("AUTOMATION_167_DOM_REMAINS_IN_LOADING_STATE")
    if acceptance["rendered_body_rows"] < 1:
        blockers.append("AUTOMATION_167_DOM_RENDERED_ZERO_GEOMETRY_ROWS")
    if acceptance["server_404_paths"]:
        blockers.append("AUTOMATION_167_HTTP_404_OBSERVED")
    return ("PASS" if not blockers else "BLOCKED", list(dict.fromkeys(blockers)))


def write_markdown(report: dict[str, Any]) -> None:
    acceptance = report["automation_167_dom_proof"]
    lines = [
        "# Ready to Sell 1 — Automation 167 DOM Proof",
        "",
        f"- SLOT_ID: `{SLOT_ID}`",
        f"- Task step: `{TASK_STEP}`",
        f"- Status: `{report['status']}`",
        f"- Target HTML HTTP: `{acceptance['html_http'].get('status')}`",
        f"- Target JavaScript HTTP: `{acceptance['javascript_http'].get('status')}`",
        f"- Browser exit: `{acceptance['browser'].get('exit_code')}`",
        f"- Rendered body rows: `{acceptance['rendered_body_rows']}`",
        f"- Loading text remains: `{acceptance['loading_text_present_after_browser']}`",
        "",
        "## Blockers",
        "",
        *([f"- `{value}`" for value in report["blockers"]] or ["- none"]),
        "",
        "## Safety",
        "",
        "`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.",
        "",
        "No parcel score, confidence, geometry, or completion percentage was increased by this proof task.",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError(f"SLOT_ID_MISMATCH: {os.environ.get('AAYS_SLOT_ID')}")
    business = collect_business_state()
    acceptance = run_dom_acceptance()
    status, blockers = determine_status(business, acceptance)
    report = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "base_slot_id": "ready_to_sell",
        "shard_index": 1,
        "parcel_partition": {"start": 1, "end": 30761, "count": 30761, "canonical_count": 92283},
        "task_id": os.environ.get("AAYS_TASK_ID"),
        "task_step": TASK_STEP,
        "status": status,
        "blockers": blockers,
        "remote_business_state": business,
        "automation_167_dom_proof": acceptance,
        "first_unverified_step_remains": TASK_STEP if status != "PASS" else None,
        "next_step": "RESTORE_OR_GENERATE_GEOMETRY_REVIEW_1264_LIVE_JAVASCRIPT_THEN_RERUN_AUTOMATION_167_DOM_PROOF" if blockers else "ADVANCE_READY_TO_SELL_1_CHECKPOINT_AFTER_REMOTE_ACCEPTANCE",
        "generated_at": utc_now(),
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    write_json(REPORT_JSON, report)
    write_markdown(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
