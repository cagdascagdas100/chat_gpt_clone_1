from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_3"

class StrictJsonError(ValueError):
    pass

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def reject_constant(value: str) -> None:
    raise StrictJsonError(f"NONFINITE_JSON_CONSTANT:{value}")

def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise StrictJsonError(f"DUPLICATE_JSON_KEY:{key}")
        out[key] = value
    return out

def strict_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs, parse_constant=reject_constant)

def load_or_none(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return strict_load(path)
    except Exception:
        return None

def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc)

def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp = Path(tmp.name)
    os.replace(temp, path)

def file_embedded_time(doc: Any, fields: list[str]) -> datetime | None:
    if not isinstance(doc, dict):
        return None
    for field in fields:
        dt = parse_time(doc.get(field))
        if dt:
            return dt
    return None

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--website-output", required=True)
    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()
    manifest = strict_load(Path(args.manifest))
    if manifest.get("slot_id") != SLOT_ID:
        raise SystemExit("MANIFEST_SLOT_MISMATCH")
    request_path = repo / manifest["active_request_path"]
    request = strict_load(request_path)
    if request.get("slot_id") != SLOT_ID or request.get("request_id") != manifest["active_request_id"]:
        raise SystemExit("ACTIVE_REQUEST_IDENTITY_INVALID")
    created = parse_time(request.get("created_at"))
    now = datetime.now(timezone.utc)
    lease = timedelta(minutes=int(manifest.get("lease_minutes", 120)))
    skew = timedelta(seconds=int(manifest.get("max_clock_skew_seconds", 300)))
    evidence = {}
    for name, meta in manifest["ack_paths"].items():
        doc = load_or_none(repo / meta["path"])
        evidence[name] = {"path": meta["path"], "exists": isinstance(doc, dict), "doc": doc, "evidence_time": file_embedded_time(doc, list(meta["time_fields"]))}
    request_future = bool(created and created > now + skew)
    expired = bool(created and now > created + lease)
    local_request = evidence["local_start_request"]["doc"]
    local_result = evidence["local_start_result"]["doc"]
    heartbeat = evidence["heartbeat"]["doc"]
    status = evidence["shared_status"]["doc"]
    preflight = evidence["preflight"]["doc"]
    outer = evidence["outer_watchdog"]["doc"]
    canonical = evidence["canonical"]["doc"]
    checks: list[dict[str, Any]] = []
    def add(code: str, passed: bool, value: Any = None) -> None:
        checks.append({"check": code, "passed": bool(passed), "value": value})
    add("request_not_future", not request_future, request.get("created_at"))
    add("request_not_expired", not expired, request.get("created_at"))
    add("request_status_active", request.get("status") == "REQUEST_PUBLISHED_EXTERNAL_HOST_ACK_PENDING")
    add("request_no_parallel_runner", request.get("new_parallel_runner_allowed") is False)
    add("local_start_request_fresh", isinstance(local_request, dict) and evidence["local_start_request"]["evidence_time"] and created and evidence["local_start_request"]["evidence_time"] >= created - skew)
    add("local_start_result_fresh", isinstance(local_result, dict) and evidence["local_start_result"]["evidence_time"] and created and evidence["local_start_result"]["evidence_time"] >= created - skew)
    add("local_start_exit_zero", isinstance(local_result, dict) and local_result.get("exit_code") == 0)
    add("local_start_runner_devam", isinstance(local_result, dict) and local_result.get("runner") == "devam.ps1")
    add("heartbeat_fresh", isinstance(heartbeat, dict) and evidence["heartbeat"]["evidence_time"] and created and evidence["heartbeat"]["evidence_time"] >= created - skew)
    add("heartbeat_runner_v4", isinstance(heartbeat, dict) and heartbeat.get("runner") == manifest["expected_runner"])
    add("shared_status_fresh", isinstance(status, dict) and evidence["shared_status"]["evidence_time"] and created and evidence["shared_status"]["evidence_time"] >= created - skew)
    add("queue_seen_true", isinstance(status, dict) and status.get("queue_seen") is True)
    add("queue_started_true", isinstance(status, dict) and status.get("queue_started") is True)
    slot_evidence_fresh = False
    for name, doc in (("preflight", preflight), ("outer_watchdog", outer), ("canonical", canonical)):
        et = evidence[name]["evidence_time"]
        fresh = bool(isinstance(doc, dict) and doc.get("slot_id") == SLOT_ID and et and created and et >= created - skew)
        add(f"{name}_fresh_slot_evidence", fresh, et.isoformat() if et else None)
        slot_evidence_fresh = slot_evidence_fresh or fresh
    add("at_least_one_fresh_slot_output", slot_evidence_fresh)
    hard_codes = {"request_not_future", "request_not_expired", "request_status_active", "request_no_parallel_runner", "heartbeat_fresh", "heartbeat_runner_v4", "shared_status_fresh", "queue_seen_true", "queue_started_true", "at_least_one_fresh_slot_output"}
    hard_ok = all(row["passed"] for row in checks if row["check"] in hard_codes)
    any_ack = any(item["exists"] for item in evidence.values())
    if hard_ok:
        state = "CANONICAL_RESTART_ACK_ACCEPTED_NONFINAL"
    elif request_future:
        state = "REQUEST_CLOCK_SKEW_FUTURE_BLOCKED"
    elif expired and not any_ack:
        state = "REQUEST_LEASE_EXPIRED_NO_ACK"
    elif any_ack:
        state = "PARTIAL_OR_STALE_ACK_REJECTED"
    else:
        state = "REQUEST_PENDING_WITHIN_LEASE"
    report = {"schema_version": 1, "slot_id": SLOT_ID, "task_id": os.environ.get("AAYS_TASK_ID") or "height-difference-3-restart-ack-reconciler-v1", "checked_at": utc_now(), "state": state, "active_request_id": request.get("request_id"), "active_request_path": manifest["active_request_path"], "request_created_at": request.get("created_at"), "request_age_seconds": round((now - created).total_seconds(), 3) if created else None, "lease_minutes": int(manifest.get("lease_minutes", 120)), "request_future_clock_skew": request_future, "request_expired": expired, "ack_accepted": hard_ok, "checks": checks, "passed_check_count": sum(1 for row in checks if row["passed"]), "failed_check_count": sum(1 for row in checks if not row["passed"]), "evidence": {name: {"path": item["path"], "exists": item["exists"], "evidence_time": item["evidence_time"].isoformat().replace("+00:00", "Z") if item["evidence_time"] else None} for name, item in evidence.items()}, "actual_business_data_rows_written": 0, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "final_ready": False, "output_semantics": "CANONICAL_RESTART_REQUEST_ID_TIME_AND_FRESH_SLOT_ACK_RECONCILIATION_NONFINAL"}
    atomic_json(Path(args.output), report)
    atomic_json(Path(args.website_output), report)
    task_id = os.environ.get("AAYS_TASK_ID")
    if task_id:
        gate = repo / f"docs/chatgpt_status/aays1/status/{task_id}_gate.json"
        atomic_json(gate, {"task_id": task_id, "source_row_gate_passed": False, "ui_token_gate_passed": False, "browser_smoke_passed": False, "post_sync_ok": False, "manual_review_required": True, "fake_data": False, "final_ready": False})
    print(f"HEIGHT_DIFFERENCE_3_RESTART_ACK_STATE={state}")
    print(f"HEIGHT_DIFFERENCE_3_RESTART_ACK_ACCEPTED={str(hard_ok).lower()}")
    print("FINAL_READY=false")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
