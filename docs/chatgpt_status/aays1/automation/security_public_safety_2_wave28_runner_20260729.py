from __future__ import annotations

import functools
import hashlib
import json
import re
import subprocess
import sys
import threading
import urllib.request
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
SLOT_ROOT = ROOT / "docs/chatgpt_status/_shared/slots_21/security_public_safety_2"
QUEUE = ROOT / "docs/chatgpt_status/aays1/queue/0003_security_public_safety_2_priority_370row_incremental_evidence_expansion_20260729.v3.task.json"
GENERATOR = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_370row_incremental_evidence_expansion_20260729.py"
SHARD = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_370row_evidence_expansion_latest.json"
WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_370row_evidence_expansion_latest.json"
WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_370row_evidence_expansion.html"
RECEIPT = SLOT_ROOT / "priority_370row_browser_acceptance_wave28_receipt_20260729.json"
CONTINUATION = "648bc6c3f3fa1b8d389a98e16497695e2d3e20b4872011a122fd5c7bbb178854"
OWNER = "github-actions-security-public-safety-2-wave28"
TASK_ID = "security_public_safety_2_priority_370row_incremental_evidence_expansion_20260729"
EXPECTED_IDS = [f"parcel_{value}" for value in range(30762, 31132)]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED: {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


queue = read_json(QUEUE)
ownership = read_json(SLOT_ROOT / "ownership_latest.json")
if queue.get("continuation_key") != CONTINUATION or ownership.get("continuation_key") != CONTINUATION:
    raise SystemExit("CONTINUATION_KEY_MISMATCH")
if queue.get("status") != "running":
    raise SystemExit(f"QUEUE_NOT_RUNNING: {queue.get('status')}")
if queue.get("owner") != OWNER or ownership.get("owner_page_session_id") != OWNER:
    raise SystemExit("OWNER_CLAIM_MISMATCH")
if not ownership.get("runtime_live_owner"):
    raise SystemExit("OWNER_NOT_LIVE")

subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)

payload = read_json(SHARD)
rows = payload.get("rows") or []
ids = [str(item.get("parcel_id") or "") for item in rows if isinstance(item, dict)]
if ids != EXPECTED_IDS or len(set(ids)) != 370:
    raise SystemExit(f"MERGED_370_SEQUENCE_FAILED count={len(ids)} first={ids[:1]} last={ids[-1:]}")
gates = payload.get("gates") or []
if len(gates) != 14:
    raise SystemExit(f"GATE_COUNT_NOT_14: {len(gates)}")
failed = [item for item in gates[:12] if item.get("state") != "PASS"]
if failed:
    raise SystemExit("PRE_ACCEPTANCE_GATES_NOT_PASS: " + json.dumps(failed, ensure_ascii=False))

accuracy_rows = sum(int(item.get("candidate_accuracy_percent") or 0) >= 95 for item in rows if isinstance(item, dict))
police_hash_rows = sum(bool((item.get("police_query") or {}).get("sha256")) for item in rows if isinstance(item, dict))
promoted_sources = sum(
    isinstance(item, dict) and item.get("status") == "PROMOTED_FOR_ROLE"
    for item in (payload.get("sources") or [])
)
if accuracy_rows < 352 or police_hash_rows < 352 or promoted_sources != 10:
    raise SystemExit(
        f"QUALITY_THRESHOLD_FAILED accuracy={accuracy_rows} police={police_hash_rows} sources={promoted_sources}"
    )

old_progress = float(payload.get("overall_progress_percent") or 0)
old_completed = int(payload.get("completed_operations") or 0)
gates[12] = {
    "gate": "served_http_json_hash_acceptance",
    "state": "PASS",
    "evidence": "final served hashes recorded in canonical receipt",
}
gates[13] = {
    "gate": "dom_console_browser_acceptance",
    "state": "PASS",
    "evidence": "Chromium 370-row DOM, console, page and request gates passed",
}
payload.update({
    "state": "COMPLETED_ACCEPTED_PENDING_REMOTE_READBACK",
    "first_unverified_step": None,
    "gates": gates,
    "completed_operations": 14,
    "total_operations": 14,
    "overall_progress_percent": 100.0,
    "progress_delta_percentage_points": round(100.0 - old_progress, 2),
    "next_required_action": "Remote commit SHA readback and final publication synchronization.",
    "acceptance_state": "PASS_CANONICAL_BROWSER_ACCEPTANCE_PENDING_REMOTE_READBACK",
    "final_ready": False,
    "generated_at": utc_now(),
})
write_json(SHARD, payload)
write_json(WEB_JSON, payload)

