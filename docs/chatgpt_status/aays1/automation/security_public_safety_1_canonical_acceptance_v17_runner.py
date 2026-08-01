from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

SLOT_ID = "security_public_safety_1"
TASK_ID = "aays1-security-public-safety-1-canonical-acceptance-v17-20260722"
ATTEMPT_ID = "security-public-safety-1-20260722-017"
BRANCH = "codex/aays-single-runner-v5-20260706"
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CORE = HERE / "security_public_safety_1_canonical_acceptance_v17.py"
CARRIER = HERE / "security_public_safety_1_canonical_acceptance_v17_carrier.ps1"
QUEUE_REL = "docs/chatgpt_status/aays1/queue/security_public_safety_1_canonical_acceptance_v17_20260722.task.json"
LEGACY_REL = "docs/chatgpt_status/aays1/queue/security_public_safety_1_canonical_acceptance_v17_20260722.queue.txt"
QUEUE = ROOT / QUEUE_REL
LEGACY = ROOT / LEGACY_REL
MANIFEST = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_1/canonical_130_endpoint_manifest_20260722.json"
REPORT_DIR = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_1/reports"
WEB_DIR = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_1"
PREFLIGHT_REPORT = REPORT_DIR / "012_security_public_safety_1_v17_runtime_preflight_latest.json"
PREFLIGHT_WEB = WEB_DIR / "runtime_preflight_v17_latest.json"
CORE_REPORT = REPORT_DIR / "011_security_public_safety_1_canonical_acceptance_v17_latest.json"
CORE_WEB = WEB_DIR / "canonical_acceptance_v17_latest.json"
PUBLISHER_REPORT = REPORT_DIR / "015_security_public_safety_1_publisher_candidate_v17_latest.json"
PUBLISHER_WEB = WEB_DIR / "publisher_candidate_v17_latest.json"
EXPECTED_CARRIER_SHA = "6b30a4ddb71d985195075d21e0209d407b8cccb4"
MAX_ATTEMPTS = 3
RETRY_DELAYS = (1.0, 2.0)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def refs() -> list[str]:
    configured = os.environ.get("AAYS_CANONICAL_QUEUE_REF", "").strip()
    return list(dict.fromkeys([x for x in (configured, f"origin/{BRANCH}", BRANCH, "HEAD") if x]))


