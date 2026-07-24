from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import threading
import time
import urllib.request
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_1"
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
BASE_ACCEPTANCE = HERE / "security_public_safety_1_acceptance_worker.py"
VISIBLE_ROWS = ROOT / "england_map_web" / "data" / "program_layer_matrix" / "security_public_safety_visible_rows.json"
PROGRESS_HTML = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "progress_v15.html"
WEB_REPORT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "browser_acceptance_v15_latest.json"
REPORT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID / "reports" / "008_security_public_safety_1_browser_acceptance_v15_latest.json"
PRODUCT_MATRIX = ROOT / "england_map_web" / "TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html"
SAMPLE_IDS = {"parcel_1", "parcel_3", "parcel_7"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_SPEC_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fetch(url: str, accept: str = "application/json,text/html,*/*", timeout: float = 45.0) -> dict[str, Any]:
    started = time.monotonic()
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-security-public-safety-1-v15/1.0",
            "Cache-Control": "no-cache",
            "Accept": accept,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            parsed: Any = None
            try:
                parsed = json.loads(body.decode("utf-8"))
            except Exception:
                parsed = None
            return {
                "url": url,
                "status": int(response.status),
                "content_type": response.headers.get("Content-Type"),
                "bytes": len(body),
                "sha256": sha256(body),
                "json": parsed,
                "text": body.decode("utf-8", errors="replace"),
                "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
                "error": None,
            }
    except Exception as exc:
        return {
            "url": url,
            "status": None,
            "content_type": None,
            "bytes": 0,
            "sha256": None,
            "json": None,
            "text": "",
            "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
            "error": f"{type(exc).__name__}: {exc}",
        }


def candidate_sample(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [row for row in rows if str(row.get("parcel_id")) in SAMPLE_IDS]
    selected.sort(key=lambda row: int(str(row.get("parcel_id")).rsplit("_", 1)[1]))
    results: list[dict[str, Any]] = []
    endpoint_cache: dict[str, dict[str, Any]] = {}
    for row in selected:
        url = str(row.get("official_api_validation_url") or "")
        if url not in endpoint_cache:
            endpoint_cache[url] = fetch(url, accept="application/json")
        live = endpoint_cache[url]
        parsed = live.get("json")
        live_count = len(parsed) if isinstance(parsed, list) else None
        checks = {
            "http_200": live.get("status") == 200,
            "json_array": isinstance(parsed, list),
            "count_parity": live_count == int(row.get("official_api_sample_crime_count") or 0),
            "sha256_parity": live.get("sha256") == str(row.get("official_api_sample_sha256") or ""),
            "accuracy_score_4": int(row.get("accuracy_score_4") or 0) == 4,
            "lsoa_semantics": str(row.get("source_geography_level") or "").upper() == "LSOA",
        }
        results.append(
            {
                "parcel_id": row.get("parcel_id"),
                "security_score_percent": row.get("security_score_percent"),
                "accuracy_score_4": row.get("accuracy_score_4"),
                "confidence_score": row.get("confidence_score"),
                "official_api_url": url,
                "stored_count": int(row.get("official_api_sample_crime_count") or 0),
                "live_count": live_count,
                "stored_sha256": row.get("official_api_sample_sha256"),
                "live_sha256": live.get("sha256"),
                "http_status": live.get("status"),
                "error": live.get("error"),
                "checks": checks,
                "status": "PASS" if all(checks.values()) else "BLOCKED",
                "output_semantics": "AREA_LEVEL_PROXY",
                "parcel_measurement": False,
            }
        )
    passed = sum(item["status"] == "PASS" for item in results)
    return {
        "status": "PASS" if len(results) == 3 and passed == 3 else "BLOCKED",
        "candidate_count": len(results),
        "candidate_passed": passed,
        "unique_endpoints": len(endpoint_cache),
        "results": results,
    }


def official_source_checks() -> dict[str, Any]:
    latest = fetch("https://data.police.uk/api/crime-last-updated", accept="application/json")
    force = fetch("https://data.police.uk/api/forces/metropolitan", accept="application/json")
    london = fetch("https://data.london.gov.uk/dataset/mps-recorded-crime-geographic-breakdown-exy3m/", accept="text/html")
    latest_json = latest.get("json")
    force_json = force.get("json")
    london_text = str(london.get("text") or "").casefold()
    checks = {
        "police_latest_http_200": latest.get("status") == 200,
        "police_latest_month_2026_05": isinstance(latest_json, dict) and str(latest_json.get("date")) == "2026-05-01",
        "metropolitan_force_http_200": force.get("status") == 200,
        "metropolitan_force_identity": isinstance(force_json, dict) and force_json.get("id") == "metropolitan" and "Metropolitan Police" in str(force_json.get("name")),
        "london_catalogue_http_200": london.get("status") == 200,
        "london_catalogue_lsoa": "lsoa" in london_text,
        "london_catalogue_june_2026": "jun 2026" in london_text or "june 2026" in london_text,
    }
    return {
        "status": "PASS" if all(checks.values()) else "BLOCKED",
        "checks": checks,
        "police_latest": {key: value for key, value in latest.items() if key not in {"json", "text"}},
        "metropolitan_force": {key: value for key, value in force.items() if key not in {"json", "text"}},
        "london_lsoa_catalogue": {key: value for key, value in london.items() if key not in {"json", "text"}},
    }


def run() -> dict[str, Any]:
    if not VISIBLE_ROWS.is_file():
        raise RuntimeError(f"VISIBLE_ROWS_MISSING:{VISIBLE_ROWS}")
    if not PROGRESS_HTML.is_file():
        raise RuntimeError(f"PROGRESS_HTML_MISSING:{PROGRESS_HTML}")
    if not PRODUCT_MATRIX.is_file():
        raise RuntimeError(f"PRODUCT_MATRIX_MISSING:{PRODUCT_MATRIX}")

    visible = json.loads(VISIBLE_ROWS.read_text(encoding="utf-8-sig"))
    rows = list(visible.get("rows") or [])
    ids = [str(row.get("parcel_id") or "") for row in rows]
    row_checks = {
        "visible_rows_300": len(rows) == 300,
        "ids_1_to_300": ids == [f"parcel_{index}" for index in range(1, 301)],
        "accuracy_score_4_all": all(int(row.get("accuracy_score_4") or 0) == 4 for row in rows),
        "lsoa_all": all(str(row.get("source_geography_level") or "").upper() == "LSOA" for row in rows),
        "stored_http_200_all": all(str(row.get("official_api_validation_status") or "") == "HTTP_200" for row in rows),
        "stored_sha256_all": all(len(str(row.get("official_api_sample_sha256") or "")) == 64 for row in rows),
        "source_urls_official": all(str(row.get("source_url") or "").startswith("https://data.police.uk/") for row in rows),
    }

    source_result = official_source_checks()
    sample_result = candidate_sample(rows)

    acceptance = load_module(BASE_ACCEPTANCE, "security_public_safety_1_acceptance_base_v15")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(acceptance.QuietHandler, directory=str(ROOT)))
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    progress_url = f"{base}/england_map_web/data/aays_21_slots/{SLOT_ID}/progress_v15.html"
    matrix_url = f"{base}/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=security_public_safety_1_v15"
    visible_url = f"{base}/england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json"
    try:
        http_proof = {
            "progress_v15": acceptance.http_get(progress_url),
            "visible_rows": acceptance.http_get(visible_url),
            "product_matrix": acceptance.http_get(matrix_url),
        }
        progress_browser = acceptance.browser_probe(progress_url)
        matrix_browser = acceptance.browser_probe(matrix_url)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    progress_dom = acceptance.normalized(str(progress_browser.get("dom") or ""))
    matrix_dom = acceptance.normalized(str(matrix_browser.get("dom") or ""))
    progress_checks = {
        "http_200": bool(http_proof["progress_v15"].get("ok")),
        "visible_json_http_200": bool(http_proof["visible_rows"].get("ok")),
        "browser_exit_zero": progress_browser.get("exit_code") == 0,
        "loaded_rows_300": "data-loaded-count=\"300\"" in progress_dom or "300 kaynakli satir" in progress_dom,
        "semantic_valid": "data-semantic-valid=\"true\"" in progress_dom,
        "area_level_proxy_visible": "area_level_proxy" in progress_dom,
        "not_parcel_measurement_visible": "parsel olcumu degildir" in progress_dom or "not a parcel measurement" in progress_dom,
        "console_zero": progress_browser.get("console_error_count") == 0,
        "dom_hash_present": bool(progress_browser.get("dom_sha256")),
    }
    matrix_checks = {
        "http_200": bool(http_proof["product_matrix"].get("ok")),
        "browser_exit_zero": matrix_browser.get("exit_code") == 0,
        "visible_rows_300": "gorunur / izlenen satir: 300" in matrix_dom or "visible / monitored rows: 300" in matrix_dom,
        "lsoa_proxy_contract_visible": (
            "area_level_proxy" in matrix_dom
            or "lsoa_proxy_partially_validated" in matrix_dom
            or ("olcum seviyesi" in matrix_dom and "lsoa" in matrix_dom and "parsel olcumu degildir" in matrix_dom)
        ),
        "console_zero": matrix_browser.get("console_error_count") == 0,
        "dom_hash_present": bool(matrix_browser.get("dom_sha256")),
    }

    gates = {
        "remote_visible_rows_reuse": all(row_checks.values()),
        "official_source_refresh": source_result["status"] == "PASS",
        "three_candidate_live_count_sha_parity": sample_result["status"] == "PASS",
        "progress_v15_http_dom_console_browser": all(progress_checks.values()),
        "product_matrix_lsoa_proxy_dom_console_browser": all(matrix_checks.values()),
    }
    status = "PASS" if all(gates.values()) else "BLOCKED"
    blockers = [name for name, passed in gates.items() if not passed]
    first_unverified = blockers[0] if blockers else "COMMIT_PUSH_REMOTE_READBACK"
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": "aays1-security-public-safety-1-hydrate-300-http-hash-dom-console-browser-acceptance-20260720",
        "attempt_id": "security-public-safety-1-20260722-015",
        "status": status,
        "acceptance_pass": status == "PASS",
        "first_unverified_step": first_unverified,
        "blockers": blockers,
        "row_checks": row_checks,
        "official_source_checks": source_result,
        "sample_live_parity": sample_result,
        "http_proof": http_proof,
        "progress_browser": {key: value for key, value in progress_browser.items() if key != "dom"},
        "progress_checks": progress_checks,
        "product_matrix_browser": {key: value for key, value in matrix_browser.items() if key != "dom"},
        "product_matrix_checks": matrix_checks,
        "gates": gates,
        "verified_rows": len(rows),
        "accuracy_score_4_rows": sum(int(row.get("accuracy_score_4") or 0) == 4 for row in rows),
        "sample_candidates": 3,
        "canonical_candidate_target": 130,
        "canonical_unique_endpoint_target": 16,
        "canonical_candidate_parity_claimed": False,
        "output_semantics": "AREA_LEVEL_PROXY",
        "measurement_level": "lsoa",
        "parcel_measurement": False,
        "display_disclaimer": "LSOA/area-level proxy; not a parcel measurement",
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "checked_at": now(),
    }


def main() -> int:
    try:
        result = run()
    except Exception as exc:
        result = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "attempt_id": "security-public-safety-1-20260722-015",
            "status": "BLOCKED",
            "acceptance_pass": False,
            "first_unverified_step": "BROWSER_ACCEPTANCE_RETRY_V15",
            "blockers": [f"{type(exc).__name__}: {exc}"],
            "output_semantics": "AREA_LEVEL_PROXY",
            "parcel_measurement": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "final_ready": False,
            "checked_at": now(),
        }
    write_json(REPORT, result)
    write_json(WEB_REPORT, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
