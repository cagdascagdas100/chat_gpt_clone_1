from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_1"
TASK_STEP = "HYDRATE_300_ROWS_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE"
PARTITION_START = 1
PARTITION_END = 30761
EXPECTED_ROWS = 300
ROOT = Path(__file__).resolve().parents[4]
SOURCE_ROOT = ROOT / "england_map_web" / "data" / "security_public_safety"
SOURCE_CSV = SOURCE_ROOT / "parcel_security_scores_verified.csv"
SOURCE_GEOJSON = SOURCE_ROOT / "parcel_security_scores_verified.geojson"
SOURCE_MANIFEST = SOURCE_ROOT / "security_evidence_manifest.json"
SHARD_ROOT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID
WEB_ROOT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID
SHARD_DATA = SHARD_ROOT / "data" / "security_public_safety_1_area_level_proxy_300.json"
WEB_DATA = WEB_ROOT / "security_public_safety_1_area_level_proxy_300.json"
PROBE_HTML = WEB_ROOT / "security_public_safety_1_acceptance.html"
REPORT_JSON = SHARD_ROOT / "reports" / "001_security_public_safety_1_http_hash_dom_console_browser_acceptance_20260720.json"
REPORT_MD = SHARD_ROOT / "reports" / "001_security_public_safety_1_http_hash_dom_console_browser_acceptance_20260720.md"
MATRIX_RELATIVE = "england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    replacements = {"ö": "o", "ü": "u", "ı": "i", "ş": "s", "ğ": "g", "ç": "c"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text)


def parcel_number(value: Any) -> int | None:
    match = re.search(r"(\d+)$", str(value or ""))
    return int(match.group(1)) if match else None


def http_get(url: str, timeout: float = 15.0) -> dict[str, Any]:
    started = time.monotonic()
    try:
        request = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "AAYS-security-slot-acceptance/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            return {
                "ok": int(response.status) == 200,
                "status": int(response.status),
                "content_type": response.headers.get("Content-Type"),
                "body_bytes": len(body),
                "body_sha256": sha256_bytes(body),
                "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
                "error": None,
            }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "content_type": None,
            "body_bytes": 0,
            "body_sha256": None,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
            "error": f"{type(exc).__name__}: {exc}",
        }


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *args: Any) -> None:
        return