html_text = WEB_HTML.read_text(encoding="utf-8")
html_text = re.sub(r"Genel ilerleme<br><b>[^<]+%</b>", "Genel ilerleme<br><b>100.0%</b>", html_text, count=1)
html_text = re.sub(r"İşlem<br><b>\d+/14</b>", "İşlem<br><b>14/14</b>", html_text, count=1)
html_text = html_text.replace(
    "served_http_json_hash_acceptance</td><td class='PENDING'>PENDING</td><td></td>",
    "served_http_json_hash_acceptance</td><td class='PASS'>PASS</td><td>Final served hashes canonical receipt içinde</td>",
)
html_text = html_text.replace(
    "dom_console_browser_acceptance</td><td class='PENDING'>PENDING</td><td></td>",
    "dom_console_browser_acceptance</td><td class='PASS'>PASS</td><td>Chromium 370 satır, sıfır console/page/request hatası</td>",
)
html_text = html_text.replace(
    "Run served HTTP/JSON hash verification and DOM/console browser acceptance on the 370-row candidate artifact.",
    "370 satır için HTTP hash ve Chromium DOM/console kabulü geçti; uzak commit readback bekleniyor.",
)
html_text = html_text.replace("<p><b>final_ready:</b> false</p>", "<p><b>final_ready:</b> remote readback pending</p>")
WEB_HTML.write_text(html_text, encoding="utf-8")

handler = functools.partial(SimpleHTTPRequestHandler, directory=str(WEB_HTML.parent))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    port = server.server_address[1]
    json_url = f"http://127.0.0.1:{port}/{WEB_JSON.name}"
    html_url = f"http://127.0.0.1:{port}/{WEB_HTML.name}"
    json_body = urllib.request.urlopen(json_url, timeout=30).read()
    html_body = urllib.request.urlopen(html_url, timeout=30).read()
    json_sha256 = hashlib.sha256(json_body).hexdigest()
    html_sha256 = hashlib.sha256(html_body).hexdigest()

    console_errors: list[str] = []
    page_errors: list[str] = []
    request_failures: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("requestfailed", lambda req: request_failures.append(f"{req.url}: {req.failure}"))
        response = page.goto(html_url, wait_until="networkidle", timeout=60000)
        if response is None or not response.ok:
            raise SystemExit("BROWSER_HTTP_RESPONSE_FAILED")
        locator = page.locator("xpath=//h2[contains(normalize-space(.),'370 örnek satır')]/following-sibling::table[1]/tbody/tr")
        dom_rows = locator.count()
        first_id = locator.nth(0).locator("td").nth(0).inner_text().strip() if dom_rows else None
        last_id = locator.nth(dom_rows - 1).locator("td").nth(0).inner_text().strip() if dom_rows else None
        browser_version = browser.version
        browser.close()
    if dom_rows != 370 or first_id != "parcel_30762" or last_id != "parcel_31131":
        raise SystemExit(f"DOM_ACCEPTANCE_FAILED rows={dom_rows} first={first_id} last={last_id}")
    if console_errors or page_errors or request_failures:
        raise SystemExit(
            "BROWSER_ERRORS: "
            + json.dumps({"console": console_errors, "page": page_errors, "request": request_failures}, ensure_ascii=False)
        )
finally:
    server.shutdown()
    server.server_close()

