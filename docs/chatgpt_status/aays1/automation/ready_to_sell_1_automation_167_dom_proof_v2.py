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
TARGET_GEOJSON = BUSINESS_ROOT / "geometry_review_3of4" / "all_1264_real_geometry_3of4.geojson"
GEOMETRY_STATUS = BUSINESS_ROOT / "geometry_review_3of4" / "all_1264_status.txt"
SOURCE_REGISTRY = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "official_source_candidates_20260720.json"
VERIFIED_CANDIDATES = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "verified_candidate_examples_20260720.json"
REPORT_JSON = SLOT_ROOT / "reports" / "001_ready_to_sell_1_automation_167_dom_proof_20260720.json"
REPORT_MD = SLOT_ROOT / "reports" / "001_ready_to_sell_1_automation_167_dom_proof_20260720.md"

EXPECTED_GEOMETRY_ROWS = 1264
EXPECTED_FIRST_BATCH_ROWS = 50
MIN_OFFICIAL_SOURCES = 3
MIN_SAMPLE_CANDIDATES = 4
MIN_EXACT_INSPIRE_MATCHES = 2
MIN_INTERNET_REVERIFIED = 4


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


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def collect_business_state() -> dict[str, Any]:
    status_text = read_text(GEOMETRY_STATUS)
    geojson = read_json(TARGET_GEOJSON)
    sources = read_json(SOURCE_REGISTRY)
    candidates = read_json(VERIFIED_CANDIDATES)

    features = geojson.get("features", []) if isinstance(geojson, dict) else []
    source_rows = sources.get("sources", []) if isinstance(sources, dict) else []
    candidate_rows = candidates.get("candidates", []) if isinstance(candidates, dict) else []
    summary = candidates.get("summary", {}) if isinstance(candidates, dict) else {}

    exact_inspire = sum(
        1
        for row in candidate_rows
        if isinstance(row, dict)
        and row.get("match_method") == "metadata_inspire_exact"
        and row.get("matched_inspire_id")
    )
    internet_reverified = sum(
        1
        for row in candidate_rows
        if isinstance(row, dict)
        and isinstance(row.get("internet_readback"), dict)
        and (
            row["internet_readback"].get("listing_page_live") is True
            or row["internet_readback"].get("secondary_channels_live") is True
        )
    )
    source_scores = [
        int(row.get("source_verification_score") or 0)
        for row in source_rows
        if isinstance(row, dict)
    ]

    return {
        "terminal_no_replay": ["146", "153", "155", "166"],
        "geometry_status_path": relative(GEOMETRY_STATUS),
        "geometry_status_present": GEOMETRY_STATUS.is_file(),
        "geometry_status_sha256": file_sha256(GEOMETRY_STATUS),
        "processed_rows_1264": bool(re.search(r"(?m)^PROCESSED_ROWS=1264\s*$", status_text)),
        "real_geometry_confirmed": bool(re.search(r"(?m)^REAL_GEOMETRY_CONFIRMED=true\s*$", status_text, re.I)),
        "business_final_ready_false": bool(re.search(r"(?m)^FINAL_READY=false\s*$", status_text, re.I)),
        "geojson_path": relative(TARGET_GEOJSON),
        "geojson_present": TARGET_GEOJSON.is_file(),
        "geojson_sha256": file_sha256(TARGET_GEOJSON),
        "geojson_feature_count": len(features),
        "geojson_declared_processed_rows": geojson.get("processed_rows") if isinstance(geojson, dict) else None,
        "geojson_real_geometry_confirmed": geojson.get("real_geometry_confirmed") if isinstance(geojson, dict) else None,
        "source_registry_path": relative(SOURCE_REGISTRY),
        "source_registry_present": SOURCE_REGISTRY.is_file(),
        "source_registry_sha256": file_sha256(SOURCE_REGISTRY),
        "official_source_count": len(source_rows),
        "official_source_scores": source_scores,
        "verified_candidates_path": relative(VERIFIED_CANDIDATES),
        "verified_candidates_present": VERIFIED_CANDIDATES.is_file(),
        "verified_candidates_sha256": file_sha256(VERIFIED_CANDIDATES),
        "candidate_count": len(candidate_rows),
        "exact_inspire_match_count": exact_inspire,
        "internet_reverified_count": internet_reverified,
        "parcel_value_publication_rows": int(summary.get("parcel_value_publication_rows") or 0),
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
            for item in relatives:
                candidate = Path(root) / item
                if candidate.is_file():
                    candidates.append(str(candidate))
    return list(dict.fromkeys(candidates))


def http_get(url: str) -> dict[str, Any]:
    started = time.monotonic()
    try:
        request = urllib.request.Request(
            url,
            headers={"Cache-Control": "no-cache", "User-Agent": "AAYS-ready-to-sell-167-v2/1.0"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read()
            return {
                "status": int(response.status),
                "bytes": len(body),
                "sha256": sha256_bytes(body),
                "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return {
            "status": int(exc.code),
            "bytes": len(body),
            "sha256": sha256_bytes(body),
            "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
            "error": f"HTTPError: {exc}",
        }
    except Exception as exc:
        return {
            "status": None,
            "bytes": 0,
            "sha256": None,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
            "error": f"{type(exc).__name__}: {exc}",
        }


def selenium_probe(url: str, binary: str) -> dict[str, Any] | None:
    try:
        from selenium import webdriver  # type: ignore
        from selenium.webdriver.chrome.options import Options as ChromeOptions  # type: ignore
    except Exception:
        return None

    options = ChromeOptions()
    options.binary_location = binary
    for argument in (
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--window-size=1440,1200",
    ):
        options.add_argument(argument)
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        driver.get(url)
        time.sleep(5)
        dom = driver.page_source or ""
        logs = driver.get_log("browser")
        severe = [entry for entry in logs if str(entry.get("level", "")).upper() in {"SEVERE", "ERROR"}]
        return {
            "engine": "selenium_chromium",
            "browser_binary": binary,
            "exit_code": 0,
            "dom": dom,
            "dom_sha256": sha256_bytes(dom.encode("utf-8")),
            "console_error_count": len(severe),
            "console_errors": severe[:50],
            "error": None,
        }
    except Exception as exc:
        return {
            "engine": "selenium_chromium",
            "browser_binary": binary,
            "exit_code": None,
            "dom": "",
            "dom_sha256": None,
            "console_error_count": None,
            "console_errors": [],
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


def cli_probe(url: str, binary: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="aays_ready_to_sell_167_v2_") as profile:
        command = [
            binary,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--enable-logging=stderr",
            "--log-level=0",
            "--window-size=1440,1200",
            "--virtual-time-budget=20000",
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
                timeout=90,
                check=False,
            )
            dom = completed.stdout or ""
            stderr = completed.stderr or ""
            console_lines = [
                line.strip()
                for line in stderr.splitlines()
                if re.search(
                    r"(?:console|javascript|uncaught).*(?:error|exception)|(?:error|exception).*(?:console|javascript)",
                    line,
                    re.I,
                )
            ]
            return {
                "engine": "chromium_cli",
                "browser_binary": binary,
                "exit_code": completed.returncode,
                "dom": dom,
                "dom_sha256": sha256_bytes(dom.encode("utf-8")) if dom else None,
                "console_error_count": len(console_lines),
                "console_errors": console_lines[:50],
                "stderr_tail": stderr[-4000:] if stderr else None,
                "error": None if completed.returncode == 0 else f"BROWSER_EXIT_{completed.returncode}",
            }
        except Exception as exc:
            return {
                "engine": "chromium_cli",
                "browser_binary": binary,
                "exit_code": None,
                "dom": "",
                "dom_sha256": None,
                "console_error_count": None,
                "console_errors": [],
                "stderr_tail": None,
                "error": f"{type(exc).__name__}: {exc}",
            }


def browser_probe(url: str) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for binary in browser_candidates():
        selenium_result = selenium_probe(url, binary)
        if selenium_result is not None:
            attempts.append({key: value for key, value in selenium_result.items() if key != "dom"})
            if selenium_result.get("exit_code") == 0 and selenium_result.get("dom"):
                selenium_result["attempts"] = attempts
                return selenium_result

        cli_result = cli_probe(url, binary)
        attempts.append({key: value for key, value in cli_result.items() if key != "dom"})
        if cli_result.get("exit_code") == 0 and cli_result.get("dom"):
            cli_result["attempts"] = attempts
            return cli_result

    return {
        "engine": None,
        "browser_binary": None,
        "exit_code": None,
        "dom": "",
        "dom_sha256": None,
        "console_error_count": None,
        "console_errors": [],
        "error": "BROWSER_EXECUTABLE_OR_WORKING_DRIVER_NOT_AVAILABLE",
        "attempts": attempts,
    }


def html_data_attribute(dom: str, name: str) -> str | None:
    match = re.search(rf'\bdata-{re.escape(name)}=["\']([^"\']*)["\']', dom, re.I)
    return match.group(1) if match else None


def parse_int(value: str | None) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def run_dom_acceptance() -> dict[str, Any]:
    CaptureHandler.events = []
    handler = partial(CaptureHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = int(server.server_port)

    paths = {
        "html": TARGET_HTML,
        "javascript": TARGET_JS,
        "geojson": TARGET_GEOJSON,
        "source_registry": SOURCE_REGISTRY,
        "verified_candidates": VERIFIED_CANDIDATES,
    }
    urls = {key: f"http://127.0.0.1:{port}/{relative(path)}" for key, path in paths.items()}

    try:
        http = {key: http_get(url) for key, url in urls.items()}
        browser = browser_probe(urls["html"])
        time.sleep(0.5)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    dom = str(browser.get("dom") or "")
    loaded_count = parse_int(html_data_attribute(dom, "loaded-count"))
    visible_count = parse_int(html_data_attribute(dom, "visible-count"))
    official_source_count = parse_int(html_data_attribute(dom, "official-source-count"))
    internet_verified_candidate_count = parse_int(html_data_attribute(dom, "internet-verified-candidate-count"))
    semantic_valid = html_data_attribute(dom, "semantic-valid")
    rendered_geometry_rows = len(re.findall(r'\bdata-row-index=["\']\d+["\']', dom, re.I))
    loading_text_present = "1264 GeoJSON yükleniyor..." in dom
    blocked_text_present = "BLOCKED:" in dom
    source_panel_present = 'id="official-source-summary"' in dom or "id='official-source-summary'" in dom
    candidate_panel_present = 'id="verified-candidate-summary"' in dom or "id='verified-candidate-summary'" in dom
    server_404_paths = [event.get("path") for event in CaptureHandler.events if event.get("status") == 404]

    return {
        "targets": {
            key: {
                "path": relative(path),
                "exists": path.is_file(),
                "sha256": file_sha256(path),
                "http": http[key],
            }
            for key, path in paths.items()
        },
        "browser": {key: value for key, value in browser.items() if key != "dom"},
        "dom_bytes": len(dom.encode("utf-8")),
        "dom_sha256": browser.get("dom_sha256"),
        "loaded_count": loaded_count,
        "visible_count": visible_count,
        "official_source_count": official_source_count,
        "internet_verified_candidate_count": internet_verified_candidate_count,
        "semantic_valid": semantic_valid,
        "rendered_geometry_rows": rendered_geometry_rows,
        "loading_text_present_after_browser": loading_text_present,
        "blocked_text_present": blocked_text_present,
        "official_source_panel_present": source_panel_present,
        "verified_candidate_panel_present": candidate_panel_present,
        "server_events": CaptureHandler.events,
        "server_404_paths": server_404_paths,
    }


def determine_status(business: dict[str, Any], acceptance: dict[str, Any]) -> tuple[str, list[str]]:
    blockers: list[str] = []

    if not business["geometry_status_present"]:
        blockers.append("REMOTE_BUSINESS_GEOMETRY_STATUS_MISSING")
    if not business["processed_rows_1264"] or not business["real_geometry_confirmed"]:
        blockers.append("REMOTE_BUSINESS_STATE_DOES_NOT_CONFIRM_1264_REAL_GEOMETRY")
    if not business["business_final_ready_false"]:
        blockers.append("BUSINESS_FINAL_READY_FALSE_CONTRACT_MISSING")
    if business["geojson_feature_count"] != EXPECTED_GEOMETRY_ROWS:
        blockers.append("GEOJSON_FEATURE_COUNT_NOT_1264")
    if business["geojson_declared_processed_rows"] != EXPECTED_GEOMETRY_ROWS:
        blockers.append("GEOJSON_DECLARED_PROCESSED_ROWS_NOT_1264")
    if business["geojson_real_geometry_confirmed"] is not True:
        blockers.append("GEOJSON_REAL_GEOMETRY_NOT_CONFIRMED")
    if business["official_source_count"] < MIN_OFFICIAL_SOURCES:
        blockers.append("OFFICIAL_SOURCE_COUNT_BELOW_3")
    if business["official_source_scores"] and min(business["official_source_scores"]) < 90:
        blockers.append("OFFICIAL_SOURCE_SCORE_BELOW_90")
    if business["candidate_count"] < MIN_SAMPLE_CANDIDATES:
        blockers.append("SAMPLE_CANDIDATE_COUNT_BELOW_4")
    if business["exact_inspire_match_count"] < MIN_EXACT_INSPIRE_MATCHES:
        blockers.append("EXACT_INSPIRE_MATCH_COUNT_BELOW_2")
    if business["internet_reverified_count"] < MIN_INTERNET_REVERIFIED:
        blockers.append("INTERNET_REVERIFIED_COUNT_BELOW_4")
    if business["parcel_value_publication_rows"] != 0:
        blockers.append("UNVERIFIED_PARCEL_VALUE_PUBLICATION_DETECTED")

    for key, target in acceptance["targets"].items():
        if not target["exists"]:
            blockers.append(f"AUTOMATION_167_{key.upper()}_MISSING")
        if target["http"].get("status") != 200:
            blockers.append(f"AUTOMATION_167_{key.upper()}_HTTP_NOT_200")

    browser = acceptance["browser"]
    if browser.get("exit_code") != 0:
        blockers.append("AUTOMATION_167_BROWSER_SESSION_NOT_ACCEPTED")
    if browser.get("console_error_count") not in (0, None):
        blockers.append("AUTOMATION_167_BROWSER_CONSOLE_ERRORS")
    if acceptance["loaded_count"] != EXPECTED_GEOMETRY_ROWS:
        blockers.append("AUTOMATION_167_DOM_LOADED_COUNT_NOT_1264")
    if (acceptance["visible_count"] or 0) < EXPECTED_FIRST_BATCH_ROWS:
        blockers.append("AUTOMATION_167_DOM_VISIBLE_COUNT_BELOW_50")
    if (acceptance["official_source_count"] or 0) < MIN_OFFICIAL_SOURCES:
        blockers.append("AUTOMATION_167_DOM_OFFICIAL_SOURCE_COUNT_BELOW_3")
    if (acceptance["internet_verified_candidate_count"] or 0) < 3:
        blockers.append("AUTOMATION_167_DOM_INTERNET_CANDIDATE_COUNT_BELOW_3")
    if str(acceptance["semantic_valid"]).casefold() != "true":
        blockers.append("AUTOMATION_167_DOM_SEMANTIC_VALID_FALSE")
    if acceptance["rendered_geometry_rows"] < EXPECTED_FIRST_BATCH_ROWS:
        blockers.append("AUTOMATION_167_DOM_RENDERED_GEOMETRY_ROWS_BELOW_50")
    if acceptance["loading_text_present_after_browser"]:
        blockers.append("AUTOMATION_167_DOM_REMAINS_IN_LOADING_STATE")
    if acceptance["blocked_text_present"]:
        blockers.append("AUTOMATION_167_DOM_BLOCKED_TEXT_PRESENT")
    if not acceptance["official_source_panel_present"]:
        blockers.append("AUTOMATION_167_OFFICIAL_SOURCE_PANEL_MISSING")
    if not acceptance["verified_candidate_panel_present"]:
        blockers.append("AUTOMATION_167_VERIFIED_CANDIDATE_PANEL_MISSING")
    if acceptance["server_404_paths"]:
        blockers.append("AUTOMATION_167_HTTP_404_OBSERVED")

    return ("PASS" if not blockers else "BLOCKED", list(dict.fromkeys(blockers)))


def write_markdown(report: dict[str, Any]) -> None:
    acceptance = report["automation_167_dom_proof"]
    business = report["remote_business_state"]
    lines = [
        "# Ready to Sell 1 — Automation 167 DOM Proof V2",
        "",
        f"- SLOT_ID: `{SLOT_ID}`",
        f"- Task step: `{TASK_STEP}`",
        f"- Status: `{report['status']}`",
        f"- GeoJSON rows: `{business['geojson_feature_count']}`",
        f"- Official sources: `{business['official_source_count']}`",
        f"- Sample candidates: `{business['candidate_count']}`",
        f"- Exact INSPIRE matches: `{business['exact_inspire_match_count']}`",
        f"- Internet reverified: `{business['internet_reverified_count']}`",
        f"- DOM loaded count: `{acceptance['loaded_count']}`",
        f"- DOM visible count: `{acceptance['visible_count']}`",
        f"- DOM official sources: `{acceptance['official_source_count']}`",
        f"- DOM internet candidates: `{acceptance['internet_verified_candidate_count']}`",
        f"- Browser exit: `{acceptance['browser'].get('exit_code')}`",
        f"- Console errors: `{acceptance['browser'].get('console_error_count')}`",
        "",
        "## Blockers",
        "",
        *([f"- `{value}`" for value in report["blockers"]] or ["- none"]),
        "",
        "## Safety",
        "",
        "`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.",
        "",
        "Source verification, parcel identity confidence and planning-detail verification remain separate signals.",
        "No parcel value is published for unbound or officially unconfirmed candidates.",
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
        "next_step": (
            "FIX_REPORTED_DOM_OR_BROWSER_BLOCKERS_THEN_RERUN_AUTOMATION_167"
            if blockers
            else "REMOTE_READBACK_THEN_ADVANCE_READY_TO_SELL_1_CHECKPOINT"
        ),
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
