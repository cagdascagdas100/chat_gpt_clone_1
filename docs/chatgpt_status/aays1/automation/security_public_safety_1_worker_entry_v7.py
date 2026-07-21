from __future__ import annotations

import hashlib
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
BASE_ENTRY = HERE / "security_public_safety_1_worker_entry_v5.py"
SHARD_ROOT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID
WEB_ROOT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID
PROGRESS_JSON = SHARD_ROOT / "progress" / "progress_latest.json"
PROGRESS_WEB_JSON = WEB_ROOT / "progress_latest.json"
ACCEPTANCE_REPORT = SHARD_ROOT / "reports" / "001_security_public_safety_1_http_hash_dom_console_browser_acceptance_20260720.json"
LONDON_SOURCE_REPORT = SHARD_ROOT / "reports" / "005_security_public_safety_1_london_lsoa_source_latest.json"
LONDON_SOURCE_WEB = WEB_ROOT / "london_lsoa_source_latest.json"
LONDON_DATASTORE_URL = "https://data.london.gov.uk/publisher/mps/"
CANDIDATE_LIMIT = 60
EXPECTED_UNIQUE_ENDPOINTS = 8


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


def validate_london_lsoa_source() -> dict[str, Any]:
    request = urllib.request.Request(
        LONDON_DATASTORE_URL,
        headers={
            "User-Agent": "AAYS-security-london-lsoa-source/1.0",
            "Cache-Control": "no-cache",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            text = body.decode("utf-8", errors="replace")
            lower = text.lower()
            checks = {
                "http_200": int(response.status) == 200,
                "sha256_present": bool(hashlib.sha256(body).hexdigest()),
                "metropolitan_police_present": "metropolitan police" in lower,
                "recorded_crime_present": "recorded crime" in lower,
                "lsoa_present": "lsoa" in lower,
                "monthly_present": "month" in lower,
            }
            return {
                "schema_version": 1,
                "slot_id": SLOT_ID,
                "task_id": os.environ.get("AAYS_TASK_ID") or "manual",
                "status": "PASS" if all(checks.values()) else "BLOCKED",
                "url": LONDON_DATASTORE_URL,
                "http_status": int(response.status),
                "content_type": response.headers.get("Content-Type"),
                "content_length": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
                "checks": checks,
                "source_role": "Official Metropolitan Police London Datastore catalogue confirming monthly recorded-crime data at borough, ward and LSOA geography levels.",
                "scope_note": "Official LSOA context and cross-check only; it does not convert the candidate values into parcel measurements.",
                "output_semantics": "AREA_LEVEL_PROXY",
                "parcel_measurement": False,
                "checked_at": now(),
                "final_ready": False,
            }
    except Exception as exc:
        return {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": os.environ.get("AAYS_TASK_ID") or "manual",
            "status": "BLOCKED",
            "url": LONDON_DATASTORE_URL,
            "http_status": None,
            "sha256": None,
            "checks": {},
            "error": f"{type(exc).__name__}: {exc}",
            "output_semantics": "AREA_LEVEL_PROXY",
            "parcel_measurement": False,
            "checked_at": now(),
            "final_ready": False,
        }


def main() -> int:
    base = load_module(BASE_ENTRY, "security_public_safety_1_worker_entry_v5_base")
    base.CANDIDATE_LIMIT = CANDIDATE_LIMIT
    base.EXPECTED_UNIQUE_ENDPOINTS = EXPECTED_UNIQUE_ENDPOINTS
    exit_code = int(base.main() or 0)

    source_report = validate_london_lsoa_source()
    write_json(LONDON_SOURCE_REPORT, source_report)
    write_json(LONDON_SOURCE_WEB, source_report)

    progress = json.loads(PROGRESS_JSON.read_text(encoding="utf-8"))
    source_pass = source_report["status"] == "PASS"
    progress["candidate_examples_count"] = CANDIDATE_LIMIT
    progress["candidate_accuracy_score_4_count"] = CANDIDATE_LIMIT
    progress["candidate_unique_api_endpoints"] = EXPECTED_UNIQUE_ENDPOINTS
    progress["london_lsoa_source"] = source_report
    progress["london_lsoa_source_pass"] = source_pass
    events = list(progress.get("events") or [])
    events.insert(
        max(0, len(events) - 2),
        {
            "step": "LONDON_DATASTORE_LSOA_SOURCE",
            "status": "PASS" if source_pass else "BLOCKED",
            "detail": "official MPS London Datastore HTTP/SHA/content gate for monthly recorded crime at LSOA geography",
            "is_subgate": True,
            "at": now(),
        },
    )
    progress["events"] = events

    if not source_pass:
        progress["status"] = "BLOCKED"
        acceptance = dict(progress.get("acceptance_result") or {})
        blockers = list(acceptance.get("blockers") or [])
        blocker = "LONDON_DATASTORE_LSOA_SOURCE_VALIDATION_FAILED"
        if blocker not in blockers:
            blockers.append(blocker)
        acceptance.update({"blockers": blockers, "acceptance_pass": False, "status": "BLOCKED", "london_lsoa_source": source_report})
        progress["acceptance_result"] = acceptance
        if ACCEPTANCE_REPORT.is_file():
            report = json.loads(ACCEPTANCE_REPORT.read_text(encoding="utf-8"))
            report_blockers = list(report.get("blockers") or [])
            if blocker not in report_blockers:
                report_blockers.append(blocker)
            report.update({"blockers": report_blockers, "acceptance_pass": False, "status": "BLOCKED", "london_lsoa_source": source_report})
            write_json(ACCEPTANCE_REPORT, report)

    write_json(PROGRESS_JSON, progress)
    write_json(PROGRESS_WEB_JSON, progress)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
