from __future__ import annotations

import csv
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
BASE_ENTRY = HERE / "security_public_safety_1_worker_entry_v2.py"
SOURCE_CSV = ROOT / "england_map_web" / "data" / "security_public_safety" / "parcel_security_scores_verified.csv"
SHARD_ROOT = ROOT / "docs" / "chatgpt_status" / "aays1" / "shards" / SLOT_ID
WEB_ROOT = ROOT / "england_map_web" / "data" / "aays_21_slots" / SLOT_ID
PROGRESS_JSON = SHARD_ROOT / "progress" / "progress_latest.json"
PROGRESS_WEB_JSON = WEB_ROOT / "progress_latest.json"
ACCEPTANCE_REPORT = SHARD_ROOT / "reports" / "001_security_public_safety_1_http_hash_dom_console_browser_acceptance_20260720.json"
CANDIDATE_REPORT = SHARD_ROOT / "reports" / "003_security_public_safety_1_candidate_live_api_parity_latest.json"
CANDIDATE_WEB = WEB_ROOT / "candidate_live_api_parity_latest.json"
CANDIDATE_LIMIT = 20
EXPECTED_UNIQUE_ENDPOINTS = 6


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def digest(data: bytes) -> str:
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


def first_twenty() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            parcel_id = str(row.get("parcel_id") or "")
            if not parcel_id.startswith("parcel_"):
                continue
            number = int(parcel_id.rsplit("_", 1)[1])
            if not 1 <= number <= 30761:
                continue
            rows.append(row)
            if len(rows) == CANDIDATE_LIMIT:
                break
    if len(rows) != CANDIDATE_LIMIT:
        raise RuntimeError(f"EXPECTED_{CANDIDATE_LIMIT}_ROWS_GOT_{len(rows)}")
    return rows


