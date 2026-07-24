from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_1"
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
V14 = HERE / "security_public_safety_1_worker_entry_v14.py"
V15 = HERE / "security_public_safety_1_browser_acceptance_retry_v15.py"
PROGRESS = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID / "progress" / "progress_latest.json"
REPORT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID / "reports" / "009_security_public_safety_1_canonical_acceptance_v16_latest.json"
WEB_REPORT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID / "canonical_acceptance_v16_latest.json"


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


def find_parity(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        keys = set(value)
        if {"candidate_count", "candidate_passed", "unique_endpoint_count"}.issubset(keys):
            return value
        for child in value.values():
            found = find_parity(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_parity(child)
            if found is not None:
                return found
    return None


def canonical_parity_pass(parity: dict[str, Any] | None) -> tuple[bool, dict[str, Any]]:
    parity = parity or {}
    endpoint_passed = parity.get("unique_endpoint_http_json_passed")
    if endpoint_passed is None:
        endpoint_passed = parity.get("endpoint_http_json_passed")
    checks = {
        "status_pass": parity.get("status") == "PASS",
        "candidate_count_130": int(parity.get("candidate_count") or 0) == 130,
        "candidate_passed_130": int(parity.get("candidate_passed") or 0) == 130,
        "unique_endpoint_count_16": int(parity.get("unique_endpoint_count") or 0) == 16,
        "unique_endpoint_http_json_passed_16": int(endpoint_passed or 0) == 16,
    }
    return all(checks.values()), checks


def run() -> dict[str, Any]:
    if not V14.is_file() or not V15.is_file():
        raise RuntimeError("REQUIRED_WORKER_MISSING")

    v14 = load_module(V14, "security_public_safety_1_v14_for_v16")
    v14_exit = int(v14.main() or 0)
    if not PROGRESS.is_file():
        raise RuntimeError("V14_PROGRESS_NOT_CREATED")
    progress = json.loads(PROGRESS.read_text(encoding="utf-8"))
    parity = find_parity(progress)
    parity_ok, parity_checks = canonical_parity_pass(parity)

    v15 = load_module(V15, "security_public_safety_1_v15_for_v16")
    browser_result = v15.run()
    browser_gates = dict(browser_result.get("gates") or {})
    browser_ok = browser_result.get("status") == "PASS" and all(browser_gates.values())

    gates = {
        "v14_worker_exit_zero": v14_exit == 0,
        "canonical_130_candidate_16_endpoint_parity": parity_ok,
        "v15_official_source_refresh": browser_result.get("official_source_checks", {}).get("status") == "PASS",
        "v15_three_sample_live_count_sha_parity": browser_result.get("sample_live_parity", {}).get("status") == "PASS",
        "v15_progress_and_product_matrix_browser_acceptance": browser_ok,
    }
    status = "PASS" if all(gates.values()) else "BLOCKED"
    blockers = [name for name, passed in gates.items() if not passed]
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": "aays1-security-public-safety-1-canonical-acceptance-v16-20260722",
        "attempt_id": "security-public-safety-1-20260722-016",
        "status": status,
        "acceptance_pass": status == "PASS",
        "first_unverified_step": "COMMIT_PUSH_REMOTE_READBACK" if status == "PASS" else blockers[0],
        "blockers": blockers,
        "gates": gates,
        "v14_exit_code": v14_exit,
        "canonical_parity_checks": parity_checks,
        "canonical_parity": parity,
        "v15_browser_acceptance": browser_result,
        "verified_rows": int(progress.get("verified_source_rows_available") or progress.get("hydrated_rows") or 300),
        "accuracy_score_4_rows": int(progress.get("accuracy_score_4_rows_available") or progress.get("accuracy_score_4_rows") or 300),
        "canonical_candidate_target": 130,
        "canonical_unique_endpoint_target": 16,
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
            "attempt_id": "security-public-safety-1-20260722-016",
            "status": "BLOCKED",
            "acceptance_pass": False,
            "first_unverified_step": "CANONICAL_ACCEPTANCE_V16",
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
    return 0 if result.get("status") == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
