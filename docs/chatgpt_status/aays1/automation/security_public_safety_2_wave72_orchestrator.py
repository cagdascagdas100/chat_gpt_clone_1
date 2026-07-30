from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path.cwd()
BRANCH = "codex/aays-single-runner-v5-20260706"
WORKSTREAM = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
SLOT = "security_public_safety_2"
SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"
FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_11110_TO_11560_ROWS_WITH_OFFICIAL_SOURCE_HASHES"
CONTINUATION_KEY = "e80c765946c15e4233d5137b2c44bfde0c56ec923f52eb105038fb4d9369b2b5"
TASK_ID = "security_public_safety_2_priority_11560row_incremental_evidence_expansion_20260730"
IDEMPOTENCY_KEY = hashlib.sha256(f"{CONTINUATION_KEY}|attempt-001".encode()).hexdigest()
OWNER = "github-actions-security-public-safety-2-wave72"

SLOT_ROOT = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2"
QUEUE = ROOT / "docs/chatgpt_status/aays1/queue/0047_security_public_safety_2_priority_11560row_incremental_evidence_expansion_20260730.v3.task.json"
CURRENT = SLOT_ROOT / "current_task_latest.json"
STATUS = SLOT_ROOT / "status_latest.json"
OWNERSHIP = SLOT_ROOT / "ownership_latest.json"
HEARTBEAT = SLOT_ROOT / "heartbeat_latest.json"
GENERATOR = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_11560row_incremental_evidence_expansion_20260730.py"
ACCEPTANCE_SCRIPT = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave72_accept_publish.py"
PREVIOUS_GENERATOR = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_11110row_incremental_evidence_expansion_20260730.py"
PREVIOUS_ACCEPTANCE_SCRIPT = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave71_accept_publish.py"
SHARD_INCREMENT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_450row_wave72_latest.json"
SHARD_FINAL = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_11560row_evidence_expansion_latest.json"
WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_11560row_evidence_expansion_latest.json"
WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_11560row_evidence_expansion.html"
RECEIPT = SLOT_ROOT / "priority_11560row_browser_acceptance_wave72_receipt_20260730.json"
DIAGNOSTIC = SLOT_ROOT / "priority_11560row_targeted_retry_wave72_diagnostic_20260730.json"

TARGETS = {
    "accepted_base_rows": 11110,
    "incremental_candidate_rows": 450,
    "merged_candidate_rows": 11560,
    "minimum_incremental_police_hash_rows": 428,
    "minimum_merged_police_hash_rows": 10982,
    "minimum_merged_accuracy_ge_95_candidate_rows": 10982,
    "website_line_by_line": True,
    "incremental_parcel_start": 41872,
    "incremental_parcel_end": 42321,
    "business_rows_to_write": 0,
}
CONCURRENCY = {
    "parallel_official_source_probes": 10,
    "parallel_incremental_row_checks": 15,
    "maximum_simultaneous_workers": 15,
    "hardware_manifest_limit_respected": True,
    "incremental_only": True,
}
EXACT_WRITE_PATHS = [
    str(SHARD_INCREMENT.relative_to(ROOT)),
    str(SHARD_FINAL.relative_to(ROOT)),
    str(WEB_JSON.relative_to(ROOT)),
    str(WEB_HTML.relative_to(ROOT)),
    str(QUEUE.relative_to(ROOT)),
    str(CURRENT.relative_to(ROOT)),
    str(STATUS.relative_to(ROOT)),
    str(OWNERSHIP.relative_to(ROOT)),
    str(HEARTBEAT.relative_to(ROOT)),
    str(RECEIPT.relative_to(ROOT)),
    str(DIAGNOSTIC.relative_to(ROOT)),
    str(GENERATOR.relative_to(ROOT)),
    str(ACCEPTANCE_SCRIPT.relative_to(ROOT)),
]


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, check=check, capture_output=False)


def output(args: list[str]) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def commit_and_push(paths: list[Path], message: str) -> str:
    run(["git", "config", "user.name", "github-actions[bot]"])
    run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
    run(["git", "add", "--", *[str(path.relative_to(ROOT)) for path in paths]])
    run(["git", "diff", "--cached", "--check"])
    changed = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode != 0
    if not changed:
        return output(["git", "rev-parse", "HEAD"])
    run(["git", "commit", "-m", message])
    for attempt in range(1, 6):
        run(["git", "fetch", "origin", BRANCH])
        rebase = subprocess.run(["git", "rebase", f"origin/{BRANCH}"], cwd=ROOT)
        if rebase.returncode != 0:
            subprocess.run(["git", "rebase", "--abort"], cwd=ROOT)
            raise SystemExit("REBASE_FAILED")
        push = subprocess.run(["git", "push", "origin", f"HEAD:{BRANCH}"], cwd=ROOT)
        if push.returncode == 0:
            return output(["git", "rev-parse", "HEAD"])
        time.sleep(attempt * 3)
    raise SystemExit("PUSH_FAILED_AFTER_RETRIES")


