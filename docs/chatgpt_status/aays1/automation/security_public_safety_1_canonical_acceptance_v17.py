from __future__ import annotations

import hashlib
import importlib.util
import json
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_1"
TASK_ID = "aays1-security-public-safety-1-canonical-acceptance-v17-20260722"
ATTEMPT_ID = "security-public-safety-1-20260722-017"
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent

VISIBLE_ROWS = ROOT / "england_map_web" / "data" / "program_layer_matrix" / "security_public_safety_visible_rows.json"
HYDRATED_REMOTE_ARTIFACT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "security_public_safety_1_area_level_proxy_300.json"
PROGRESS_HTML = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "progress_v15.html"
PRODUCT_MATRIX = ROOT / "england_map_web" / "TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html"
ACCEPTANCE_BASE = HERE / "security_public_safety_1_acceptance_worker.py"

REPORT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID / "reports" / "011_security_public_safety_1_canonical_acceptance_v17_latest.json"
WEB_REPORT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "canonical_acceptance_v17_latest.json"
EXPECTED_GIT_BLOB_SHA = "ab876129928ec0370d482ca491f31a5dd1216aab"
EXPECTED_CANDIDATES = 130
EXPECTED_ENDPOINTS = 16


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


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
            "User-Agent": "AAYS-security-public-safety-1-v17/1.0",
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
                "http_status": int(response.status),
                "content_type": response.headers.get("Content-Type"),
                "body_bytes": len(body),
                "body_sha256": sha256(body),
                "json": parsed,
                "text": body.decode("utf-8", errors="replace"),
                "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
                "error": None,
            }
    except Exception as exc:
        return {
            "url": url,
            "http_status": None,
            "content_type": None,
            "body_bytes": 0,
            "body_sha256": None,
            "json": None,
            "text": "",
            "elapsed_ms": round((time.monotonic() - started) * 1000, 2),
            "error": f"{type(exc).__name__}: {exc}",
        }


def read_existing_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    required = [VISIBLE_ROWS, HYDRATED_REMOTE_ARTIFACT, PROGRESS_HTML, PRODUCT_MATRIX, ACCEPTANCE_BASE]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"REQUIRED_FILES_MISSING:{missing}")

    visible_bytes = VISIBLE_ROWS.read_bytes()
    hydrated_bytes = HYDRATED_REMOTE_ARTIFACT.read_bytes()
    visible = json.loads(visible_bytes.decode("utf-8-sig"))
    hydrated = json.loads(hydrated_bytes.decode("utf-8-sig"))
    rows = list(visible.get("rows") or [])
    hydrated_rows = list(hydrated.get("rows") or [])

    ids = [str(row.get("parcel_id") or "") for row in rows]
    checks = {
        "visible_rows_300": len(rows) == 300,
        "hydrated_rows_300": len(hydrated_rows) == 300,
        "visible_and_hydrated_bytes_equal": visible_bytes == hydrated_bytes,
        "remote_git_blob_sha_matches": git_blob_sha(hydrated_bytes) == EXPECTED_GIT_BLOB_SHA,
        "ids_1_to_300": ids == [f"parcel_{index}" for index in range(1, 301)],
        "accuracy_score_4_all_300": all(int(row.get("accuracy_score_4") or 0) == 4 for row in rows),
        "lsoa_all_300": all(str(row.get("source_geography_level") or "").upper() == "LSOA" for row in rows),
        "stored_http_200_all_300": all(str(row.get("official_api_validation_status") or "") == "HTTP_200" for row in rows),
        "stored_sha256_all_300": all(len(str(row.get("official_api_sample_sha256") or "")) == 64 for row in rows),
        "official_source_urls_all_300": all(str(row.get("source_url") or "").startswith("https://data.police.uk/") for row in rows),
    }
    if not all(checks.values()):
        raise RuntimeError(f"EXISTING_REMOTE_ARTIFACT_CONTRACT_FAILED:{checks}")
    return rows, {
        "status": "PASS",
        "checks": checks,
        "visible_file_sha256": sha256(visible_bytes),
        "hydrated_file_sha256": sha256(hydrated_bytes),
        "git_blob_sha": git_blob_sha(hydrated_bytes),
        "rows": len(rows),
        "accuracy_score_4_rows": sum(int(row.get("accuracy_score_4") or 0) == 4 for row in rows),
        "hydration_replayed": False,
    }