def browser_candidates() -> list[str]:
    candidates: list[str] = []
    for name in ("google-chrome", "chrome", "chromium", "chromium-browser", "msedge"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    if os.name == "nt":
        roots = [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")]
        relatives = [
            Path("Google/Chrome/Application/chrome.exe"),
            Path("Microsoft/Edge/Application/msedge.exe"),
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


def selenium_probe(url: str, browser_binary: str) -> dict[str, Any] | None:
    try:
        from selenium import webdriver  # type: ignore
        from selenium.webdriver.chrome.options import Options as ChromeOptions  # type: ignore
    except Exception:
        return None
    options = ChromeOptions()
    options.binary_location = browser_binary
    for argument in ("--headless=new", "--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--window-size=1440,1200"):
        options.add_argument(argument)
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(45)
        driver.get(url)
        time.sleep(4)
        dom = driver.page_source
        logs = driver.get_log("browser")
        severe = [entry for entry in logs if str(entry.get("level", "")).upper() in {"SEVERE", "ERROR"}]
        return {
            "engine": "selenium_chromium",
            "browser_binary": browser_binary,
            "url": url,
            "exit_code": 0,
            "dom": dom,
            "dom_sha256": sha256_bytes(dom.encode("utf-8")),
            "console_capture": "webdriver_browser_log",
            "console_error_count": len(severe),
            "console_errors": severe,
            "stderr": None,
            "error": None,
        }
    except Exception as exc:
        return {
            "engine": "selenium_chromium",
            "browser_binary": browser_binary,
            "url": url,
            "exit_code": None,
            "dom": "",
            "dom_sha256": None,
            "console_capture": "webdriver_browser_log",
            "console_error_count": None,
            "console_errors": [],
            "stderr": None,
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


def cli_probe(url: str, browser_binary: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="aays_security_browser_") as profile:
        command = [
            browser_binary,
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
            completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", timeout=60, check=False)
            dom = completed.stdout or ""
            stderr = completed.stderr or ""
            console_lines = [
                line.strip()
                for line in stderr.splitlines()
                if re.search(r"(?:console|javascript|uncaught).*(?:error|exception)|(?:error|exception).*(?:console|javascript)", line, re.I)
            ]
            return {
                "engine": "chromium_cli",
                "browser_binary": browser_binary,
                "url": url,
                "exit_code": completed.returncode,
                "dom": dom,
                "dom_sha256": sha256_bytes(dom.encode("utf-8")) if dom else None,
                "console_capture": "chromium_stderr_console_filter",
                "console_error_count": len(console_lines),
                "console_errors": console_lines[:50],
                "stderr": stderr[-4000:] if stderr else None,
                "error": None if completed.returncode == 0 else f"BROWSER_EXIT_{completed.returncode}",
            }
        except Exception as exc:
            return {
                "engine": "chromium_cli",
                "browser_binary": browser_binary,
                "url": url,
                "exit_code": None,
                "dom": "",
                "dom_sha256": None,
                "console_capture": "chromium_stderr_console_filter",
                "console_error_count": None,
                "console_errors": [],
                "stderr": None,
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
        "url": url,
        "exit_code": None,
        "dom": "",
        "dom_sha256": None,
        "console_capture": None,
        "console_error_count": None,
        "console_errors": [],
        "stderr": None,
        "error": "BROWSER_EXECUTABLE_OR_WORKING_DRIVER_NOT_AVAILABLE",
        "attempts": attempts,
    }


def build_probe_html() -> str:
    return """<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\"><title>AAYS Security Public Safety Shard 1 Acceptance</title></head>
<body data-slot-id=\"security_public_safety_1\" data-output-semantics=\"AREA_LEVEL_PROXY\" data-parcel-measurement=\"false\" data-row-count=\"300\">
<h1>Security / Public Safety — Shard 1</h1>
<p id=\"semantic-label\">AREA_LEVEL_PROXY — LSOA/area-level evidence; not a parcel measurement.</p>
<p id=\"visible-rows\">Görünür / izlenen satır: yükleniyor</p>
<table><thead><tr><th>Parcel reference</th><th>Area proxy score</th><th>Source geography</th></tr></thead><tbody id=\"rows\"></tbody></table>
<script>
(async () => {
  const response = await fetch('./security_public_safety_1_area_level_proxy_300.json', {cache: 'no-store'});
  if (!response.ok) throw new Error(`proxy_json_http_${response.status}`);
  const payload = await response.json();
  const valid = payload.output_semantics === 'AREA_LEVEL_PROXY' && payload.parcel_measurement === false && payload.row_count === 300;
  document.body.dataset.loadedCount = String(payload.row_count);
  document.body.dataset.semanticValid = String(valid);
  document.getElementById('visible-rows').textContent = `Görünür / izlenen satır: ${payload.row_count}`;
  document.getElementById('rows').innerHTML = payload.rows.slice(0, 20).map(row => `<tr><td>${row.parcel_id}</td><td>${row.security_score_percent}</td><td>${row.source_geography_level}</td></tr>`).join('');
  if (!valid) throw new Error('area_level_proxy_contract_failed');
})().catch(error => { document.body.dataset.acceptanceError = String(error); console.error(error); });
</script></body></html>\n"""


def hydrate() -> dict[str, Any]:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8-sig"))
    with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    geojson = json.loads(SOURCE_GEOJSON.read_text(encoding="utf-8-sig"))
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        number = parcel_number(row.get("parcel_id"))
        if number is None or not (PARTITION_START <= number <= PARTITION_END):
            continue
        normalized = dict(row)
        normalized.update({
            "parcel_number": number,
            "measurement_level": "lsoa",
            "output_semantics": "AREA_LEVEL_PROXY",
            "parcel_measurement": False,
            "display_disclaimer": "LSOA/area-level proxy; not a parcel measurement",
        })
        rows.append(normalized)
    rows.sort(key=lambda item: int(item["parcel_number"]))
    feature_rows = []
    for feature in geojson.get("features", []):
        properties = feature.get("properties") or {}
        number = parcel_number(properties.get("parcel_id") or properties.get("id"))
        if number is None or not (PARTITION_START <= number <= PARTITION_END):
            continue
        copied = dict(feature)
        copied_properties = dict(properties)
        copied_properties.update({
            "parcel_number": number,
            "measurement_level": "lsoa",
            "output_semantics": "AREA_LEVEL_PROXY",
            "parcel_measurement": False,
            "display_disclaimer": "LSOA/area-level proxy; not a parcel measurement",
        })
        copied["properties"] = copied_properties
        feature_rows.append(copied)
    ids = [int(item["parcel_number"]) for item in rows]
    validations = {
        "manifest_selected_verified_rows_300": int(manifest.get("selected_verified_rows") or 0) == EXPECTED_ROWS,
        "csv_rows_300": len(rows) == EXPECTED_ROWS,
        "geojson_features_300": len(feature_rows) == EXPECTED_ROWS,
        "csv_geojson_count_parity": len(rows) == len(feature_rows),
        "all_rows_in_shard_1_30761": all(PARTITION_START <= value <= PARTITION_END for value in ids),
        "expected_ids_1_through_300": ids == list(range(1, EXPECTED_ROWS + 1)),
        "source_geography_lsoa": all(str(item.get("source_geography_level", "")).upper() == "LSOA" for item in rows),
        "official_source_only": all(str(item.get("source_url", "")).startswith("https://data.police.uk/") for item in rows),
        "no_manual_review_rows": all(str(item.get("needs_manual_review", "")).casefold() in {"false", "0", ""} for item in rows),
    }
    payload = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_step": TASK_STEP,
        "parcel_partition": {"start": PARTITION_START, "end": PARTITION_END, "count": PARTITION_END - PARTITION_START + 1},
        "row_count": len(rows),
        "measurement_level": "lsoa",
        "output_semantics": "AREA_LEVEL_PROXY",
        "parcel_measurement": False,
        "display_disclaimer": "LSOA/area-level proxy; not a parcel measurement",
        "source_url": manifest.get("source_url"),
        "source_snapshot_date": manifest.get("official_api_latest_month"),
        "source_manifest_sha256": file_sha256(SOURCE_MANIFEST),
        "source_csv_sha256": file_sha256(SOURCE_CSV),
        "source_geojson_sha256": file_sha256(SOURCE_GEOJSON),
        "validations": validations,
        "rows": rows,
        "geojson": {"type": "FeatureCollection", "features": feature_rows},
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "generated_at": utc_now(),
    }
    write_json(SHARD_DATA, payload)
    write_json(WEB_DATA, payload)
    PROBE_HTML.parent.mkdir(parents=True, exist_ok=True)
    PROBE_HTML.write_text(build_probe_html(), encoding="utf-8")
    return {"payload": payload, "validations": validations}


def run_acceptance() -> dict[str, Any]:
    slot_env = os.environ.get("AAYS_SLOT_ID")
    task_env = os.environ.get("AAYS_TASK_ID")
    if slot_env and slot_env != SLOT_ID:
        raise RuntimeError(f"WRONG_SLOT_ENV:{slot_env}")
    hydrated = hydrate()
    handler = partial(QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, name="aays-security-http", daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    probe_url = f"{base}/england_map_web/data/aays_21_slots/{SLOT_ID}/security_public_safety_1_acceptance.html?task={task_env or 'manual'}"
    data_url = f"{base}/england_map_web/data/aays_21_slots/{SLOT_ID}/security_public_safety_1_area_level_proxy_300.json?task={task_env or 'manual'}"
    matrix_url = f"{base}/{MATRIX_RELATIVE}?refresh=security_public_safety_1_20260720"
    try:
        http_proof = {
            "probe_html": http_get(probe_url),
            "proxy_json": http_get(data_url),
            "product_matrix": http_get(matrix_url),
            "canonical_8012_health": http_get("http://127.0.0.1:8012/health", timeout=5.0),
        }
        probe_browser = browser_probe(probe_url)
        matrix_browser = browser_probe(matrix_url)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    probe_dom = normalize_text(str(probe_browser.get("dom") or ""))
    matrix_dom = normalize_text(str(matrix_browser.get("dom") or ""))
    probe_checks = {
        "http_200": bool(http_proof["probe_html"].get("ok")),
        "json_http_200": bool(http_proof["proxy_json"].get("ok")),
        "browser_exit_zero": probe_browser.get("exit_code") == 0,
        "dom_row_count_300": "gorunur / izlenen satir: 300" in probe_dom and 'data-loaded-count="300"' in probe_dom,
        "dom_area_level_proxy": "area_level_proxy" in probe_dom,
        "dom_not_parcel_measurement": "not a parcel measurement" in probe_dom and 'data-parcel-measurement="false"' in probe_dom,
        "semantic_contract_true": 'data-semantic-valid="true"' in probe_dom,
        "console_zero": probe_browser.get("console_error_count") == 0,
        "dom_hash_present": bool(probe_browser.get("dom_sha256")),
        "http_hash_present": bool(http_proof["probe_html"].get("body_sha256") and http_proof["proxy_json"].get("body_sha256")),
    }
    matrix_checks = {
        "http_200": bool(http_proof["product_matrix"].get("ok")),
        "browser_exit_zero": matrix_browser.get("exit_code") == 0,
        "visible_rows_300": "gorunur / izlenen satir: 300" in matrix_dom or "visible / monitored rows: 300" in matrix_dom,
        "area_level_proxy_visible": "area_level_proxy" in matrix_dom and "not a parcel measurement" in matrix_dom,
        "console_zero": matrix_browser.get("console_error_count") == 0,
        "dom_hash_present": bool(matrix_browser.get("dom_sha256")),
    }
    hydration_pass = all(hydrated["validations"].values())
    shard_probe_pass = all(probe_checks.values())
    product_matrix_pass = all(matrix_checks.values())
    acceptance_pass = hydration_pass and shard_probe_pass and product_matrix_pass
    blockers: list[str] = []
    if not hydration_pass:
        blockers.append("HYDRATION_300_ROW_VALIDATION_FAILED")
    if not shard_probe_pass:
        blockers.append("SHARD_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FAILED")
    if not product_matrix_pass:
        blockers.append("PRODUCT_MATRIX_AREA_LEVEL_PROXY_DOM_ACCEPTANCE_FAILED")
    result = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": task_env,
        "task_step": TASK_STEP,
        "status": "PASS" if acceptance_pass else "BLOCKED",
        "acceptance_pass": acceptance_pass,
        "completed_steps": ["HYDRATE_300_ROWS"] + (["HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE"] if acceptance_pass else []),
        "first_unverified_step": None if acceptance_pass else "HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE",
        "blockers": blockers,
        "parcel_partition": {"start": PARTITION_START, "end": PARTITION_END, "count": PARTITION_END - PARTITION_START + 1},
        "hydrated_rows": hydrated["payload"]["row_count"],
        "measurement_level": "lsoa",
        "output_semantics": "AREA_LEVEL_PROXY",
        "parcel_measurement": False,
        "display_disclaimer": "LSOA/area-level proxy; not a parcel measurement",
        "hydration_validations": hydrated["validations"],
        "hash_proof": {
            "source_manifest_sha256": hydrated["payload"]["source_manifest_sha256"],
            "source_csv_sha256": hydrated["payload"]["source_csv_sha256"],
            "source_geojson_sha256": hydrated["payload"]["source_geojson_sha256"],
            "shard_output_sha256": file_sha256(SHARD_DATA),
            "web_output_sha256": file_sha256(WEB_DATA),
            "probe_html_sha256": file_sha256(PROBE_HTML),
        },
        "http_proof": http_proof,
        "probe_browser": {key: value for key, value in probe_browser.items() if key != "dom"},
        "probe_checks": probe_checks,
        "product_matrix_browser": {key: value for key, value in matrix_browser.items() if key != "dom"},
        "product_matrix_checks": matrix_checks,
        "source_evidence": {
            "source_url": hydrated["payload"]["source_url"],
            "source_snapshot_date": hydrated["payload"]["source_snapshot_date"],
            "matching_method": "parcel_centroid_inside_lsoa_polygon",
            "interpretation": "AREA_LEVEL_PROXY_ONLY_NOT_PARCEL_MEASUREMENT",
        },
        "outputs": [
            str(SHARD_DATA.relative_to(ROOT)).replace("\\", "/"),
            str(WEB_DATA.relative_to(ROOT)).replace("\\", "/"),
            str(PROBE_HTML.relative_to(ROOT)).replace("\\", "/"),
            str(REPORT_JSON.relative_to(ROOT)).replace("\\", "/"),
            str(REPORT_MD.relative_to(ROOT)).replace("\\", "/"),
        ],
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "product_final_ready": False,
        "checked_at": utc_now(),
    }
    return result


def write_report(result: dict[str, Any]) -> None:
    write_json(REPORT_JSON, result)
    lines = [
        "# Security / Public Safety Shard 1 — HTTP, Hash, DOM, Console and Browser Acceptance",
        "",
        f"- SLOT_ID: `{SLOT_ID}`",
        f"- Task: `{result.get('task_id')}`",
        f"- Parcel partition: `{PARTITION_START}-{PARTITION_END}`",
        f"- Status: `{result.get('status')}`",
        f"- Hydrated rows: `{result.get('hydrated_rows')}`",
        "- Data semantics: `AREA_LEVEL_PROXY`",
        "- Parcel measurement: `false`",
        "- Display disclaimer: `LSOA/area-level proxy; not a parcel measurement`",
        "",
        "## Acceptance",
        "",
        f"- Shard probe checks: `{json.dumps(result.get('probe_checks'), ensure_ascii=False, sort_keys=True)}`",
        f"- Product matrix checks: `{json.dumps(result.get('product_matrix_checks'), ensure_ascii=False, sort_keys=True)}`",
        f"- Blockers: `{'; '.join(result.get('blockers') or []) or 'none'}`",
        "",
        "## Safety",
        "",
        "`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    try:
        result = run_acceptance()
    except Exception as exc:
        result = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": os.environ.get("AAYS_TASK_ID"),
            "task_step": TASK_STEP,
            "status": "BLOCKED",
            "acceptance_pass": False,
            "completed_steps": [],
            "first_unverified_step": TASK_STEP,
            "blockers": [f"{type(exc).__name__}: {exc}"],
            "output_semantics": "AREA_LEVEL_PROXY",
            "parcel_measurement": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "final_ready": False,
            "product_final_ready": False,
            "checked_at": utc_now(),
        }
    write_report(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # A blocked acceptance is still a genuine declared evidence output. The single
    # coordinator must publish it so remote readback exposes the exact blocker.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