def sync_remote() -> str:
    run(["git", "fetch", "origin", BRANCH])
    rebase = subprocess.run(["git", "rebase", f"origin/{BRANCH}"], cwd=ROOT)
    if rebase.returncode != 0:
        subprocess.run(["git", "rebase", "--abort"], cwd=ROOT)
        raise SystemExit("REMOTE_SYNC_REBASE_FAILED")
    return output(["git", "rev-parse", "HEAD"])


def materialize_scripts() -> None:
    if not PREVIOUS_GENERATOR.is_file() or not PREVIOUS_ACCEPTANCE_SCRIPT.is_file():
        raise SystemExit("PREVIOUS_VERIFIED_SCRIPTS_MISSING")

    gen = PREVIOUS_GENERATOR.read_text(encoding="utf-8")
    replacements = [
        ("range(41422, 41872)", "range(41872, 42322)"),
        ("range(30762, 41422)", "range(30762, 41872)"),
        ("11110", "11560"),
        ("10660", "11110"),
        ("10555", "10982"),
        ('"schema_version": 49', '"schema_version": 50'),
        ("wave71", "wave72"),
    ]
    for old, new in replacements:
        if old not in gen:
            raise SystemExit(f"GENERATOR_TRANSFORM_FRAGMENT_MISSING:{old}")
        gen = gen.replace(old, new)
    for fragment in (
        "priority_11560row_evidence_expansion_latest.json",
        "priority_11110row_evidence_expansion_latest.json",
        "priority_450row_wave72_latest.json",
        "range(41872, 42322)",
        "accuracy_rows >= 10982",
    ):
        if fragment not in gen:
            raise SystemExit(f"GENERATOR_FINAL_FRAGMENT_MISSING:{fragment}")
    GENERATOR.write_text(gen, encoding="utf-8")

    acc = PREVIOUS_ACCEPTANCE_SCRIPT.read_text(encoding="utf-8")
    acc_replacements = [
        ("11110", "11560"),
        ("10660", "11110"),
        ("10555", "10982"),
        ("range(30762, 41872)", "range(30762, 42322)"),
        ("parcel_41871", "parcel_42321"),
        ('"progress_delta_percentage_points": 4.05', '"progress_delta_percentage_points": 3.89'),
        ("0046_", "0047_"),
        ("37bd2b96152653939629ac9da1daebc79fa1c68bf1127b97a6d9773e5410baf3", CONTINUATION_KEY),
        ("wave71", "wave72"),
    ]
    for old, new in acc_replacements:
        if old not in acc:
            raise SystemExit(f"ACCEPTANCE_TRANSFORM_FRAGMENT_MISSING:{old}")
        acc = acc.replace(old, new)
    for fragment in (
        f'CONTINUATION_KEY = "{CONTINUATION_KEY}"',
        "0047_security_public_safety_2_priority_11560row_incremental_evidence_expansion_20260730.v3.task.json",
        'OWNER = "github-actions-security-public-safety-2-wave72"',
        "while dom_rows < 11560",
    ):
        if fragment not in acc:
            raise SystemExit(f"ACCEPTANCE_FINAL_FRAGMENT_MISSING:{fragment}")
    ACCEPTANCE_SCRIPT.write_text(acc, encoding="utf-8")


