from __future__ import annotations

import hashlib
import importlib.util
import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

SLOT_ID = "security_public_safety_1"
TASK_ID = "aays1-security-public-safety-1-canonical-acceptance-v17-20260722"
ATTEMPT_ID = "security-public-safety-1-20260722-017"
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CORE = HERE / "security_public_safety_1_canonical_acceptance_v17.py"
CARRIER = HERE / "security_public_safety_1_canonical_acceptance_v17_carrier.ps1"
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
CARRIER_NAME = CARRIER.name
EXPECTED_CARRIER_BLOB_SHA = "a3cb8d7129caeb8e694f41c943dc3cf2a3277071"
MAX_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = (1.0, 2.0)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


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
    required = [CORE, CARRIER, QUEUE_JSON, LEGACY_QUEUE, MANIFEST]
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
        checks["carrier_blob_exact"] = git_blob_sha(CARRIER) == EXPECTED_CARRIER_BLOB_SHA
        carrier_text = CARRIER.read_text(encoding="utf-8-sig")
        checks["carrier_invokes_python_wrapper"] = WRAPPER_NAME in carrier_text and "POWERSHELL_CARRIER_TO_PYTHON" in carrier_text
        checks["carrier_safety_contract"] = all(token in carrier_text for token in ("NEW_RUNNER=false", "PARALLEL_RUNNER=false", "FINAL_READY=false"))
        checks["carrier_internal_watchdog_1500"] = "$internalTimeoutSeconds = 1500" in carrier_text and "INTERNAL_TIMEOUT_SECONDS=" in carrier_text
        checks["carrier_process_tree_cleanup"] = "taskkill.exe" in carrier_text and "/T /F" in carrier_text and "PROCESS_TREE_KILL_ON_TIMEOUT=true" in carrier_text
    except Exception as exc:
        checks["carrier_readable"] = False
        errors.append(f"CARRIER:{type(exc).__name__}:{exc}")

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
            "queue_carrier_path": str(queue.get("script_path") or "").endswith(CARRIER_NAME),
            "queue_python_wrapper_path": str(queue.get("python_wrapper_path") or "").endswith(WRAPPER_NAME),
            "queue_carrier_blob": queue.get("carrier_blob_sha") == EXPECTED_CARRIER_BLOB_SHA,
            "queue_execution_host": contract.get("execution_host") == "powershell_carrier_to_python",
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
            "legacy_carrier_path": str(legacy.get("WORKER_PATH") or "").endswith(CARRIER_NAME),
            "legacy_python_wrapper_path": str(legacy.get("PYTHON_WORKER_PATH") or "").endswith(WRAPPER_NAME),
            "legacy_carrier_blob": legacy.get("CARRIER_BLOB_SHA") == EXPECTED_CARRIER_BLOB_SHA,
            "legacy_execution_host": legacy.get("EXECUTION_HOST") == "powershell_carrier_to_python",
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
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": status,
        "checks": checks,
        "file_checks": file_checks,
        "errors": errors,
        "network_requests_performed": 0,
        "hydration_replayed": False,
        "execution_host": "powershell_carrier_to_python",
        "carrier_path": str(CARRIER.relative_to(ROOT)),
        "carrier_blob_sha": EXPECTED_CARRIER_BLOB_SHA,
        "python_wrapper_path": str(Path(__file__).resolve().relative_to(ROOT)),
        "retry_policy": {"max_attempts": MAX_ATTEMPTS, "delays_seconds": list(RETRY_DELAYS_SECONDS), "retry_only_transient": True},
        "publisher_candidate_required": True,
        "failure_receipts_required": True,
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
            if status == 200 and not error:
                return result
            permanent_4xx = "HTTP Error 4" in error and "HTTP Error 429" not in error
            if permanent_4xx or attempt >= MAX_ATTEMPTS:
                return result
            time.sleep(RETRY_DELAYS_SECONDS[attempt - 1])
        return result
    return retry_fetch


