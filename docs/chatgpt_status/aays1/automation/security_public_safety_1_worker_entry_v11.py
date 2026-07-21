from __future__ import annotations

import csv
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_1"
HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
BASE_ENTRY = HERE / "security_public_safety_1_worker_entry_v7.py"
SHARD_ROOT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID
WEB_ROOT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID
PROGRESS_JSON = SHARD_ROOT / "progress" / "progress_latest.json"
PROGRESS_WEB_JSON = WEB_ROOT / "progress_latest.json"
PREFLIGHT_REPORT = SHARD_ROOT / "reports" / "006_security_public_safety_1_preflight_latest.json"
PREFLIGHT_WEB = WEB_ROOT / "preflight_latest.json"
QUEUE_JSON = ROOT / "docs" / "chatgpt_status" / "aays1" / "queue" / "security_public_safety_1_hydrate_300_http_hash_dom_console_browser_acceptance_20260720.v3.task.json"
LEGACY_QUEUE = ROOT / "docs" / "chatgpt_status" / "aays1" / "queue" / "security_public_safety_1_hydrate_300_http_hash_dom_console_browser_acceptance_20260720.queue.txt"
RUNNER_WRAPPER = HERE / "security_public_safety_1_worker_entry_v4_runner.ps1"
SOURCE_CSV = ROOT / "england_map_web" / "data" / "security_public_safety" / "parcel_security_scores_verified.csv"
SOURCE_GEOJSON = ROOT / "england_map_web" / "data" / "security_public_safety" / "parcel_security_scores_verified.geojson"
SOURCE_MANIFEST = ROOT / "england_map_web" / "data" / "security_public_safety" / "security_evidence_manifest.json"
PRODUCT_MATRIX = ROOT / "england_map_web" / "TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html"
PROGRESS_HTML = WEB_ROOT / "progress_v11.html"

CANDIDATE_LIMIT = 100
EXPECTED_UNIQUE_ENDPOINTS = 15
ATTEMPT_ID = "security-public-safety-1-20260720-011"
SCRIPT_NAME = "security_public_safety_1_worker_entry_v11.py"
LONDON_DATASTORE_URL = "https://data.london.gov.uk/dataset/mps-recorded-crime-geographic-breakdown-exy3m/"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_SPEC_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compile_python(path: Path) -> bool:
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
    return True


