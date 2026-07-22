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
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": status,
        "checks": checks,
        "file_checks": file_checks,
        "errors": errors,
        "network_requests_performed": 0,
        "hydration_replayed": False,
        "retry_policy": {
            "max_attempts": MAX_ATTEMPTS,
            "delays_seconds": list(RETRY_DELAYS_SECONDS),
            "retry_only_transient": True,
        },
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


def main() -> int:
    preflight = run_preflight()
    write_json(PREFLIGHT_REPORT, preflight)
    write_json(PREFLIGHT_WEB, preflight)
    if preflight["status"] != "PASS":
        return 3

    core = load_module(CORE, "security_public_safety_1_canonical_acceptance_v17_core")
    core.fetch = make_retry_fetch(core.fetch)
    return int(core.main() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