def blocked_core_result(first_unverified_step: str, blocker: str, detail: Any = None) -> dict[str, Any]:
    blockers = [blocker]
    if detail not in (None, "", [], {}):
        blockers.append(f"DETAIL:{detail}")
    return {
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": "BLOCKED",
        "acceptance_pass": False,
        "canonical_live_parity": {
            "status": "BLOCKED",
            "candidate_count": None,
            "candidate_passed": None,
            "unique_endpoint_count": None,
            "unique_endpoint_http_json_passed": None,
            "network_requests_performed": 0,
        },
        "browser_acceptance": {"status": "BLOCKED"},
        "first_unverified_step": first_unverified_step,
        "blockers": blockers,
        "failure_receipt_generated": True,
        "hydration_replayed": False,
        "execution_host": "powershell_carrier_to_python",
        "output_semantics": "AREA_LEVEL_PROXY",
        "measurement_level": "lsoa",
        "parcel_measurement": False,
        "single_runner_only": True,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
        "generated_at": now(),
    }


def persist_core_result(payload: dict[str, Any]) -> None:
    write_json(CORE_REPORT, payload)
    write_json(CORE_WEB_REPORT, payload)


def build_publisher_candidate(core_result: dict[str, Any], exit_code: int) -> dict[str, Any]:
    parity = dict(core_result.get("canonical_live_parity") or {})
    browser = dict(core_result.get("browser_acceptance") or {})
    acceptance_pass = core_result.get("acceptance_pass") is True
    completed_units = 7 if acceptance_pass else 5
    return {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": "READY_FOR_SINGLE_PUBLISHER_COMMIT_PUSH_READBACK" if acceptance_pass else "BLOCKED_RUNTIME_ACCEPTANCE",
        "acceptance_pass": acceptance_pass,
        "core_exit_code": exit_code,
        "failure_receipt_generated": core_result.get("failure_receipt_generated") is True,
        "execution_host": "powershell_carrier_to_python",
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


def persist_publisher_candidate(core_result: dict[str, Any], exit_code: int) -> None:
    publisher_candidate = build_publisher_candidate(core_result, exit_code)
    write_json(PUBLISHER_CANDIDATE_REPORT, publisher_candidate)
    write_json(PUBLISHER_CANDIDATE_WEB, publisher_candidate)


def main() -> int:
    preflight = run_preflight()
    write_json(PREFLIGHT_REPORT, preflight)
    write_json(PREFLIGHT_WEB, preflight)

    if preflight["status"] != "PASS":
        core_result = blocked_core_result(
            "RUNTIME_PREFLIGHT_BLOCKED",
            "RUNTIME_PREFLIGHT_BLOCKED",
            {"errors": preflight.get("errors"), "failed_checks": [name for name, passed in preflight.get("checks", {}).items() if not passed]},
        )
        persist_core_result(core_result)
        persist_publisher_candidate(core_result, 3)
        return 3

    exit_code = 4
    try:
        core = load_module(CORE, "security_public_safety_1_canonical_acceptance_v17_core")
        core.fetch = make_retry_fetch(core.fetch)
        exit_code = int(core.main() or 0)
        if CORE_REPORT.is_file():
            try:
                core_result = json.loads(CORE_REPORT.read_text(encoding="utf-8-sig"))
            except Exception as exc:
                core_result = blocked_core_result("READ_CORE_ACCEPTANCE_REPORT", "CORE_ACCEPTANCE_REPORT_UNREADABLE", f"{type(exc).__name__}: {exc}")
                persist_core_result(core_result)
        else:
            core_result = blocked_core_result("CORE_ACCEPTANCE_REPORT_MISSING", "CORE_ACCEPTANCE_REPORT_MISSING")
            persist_core_result(core_result)
    except Exception as exc:
        core_result = blocked_core_result(
            "CORE_RUNTIME_EXCEPTION",
            f"CORE_RUNTIME_EXCEPTION:{type(exc).__name__}:{exc}",
            traceback.format_exc(limit=20),
        )
        persist_core_result(core_result)
        exit_code = 4

    identity_ok = core_result.get("slot_id") == SLOT_ID and core_result.get("task_id") == TASK_ID and core_result.get("attempt_id") == ATTEMPT_ID
    if not identity_ok:
        core_result["acceptance_pass"] = False
        core_result["status"] = "BLOCKED"
        core_result["first_unverified_step"] = "CORE_RESULT_IDENTITY_MISMATCH"
        core_result["blockers"] = list(core_result.get("blockers") or []) + ["CORE_RESULT_IDENTITY_MISMATCH"]
        core_result["failure_receipt_generated"] = True
        core_result["final_ready"] = False
        persist_core_result(core_result)
        exit_code = 4 if exit_code == 0 else exit_code

    persist_publisher_candidate(core_result, exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