def fetch_endpoint(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-security-candidate-live-parity/1.0",
            "Cache-Control": "no-cache",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read()
            parsed = json.loads(body.decode("utf-8"))
            return {
                "http_status": int(response.status),
                "content_type": response.headers.get("Content-Type"),
                "body_bytes": len(body),
                "body_sha256": digest(body),
                "json_array": isinstance(parsed, list),
                "crime_count": len(parsed) if isinstance(parsed, list) else None,
                "error": None,
            }
    except Exception as exc:
        return {
            "http_status": None,
            "content_type": None,
            "body_bytes": 0,
            "body_sha256": None,
            "json_array": False,
            "crime_count": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def validate_candidates() -> dict[str, Any]:
    rows = first_twenty()
    by_url: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        url = str(row.get("official_api_validation_url") or "")
        if not url.startswith("https://data.police.uk/api/crimes-street/"):
            raise RuntimeError(f"INVALID_OFFICIAL_API_URL:{row.get('parcel_id')}:{url}")
        by_url.setdefault(url, []).append(row)
    if len(by_url) != EXPECTED_UNIQUE_ENDPOINTS:
        raise RuntimeError(f"EXPECTED_{EXPECTED_UNIQUE_ENDPOINTS}_UNIQUE_ENDPOINTS_GOT_{len(by_url)}")

    endpoint_results: dict[str, dict[str, Any]] = {}
    for url in sorted(by_url):
        endpoint_results[url] = fetch_endpoint(url)

    candidate_results: list[dict[str, Any]] = []
    for row in rows:
        url = str(row["official_api_validation_url"])
        live = endpoint_results[url]
        stored_count = int(row.get("official_api_sample_crime_count") or 0)
        stored_hash = str(row.get("official_api_sample_sha256") or "")
        checks = {
            "http_200": live.get("http_status") == 200,
            "json_array": live.get("json_array") is True,
            "month_2026_05": str(row.get("official_api_latest_month")) == "2026-05" and "date=2026-05" in url,
            "stored_http_200": str(row.get("official_api_validation_status")) == "HTTP_200",
            "crime_count_parity": live.get("crime_count") == stored_count,
            "sha256_parity": live.get("body_sha256") == stored_hash,
            "area_proxy_semantics": str(row.get("source_geography_level")).upper() == "LSOA",
            "accuracy_4": str(row.get("accuracy_score_4")) == "4",
        }
        status = "PASS" if all(checks.values()) else "BLOCKED"
        candidate_results.append(
            {
                "parcel_id": row.get("parcel_id"),
                "security_score_percent": row.get("security_score_percent"),
                "security_level": row.get("security_level"),
                "accuracy_score_4": int(row.get("accuracy_score_4") or 0),
                "confidence_score": row.get("confidence_score"),
                "spatial_score": row.get("spatial_score"),
                "source_geography_level": row.get("source_geography_level"),
                "output_semantics": "AREA_LEVEL_PROXY",
                "parcel_measurement": False,
                "official_api_url": url,
                "stored_crime_count": stored_count,
                "live_crime_count": live.get("crime_count"),
                "stored_sha256": stored_hash,
                "live_sha256": live.get("body_sha256"),
                "http_status": live.get("http_status"),
                "checks": checks,
                "status": status,
            }
        )

    passed = sum(item["status"] == "PASS" for item in candidate_results)
    endpoint_passed = sum(
        item.get("http_status") == 200 and item.get("json_array") is True
        for item in endpoint_results.values()
    )
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID") or "manual",
        "status": "PASS" if passed == CANDIDATE_LIMIT else "BLOCKED",
        "candidate_count": CANDIDATE_LIMIT,
        "candidate_passed": passed,
        "unique_endpoint_count": len(endpoint_results),
        "unique_endpoint_http_json_passed": endpoint_passed,
        "candidate_live_parity_required": True,
        "output_semantics": "AREA_LEVEL_PROXY",
        "measurement_level": "lsoa",
        "parcel_measurement": False,
        "method_note": "Six unique one-mile representative-point API responses are reused across 20 LSOA-bound candidate references; they are supporting area evidence, not parcel measurements.",
        "endpoint_results": endpoint_results,
        "candidates": candidate_results,
        "checked_at": now(),
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


def main() -> int:
    base = load_module(BASE_ENTRY, "security_public_safety_1_worker_entry_v2_base")
    exit_code = int(base.main() or 0)
    candidate_report = validate_candidates()
    write_json(CANDIDATE_REPORT, candidate_report)
    write_json(CANDIDATE_WEB, candidate_report)

    progress = json.loads(PROGRESS_JSON.read_text(encoding="utf-8"))
    parity_pass = candidate_report["status"] == "PASS"
    progress["candidate_live_api_parity"] = candidate_report
    progress["candidate_live_api_parity_pass"] = parity_pass
    progress["candidate_examples"] = candidate_report["candidates"]
    progress["candidate_examples_count"] = candidate_report["candidate_count"]
    progress["candidate_accuracy_score_4_count"] = sum(
        item.get("accuracy_score_4") == 4 for item in candidate_report["candidates"]
    )
    events = list(progress.get("events") or [])
    events.insert(
        max(0, len(events) - 2),
        {
            "step": "CANDIDATE_LIVE_API_PARITY",
            "status": "PASS" if parity_pass else "BLOCKED",
            "detail": (
                f"candidate_passed={candidate_report['candidate_passed']}/{candidate_report['candidate_count']};"
                f"unique_endpoint_http_json={candidate_report['unique_endpoint_http_json_passed']}/{candidate_report['unique_endpoint_count']}"
            ),
            "is_subgate": True,
            "at": now(),
        },
    )
    progress["events"] = events

    if not parity_pass:
        progress["status"] = "BLOCKED"
        acceptance = dict(progress.get("acceptance_result") or {})
        blockers = list(acceptance.get("blockers") or [])
        if "CANDIDATE_LIVE_API_PARITY_FAILED" not in blockers:
            blockers.append("CANDIDATE_LIVE_API_PARITY_FAILED")
        acceptance["blockers"] = blockers
        acceptance["acceptance_pass"] = False
        acceptance["status"] = "BLOCKED"
        acceptance["candidate_live_api_parity"] = candidate_report
        progress["acceptance_result"] = acceptance
        if ACCEPTANCE_REPORT.is_file():
            report = json.loads(ACCEPTANCE_REPORT.read_text(encoding="utf-8"))
            report_blockers = list(report.get("blockers") or [])
            if "CANDIDATE_LIVE_API_PARITY_FAILED" not in report_blockers:
                report_blockers.append("CANDIDATE_LIVE_API_PARITY_FAILED")
            report["blockers"] = report_blockers
            report["acceptance_pass"] = False
            report["status"] = "BLOCKED"
            report["candidate_live_api_parity"] = candidate_report
            write_json(ACCEPTANCE_REPORT, report)

    base.publish_progress(progress)
    write_json(PROGRESS_WEB_JSON, progress)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