def claim() -> None:
    expected = hashlib.sha256(f"{WORKSTREAM}|{SLOT}|{BRANCH}|{FIRST_STEP}|{SOURCE_HEAD}".encode()).hexdigest()
    if expected != CONTINUATION_KEY:
        raise SystemExit(f"CONTINUATION_KEY_FORMULA_MISMATCH:{expected}")

    current = load(CURRENT)
    status = load(STATUS)
    ownership = load(OWNERSHIP)
    if ownership.get("runtime_live_owner") or ownership.get("owner_page_session_id"):
        raise SystemExit("LIVE_OWNER_EXISTS_NO_SECOND_TASK")
    if QUEUE.exists() or current.get("continuation_key") == CONTINUATION_KEY:
        raise SystemExit("DUPLICATE_CONTINUATION_KEY_NO_SECOND_TASK")
    if current.get("state") != "COMPLETED_ACCEPTED_PUBLISHED":
        raise SystemExit(f"PREVIOUS_SCOPE_NOT_TERMINAL:{current.get('state')}")
    previous_acceptance = current.get("acceptance") or {}
    if previous_acceptance.get("state") != "PASS_REMOTE_COMMIT_READBACK":
        raise SystemExit("PREVIOUS_ACCEPTANCE_NOT_REMOTE_READBACK")
    if int(previous_acceptance.get("candidate_rows") or 0) != 11110:
        raise SystemExit("PREVIOUS_11110_ROW_COUNT_MISMATCH")
    if status.get("blocker"):
        raise SystemExit(f"BLOCKER_PRESENT:{status.get('blocker')}")

    materialize_scripts()
    created = now_z()
    lease = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat().replace("+00:00", "Z")
    previous_result = current.get("result") or {}
    progress = {
        "accepted_base_candidate_rows": 11110,
        "incremental_rows_target": 450,
        "incremental_rows_completed": 0,
        "merged_rows_target": 11560,
        "merged_rows_ready": 11110,
        "candidate_accuracy_ge_95_rows": int(previous_result.get("candidate_accuracy_ge_95_rows") or 10964),
        "police_response_sha256_rows": int(previous_result.get("police_response_sha256_rows") or 11110),
        "sources_promoted": int(previous_result.get("sources_promoted") or 10),
        "expanded_scope_progress_percent": 96.11,
        "expanded_scope_delta_percentage_points": 3.89,
        "new_acceptance_operations_completed": 0,
        "new_acceptance_operations_total": 14,
    }
    recovery = {
        "triggered": False,
        "reason": None,
        "attempt": 0,
        "targeted_retry_recovered_rows": 0,
        "ons_boundary_recovered_rows": 0,
        "concurrent_duplicate_runner_created": False,
        "second_task_created": False,
    }
    queue_payload = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM,
        "slot_id": SLOT,
        "base_slot_id": "security_public_safety",
        "shard_index": 2,
        "task_id": TASK_ID,
        "attempt_id": "attempt-001",
        "continuation_key": CONTINUATION_KEY,
        "idempotency_key": IDEMPOTENCY_KEY,
        "status": "running",
        "priority": -148,
        "claimable": False,
        "ready_for_claim": False,
        "single_runner_only": True,
        "page_key": "aays1",
        "owner": OWNER,
        "first_unverified_step": FIRST_STEP,
        "script_path": str(GENERATOR.relative_to(ROOT)),
        "acceptance_script_path": str(ACCEPTANCE_SCRIPT.relative_to(ROOT)),
        "orchestrator_path": "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave72_orchestrator.py",
        "read_paths": [
            "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_11110row_evidence_expansion_latest.json",
            str(PREVIOUS_GENERATOR.relative_to(ROOT)),
            str(PREVIOUS_ACCEPTANCE_SCRIPT.relative_to(ROOT)),
            str(CURRENT.relative_to(ROOT)),
            str(STATUS.relative_to(ROOT)),
            str(OWNERSHIP.relative_to(ROOT)),
        ],
        "exact_write_paths": EXACT_WRITE_PATHS,
        "resource_class": "NETWORK_IO_15_ROW_WORKERS_BROWSER_ACCEPTANCE",
        "timeout_seconds": 10800,
        "concurrency": CONCURRENCY,
        "targets": TARGETS,
        "acceptance_conditions": {
            "candidate_rows": 11560,
            "candidate_accuracy_ge_95_rows_min": 10982,
            "police_response_sha256_rows_min": 10982,
            "candidate_dom_rows": 11560,
            "console_errors": 0,
            "page_errors": 0,
            "request_failures": 0,
            "remote_commit_readback": "PASS",
        },
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "created_at": created,
        "updated_at": created,
        "source_head": SOURCE_HEAD,
        "previous_task_id": current.get("task_id"),
        "previous_continuation_key": current.get("continuation_key"),
        "previous_output_blob_sha": current.get("shard_output_blob_sha"),
        "previous_acceptance": previous_acceptance,
        "runner_state": "CLAIMED_RUNNING",
        "blocker": None,
        "final_ready": False,
        "recovery": recovery,
    }
    current_payload = {
        "schema_version": 95,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM,
        "slot_id": SLOT,
        "base_slot_id": "security_public_safety",
        "shard_index": 2,
        "state": "CLAIMED_RUNNING",
        "status": "running",
        "task_id": TASK_ID,
        "attempt_id": "attempt-001",
        "continuation_key": CONTINUATION_KEY,
        "idempotency_key": IDEMPOTENCY_KEY,
        "queue_path": str(QUEUE.relative_to(ROOT)),
        "script_path": str(GENERATOR.relative_to(ROOT)),
        "first_unverified_step": FIRST_STEP,
        "owner": OWNER,
        "targets": TARGETS,
        "concurrency": CONCURRENCY,
        "previous_acceptance": previous_acceptance,
        "blocker": None,
        "fake_data": False,
        "updated_at": created,
        "final_ready": False,
        "recovery": recovery,
    }
    status_payload = {
        "schema_version": 95,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM,
        "slot_id": SLOT,
        "base_slot_id": "security_public_safety",
        "shard_index": 2,
        "parcel_partition": {"start": 30762, "end": 61522, "count": 30761},
        "state": "CLAIMED_RUNNING",
        "task_id": TASK_ID,
        "attempt_id": "attempt-001",
        "continuation_key": CONTINUATION_KEY,
        "blocker": None,
        "owner": OWNER,
        "progress": progress,
        "parallelism": {"official_source_probes": 10, "incremental_row_checks": 15, "maximum_simultaneous_workers": 15},
        "website_targets": {"json": str(WEB_JSON.relative_to(ROOT)), "html": str(WEB_HTML.relative_to(ROOT)), "line_by_line_rows": 11560},
        "fake_data": False,
        "updated_at": created,
        "final_ready": False,
        "recovery": recovery,
    }
    ownership_payload = {
        "schema_version": 99,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM,
        "slot_id": SLOT,
        "base_slot_id": "security_public_safety",
        "shard_index": 2,
        "parcel_partition": {"start": 30762, "end": 61522, "count": 30761, "canonical_count": 92283},
        "state": "CLAIMED_RUNNING",
        "lease_version": int(ownership.get("lease_version") or 121) + 1,
        "owner_page_session_id": OWNER,
        "lease_token_hash": CONTINUATION_KEY,
        "heartbeat_at": created,
        "lease_expires_at": lease,
        "stale_after_seconds": 10800,
        "runtime_live_owner": True,
        "continuation_key": CONTINUATION_KEY,
        "task_id": TASK_ID,
        "attempt_id": "attempt-001",
        "queue_path": str(QUEUE.relative_to(ROOT)),
        "single_runner_only": True,
        "claimable": False,
        "ready_for_claim": False,
        "takeover_rule": "Live owner exists; do not create a second task, continuation or runner.",
        "wrong_slot_write_forbidden": True,
        "runner_write_allowed_only_after_claim": True,
        "business_write_forbidden": True,
        "accepted_base_scope": "priority_11110row_incremental_evidence_expansion_full_remote_and_canonical_browser_acceptance",
        "accepted_base_evidence_blob_sha": current.get("website_html_blob_sha"),
        "next_scope": {"incremental_candidate_rows": 450, "merged_candidate_rows": 11560, "website_line_by_line": True, "parallel_row_checks": 15, "parallel_source_probes": 10, "targeted_retry_enabled": True, "ons_exact_code_boundary_recovery_enabled": True},
        "generator_rerun": False,
        "second_runner_created": False,
        "second_task_created": False,
        "updated_at": created,
        "final_ready": False,
    }
    heartbeat_payload = {
        "state": "CLAIMED_RUNNING",
        "heartbeat_at": created,
        "schema_version": 94,
        "architecture_version": 3,
        "workstream_id": WORKSTREAM,
        "slot_id": SLOT,
        "base_slot_id": "security_public_safety",
        "shard_index": 2,
        "parcel_partition": {"start": 30762, "end": 61522, "count": 30761},
        "task_id": TASK_ID,
        "attempt_id": "attempt-001",
        "continuation_key": CONTINUATION_KEY,
        "owner_page_session_id": OWNER,
        "stale_after_seconds": 10800,
        "lease_expires_at": lease,
        "recovery_attempt": 0,
        "targeted_retry_recovered_rows": 0,
        "ons_boundary_recovered_rows": 0,
        "final_ready": False,
    }
    for path, payload in ((QUEUE, queue_payload), (CURRENT, current_payload), (STATUS, status_payload), (OWNERSHIP, ownership_payload), (HEARTBEAT, heartbeat_payload)):
        save(path, payload)
    commit_and_push([QUEUE, CURRENT, STATUS, OWNERSHIP, HEARTBEAT, GENERATOR, ACCEPTANCE_SCRIPT], "claim security_public_safety_2 11560-row wave72")