def contract_text(path: Path, rel: str) -> tuple[str, str]:
    if path.is_file():
        return path.read_text(encoding="utf-8-sig"), "worktree"
    errors: list[str] = []
    for ref in refs():
        try:
            proc = subprocess.run(
                ["git", "-C", str(ROOT), "show", f"{ref}:{rel}"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=30, check=False,
            )
        except Exception as exc:
            errors.append(f"{ref}:{type(exc).__name__}:{exc}")
            continue
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout.lstrip("\ufeff"), f"git:{ref}"
        errors.append(f"{ref}:exit={proc.returncode}:{proc.stderr.strip()[:200]}")
    raise FileNotFoundError(f"CONTRACT_INPUT_UNRESOLVED:{rel}:{errors}")


def legacy_values(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"IMPORT_SPEC_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_preflight() -> dict[str, Any]:
    checks: dict[str, bool] = {}
    errors: list[str] = []
    sources = {"queue": "unresolved", "legacy": "unresolved"}
    queue_text = legacy_text = ""

    for key, path, rel in (("queue", QUEUE, QUEUE_REL), ("legacy", LEGACY, LEGACY_REL)):
        try:
            text, source = contract_text(path, rel)
            sources[key] = source
            if key == "queue":
                queue_text = text
            else:
                legacy_text = text
            checks[f"{key}_contract_resolved"] = True
        except Exception as exc:
            checks[f"{key}_contract_resolved"] = False
            errors.append(f"{key.upper()}_RESOLUTION:{type(exc).__name__}:{exc}")

    checks["required_files_present"] = all(p.is_file() for p in (CORE, CARRIER, MANIFEST)) and all(
        checks.get(k) for k in ("queue_contract_resolved", "legacy_contract_resolved")
    )
    try:
        compile(CORE.read_text(encoding="utf-8"), str(CORE), "exec")
        checks["core_compile"] = True
    except Exception as exc:
        checks["core_compile"] = False
        errors.append(f"CORE:{type(exc).__name__}:{exc}")

    try:
        carrier = CARRIER.read_text(encoding="utf-8-sig")
        checks.update({
            "carrier_blob": blob_sha(CARRIER) == EXPECTED_CARRIER_SHA,
            "carrier_wrapper": Path(__file__).name in carrier and "POWERSHELL_CARRIER_TO_PYTHON" in carrier,
            "carrier_watchdog": "$internalTimeoutSeconds = 1500" in carrier and "taskkill.exe" in carrier,
            "carrier_safety": all(x in carrier for x in ("NEW_RUNNER=false", "PARALLEL_RUNNER=false", "FINAL_READY=false")),
        })
    except Exception as exc:
        checks["carrier_readable"] = False
        errors.append(f"CARRIER:{type(exc).__name__}:{exc}")

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
        checks.update({
            "manifest_130": manifest.get("candidate_rows") == 130,
            "manifest_accuracy_130": manifest.get("accuracy_score_4_rows") == 130,
            "manifest_http_130": manifest.get("stored_http_200_rows") == 130,
            "manifest_sha_130": manifest.get("stored_sha256_rows") == 130,
            "manifest_endpoints_16": manifest.get("unique_endpoints") == 16,
            "manifest_acceptance_false": manifest.get("acceptance_evidence") is False,
        })
    except Exception as exc:
        checks["manifest_readable"] = False
        errors.append(f"MANIFEST:{type(exc).__name__}:{exc}")

    try:
        queue = json.loads(queue_text)
        contract = dict(queue.get("execution_contract") or {})
        safety = dict(queue.get("safety_flags") or {})
        checks.update({
            "queue_identity": queue.get("task_id") == TASK_ID and queue.get("attempt_id") == ATTEMPT_ID,
            "queue_carrier": str(queue.get("script_path") or "").endswith(CARRIER.name) and queue.get("carrier_blob_sha") == EXPECTED_CARRIER_SHA,
            "queue_wrapper": str(queue.get("python_wrapper_path") or "").endswith(Path(__file__).name),
            "queue_runtime": contract.get("execution_host") == "powershell_carrier_to_python" and contract.get("internal_watchdog_seconds") == 1500,
            "queue_counts": contract.get("canonical_candidate_count") == 130 and contract.get("canonical_unique_endpoints") == 16,
            "queue_no_replay": contract.get("hydration_replay_forbidden") is True,
            "queue_safety": all(safety.get(k) is False for k in ("fake_data", "db_write", "migration", "production_deploy")),
            "queue_not_final": queue.get("final_ready") is False,
        })
    except Exception as exc:
        checks["queue_readable"] = False
        errors.append(f"QUEUE:{type(exc).__name__}:{exc}")

    try:
        legacy = legacy_values(legacy_text)
        checks.update({
            "legacy_identity": legacy.get("TASK_ID") == TASK_ID and legacy.get("ATTEMPT_ID") == ATTEMPT_ID,
            "legacy_carrier": str(legacy.get("WORKER_PATH") or "").endswith(CARRIER.name) and legacy.get("CARRIER_BLOB_SHA") == EXPECTED_CARRIER_SHA,
            "legacy_wrapper": str(legacy.get("PYTHON_WORKER_PATH") or "").endswith(Path(__file__).name),
            "legacy_runtime": legacy.get("EXECUTION_HOST") == "powershell_carrier_to_python" and legacy.get("INTERNAL_WATCHDOG_SECONDS") == "1500",
            "legacy_counts": legacy.get("CANDIDATE_COUNT_REQUIRED") == "130" and legacy.get("CANDIDATE_UNIQUE_ENDPOINTS_REQUIRED") == "16",
            "legacy_safety": all(legacy.get(k) == "false" for k in ("FAKE_DATA", "DB_WRITE", "MIGRATION", "PRODUCTION_DEPLOY")),
            "legacy_not_final": legacy.get("FINAL_READY_CONFIRMED") == "false",
        })
    except Exception as exc:
        checks["legacy_readable"] = False
        errors.append(f"LEGACY:{type(exc).__name__}:{exc}")

    return {
        "schema_version": 5,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": "PASS" if checks and all(checks.values()) else "BLOCKED",
        "checks": checks,
        "file_checks": {
            str(CORE.relative_to(ROOT)): CORE.is_file(),
            str(CARRIER.relative_to(ROOT)): CARRIER.is_file(),
            str(MANIFEST.relative_to(ROOT)): MANIFEST.is_file(),
            QUEUE_REL: QUEUE.is_file(),
            LEGACY_REL: LEGACY.is_file(),
        },
        "queue_contract_source": sources["queue"],
        "legacy_contract_source": sources["legacy"],
        "canonical_git_read_only_fallback": any(v.startswith("git:") for v in sources.values()),
        "errors": errors,
        "network_requests_performed": 0,
        "hydration_replayed": False,
        "execution_host": "powershell_carrier_to_python",
        "carrier_blob_sha": EXPECTED_CARRIER_SHA,
        "watchdog": {"internal_seconds": 1500, "outer_seconds": 1800, "process_tree_kill": True, "orphan_browser_cleanup": True},
        "failure_receipts_required": True,
        "checked_at": now(),
        "fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "final_ready": False,
    }


def retry_fetch(original: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
    def wrapped(url: str, accept: str = "application/json,text/html,*/*", timeout: float = 45.0) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for attempt in range(1, MAX_ATTEMPTS + 1):
            result = original(url, accept, timeout)
            result["attempt"] = attempt
            error, status = str(result.get("error") or ""), result.get("http_status")
            if status == 200 and not error:
                return result
            if ("HTTP Error 4" in error and "HTTP Error 429" not in error) or attempt == MAX_ATTEMPTS:
                return result
            time.sleep(RETRY_DELAYS[attempt - 1])
        return result
    return wrapped


def blocked(step: str, reason: str, detail: Any = None) -> dict[str, Any]:
    blockers = [reason] + ([f"DETAIL:{detail}"] if detail not in (None, "", [], {}) else [])
    return {
        "schema_version": 4, "slot_id": SLOT_ID, "task_id": TASK_ID, "attempt_id": ATTEMPT_ID,
        "status": "BLOCKED", "acceptance_pass": False,
        "canonical_live_parity": {"status": "BLOCKED", "candidate_count": None, "candidate_passed": None, "unique_endpoint_count": None, "unique_endpoint_http_json_passed": None, "network_requests_performed": 0},
        "browser_acceptance": {"status": "BLOCKED"}, "first_unverified_step": step, "blockers": blockers,
        "failure_receipt_generated": True, "hydration_replayed": False, "execution_host": "powershell_carrier_to_python",
        "output_semantics": "AREA_LEVEL_PROXY", "measurement_level": "lsoa", "parcel_measurement": False,
        "single_runner_only": True, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False,
        "final_ready": False, "generated_at": now(),
    }


def persist_core(payload: dict[str, Any]) -> None:
    write_json(CORE_REPORT, payload)
    write_json(CORE_WEB, payload)


def publisher(core: dict[str, Any], exit_code: int) -> dict[str, Any]:
    parity, browser = dict(core.get("canonical_live_parity") or {}), dict(core.get("browser_acceptance") or {})
    passed = core.get("acceptance_pass") is True
    return {
        "schema_version": 3, "slot_id": SLOT_ID, "task_id": TASK_ID, "attempt_id": ATTEMPT_ID,
        "status": "READY_FOR_SINGLE_PUBLISHER_COMMIT_PUSH_READBACK" if passed else "BLOCKED_RUNTIME_ACCEPTANCE",
        "acceptance_pass": passed, "core_exit_code": exit_code,
        "failure_receipt_generated": core.get("failure_receipt_generated") is True,
        "execution_host": "powershell_carrier_to_python",
        "canonical_progress_candidate": {"completed_units": 7 if passed else 5, "total_units": 8, "overall_percent": 87.5 if passed else 62.5, "publisher_readback_still_required": True, "may_publish_8_of_8": False},
        "runtime_evidence": {
            "candidate_count": parity.get("candidate_count"), "candidate_passed": parity.get("candidate_passed"),
            "unique_endpoint_count": parity.get("unique_endpoint_count"), "unique_endpoint_http_json_passed": parity.get("unique_endpoint_http_json_passed"),
            "network_requests_performed": parity.get("network_requests_performed"), "duplicate_live_requests_avoided": parity.get("duplicate_live_requests_avoided"),
            "browser_status": browser.get("status"), "progress_console_errors": (browser.get("progress_browser") or {}).get("console_error_count"),
            "product_matrix_console_errors": (browser.get("product_matrix_browser") or {}).get("console_error_count"),
        },
        "source_reports": {"core_report": str(CORE_REPORT.relative_to(ROOT)), "core_web_report": str(CORE_WEB.relative_to(ROOT))},
        "first_unverified_step": "SINGLE_PUBLISHER_COMMIT_PUSH_REMOTE_READBACK" if passed else core.get("first_unverified_step"),
        "blockers": [] if passed else list(core.get("blockers") or []),
        "output_semantics": "AREA_LEVEL_PROXY", "measurement_level": "lsoa", "parcel_measurement": False,
        "hydration_replayed": False, "single_runner_only": True, "child_direct_push_forbidden": True,
        "fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "final_ready": False,
        "generated_at": now(),
    }


def persist_publisher(core: dict[str, Any], exit_code: int) -> None:
    payload = publisher(core, exit_code)
    write_json(PUBLISHER_REPORT, payload)
    write_json(PUBLISHER_WEB, payload)


def main() -> int:
    preflight = run_preflight()
    write_json(PREFLIGHT_REPORT, preflight)
    write_json(PREFLIGHT_WEB, preflight)
    if preflight["status"] != "PASS":
        result = blocked("RUNTIME_PREFLIGHT_BLOCKED", "RUNTIME_PREFLIGHT_BLOCKED", {"errors": preflight["errors"], "failed_checks": [k for k, v in preflight["checks"].items() if not v]})
        persist_core(result)
        persist_publisher(result, 3)
        return 3

    exit_code = 4
    try:
        module = load_module(CORE, "security_public_safety_1_canonical_acceptance_v17_core")
        module.fetch = retry_fetch(module.fetch)
        exit_code = int(module.main() or 0)
        result = json.loads(CORE_REPORT.read_text(encoding="utf-8-sig")) if CORE_REPORT.is_file() else blocked("CORE_ACCEPTANCE_REPORT_MISSING", "CORE_ACCEPTANCE_REPORT_MISSING")
    except Exception as exc:
        result = blocked("CORE_RUNTIME_EXCEPTION", f"CORE_RUNTIME_EXCEPTION:{type(exc).__name__}:{exc}", traceback.format_exc(limit=20))
        exit_code = 4

    if not (result.get("slot_id") == SLOT_ID and result.get("task_id") == TASK_ID and result.get("attempt_id") == ATTEMPT_ID):
        result = blocked("CORE_RESULT_IDENTITY_MISMATCH", "CORE_RESULT_IDENTITY_MISMATCH")
        exit_code = 4
    persist_core(result)
    persist_publisher(result, exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