def validate_canonical_candidates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = rows[:EXPECTED_CANDIDATES]
    ids = [str(row.get("parcel_id") or "") for row in candidates]
    static_checks = {
        "candidate_count_130": len(candidates) == EXPECTED_CANDIDATES,
        "candidate_ids_1_to_130": ids == [f"parcel_{index}" for index in range(1, EXPECTED_CANDIDATES + 1)],
        "accuracy_score_4_all_130": all(int(row.get("accuracy_score_4") or 0) == 4 for row in candidates),
        "lsoa_all_130": all(str(row.get("source_geography_level") or "").upper() == "LSOA" for row in candidates),
        "stored_http_200_all_130": all(str(row.get("official_api_validation_status") or "") == "HTTP_200" for row in candidates),
        "stored_sha256_all_130": all(len(str(row.get("official_api_sample_sha256") or "")) == 64 for row in candidates),
    }

    by_url: dict[str, list[dict[str, Any]]] = {}
    for row in candidates:
        url = str(row.get("official_api_validation_url") or "")
        if not url.startswith("https://data.police.uk/api/crimes-street/all-crime?"):
            raise RuntimeError(f"INVALID_CANDIDATE_URL:{row.get('parcel_id')}:{url}")
        by_url.setdefault(url, []).append(row)
    static_checks["unique_endpoint_count_16"] = len(by_url) == EXPECTED_ENDPOINTS
    if not all(static_checks.values()):
        raise RuntimeError(f"CANONICAL_STATIC_CONTRACT_FAILED:{static_checks}")

    endpoint_results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=8, thread_name_prefix="aays_security_v17") as pool:
        futures = {pool.submit(fetch, url, "application/json"): url for url in sorted(by_url)}
        for future in as_completed(futures):
            url = futures[future]
            try:
                endpoint_results[url] = future.result()
            except Exception as exc:
                endpoint_results[url] = {
                    "url": url,
                    "http_status": None,
                    "json": None,
                    "body_sha256": None,
                    "error": f"{type(exc).__name__}: {exc}",
                }

    endpoint_summary: list[dict[str, Any]] = []
    candidate_results: list[dict[str, Any]] = []
    for url in sorted(by_url):
        live = endpoint_results[url]
        parsed = live.get("json")
        live_count = len(parsed) if isinstance(parsed, list) else None
        endpoint_ok = live.get("http_status") == 200 and isinstance(parsed, list)
        endpoint_summary.append({
            "url": url,
            "candidate_reuse_count": len(by_url[url]),
            "http_status": live.get("http_status"),
            "json_array": isinstance(parsed, list),
            "live_count": live_count,
            "live_sha256": live.get("body_sha256"),
            "elapsed_ms": live.get("elapsed_ms"),
            "error": live.get("error"),
            "status": "PASS" if endpoint_ok else "BLOCKED",
        })
        for row in by_url[url]:
            stored_count = int(row.get("official_api_sample_crime_count") or 0)
            stored_hash = str(row.get("official_api_sample_sha256") or "")
            checks = {
                "http_200": live.get("http_status") == 200,
                "json_array": isinstance(parsed, list),
                "count_parity": live_count == stored_count,
                "sha256_parity": live.get("body_sha256") == stored_hash,
                "accuracy_score_4": int(row.get("accuracy_score_4") or 0) == 4,
                "lsoa_semantics": str(row.get("source_geography_level") or "").upper() == "LSOA",
            }
            candidate_results.append({
                "parcel_id": row.get("parcel_id"),
                "security_score_percent": row.get("security_score_percent"),
                "confidence_score": row.get("confidence_score"),
                "accuracy_score_4": row.get("accuracy_score_4"),
                "official_api_url": url,
                "stored_count": stored_count,
                "live_count": live_count,
                "stored_sha256": stored_hash,
                "live_sha256": live.get("body_sha256"),
                "checks": checks,
                "status": "PASS" if all(checks.values()) else "BLOCKED",
                "output_semantics": "AREA_LEVEL_PROXY",
                "parcel_measurement": False,
            })

    candidate_results.sort(key=lambda item: int(str(item["parcel_id"]).rsplit("_", 1)[1]))
    candidate_passed = sum(item["status"] == "PASS" for item in candidate_results)
    endpoint_passed = sum(item["status"] == "PASS" for item in endpoint_summary)
    status = "PASS" if candidate_passed == EXPECTED_CANDIDATES and endpoint_passed == EXPECTED_ENDPOINTS else "BLOCKED"
    return {
        "schema_version": 2,
        "status": status,
        "candidate_count": len(candidate_results),
        "candidate_passed": candidate_passed,
        "unique_endpoint_count": len(endpoint_summary),
        "unique_endpoint_http_json_passed": endpoint_passed,
        "network_requests_performed": len(endpoint_summary),
        "duplicate_live_requests_avoided": EXPECTED_CANDIDATES - len(endpoint_summary),
        "parallel_fetch_workers": 8,
        "static_checks": static_checks,
        "endpoint_results": endpoint_summary,
        "candidates": candidate_results,
        "output_semantics": "AREA_LEVEL_PROXY",
        "measurement_level": "lsoa",
        "parcel_measurement": False,
        "checked_at": now(),
    }