def execute_run() -> None:
    current = load(CURRENT)
    ownership = load(OWNERSHIP)
    if current.get("continuation_key") != CONTINUATION_KEY or current.get("state") != "CLAIMED_RUNNING":
        raise SystemExit("WAVE72_CLAIM_NOT_ACTIVE")
    if ownership.get("owner_page_session_id") != OWNER or not ownership.get("runtime_live_owner"):
        raise SystemExit("WAVE72_OWNER_CLAIM_MISMATCH")
    run([sys.executable, str(GENERATOR.relative_to(ROOT))])
    run([sys.executable, str(ACCEPTANCE_SCRIPT.relative_to(ROOT))])
    for path in (SHARD_INCREMENT, SHARD_FINAL, WEB_JSON, WEB_HTML, RECEIPT, DIAGNOSTIC):
        if not path.is_file():
            raise SystemExit(f"EXPECTED_OUTPUT_MISSING:{path}")
    commit_and_push([SHARD_INCREMENT, SHARD_FINAL, WEB_JSON, WEB_HTML, QUEUE, CURRENT, STATUS, OWNERSHIP, HEARTBEAT, RECEIPT, DIAGNOSTIC], "publish security_public_safety_2 11560-row evidence")


def terminalize() -> None:
    remote_head = sync_remote()
    queue = load(QUEUE)
    current = load(CURRENT)
    status = load(STATUS)
    ownership = load(OWNERSHIP)
    heartbeat = load(HEARTBEAT)
    receipt = load(RECEIPT)
    for label, payload in (("queue", queue), ("current", current), ("status", status), ("ownership", ownership), ("heartbeat", heartbeat), ("receipt", receipt)):
        if payload.get("continuation_key") != CONTINUATION_KEY or payload.get("task_id") != TASK_ID:
            raise SystemExit(f"{label.upper()}_CONTINUATION_OR_TASK_MISMATCH")
    if current.get("state") != "PUBLISH_PENDING_ACCEPTED" or queue.get("status") != "publish_pending":
        raise SystemExit(f"NOT_EXPECTED_PUBLISH_PENDING_STATE:{current.get('state')}:{queue.get('status')}")
    if ownership.get("runtime_live_owner") or ownership.get("owner_page_session_id"):
        raise SystemExit("LIVE_OWNER_PRESENT_DURING_TERMINAL_READBACK")
    if receipt.get("state") != "PASS_PENDING_REMOTE_COMMIT_READBACK":
        raise SystemExit("ACCEPTANCE_NOT_READY_FOR_REMOTE_READBACK")

    web_json_bytes = WEB_JSON.read_bytes()
    web_html_bytes = WEB_HTML.read_bytes()
    json_sha256 = hashlib.sha256(web_json_bytes).hexdigest()
    html_sha256 = hashlib.sha256(web_html_bytes).hexdigest()
    if json_sha256 != receipt.get("served_json_sha256"):
        raise SystemExit("REMOTE_JSON_SHA256_MISMATCH")
    if html_sha256 != receipt.get("served_html_sha256"):
        raise SystemExit("REMOTE_HTML_SHA256_MISMATCH")
    payload = json.loads(web_json_bytes.decode("utf-8-sig"))
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or len(rows) != 11560:
        raise SystemExit("REMOTE_JSON_ROW_COUNT_MISMATCH")
    html_text = web_html_bytes.decode("utf-8")
    if "parcel_30762" not in html_text or "parcel_42321" not in html_text:
        raise SystemExit("REMOTE_HTML_BOUNDARY_ROWS_MISSING")

    json_blob_sha = output(["git", "hash-object", str(WEB_JSON)])
    html_blob_sha = output(["git", "hash-object", str(WEB_HTML)])
    shard_blob_sha = output(["git", "hash-object", str(SHARD_FINAL)])
    accepted = now_z()
    acceptance = dict(receipt)
    acceptance.update({"state": "PASS_REMOTE_COMMIT_READBACK", "output_publish_remote_head": remote_head, "json_blob_sha": json_blob_sha, "html_blob_sha": html_blob_sha, "final_ready": True})
    result = dict(current.get("result") or status.get("result") or {})
    queue.update({"status": "completed_accepted", "owner": None, "first_unverified_step": None, "runner_state": "COMPLETED_ACCEPTED_PUBLISHED", "updated_at": accepted, "blocker": None, "final_ready": True, "acceptance": acceptance, "result": result, "output_publish_remote_head": remote_head, "shard_output_blob_sha": shard_blob_sha, "website_html_blob_sha": html_blob_sha})
    current.update({"state": "COMPLETED_ACCEPTED_PUBLISHED", "status": "completed_accepted", "owner": None, "first_unverified_step": None, "updated_at": accepted, "blocker": None, "final_ready": True, "acceptance": acceptance, "result": result, "output_publish_remote_head": remote_head, "shard_output_blob_sha": shard_blob_sha, "website_html_blob_sha": html_blob_sha})
    status.update({"state": "COMPLETED_ACCEPTED_PUBLISHED", "owner": None, "updated_at": accepted, "blocker": None, "final_ready": True, "acceptance": acceptance, "result": result, "output_publish_remote_head": remote_head})
    ownership.update({"state": "COMPLETED_ACCEPTED_OWNER_RELEASED", "owner_page_session_id": None, "lease_token_hash": None, "heartbeat_at": None, "lease_expires_at": None, "runtime_live_owner": False, "claimable": False, "ready_for_claim": False, "takeover_rule": "Task is completed, accepted and remotely read back. Do not restart, reclaim, duplicate or create another runner for this continuation key.", "updated_at": accepted, "final_ready": True, "acceptance": acceptance, "result": result, "output_publish_remote_head": remote_head, "generator_rerun": False, "second_runner_created": False, "second_task_created": False})
    heartbeat.update({"state": "COMPLETED_ACCEPTED_PUBLISHED", "heartbeat_at": accepted, "owner_page_session_id": None, "lease_expires_at": None, "output_publish_remote_head": remote_head, "final_ready": True})
    receipt.clear()
    receipt.update(acceptance)
    for path, data in ((QUEUE, queue), (CURRENT, current), (STATUS, status), (OWNERSHIP, ownership), (HEARTBEAT, heartbeat), (RECEIPT, receipt)):
        save(path, data)
    commit_and_push([QUEUE, CURRENT, STATUS, OWNERSHIP, HEARTBEAT, RECEIPT], "terminalize security_public_safety_2 11560-row readback")


