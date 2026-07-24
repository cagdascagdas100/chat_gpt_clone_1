from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
EXPECTED_SAMPLE_COUNT = 3
EXPECTED_ROWS = 300


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_contract(repo: Path, slot_id: str, target_branch: str) -> dict[str, Any]:
    failures: list[str] = []
    if slot_id != SLOT_ID:
        failures.append(f"WRONG_SLOT:{slot_id}")
    if target_branch != TARGET_BRANCH:
        failures.append(f"WRONG_BRANCH:{target_branch}")
    shared = repo / "docs/chatgpt_status/_shared/slots_18" / SLOT_ID
    required = {
        "status": shared / "status_latest.json",
        "ownership": shared / "ownership_latest.json",
        "current_task": shared / "current_task_latest.json",
    }
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in required.items():
        if not path.is_file():
            failures.append(f"MISSING_CONTRACT:{path}")
            continue
        try:
            payloads[name] = read_json(path)
        except Exception as exc:
            failures.append(f"INVALID_CONTRACT:{name}:{type(exc).__name__}:{exc}")
    for name, payload in payloads.items():
        if payload.get("slot_id") != SLOT_ID:
            failures.append(f"WRONG_SLOT_CONTRACT:{name}")
    current_task = payloads.get("current_task") or {}
    allowed = current_task.get("allowed_paths") or []
    expected_web = "england_map_web/data/aays_18_slots/security_public_safety_2"
    if current_task and expected_web not in allowed:
        failures.append("WEB_PATH_NOT_ALLOWED")
    if current_task and current_task.get("direct_push_forbidden") is not True:
        failures.append("DIRECT_PUSH_GUARD_MISSING")
    return {
        "pass": not failures,
        "failures": failures,
        "shared_root": str(shared),
        "slot_id": slot_id,
        "target_branch": target_branch,
    }


def sample_gate(payload: dict[str, Any]) -> tuple[bool, str]:
    canonical = int(payload.get("canonical_sample_count") or 0)
    api = int(payload.get("accuracy_score_3_count") or 0)
    rows = payload.get("rows") or []
    exact_ids = [str(row.get("parcel_id") or "") for row in rows] == [
        "parcel_30762", "parcel_30763", "parcel_30764"
    ]
    passed = canonical == EXPECTED_SAMPLE_COUNT and api == EXPECTED_SAMPLE_COUNT and exact_ids
    return passed, f"canonical={canonical}/3;api={api}/3;exact_ids={exact_ids}"


def hydration_gate(payload: dict[str, Any]) -> tuple[bool, str]:
    rows = payload.get("rows") or []
    canonical = int(payload.get("canonical_rows") or 0)
    parity = bool((payload.get("artifacts") or {}).get("parity_pass"))
    exact_ids = [str(row.get("parcel_id") or "") for row in rows] == [
        f"parcel_{number}" for number in range(30762, 31062)
    ]
    no_missing = all(row.get("candidate_status") != "CANONICAL_FEATURE_NOT_FOUND" for row in rows)
    passed = len(rows) == EXPECTED_ROWS and canonical == EXPECTED_ROWS and parity and exact_ids and no_missing
    return passed, f"rows={len(rows)}/300;canonical={canonical}/300;parity={parity};exact_ids={exact_ids};no_missing={no_missing}"


def acceptance_gate(payload: dict[str, Any]) -> tuple[bool, str]:
    passed = payload.get("all_checks_pass") is True
    return passed, f"passed={payload.get('passed')}/{payload.get('total')};all_checks_pass={payload.get('all_checks_pass')}"


