from __future__ import annotations

import importlib.util
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

SLOT_ID = "security_public_safety_1"
TASK_ID = "aays1-security-public-safety-1-canonical-acceptance-v17-20260722"
ATTEMPT_ID = "security-public-safety-1-20260722-017"
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CORE = HERE / "security_public_safety_1_canonical_acceptance_v17.py"
QUEUE_JSON = ROOT / "docs" / "chatgpt_status" / "aays1" / "queue" / "security_public_safety_1_canonical_acceptance_v17_20260722.task.json"
LEGACY_QUEUE = ROOT / "docs" / "chatgpt_status" / "aays1" / "queue" / "security_public_safety_1_canonical_acceptance_v17_20260722.queue.txt"
MANIFEST = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "canonical_130_endpoint_manifest_20260722.json"
PREFLIGHT_REPORT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID / "reports" / "012_security_public_safety_1_v17_runtime_preflight_latest.json"
PREFLIGHT_WEB = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "runtime_preflight_v17_latest.json"
CORE_REPORT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID / "reports" / "011_security_public_safety_1_canonical_acceptance_v17_latest.json"
CORE_WEB_REPORT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "canonical_acceptance_v17_latest.json"
PUBLISHER_CANDIDATE_REPORT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID / "reports" / "015_security_public_safety_1_publisher_candidate_v17_latest.json"
PUBLISHER_CANDIDATE_WEB = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "publisher_candidate_v17_latest.json"
WRAPPER_NAME = Path(__file__).name
MAX_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = (1.0, 2.0)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_legacy(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_SPEC_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_preflight() -> dict[str, Any]:
    required = [CORE, QUEUE_JSON, LEGACY_QUEUE, MANIFEST]
    file_checks = {str(path.relative_to(ROOT)): path.is_file() for path in required}
    errors: list[str] = []
    checks: dict[str, bool] = {"required_files_present": all(file_checks.values())}

    try:
        compile(CORE.read_text(encoding="utf-8"), str(CORE), "exec")
        checks["core_python_compile"] = True
    except Exception as exc:
        checks["core_python_compile"] = False
        errors.append(f"CORE_COMPILE:{type(exc).__name__}:{exc}")

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
        checks.update({
            "manifest_candidates_130": manifest.get("candidate_rows") == 130,
            "manifest_accuracy_130": manifest.get("accuracy_score_4_rows") == 130,
            "manifest_stored_http_130": manifest.get("stored_http_200_rows") == 130,
            "manifest_stored_sha_130": manifest.get("stored_sha256_rows") == 130,
            "manifest_endpoints_16": manifest.get("unique_endpoints") == 16,
            "manifest_distribution_130": manifest.get("row_count_sum") == 130,
            "manifest_acceptance_false": manifest.get("acceptance_evidence") is False,
        })
    except Exception as exc:
        errors.append(f"MANIFEST:{type(exc).__name__}:{exc}")
        checks["manifest_readable"] = False

    try:
        queue = json.loads(QUEUE_JSON.read_text(encoding="utf-8-sig"))
        contract = dict(queue.get("execution_contract") or {})
        safety = dict(queue.get("safety_flags") or {})
        checks.update({
            "queue_task_matches": queue.get("task_id") == TASK_ID,
            "queue_attempt_matches": queue.get("attempt_id") == ATTEMPT_ID,
            "queue_wrapper_path": str(queue.get("script_path") or "").endswith(WRAPPER_NAME),
            "queue_no_replay": contract.get("hydration_replay_forbidden") is True,
            "queue_candidates_130": contract.get("canonical_candidate_count") == 130,
            "queue_endpoints_16": contract.get("canonical_unique_endpoints") == 16,
            "queue_safety_false": all(safety.get(key) is False for key in ("fake_data", "db_write", "migration", "production_deploy")),
            "queue_final_ready_false": queue.get("final_ready") is False,
        })
    except Exception as exc:
        errors.append(f"QUEUE:{type(exc).__name__}:{exc}")
        checks["queue_readable"] = False

    try:
        legacy = parse_legacy(LEGACY_QUEUE)
        checks.update({
            "legacy_task_matches": legacy.get("TASK_ID") == TASK_ID,
            "legacy_attempt_matches": legacy.get("ATTEMPT_ID") == ATTEMPT_ID,
            "legacy_wrapper_path": str(legacy.get("WORKER_PATH") or "").endswith(WRAPPER_NAME),
            "legacy_no_replay": legacy.get("HYDRATION_REPLAY_FORBIDDEN") == "true",
            "legacy_candidates_130": legacy.get("CANDIDATE_COUNT_REQUIRED") == "130",
            "legacy_endpoints_16": legacy.get("CANDIDATE_UNIQUE_ENDPOINTS_REQUIRED") == "16",
            "legacy_safety_false": all(legacy.get(key) == "false" for key in ("FAKE_DATA", "DB_WRITE", "MIGRATION", "PRODUCTION_DEPLOY")),
            "legacy_final_ready_false": legacy.get("FINAL_READY_CONFIRMED") == "false",
        })
    except Exception as exc:
        errors.append(f"LEGACY:{type(exc).__name__}:{exc}")
        checks["legacy_readable"] = False

    status = "PASS" if checks and all(checks.values()) else "BLOCKED"
    return {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": status,
        "checks": checks,
        "file_checks": file_checks,
        "errors": errors,
        "network_requests_performed": 0,
        "hydration_replayed": False,
        "retry_policy": {"max_attempts": MAX_ATTEMPTS, "delays_seconds": list(RETRY_DELAYS_SECONDS), "retry_only_transient": True},
        "publisher_candidate_required": True,
        "publisher_candidate_paths": [str(PUBLISHER_CANDIDATE_REPORT.relative_to(ROOT)), str(PUBLISHER_CANDIDATE_WEB.relative_to(ROOT))],
        "output_semantics": "AREA_LEVEL_PROXY",
        "parcel_measurement": False,
        "checked_at": now(),
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


def make_retry_fetch(original_fetch: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    def retry_fetch(url: str, accept: str = "application/json,text/html,*/*", timeout: float = 45.0) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for attempt in range(1, MAX_ATTEMPTS + 1):
            result = original_fetch(url, accept, timeout)
            result["attempt"] = attempt
            error = str(result.get("error") or "")
            status = result.get("http_status")
            success = status == 200 and not error
            if success:
                return result
            permanent_4xx = "HTTP Error 4" in error and "HTTP Error 429" not in error
            if permanent_4xx or attempt >= MAX_ATTEMPTS:
                return result
            time.sleep(RETRY_DELAYS_SECONDS[attempt - 1])
        return result
    return retry_fetch


def build_publisher_candidate(core_result: dict[str, Any], exit_code: int) -> dict[str, Any]:
    parity = dict(core_result.get("canonical_live_parity") or {})
    browser = dict(core_result.get("browser_acceptance") or {})
    acceptance_pass = core_result.get("acceptance_pass") is True
    completed_units = 7 if acceptance_pass else 5
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": "READY_FOR_SINGLE_PUBLISHER_COMMIT_PUSH_READBACK" if acceptance_pass else "BLOCKED_RUNTIME_ACCEPTANCE",
        "acceptance_pass": acceptance_pass,
        "core_exit_code": exit_code,
        "canonical_progress_candidate": {
            "completed_units": completed_units,
            "total_units": 8,
            "overall_percent": 87.5 if acceptance_pass else 62.5,
            "percent_change_from_published_62_5": 25.0 if acceptance_pass else 0.0,
            "publisher_readback_still_required": True,
            "may_publish_8_of_8": False,
        },
        "runtime_evidence": {
            "candidate_count": parity.get("candidate_count"),
            "candidate_passed": parity.get("candidate_passed"),
            "unique_endpoint_count": parity.get("unique_endpoint_count"),
            "unique_endpoint_http_json_passed": parity.get("unique_endpoint_http_json_passed"),
            "network_requests_performed": parity.get("network_requests_performed"),
            "duplicate_live_requests_avoided": parity.get("duplicate_live_requests_avoided"),
            "browser_status": browser.get("status"),
            "progress_console_errors": (browser.get("progress_browser") or {}).get("console_error_count"),
            "product_matrix_console_errors": (browser.get("product_matrix_browser") or {}).get("console_error_count"),
        },
        "source_reports": {"core_report": str(CORE_REPORT.relative_to(ROOT)), "core_web_report": str(CORE_WEB_REPORT.relative_to(ROOT))},
        "first_unverified_step": "SINGLE_PUBLISHER_COMMIT_PUSH_REMOTE_READBACK" if acceptance_pass else core_result.get("first_unverified_step"),
        "blockers": [] if acceptance_pass else list(core_result.get("blockers") or []),
        "output_semantics": "AREA_LEVEL_PROXY",
        "measurement_level": "lsoa",
        "parcel_measurement": False,
        "hydration_replayed": False,
        "single_runner_only": True,
        "child_direct_push_forbidden": True,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "generated_at": now(),
    }


def main() -> int:
    preflight = run_preflight()
    write_json(PREFLIGHT_REPORT, preflight)
    write_json(PREFLIGHT_WEB, preflight)
    if preflight["status"] != "PASS":
        return 3
    core = load_module(CORE, "security_public_safety_1_canonical_acceptance_v17_core")
    core.fetch = make_retry_fetch(core.fetch)
    exit_code = int(core.main() or 0)
    if CORE_REPORT.is_file():
        try:
            core_result = json.loads(CORE_REPORT.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            core_result = {"slot_id": SLOT_ID, "task_id": TASK_ID, "attempt_id": ATTEMPT_ID, "acceptance_pass": False, "first_unverified_step": "READ_CORE_ACCEPTANCE_REPORT", "blockers": [f"{type(exc).__name__}: {exc}"]}
    else:
        core_result = {"slot_id": SLOT_ID, "task_id": TASK_ID, "attempt_id": ATTEMPT_ID, "acceptance_pass": False, "first_unverified_step": "CORE_ACCEPTANCE_REPORT_MISSING", "blockers": ["CORE_ACCEPTANCE_REPORT_MISSING"]}
    identity_ok = core_result.get("slot_id") == SLOT_ID and core_result.get("task_id") == TASK_ID and core_result.get("attempt_id") == ATTEMPT_ID
    if not identity_ok:
        core_result["acceptance_pass"] = False
        core_result["first_unverified_step"] = "CORE_RESULT_IDENTITY_MISMATCH"
        core_result["blockers"] = list(core_result.get("blockers") or []) + ["CORE_RESULT_IDENTITY_MISMATCH"]
    publisher_candidate = build_publisher_candidate(core_result, exit_code)
    write_json(PUBLISHER_CANDIDATE_REPORT, publisher_candidate)
    write_json(PUBLISHER_CANDIDATE_WEB, publisher_candidate)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