def park() -> None:
    try:
        sync_remote()
    except Exception:
        pass
    if not QUEUE.is_file() or not CURRENT.is_file():
        return
    queue = load(QUEUE)
    current = load(CURRENT)
    if current.get("continuation_key") != CONTINUATION_KEY or current.get("state") == "COMPLETED_ACCEPTED_PUBLISHED":
        return
    status = load(STATUS)
    ownership = load(OWNERSHIP)
    heartbeat = load(HEARTBEAT)
    timestamp = now_z()
    reason = "WAVE72_REMOTE_TERMINAL_READBACK_FAILED" if current.get("state") == "PUBLISH_PENDING_ACCEPTED" else "WAVE72_WORKFLOW_FAILED_FAIL_CLOSED"
    for payload in (queue, current, status):
        payload["state"] = "RECOVERY_PARKED"
        payload["status"] = "recovery_parked"
        payload["blocker"] = reason
        payload["updated_at"] = timestamp
        payload["final_ready"] = False
        payload.setdefault("recovery", {}).update({"triggered": True, "reason": reason, "attempt": 1})
    ownership.update({"state": "RECOVERY_PARKED_OWNER_RELEASED", "owner_page_session_id": None, "lease_token_hash": None, "heartbeat_at": None, "lease_expires_at": None, "runtime_live_owner": False, "claimable": False, "ready_for_claim": False, "takeover_rule": "Recovery parked after one failed workflow; diagnose before one safe retry and do not create a duplicate continuation.", "updated_at": timestamp, "final_ready": False})
    heartbeat.update({"state": "RECOVERY_PARKED", "heartbeat_at": timestamp, "owner_page_session_id": None, "lease_expires_at": None, "final_ready": False})
    for path, payload in ((QUEUE, queue), (CURRENT, current), (STATUS, status), (OWNERSHIP, ownership), (HEARTBEAT, heartbeat)):
        save(path, payload)
    try:
        commit_and_push([QUEUE, CURRENT, STATUS, OWNERSHIP, HEARTBEAT], "park security_public_safety_2 wave72 failure")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("claim", "run", "terminalize", "park"))
    args = parser.parse_args()
    {"claim": claim, "run": execute_run, "terminalize": terminalize, "park": park}[args.mode]()


if __name__ == "__main__":
    main()