def run_command(command: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    completed = subprocess.run(command, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "pass": completed.returncode == 0,
    }


def wait_http(url: str, timeout: int = 30) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                return {"pass": response.status == 200, "http_status": response.status, "error": None}
        except Exception as exc:
            last_error = f"{type(exc).__name__}:{exc}"
            time.sleep(0.5)
    return {"pass": False, "http_status": None, "error": last_error or "HTTP_TIMEOUT"}


def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    slot_id = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    target_branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    shard = repo / "docs/chatgpt_status/aays1/shards" / SLOT_ID
    out = shard / "runner_outputs"
    web = repo / "england_map_web/data/aays_18_slots" / SLOT_ID
    out.mkdir(parents=True, exist_ok=True)
    web.mkdir(parents=True, exist_ok=True)
    receipt_path = out / "security_public_safety_2_pipeline_receipt_latest.json"
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "steps": [],
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }

    def finish(state: str, blocker: str | None, code: int) -> dict[str, Any]:
        receipt["state"] = state
        receipt["blocker"] = blocker
        receipt["exit_code"] = code
        receipt["completed_at"] = utc_now()
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt

    contract = validate_contract(repo, slot_id, target_branch)
    receipt["steps"].append({"name": "CONTRACT", **contract})
    if not contract["pass"]:
        return finish("BLOCKED_CONTRACT", ";".join(contract["failures"]), 2)

    sample_script = shard / "automation/security_public_safety_2_sample_hydrate.py"
    sample_result = run_command([sys.executable, str(sample_script)], repo, args.step_timeout)
    receipt["steps"].append({"name": "THREE_SAMPLE_COMMAND", **sample_result})
    sample_path = out / "security_public_safety_2_sample_candidates_latest.json"
    if not sample_result["pass"] or not sample_path.is_file():
        return finish("BLOCKED_SAMPLE_COMMAND", "THREE_SAMPLE_COMMAND_FAILED_OR_OUTPUT_MISSING", 3)
    sample_payload = read_json(sample_path)
    sample_ok, sample_detail = sample_gate(sample_payload)
    receipt["steps"].append({"name": "THREE_SAMPLE_GATE", "pass": sample_ok, "detail": sample_detail})
    if not sample_ok:
        return finish("BLOCKED_SAMPLE_GATE", sample_detail, 4)

    batch_script = shard / "automation/security_public_safety_2_batch_hydrate_v3_guarded.py"
    batch_result = run_command([sys.executable, str(batch_script)], repo, args.batch_timeout)
    receipt["steps"].append({"name": "HYDRATE_300_COMMAND", **batch_result})
    hydrated_path = out / "security_public_safety_2_hydrated_300_latest.json"
    if not batch_result["pass"] or not hydrated_path.is_file():
        return finish("BLOCKED_HYDRATE_COMMAND", "HYDRATE_COMMAND_FAILED_OR_OUTPUT_MISSING", 5)
    hydrated = read_json(hydrated_path)
    hydrated_ok, hydrated_detail = hydration_gate(hydrated)
    receipt["steps"].append({"name": "HYDRATE_300_GATE", "pass": hydrated_ok, "detail": hydrated_detail})
    if not hydrated_ok:
        return finish("BLOCKED_HYDRATE_GATE", hydrated_detail, 6)

    server_log = out / "security_public_safety_2_http_server_latest.log"
    with server_log.open("w", encoding="utf-8") as log:
        server = subprocess.Popen([sys.executable, "-m", "http.server", str(args.port), "--bind", "127.0.0.1"], cwd=str(repo), stdout=log, stderr=subprocess.STDOUT, text=True)
    try:
        base_url = f"http://127.0.0.1:{args.port}"
        html_url = base_url + "/england_map_web/data/aays_18_slots/security_public_safety_2/progress.html"
        json_url = base_url + "/england_map_web/data/aays_18_slots/security_public_safety_2/hydrated_300_latest.json"
        health = wait_http(html_url, args.http_wait_timeout)
        receipt["steps"].append({"name": "HTTP_SERVER", **health, "url": html_url})
        if not health["pass"]:
            return finish("BLOCKED_HTTP_SERVER", str(health.get("error")), 7)
        acceptance_script = shard / "automation/security_public_safety_2_acceptance_v3.py"
        acceptance_path = out / "security_public_safety_2_acceptance_latest.json"
        command = [sys.executable, str(acceptance_script), "--html-url", html_url, "--json-url", json_url, "--browser", "--browser-url", html_url, "--output", str(acceptance_path)]
        acceptance_result = run_command(command, repo, args.acceptance_timeout)
        receipt["steps"].append({"name": "HTTP_SHA_DOM_CONSOLE_BROWSER_COMMAND", **acceptance_result})
        if not acceptance_result["pass"] or not acceptance_path.is_file():
            return finish("BLOCKED_ACCEPTANCE_COMMAND", "ACCEPTANCE_COMMAND_FAILED_OR_OUTPUT_MISSING", 8)
        acceptance = read_json(acceptance_path)
        accepted, acceptance_detail = acceptance_gate(acceptance)
        receipt["steps"].append({"name": "HTTP_SHA_DOM_CONSOLE_BROWSER_GATE", "pass": accepted, "detail": acceptance_detail})
        if not accepted:
            return finish("BLOCKED_ACCEPTANCE_GATE", acceptance_detail, 9)
        return finish("PIPELINE_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK", None, 0)
    finally:
        try:
            server.terminate()
            server.wait(timeout=10)
        except Exception:
            try:
                server.kill()
            except Exception:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--port", type=int, default=8012)
    parser.add_argument("--step-timeout", type=int, default=900)
    parser.add_argument("--batch-timeout", type=int, default=3600)
    parser.add_argument("--acceptance-timeout", type=int, default=300)
    parser.add_argument("--http-wait-timeout", type=int, default=30)
    return parser.parse_args()


if __name__ == "__main__":
    result = run_pipeline(parse_args())
    print(json.dumps({"slot_id": SLOT_ID, "state": result.get("state"), "blocker": result.get("blocker"), "exit_code": result.get("exit_code"), "final_ready": False}))
    raise SystemExit(int(result.get("exit_code") or 0))