def official_source_refresh() -> dict[str, Any]:
    urls = {
        "latest": "https://data.police.uk/api/crime-last-updated",
        "availability": "https://data.police.uk/api/crimes-street-dates",
        "force": "https://data.police.uk/api/forces/metropolitan",
        "london": "https://data.london.gov.uk/dataset/mps-recorded-crime-geographic-breakdown-exy3m/",
        "changelog": "https://data.police.uk/changelog/",
    }
    results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=5, thread_name_prefix="aays_security_sources") as pool:
        futures = {
            pool.submit(fetch, url, "application/json" if key in {"latest", "availability", "force"} else "text/html"): key
            for key, url in urls.items()
        }
        for future in as_completed(futures):
            key = futures[future]
            results[key] = future.result()

    latest_json = results["latest"].get("json")
    availability_json = results["availability"].get("json")
    force_json = results["force"].get("json")
    london_text = str(results["london"].get("text") or "").casefold()
    changelog_text = str(results["changelog"].get("text") or "").casefold()
    checks = {
        "police_latest_http_200": results["latest"].get("http_status") == 200,
        "police_latest_month_2026_05": isinstance(latest_json, dict) and str(latest_json.get("date")) == "2026-05-01",
        "availability_http_200": results["availability"].get("http_status") == 200,
        "availability_contains_2026_05": isinstance(availability_json, list) and any(str(item.get("date")) == "2026-05" for item in availability_json if isinstance(item, dict)),
        "metropolitan_force_http_200": results["force"].get("http_status") == 200,
        "metropolitan_force_identity": isinstance(force_json, dict) and force_json.get("id") == "metropolitan" and "Metropolitan Police" in str(force_json.get("name")),
        "london_catalogue_http_200": results["london"].get("http_status") == 200,
        "london_catalogue_lsoa": "lsoa" in london_text,
        "london_catalogue_june_2026": "jun 2026" in london_text or "june 2026" in london_text,
        "changelog_http_200": results["changelog"].get("http_status") == 200,
        "may_2026_missing_force_limit_recorded": all(name in changelog_text for name in ("british transport police", "gloucestershire", "greater manchester", "lincolnshire")),
    }
    return {
        "status": "PASS" if all(checks.values()) else "BLOCKED",
        "checks": checks,
        "results": {
            key: {field: value for field, value in result.items() if field not in {"json", "text"}}
            for key, result in results.items()
        },
        "quality_limits": [
            "Street-level results cover a one-mile radius and published locations are approximate/anonymised.",
            "May 2026 crime data is missing for British Transport Police, Gloucestershire, Greater Manchester and Lincolnshire; values are not inferred.",
            "London LSOA data omits sexual offences and has CONNECT comparability limits.",
        ],
        "checked_at": now(),
    }


