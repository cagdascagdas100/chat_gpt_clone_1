from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def run_command(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, cwd=str(cwd), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:], "pass": completed.returncode == 0, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "returncode": None, "stdout_tail": str(exc.stdout or "")[-4000:], "stderr_tail": str(exc.stderr or "")[-4000:], "pass": False, "timed_out": True, "error": "TIMEOUT"}
    except Exception as exc:
        return {"command": command, "returncode": None, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}:{exc}", "pass": False, "timed_out": False, "error": "EXECUTION_EXCEPTION"}

def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or Path.cwd()).resolve()
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    shard = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2"
    out = shard / "runner_outputs"
    out.mkdir(parents=True, exist_ok=True)
    output = out / "security_public_safety_2_pipeline_v5_receipt_latest.json"
    receipt: dict[str, Any] = {"schema_version": 1, "slot_id": SLOT_ID, "pipeline_version": "5.0-live-attested-timeout-safe", "generated_at": utc_now(), "steps": [], "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}
    def finish(state: str, blocker: str | None, code: int) -> dict[str, Any]:
        receipt.update({"state": state, "blocker": blocker, "exit_code": code, "completed_at": utc_now(), "pass": code == 0})
        output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt
    if slot != SLOT_ID or branch != TARGET_BRANCH:
        return finish("BLOCKED_CONTRACT", f"slot={slot};branch={branch}", 2)
    env = os.environ.copy()
    env.update({"AAYS_REPO_ROOT": str(repo), "AAYS_SLOT_ID": SLOT_ID, "AAYS_TARGET_BRANCH": TARGET_BRANCH})

    attestation_script = shard / "automation/security_public_safety_2_live_source_attestation_v2.py"
    attestation_output = out / "security_public_safety_2_live_source_attestation_latest.json"
    result = run_command([sys.executable, str(attestation_script), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--timeout", str(args.source_timeout)], repo, env, args.source_timeout * 4 + 300)
    receipt["steps"].append({"name": "LIVE_SOURCE_ATTESTATION", **result})
    if not result["pass"] or not attestation_output.is_file():
        return finish("BLOCKED_LIVE_SOURCE_ATTESTATION", "COMMAND_FAILED_OR_RECEIPT_MISSING", 3)
    attestation = read_json(attestation_output)
    receipt["attestation"] = attestation
    if attestation.get("pass") is not True or attestation.get("state") != "LIVE_SOURCE_ATTESTATION_PASSED":
        return finish("BLOCKED_LIVE_SOURCE_ATTESTATION_GATE", str(attestation.get("blocker")), 4)
    resolved = attestation.get("resolved_env") or {}
    if not resolved.get("AAYS_IOD25_V2_CSV") or not resolved.get("AAYS_MPS_LSOA_CSV"):
        return finish("BLOCKED_LIVE_SOURCE_ENV", "RESOLVED_ENV_MISSING", 5)
    env.update({key: str(value) for key, value in resolved.items() if value})

    resume_script = shard / "automation/security_public_safety_2_runner_pipeline_v3_resume_hardened.py"
    resume_output = out / "security_public_safety_2_hardened_resume_receipt_latest.json"
    command = [sys.executable, str(resume_script), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--port", str(args.port), "--pipeline-timeout", str(args.pipeline_timeout), "--sample-timeout", str(args.sample_timeout), "--batch-timeout", str(args.batch_timeout), "--acceptance-timeout", str(args.acceptance_timeout), "--http-wait-timeout", str(args.http_wait_timeout)]
    result = run_command(command, repo, env, args.pipeline_timeout + 180)
    receipt["steps"].append({"name": "HARDENED_RESUME_PIPELINE", **result})
    if not result["pass"] or not resume_output.is_file():
        return finish("BLOCKED_HARDENED_RESUME", "COMMAND_FAILED_OR_RECEIPT_MISSING", 6)
    resume = read_json(resume_output)
    receipt["resume"] = resume
    if resume.get("pass") is not True or resume.get("state") != "HARDENED_RESUME_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_READBACK":
        return finish("BLOCKED_HARDENED_RESUME_GATE", str(resume.get("blocker")), 7)
    return finish("PIPELINE_V5_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK", None, 0)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--source-timeout", type=int, default=180)
    parser.add_argument("--pipeline-timeout", type=int, default=5700)
    parser.add_argument("--port", type=int, default=8012)
    parser.add_argument("--sample-timeout", type=int, default=900)
    parser.add_argument("--batch-timeout", type=int, default=3600)
    parser.add_argument("--acceptance-timeout", type=int, default=300)
    parser.add_argument("--http-wait-timeout", type=int, default=30)
    return parser.parse_args()

if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({"slot_id": SLOT_ID, "pipeline_version": "5.0-live-attested-timeout-safe", "state": result.get("state"), "pass": result.get("pass"), "exit_code": result.get("exit_code"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(int(result.get("exit_code") or 0))