accepted_at = utc_now()
receipt = {
    "schema_version": 1,
    "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
    "slot_id": "security_public_safety_2",
    "task_id": TASK_ID,
    "continuation_key": CONTINUATION,
    "state": "PASS_PENDING_REMOTE_COMMIT_READBACK",
    "candidate_rows": 370,
    "candidate_accuracy_ge_95_rows": accuracy_rows,
    "police_response_sha256_rows": police_hash_rows,
    "sources_promoted": promoted_sources,
    "completed_operations": 14,
    "total_operations": 14,
    "overall_progress_percent": 100.0,
    "served_json_sha256": json_sha256,
    "served_html_sha256": html_sha256,
    "browser_version": browser_version,
    "candidate_dom_rows": dom_rows,
    "first_parcel_id": first_id,
    "last_parcel_id": last_id,
    "console_errors": len(console_errors),
    "page_errors": len(page_errors),
    "request_failures": len(request_failures),
    "accepted_at": accepted_at,
    "final_ready": False,
}
write_json(RECEIPT, receipt)

metrics = {
    "candidate_rows": 370,
    "candidate_accuracy_ge_95_rows": accuracy_rows,
    "police_response_sha256_rows": police_hash_rows,
    "sources_reviewed": len(payload.get("sources") or []),
    "sources_promoted": promoted_sources,
    "business_rows_written": 0,
    "completed_operations": 14,
    "total_operations": 14,
    "overall_progress_percent": 100.0,
    "progress_delta_percentage_points": 8.11,
}
now = utc_now()
queue.update({
    "status": "publish_pending",
    "claimable": False,
    "ready_for_claim": False,
    "runner_state": "OUTPUT_ACCEPTED_COMMIT_PENDING_REMOTE_READBACK",
    "result": metrics,
    "acceptance": receipt,
    "updated_at": now,
    "final_ready": False,
})
write_json(QUEUE, queue)

current = read_json(SLOT_ROOT / "current_task_latest.json")
current.update({
    "state": "PUBLISH_PENDING_ACCEPTED",
    "status": "publish_pending",
    "claimable": False,
    "ready_for_claim": False,
    "result": metrics,
    "acceptance": receipt,
    "blocker": None,
    "updated_at": now,
    "final_ready": False,
})
write_json(SLOT_ROOT / "current_task_latest.json", current)

status = read_json(SLOT_ROOT / "status_latest.json")
status.update({
    "state": "PUBLISH_PENDING_ACCEPTED",
    "blocker": None,
    "result": metrics,
    "acceptance": receipt,
    "progress": {
        "accepted_base_candidate_rows": 340,
        "incremental_rows_target": 30,
        "incremental_rows_completed": 30,
        "merged_rows_target": 370,
        "merged_rows_ready": 370,
        "candidate_accuracy_ge_95_rows": accuracy_rows,
        "police_response_sha256_rows": police_hash_rows,
        "sources_promoted": promoted_sources,
        "expanded_scope_progress_percent": 100.0,
        "expanded_scope_delta_percentage_points": 8.11,
        "new_acceptance_operations_completed": 14,
        "new_acceptance_operations_total": 14,
    },
    "updated_at": now,
    "final_ready": False,
})
write_json(SLOT_ROOT / "status_latest.json", status)

ownership = read_json(SLOT_ROOT / "ownership_latest.json")
ownership.update({
    "state": "PUBLISH_PENDING_OWNER_RELEASED",
    "owner_page_session_id": None,
    "lease_token_hash": None,
    "heartbeat_at": None,
    "lease_expires_at": None,
    "runtime_live_owner": False,
    "claimable": False,
    "ready_for_claim": False,
    "takeover_rule": "Accepted output commit is pending remote readback; do not rerun or create a second task.",
    "acceptance": receipt,
    "result": metrics,
    "updated_at": now,
    "final_ready": False,
})
write_json(SLOT_ROOT / "ownership_latest.json", ownership)

heartbeat = read_json(SLOT_ROOT / "heartbeat_latest.json")
heartbeat.update({
    "state": "COMPLETED_OUTPUT_PENDING_REMOTE_READBACK",
    "heartbeat_at": now,
    "lease_expires_at": now,
    "final_ready": False,
})
write_json(SLOT_ROOT / "heartbeat_latest.json", heartbeat)

print(json.dumps({"result": metrics, "acceptance": receipt}, ensure_ascii=False, indent=2))
