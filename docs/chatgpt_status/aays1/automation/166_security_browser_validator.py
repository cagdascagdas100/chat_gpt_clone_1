from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

TASK_ID = "aays1-147-security-300-browser-validation-20260711"


def first_existing(paths: list[str | None]) -> str | None:
    for value in paths:
        if value and Path(value).exists():
            return str(Path(value))
    return None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("repo_root_argument_required")

    repo_root = Path(sys.argv[1]).resolve()
    proof_path = repo_root / "docs/chatgpt_status/_shared/reports/security_300_rows_browser_validation_20260711.json"
    output_path = repo_root / "docs/chatgpt_status/aays1/runner_outputs/147_security_300_browser_validation.json"
    probe_path = repo_root / "england_map_web/__aays_security_browser_probe_166.html"

    proof: dict[str, Any] = {
        "status": "failed",
        "browser_engine": None,
        "url": None,
        "visible_rows_text": None,
        "geojson_metric_present": False,
        "latest_filter_rows": None,
        "source_link_count": 0,
        "artifact_link_count": 0,
        "console_error_count": None,
        "console_errors": [],
        "diagnostics": [],
        "error": None,
    }

    output: dict[str, Any] = {
        "task_id": TASK_ID,
        "page_key": "aays1",
        "status": "started",
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "expected_visible_rows": 300,
        "expected_new_batch_rows": 150,
        "expected_geojson_features": 300,
        "browser_status": "not_run",
        "browser_engine": None,
        "browser_url": None,
        "visible_rows_text": None,
        "geojson_metric_present": False,
        "latest_filter_rows": None,
        "source_link_count": 0,
        "artifact_link_count": 0,
        "console_error_count": None,
        "worktree_http_server_started": False,
        "worktree_http_server_url": None,
        "diagnostics": [],
        "blockers": [],
        "single_runner_only": True,
        "parallel_runner": False,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }

    probe_html = r'''<!doctype html>
<html><head><meta charset="utf-8"><title>AAYS Security Browser Probe</title></head>
<body>
<pre id="proof">waiting</pre>
<iframe id="target" style="width:1800px;height:1000px" src="/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=166"></iframe>
<script>
(function () {
  const result = {
    status: "failed",
    visible_rows_text: null,
    geojson_metric_present: false,
    total_page_info: null,
    latest_filter_rows: null,
    source_link_count: 0,
    artifact_link_count: 0,
    console_errors: [],
    error: null
  };
  const proof = document.getElementById("proof");
  const frame = document.getElementById("target");
  function finish() {
    result.status = (
      result.visible_rows_text && result.visible_rows_text.includes("300") &&
      result.geojson_metric_present &&
      result.total_page_info && result.total_page_info.includes("300 satır") &&
      result.latest_filter_rows && result.latest_filter_rows.includes("150 satır") &&
      result.source_link_count > 0 &&
      result.artifact_link_count > 0 &&
      result.console_errors.length === 0
    ) ? "pass" : "failed";
    proof.textContent = JSON.stringify(result);
  }
  frame.addEventListener("load", function () {
    setTimeout(function () {
      try {
        const win = frame.contentWindow;
        const doc = frame.contentDocument;
        win.addEventListener("error", function (e) {
          result.console_errors.push(String(e.message || "window_error"));
        });
        win.addEventListener("unhandledrejection", function (e) {
          result.console_errors.push(String(e.reason || "unhandled_rejection"));
        });
        const body = doc.body ? doc.body.innerText : "";
        result.visible_rows_text = body.split(/\r?\n/).find(
          line => line.includes("Görünür") && line.includes("satır")
        ) || null;
        result.geojson_metric_present = body.includes("GeoJSON feature: 300");
        const pageInfo = doc.getElementById("pageInfo");
        result.total_page_info = pageInfo ? pageInfo.innerText : null;
        result.source_link_count = doc.querySelectorAll('a[href^="https://data.police.uk"]').length;
        result.artifact_link_count = doc.querySelectorAll('a[data-artifact-link="true"]').length;
        const filter = doc.getElementById("statusFilter");
        if (!filter) throw new Error("statusFilter_missing");
        filter.value = "latest";
        filter.dispatchEvent(new Event("change", {bubbles:true}));
        setTimeout(function () {
          result.latest_filter_rows = pageInfo ? pageInfo.innerText : null;
          finish();
        }, 3000);
      } catch (e) {
        result.error = String(e && e.stack ? e.stack : e);
        finish();
      }
    }, 5000);
  });
  setTimeout(function () {
    if (proof.textContent === "waiting") {
      result.error = result.error || "probe_timeout";
      finish();
    }
  }, 18000);
})();
</script>
</body></html>
'''
    probe_path.write_text(probe_html, encoding="utf-8")

    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local_app_data = os.environ.get("LOCALAPPDATA", "")

    chrome_binary = first_existing([
        shutil.which("chrome"),
        shutil.which("google-chrome"),
        shutil.which("chrome.exe"),
        str(Path(program_files) / "Google/Chrome/Application/chrome.exe"),
        str(Path(program_files_x86) / "Google/Chrome/Application/chrome.exe"),
        str(Path(local_app_data) / "Google/Chrome/Application/chrome.exe") if local_app_data else None,
    ])
    edge_binary = first_existing([
        shutil.which("msedge"),
        shutil.which("msedge.exe"),
        str(Path(program_files_x86) / "Microsoft/Edge/Application/msedge.exe"),
        str(Path(program_files) / "Microsoft/Edge/Application/msedge.exe"),
    ])

    server: subprocess.Popen[str] | None = None
    selected_port: int | None = None
    try:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        for port in (8020, 8021):
            candidate = subprocess.Popen(
                [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(repo_root)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
                creationflags=creationflags,
            )
            ready = False
            for _ in range(30):
                time.sleep(0.5)
                if candidate.poll() is not None:
                    break
                try:
                    import urllib.request

                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as response:
                        if response.status == 200:
                            ready = True
                            break
                except Exception:
                    pass
            if ready:
                server = candidate
                selected_port = port
                break
            candidate.terminate()
            try:
                candidate.wait(timeout=5)
            except Exception:
                candidate.kill()

        if selected_port is None:
            raise RuntimeError("worktree_http_server_not_ready")

        output["worktree_http_server_started"] = True
        output["worktree_http_server_url"] = f"http://127.0.0.1:{selected_port}/"
        direct_urls = [
            f"http://127.0.0.1:{selected_port}/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=166",
            "http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=166",
        ]

        def validate_driver(driver: Any, engine: str, url: str) -> bool:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import Select, WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            driver.set_page_load_timeout(60)
            driver.get(url)
            WebDriverWait(driver, 45).until(EC.presence_of_element_located((By.ID, "table")))
            WebDriverWait(driver, 45).until(
                lambda d: "Security / Public Safety" in d.find_element(By.ID, "title").text
            )
            WebDriverWait(driver, 45).until(
                lambda d: "300 satır" in d.find_element(By.ID, "pageInfo").text
            )
            time.sleep(2)
            body = driver.find_element(By.TAG_NAME, "body").text
            visible_text = next(
                (line for line in body.splitlines() if "Görünür" in line and "satır" in line),
                None,
            )
            geo_ok = "GeoJSON feature: 300" in body
            source_links = len(driver.find_elements(By.CSS_SELECTOR, 'a[href^="https://data.police.uk"]'))
            artifact_links = len(driver.find_elements(By.CSS_SELECTOR, 'a[data-artifact-link="true"]'))
            element = driver.find_element(By.ID, "statusFilter")
            Select(element).select_by_value("latest")
            driver.execute_script(
                "arguments[0].dispatchEvent(new Event('change', {bubbles:true}))", element
            )
            WebDriverWait(driver, 25).until(
                lambda d: "150 satır" in d.find_element(By.ID, "pageInfo").text
            )
            latest_text = driver.find_element(By.ID, "pageInfo").text
            try:
                logs = driver.get_log("browser")
            except Exception as exc:
                proof["diagnostics"].append(
                    f"{engine} browser log unavailable: {type(exc).__name__}: {exc!r}"
                )
                logs = []
            errors = [item for item in logs if item.get("level") == "SEVERE"]
            passed = bool(
                visible_text
                and "300" in visible_text
                and geo_ok
                and "150 satır" in latest_text
                and source_links > 0
                and artifact_links > 0
                and len(errors) == 0
            )
            proof.update({
                "status": "pass" if passed else "failed",
                "browser_engine": engine,
                "url": url,
                "visible_rows_text": visible_text,
                "geojson_metric_present": geo_ok,
                "latest_filter_rows": latest_text,
                "source_link_count": source_links,
                "artifact_link_count": artifact_links,
                "console_error_count": len(errors),
                "console_errors": errors[:20],
            })
            return passed

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.edge.options import Options as EdgeOptions

            common_args = [
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--no-first-run",
                "--no-default-browser-check",
                "--remote-allow-origins=*",
                "--window-size=1920,1080",
            ]
            factories: list[Any] = []
            if chrome_binary:
                def make_chrome() -> tuple[Any, str, str]:
                    options = ChromeOptions()
                    for arg in common_args:
                        options.add_argument(arg)
                    profile = tempfile.mkdtemp(prefix="aays_chrome_")
                    options.add_argument("--user-data-dir=" + profile)
                    options.binary_location = chrome_binary
                    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
                    return webdriver.Chrome(options=options), profile, "chrome_selenium"

                factories.append(make_chrome)
            if edge_binary:
                def make_edge() -> tuple[Any, str, str]:
                    options = EdgeOptions()
                    for arg in common_args:
                        options.add_argument(arg)
                    profile = tempfile.mkdtemp(prefix="aays_edge_")
                    options.add_argument("--user-data-dir=" + profile)
                    options.binary_location = edge_binary
                    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
                    return webdriver.Edge(options=options), profile, "edge_selenium"

                factories.append(make_edge)

            for factory in factories:
                for url in direct_urls:
                    driver = None
                    profile = None
                    engine = factory.__name__
                    try:
                        driver, profile, engine = factory()
                        if validate_driver(driver, engine, url):
                            break
                        proof["diagnostics"].append(f"{engine} {url}: contract mismatch")
                    except Exception as exc:
                        proof["diagnostics"].append(
                            f"{engine} {url}: {type(exc).__name__}: {exc!r}"
                        )
                    finally:
                        if driver is not None:
                            try:
                                driver.quit()
                            except Exception:
                                pass
                        if profile:
                            shutil.rmtree(profile, ignore_errors=True)
                if proof["status"] == "pass":
                    break
        except Exception as exc:
            proof["diagnostics"].append(
                f"selenium_setup: {type(exc).__name__}: {exc!r}"
            )

        if proof["status"] != "pass":
            wrapper_url = f"http://127.0.0.1:{selected_port}/england_map_web/__aays_security_browser_probe_166.html"
            for binary, engine in ((chrome_binary, "chrome_cli"), (edge_binary, "edge_cli")):
                if not binary:
                    continue
                cli_profile = tempfile.mkdtemp(prefix=f"aays_{engine}_")
                try:
                    process = subprocess.run(
                        [
                            binary,
                            "--headless=new",
                            "--disable-gpu",
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-extensions",
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--user-data-dir=" + cli_profile,
                            "--virtual-time-budget=22000",
                            "--dump-dom",
                            wrapper_url,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=75,
                        errors="replace",
                    )
                    match = re.search(r"""<pre[^>]*\bid\s*=\s*['"]proof['"][^>]*>(.*?)</pre>""", process.stdout, re.S | re.I)
                    if not match:
                        proof["diagnostics"].append(
                            f"{engine}: probe block missing; rc={process.returncode}; stderr={process.stderr[-1200:]}"
                        )
                        continue
                    data = json.loads(html.unescape(match.group(1)))
                    passed = bool(
                        data.get("status") == "pass"
                        and data.get("visible_rows_text")
                        and "300" in data["visible_rows_text"]
                        and data.get("geojson_metric_present") is True
                        and data.get("latest_filter_rows")
                        and "150 satır" in data["latest_filter_rows"]
                        and int(data.get("source_link_count") or 0) > 0
                        and int(data.get("artifact_link_count") or 0) > 0
                        and len(data.get("console_errors") or []) == 0
                    )
                    proof.update({
                        "status": "pass" if passed else "failed",
                        "browser_engine": engine,
                        "url": wrapper_url,
                        "visible_rows_text": data.get("visible_rows_text"),
                        "geojson_metric_present": bool(data.get("geojson_metric_present")),
                        "latest_filter_rows": data.get("latest_filter_rows"),
                        "source_link_count": int(data.get("source_link_count") or 0),
                        "artifact_link_count": int(data.get("artifact_link_count") or 0),
                        "console_error_count": len(data.get("console_errors") or []),
                        "console_errors": data.get("console_errors") or [],
                        "error": data.get("error"),
                    })
                    if passed:
                        break
                    proof["diagnostics"].append(
                        f"{engine}: contract mismatch: {json.dumps(data, ensure_ascii=False)}"
                    )
                except Exception as exc:
                    proof["diagnostics"].append(
                        f"{engine}: {type(exc).__name__}: {exc!r}"
                    )
                finally:
                    shutil.rmtree(cli_profile, ignore_errors=True)

        if proof["status"] != "pass":
            proof["error"] = proof.get("error") or (
                proof["diagnostics"][-1]
                if proof["diagnostics"]
                else "no_browser_attempt_passed"
            )

    except Exception as exc:
        proof["error"] = f"{type(exc).__name__}: {exc!r}"
        proof["diagnostics"].append(proof["error"])
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=8)
            except Exception:
                server.kill()
        try:
            probe_path.unlink(missing_ok=True)
        except Exception:
            pass

    output.update({
        "browser_status": proof["status"],
        "browser_engine": proof.get("browser_engine"),
        "browser_url": proof.get("url"),
        "visible_rows_text": proof.get("visible_rows_text"),
        "geojson_metric_present": bool(proof.get("geojson_metric_present")),
        "latest_filter_rows": proof.get("latest_filter_rows"),
        "source_link_count": int(proof.get("source_link_count") or 0),
        "artifact_link_count": int(proof.get("artifact_link_count") or 0),
        "console_error_count": proof.get("console_error_count"),
        "diagnostics": proof.get("diagnostics") or [],
    })
    if proof["status"] == "pass" and proof.get("console_error_count") == 0:
        output["status"] = "completed_300_rows_browser_pass"
    else:
        output["status"] = "blocked_300_rows_browser_validation"
        output["blockers"] = [f"browser_validation_failed:{proof.get('error') or 'contract_mismatch'}"]
        if proof.get("console_error_count") not in (None, 0):
            output["blockers"].append(
                f"browser_console_errors:{proof['console_error_count']}"
            )

    write_json(proof_path, proof)
    write_json(output_path, output)
    print(f"OUTPUT={output_path}")
    return 0 if output["status"] == "completed_300_rows_browser_pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
