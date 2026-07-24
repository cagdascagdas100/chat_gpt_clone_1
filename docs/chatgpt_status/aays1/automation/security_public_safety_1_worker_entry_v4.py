from __future__ import annotations

import importlib.util
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_1"
HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
V3_ENTRY = HERE / "security_public_safety_1_worker_entry_v3.py"
SHARD_ROOT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID
WEB_ROOT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID
PROGRESS_JSON = SHARD_ROOT / "progress" / "progress_latest.json"
PROGRESS_WEB_JSON = WEB_ROOT / "progress_latest.json"
FORCE_REPORT = SHARD_ROOT / "reports" / "004_security_public_safety_1_metropolitan_force_scope_latest.json"
FORCE_WEB = WEB_ROOT / "metropolitan_force_scope_latest.json"
ACCEPTANCE_REPORT = SHARD_ROOT / "reports" / "001_security_public_safety_1_http_hash_dom_console_browser_acceptance_20260720.json"


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


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AAYS-security-metropolitan-scope/1.0", "Cache-Control": "no-cache", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            return {
                "url": url,
                "http_status": int(response.status),
                "content_type": response.headers.get("Content-Type"),
                "json": json.loads(body.decode("utf-8")),
                "error": None,
            }
    except Exception as exc:
        return {"url": url, "http_status": None, "content_type": None, "json": None, "error": f"{type(exc).__name__}: {exc}"}


def validate_force_scope() -> dict[str, Any]:
    force_list = fetch_json("https://data.police.uk/api/forces")
    force_detail = fetch_json("https://data.police.uk/api/forces/metropolitan")
    list_json = force_list.get("json")
    detail_json = force_detail.get("json")
    list_has_metropolitan = isinstance(list_json, list) and any(
        str(item.get("id")) == "metropolitan" and "Metropolitan" in str(item.get("name"))
        for item in list_json if isinstance(item, dict)
    )
    detail_is_metropolitan = isinstance(detail_json, dict) and "Metropolitan" in str(detail_json.get("name"))
    checks = {
        "force_list_http_200": force_list.get("http_status") == 200,
        "force_list_json_array": isinstance(list_json, list),
        "force_list_contains_metropolitan": list_has_metropolitan,
        "force_detail_http_200": force_detail.get("http_status") == 200,
        "force_detail_json_object": isinstance(detail_json, dict),
        "force_detail_name_metropolitan": detail_is_metropolitan,
    }
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID") or "manual",
        "status": "PASS" if all(checks.values()) else "BLOCKED",
        "checks": checks,
        "force_list": {key: value for key, value in force_list.items() if key != "json"},
        "force_detail": {key: value for key, value in force_detail.items() if key != "json"},
        "force_id": "metropolitan",
        "scope_note": "Force identity is contextual provenance only; candidate values remain LSOA AREA_LEVEL_PROXY and are not parcel measurements.",
        "output_semantics": "AREA_LEVEL_PROXY",
        "parcel_measurement": False,
        "checked_at": now(),
        "final_ready": False,
    }


def main() -> int:
    v3 = load_module(V3_ENTRY, "security_public_safety_1_worker_entry_v3_base")
    v3.CANDIDATE_LIMIT = 30
    v3.EXPECTED_UNIQUE_ENDPOINTS = 6
    exit_code = int(v3.main() or 0)

    force_report = validate_force_scope()
    write_json(FORCE_REPORT, force_report)
    write_json(FORCE_WEB, force_report)

    progress = json.loads(PROGRESS_JSON.read_text(encoding="utf-8"))
    force_pass = force_report["status"] == "PASS"
    progress["candidate_examples_count"] = 30
    progress["candidate_accuracy_score_4_count"] = 30
    progress["metropolitan_force_scope"] = force_report
    progress["metropolitan_force_scope_pass"] = force_pass
    events = list(progress.get("events") or [])
    events.insert(
        max(0, len(events) - 2),
        {
            "step": "METROPOLITAN_FORCE_SCOPE",
            "status": "PASS" if force_pass else "BLOCKED",
            "detail": "data.police.uk force list and specific Metropolitan force JSON identity check",
            "is_subgate": True,
            "at": now(),
        },
    )
    progress["events"] = events

    if not force_pass:
        progress["status"] = "BLOCKED"
        acceptance = dict(progress.get("acceptance_result") or {})
        blockers = list(acceptance.get("blockers") or [])
        if "METROPOLITAN_FORCE_SCOPE_VALIDATION_FAILED" not in blockers:
            blockers.append("METROPOLITAN_FORCE_SCOPE_VALIDATION_FAILED")
        acceptance.update({"blockers": blockers, "acceptance_pass": False, "status": "BLOCKED", "metropolitan_force_scope": force_report})
        progress["acceptance_result"] = acceptance
        if ACCEPTANCE_REPORT.is_file():
            report = json.loads(ACCEPTANCE_REPORT.read_text(encoding="utf-8"))
            report_blockers = list(report.get("blockers") or [])
            if "METROPOLITAN_FORCE_SCOPE_VALIDATION_FAILED" not in report_blockers:
                report_blockers.append("METROPOLITAN_FORCE_SCOPE_VALIDATION_FAILED")
            report.update({"blockers": report_blockers, "acceptance_pass": False, "status": "BLOCKED", "metropolitan_force_scope": force_report})
            write_json(ACCEPTANCE_REPORT, report)

    write_json(PROGRESS_JSON, progress)
    write_json(PROGRESS_WEB_JSON, progress)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