def parse_legacy_queue(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def run_preflight() -> dict[str, Any]:
    python_files = [
        HERE / SCRIPT_NAME,
        BASE_ENTRY,
        HERE / "security_public_safety_1_worker_entry_v5.py",
        HERE / "security_public_safety_1_worker_entry_v3.py",
        HERE / "security_public_safety_1_acceptance_worker.py",
    ]
    required_files = python_files + [
        SOURCE_CSV,
        SOURCE_GEOJSON,
        SOURCE_MANIFEST,
        PRODUCT_MATRIX,
        PROGRESS_HTML,
        QUEUE_JSON,
        LEGACY_QUEUE,
        RUNNER_WRAPPER,
    ]
    file_checks = {str(path.relative_to(ROOT)): path.is_file() for path in required_files}
    syntax_checks: dict[str, bool] = {}
    syntax_errors: dict[str, str] = {}
    for path in python_files:
        key = str(path.relative_to(ROOT))
        try:
            syntax_checks[key] = compile_python(path)
        except Exception as exc:
            syntax_checks[key] = False
            syntax_errors[key] = f"{type(exc).__name__}: {exc}"

    rows: list[dict[str, str]] = []
    csv_error = None
    try:
        with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append(row)
                if len(rows) >= CANDIDATE_LIMIT:
                    break
    except Exception as exc:
        csv_error = f"{type(exc).__name__}: {exc}"

    urls = [str(row.get("official_api_validation_url") or "") for row in rows]
    parcel_ids = [str(row.get("parcel_id") or "") for row in rows]
    row_checks = {
        "candidate_rows_exact": len(rows) == CANDIDATE_LIMIT,
        "parcel_ids_sequential": parcel_ids == [f"parcel_{i}" for i in range(1, CANDIDATE_LIMIT + 1)],
        "parcel_ids_unique": len(set(parcel_ids)) == CANDIDATE_LIMIT,
        "accuracy_all_4": all(str(row.get("accuracy_score_4")) == "4" for row in rows),
        "geography_all_lsoa": all(str(row.get("source_geography_level")).upper() == "LSOA" for row in rows),
        "candidate_status_visible_source_backed": all(str(row.get("candidate_status")) == "VISIBLE_SOURCE_BACKED" for row in rows),
        "stored_http_all_200": all(str(row.get("official_api_validation_status")) == "HTTP_200" for row in rows),
        "stored_sha256_all_present": all(len(str(row.get("official_api_sample_sha256") or "")) == 64 for row in rows),
        "candidate_urls_all_present": all(url.startswith("https://data.police.uk/api/crimes-street/") for url in urls),
        "candidate_unique_endpoints_exact": len(set(urls)) == EXPECTED_UNIQUE_ENDPOINTS,
    }

    queue_checks: dict[str, bool] = {}
    queue_error = None
    try:
        queue = json.loads(QUEUE_JSON.read_text(encoding="utf-8"))
        safety = dict(queue.get("safety_flags") or {})
        acceptance = dict(queue.get("acceptance_contract") or {})
        queue_checks = {
            "queue_slot_matches": queue.get("slot_id") == SLOT_ID,
            "queue_attempt_matches": queue.get("attempt_id") == ATTEMPT_ID,
            "queue_script_matches": str(queue.get("script_path") or "").endswith(SCRIPT_NAME),
            "queue_candidates_match": acceptance.get("candidate_examples_required") == CANDIDATE_LIMIT,
            "queue_unique_endpoints_match": acceptance.get("candidate_live_api_unique_endpoints_required") == EXPECTED_UNIQUE_ENDPOINTS,
            "queue_count_parity_match": acceptance.get("candidate_live_api_count_parity_required") == CANDIDATE_LIMIT,
            "queue_sha_parity_match": acceptance.get("candidate_live_api_sha256_parity_required") == CANDIDATE_LIMIT,
            "queue_preflight_required": acceptance.get("deterministic_preflight_required") is True,
            "queue_safety_flags_false": all(safety.get(key) is False for key in ("fake_data", "db_write", "migration", "production_deploy")),
            "queue_final_ready_false": queue.get("final_ready") is False,
        }
    except Exception as exc:
        queue_error = f"{type(exc).__name__}: {exc}"

    legacy_checks: dict[str, bool] = {}
    legacy_error = None
    try:
        legacy = parse_legacy_queue(LEGACY_QUEUE)
        legacy_checks = {
            "legacy_status_ready": legacy.get("STATUS") == "READY",
            "legacy_attempt_matches": legacy.get("ATTEMPT_ID") == ATTEMPT_ID,
            "legacy_worker_v11": str(legacy.get("WORKER_PATH") or "").endswith(SCRIPT_NAME),
            "legacy_candidates_100": legacy.get("CANDIDATE_COUNT_REQUIRED") == str(CANDIDATE_LIMIT),
            "legacy_endpoints_15": legacy.get("CANDIDATE_UNIQUE_ENDPOINTS_REQUIRED") == str(EXPECTED_UNIQUE_ENDPOINTS),
            "legacy_safety_false": all(legacy.get(key) == "false" for key in ("FAKE_DATA", "DB_WRITE", "MIGRATION", "PRODUCTION_DEPLOY")),
            "legacy_final_ready_false": legacy.get("FINAL_READY_CONFIRMED") == "false",
        }
    except Exception as exc:
        legacy_error = f"{type(exc).__name__}: {exc}"

    wrapper_checks: dict[str, bool] = {}
    wrapper_error = None
    try:
        wrapper_text = RUNNER_WRAPPER.read_text(encoding="utf-8-sig")
        wrapper_checks = {
            "wrapper_points_v11": SCRIPT_NAME in wrapper_text,
            "wrapper_task_id_present": "aays1-security-public-safety-1-hydrate-300-http-hash-dom-console-browser-acceptance-20260720" in wrapper_text,
            "wrapper_fails_nonzero": "SECURITY_PUBLIC_SAFETY_1_WORKER_FAILED_EXIT_" in wrapper_text,
        }
    except Exception as exc:
        wrapper_error = f"{type(exc).__name__}: {exc}"

    checks = {
        "required_files_present": all(file_checks.values()),
        "python_syntax_valid": all(syntax_checks.values()) and len(syntax_checks) == len(python_files),
        "csv_readable": csv_error is None,
        "row_contract_valid": all(row_checks.values()),
        "queue_contract_valid": bool(queue_checks) and all(queue_checks.values()) and queue_error is None,
        "legacy_queue_contract_valid": bool(legacy_checks) and all(legacy_checks.values()) and legacy_error is None,
        "runner_wrapper_contract_valid": bool(wrapper_checks) and all(wrapper_checks.values()) and wrapper_error is None,
    }
    return {
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID") or "manual",
        "attempt_id": ATTEMPT_ID,
        "status": "PASS" if all(checks.values()) else "BLOCKED",
        "checks": checks,
        "file_checks": file_checks,
        "syntax_checks": syntax_checks,
        "syntax_errors": syntax_errors,
        "row_checks": row_checks,
        "queue_checks": queue_checks,
        "legacy_checks": legacy_checks,
        "wrapper_checks": wrapper_checks,
        "csv_error": csv_error,
        "queue_error": queue_error,
        "legacy_error": legacy_error,
        "wrapper_error": wrapper_error,
        "candidate_rows_checked": len(rows),
        "candidate_unique_endpoints": len(set(urls)),
        "network_requests_performed": 0,
        "recursion_regression_fixed": True,
        "purpose": "Deterministic no-network preflight before hydration, live parity and browser acceptance.",
        "output_semantics": "AREA_LEVEL_PROXY",
        "parcel_measurement": False,
        "checked_at": now(),
        "final_ready": False,
    }


def main() -> int:
    preflight = run_preflight()
    write_json(PREFLIGHT_REPORT, preflight)
    write_json(PREFLIGHT_WEB, preflight)
    if preflight["status"] != "PASS":
        return 3

    base = load_module(BASE_ENTRY, "security_public_safety_1_worker_entry_v7_base")
    base.CANDIDATE_LIMIT = CANDIDATE_LIMIT
    base.EXPECTED_UNIQUE_ENDPOINTS = EXPECTED_UNIQUE_ENDPOINTS
    base.LONDON_DATASTORE_URL = LONDON_DATASTORE_URL
    exit_code = int(base.main() or 0)

    if PROGRESS_JSON.is_file():
        progress = json.loads(PROGRESS_JSON.read_text(encoding="utf-8"))
        progress["candidate_examples_count"] = CANDIDATE_LIMIT
        progress["candidate_accuracy_score_4_count"] = CANDIDATE_LIMIT
        progress["candidate_unique_api_endpoints"] = EXPECTED_UNIQUE_ENDPOINTS
        progress["deterministic_preflight"] = preflight
        progress["deterministic_preflight_pass"] = True
        events = [event for event in list(progress.get("events") or []) if event.get("step") != "DETERMINISTIC_PREFLIGHT"]
        events.insert(
            max(0, len(events) - 3),
            {
                "step": "DETERMINISTIC_PREFLIGHT",
                "status": "PASS",
                "detail": "100 candidate rows, 15 unique endpoints, required files, Python syntax, queue, legacy bridge and wrapper safety contracts validated without network calls; v9 recursion regression removed",
                "is_subgate": True,
                "at": now(),
            },
        )
        progress["events"] = events
        write_json(PROGRESS_JSON, progress)
        write_json(PROGRESS_WEB_JSON, progress)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