def browser_acceptance() -> dict[str, Any]:
    acceptance = load_module(ACCEPTANCE_BASE, "security_public_safety_1_acceptance_base_v17")
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(acceptance.QuietHandler, directory=str(ROOT)))
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    progress_url = f"{base}/england_map_web/data/aays_21_slots/{SLOT_ID}/progress_v15.html?task={TASK_ID}"
    visible_url = f"{base}/england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json?task={TASK_ID}"
    matrix_url = f"{base}/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=security_public_safety_1_v17"
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
        "loaded_rows_300": 'data-loaded-count="300"' in progress_dom or "300 kaynakli satir" in progress_dom,
        "semantic_valid": 'data-semantic-valid="true"' in progress_dom,
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
    status = "PASS" if all(progress_checks.values()) and all(matrix_checks.values()) else "BLOCKED"
    return {
        "status": status,
        "http_proof": http_proof,
        "progress_browser": {key: value for key, value in progress_browser.items() if key != "dom"},
        "progress_checks": progress_checks,
        "product_matrix_browser": {key: value for key, value in matrix_browser.items() if key != "dom"},
        "product_matrix_checks": matrix_checks,
        "checked_at": now(),
    }


def run() -> dict[str, Any]:
    rows, artifact = read_existing_rows()
    source_result = official_source_refresh()
    parity_result = validate_canonical_candidates(rows)
    browser_result = browser_acceptance()

    gates = {
        "reuse_existing_remote_300_row_artifact_without_hydration_replay": artifact["status"] == "PASS" and artifact["hydration_replayed"] is False,
        "official_source_refresh": source_result["status"] == "PASS",
        "canonical_130_candidate_16_endpoint_live_count_sha_parity": parity_result["status"] == "PASS",
        "headless_browser_dom_console_product_matrix_acceptance": browser_result["status"] == "PASS",
    }
    status = "PASS" if all(gates.values()) else "BLOCKED"
    blockers = [name for name, passed in gates.items() if not passed]
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": status,
        "acceptance_pass": status == "PASS",
        "first_unverified_step": "COMMIT_PUSH_REMOTE_READBACK" if status == "PASS" else blockers[0],
        "blockers": blockers,
        "gates": gates,
        "existing_remote_artifact": artifact,
        "official_source_refresh": source_result,
        "canonical_live_parity": parity_result,
        "browser_acceptance": browser_result,
        "verified_rows": 300,
        "accuracy_score_4_rows": 300,
        "canonical_candidate_target": EXPECTED_CANDIDATES,
        "canonical_unique_endpoint_target": EXPECTED_ENDPOINTS,
        "output_semantics": "AREA_LEVEL_PROXY",
        "measurement_level": "lsoa",
        "parcel_measurement": False,
        "display_disclaimer": "LSOA/area-level proxy; not a parcel measurement",
        "single_runner_only": True,
        "hydration_replayed": False,
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
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "status": "BLOCKED",
            "acceptance_pass": False,
            "first_unverified_step": "CANONICAL_ACCEPTANCE_V17",
            "blockers": [f"{type(exc).__name__}: {exc}"],
            "output_semantics": "AREA_LEVEL_PROXY",
            "parcel_measurement": False,
            "single_runner_only": True,
            "hydration_replayed": False,
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
    return 0 if result.get("status") == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
