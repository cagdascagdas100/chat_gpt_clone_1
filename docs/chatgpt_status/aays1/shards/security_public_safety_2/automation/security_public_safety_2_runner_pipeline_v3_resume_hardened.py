from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
SOURCE_RECEIPT = "security_public_safety_2_pipeline_receipt_latest.json"
OUTPUT_RECEIPT = "security_public_safety_2_hardened_resume_receipt_latest.json"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def parse_time(value: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

def choose_port(preferred: int) -> int:
    for candidate in (preferred, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", candidate))
                return int(sock.getsockname()[1])
            except OSError:
                continue
    raise RuntimeError("NO_LOCAL_HTTP_PORT_AVAILABLE")

def run_command(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=str(cwd), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:], "elapsed_seconds": round(time.monotonic() - started, 3), "pass": completed.returncode == 0, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {"command": command, "returncode": None, "stdout_tail": stdout[-4000:], "stderr_tail": stderr[-4000:], "elapsed_seconds": round(time.monotonic() - started, 3), "pass": False, "timed_out": True, "error": "TIMEOUT"}
    except Exception as exc:
        return {"command": command, "returncode": None, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}:{exc}", "elapsed_seconds": round(time.monotonic() - started, 3), "pass": False, "timed_out": False, "error": "EXECUTION_EXCEPTION"}

def validate_pipeline_receipt(payload: dict[str, Any], started_at: datetime) -> dict[str, Any]:
    steps = payload.get("steps") or []
    acceptance = next((step for step in steps if step.get("name") in {"ACCEPTANCE_GATE", "ACCEPTANCE_RESUME"}), None)
    generated = parse_time(payload.get("generated_at"))
    completed = parse_time(payload.get("completed_at"))
    checks = {
        "slot_exact": payload.get("slot_id") == SLOT_ID,
        "state_exact": payload.get("state") == "PIPELINE_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK",
        "exit_zero": int(payload.get("exit_code") or 0) == 0,
        "fresh_generated": bool(generated and generated >= started_at),
        "fresh_completed": bool(completed and completed >= started_at),
        "acceptance_step_present": acceptance is not None,
        "acceptance_step_pass": bool(acceptance and acceptance.get("pass") is True),
        "business_rows_zero": int(payload.get("actual_business_rows_written") or 0) == 0,
        "fake_data_false": payload.get("fake_data") is False,
        "final_ready_false": payload.get("final_ready") is False,
    }
    return {"pass": all(checks.values()), "checks": checks, "passed": sum(checks.values()), "total": len(checks), "blocker": None if all(checks.values()) else "PIPELINE_RECEIPT_NOT_FRESH_OR_ACCEPTED"}

def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or Path.cwd()).resolve()
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    out.mkdir(parents=True, exist_ok=True)
    output_path = out / OUTPUT_RECEIPT
    source_path = out / SOURCE_RECEIPT
    receipt: dict[str, Any] = {"schema_version": 1, "slot_id": SLOT_ID, "wrapper_version": "3.0-timeout-safe-owned-port", "generated_at": utc_now(), "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}
    def finish(state: str, blocker: str | None, code: int) -> dict[str, Any]:
        receipt.update({"state": state, "blocker": blocker, "exit_code": code, "completed_at": utc_now(), "pass": code == 0})
        output_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt
    if slot != SLOT_ID or branch != TARGET_BRANCH:
        return finish("BLOCKED_CONTRACT", f"slot={slot};branch={branch}", 2)

    started_at = datetime.now(timezone.utc)
    stale = None
    if source_path.is_file():
        stale = {"sha256": __import__("hashlib").sha256(source_path.read_bytes()).hexdigest(), "bytes": source_path.stat().st_size}
        source_path.unlink()
    receipt["stale_receipt_removed"] = stale
    port = choose_port(args.port)
    receipt["requested_port"] = args.port
    receipt["selected_port"] = port
    env = os.environ.copy()
    env.update({"AAYS_REPO_ROOT": str(repo), "AAYS_SLOT_ID": SLOT_ID, "AAYS_TARGET_BRANCH": TARGET_BRANCH})
    pipeline = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation/security_public_safety_2_runner_pipeline_v2_resume.py"
    command = [sys.executable, str(pipeline), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--port", str(port), "--sample-timeout", str(args.sample_timeout), "--batch-timeout", str(args.batch_timeout), "--acceptance-timeout", str(args.acceptance_timeout), "--http-wait-timeout", str(args.http_wait_timeout)]
    result = run_command(command, repo, env, args.pipeline_timeout)
    receipt["pipeline_command"] = result
    if not result["pass"]:
        return finish("BLOCKED_RESUME_PIPELINE_EXECUTION", "TIMEOUT" if result.get("timed_out") else "NONZERO_OR_EXCEPTION", 3)
    if not source_path.is_file():
        return finish("BLOCKED_RESUME_PIPELINE_RECEIPT", "FRESH_PIPELINE_RECEIPT_MISSING", 4)
    try:
        source_receipt = json.loads(source_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return finish("BLOCKED_RESUME_PIPELINE_RECEIPT", f"READ:{type(exc).__name__}:{exc}", 5)
    validation = validate_pipeline_receipt(source_receipt, started_at)
    receipt["pipeline_receipt"] = source_receipt
    receipt["validation"] = validation
    if not validation["pass"]:
        return finish("BLOCKED_RESUME_PIPELINE_GATE", validation.get("blocker"), 6)
    return finish("HARDENED_RESUME_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_READBACK", None, 0)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--port", type=int, default=8012)
    parser.add_argument("--pipeline-timeout", type=int, default=5700)
    parser.add_argument("--sample-timeout", type=int, default=900)
    parser.add_argument("--batch-timeout", type=int, default=3600)
    parser.add_argument("--acceptance-timeout", type=int, default=300)
    parser.add_argument("--http-wait-timeout", type=int, default=30)
    return parser.parse_args()

if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({"slot_id": SLOT_ID, "wrapper_version": "3.0-timeout-safe-owned-port", "state": result.get("state"), "pass": result.get("pass"), "exit_code": result.get("exit_code"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(int(result.get("exit_code") or 0))
