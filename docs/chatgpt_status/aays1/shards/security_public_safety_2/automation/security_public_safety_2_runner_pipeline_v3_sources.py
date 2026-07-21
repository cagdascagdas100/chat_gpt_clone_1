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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_command(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, cwd=str(cwd), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:], "pass": completed.returncode == 0}
    except Exception as exc:
        return {"command": command, "returncode": None, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}:{exc}", "pass": False}


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    shard = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2"
    out = shard / "runner_outputs"
    out.mkdir(parents=True, exist_ok=True)
    receipt_path = out / "security_public_safety_2_source_aware_carrier_receipt_latest.json"
    receipt: dict[str, Any] = {"schema_version": 1, "slot_id": SLOT_ID, "carrier_version": "5.3-source-aware-resume-safe", "generated_at": utc_now(), "steps": [], "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}

    def finish(state: str, blocker: str | None, exit_code: int) -> dict[str, Any]:
        receipt.update({"state": state, "blocker": blocker, "exit_code": exit_code, "completed_at": utc_now()})
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt

    if slot != SLOT_ID or branch != TARGET_BRANCH:
        return finish("BLOCKED_CONTRACT", f"slot={slot};branch={branch}", 2)

    env = os.environ.copy()
    env.update({"AAYS_REPO_ROOT": str(repo), "AAYS_SLOT_ID": SLOT_ID, "AAYS_TARGET_BRANCH": TARGET_BRANCH})
    bootstrap = shard / "automation/security_public_safety_2_official_source_bootstrap.py"
    bootstrap_command = [sys.executable, str(bootstrap), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--timeout", str(args.source_timeout)]
    source_result = run_command(bootstrap_command, cwd=repo, env=env, timeout=args.source_timeout + 120)
    receipt["steps"].append({"name": "OFFICIAL_SOURCE_BOOTSTRAP", **source_result})
    manifest_path = out / "security_public_safety_2_official_source_manifest_latest.json"
    if not source_result["pass"] or not manifest_path.is_file():
        return finish("BLOCKED_OFFICIAL_SOURCE_BOOTSTRAP", "SOURCE_BOOTSTRAP_COMMAND_FAILED_OR_MANIFEST_MISSING", 3)
    try:
        manifest = read_json(manifest_path)
    except Exception as exc:
        return finish("BLOCKED_OFFICIAL_SOURCE_MANIFEST", f"MANIFEST_READ:{type(exc).__name__}:{exc}", 4)
    receipt["source_manifest"] = manifest
    if manifest.get("pass") is not True:
        return finish("BLOCKED_OFFICIAL_SOURCE_GATE", str(manifest.get("blocker")), 5)
    resolved = manifest.get("resolved_env") or {}
    iod_path = resolved.get("AAYS_IOD25_V2_CSV")
    mps_path = resolved.get("AAYS_MPS_LSOA_CSV")
    if not iod_path or not mps_path:
        return finish("BLOCKED_OFFICIAL_SOURCE_ENV", "RESOLVED_SOURCE_PATH_MISSING", 6)
    env["AAYS_IOD25_V2_CSV"] = str(iod_path)
    env["AAYS_MPS_LSOA_CSV"] = str(mps_path)

    pipeline = shard / "automation/security_public_safety_2_runner_pipeline_v2_resume.py"
    pipeline_command = [sys.executable, str(pipeline), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--port", str(args.port), "--sample-timeout", str(args.sample_timeout), "--batch-timeout", str(args.batch_timeout), "--acceptance-timeout", str(args.acceptance_timeout), "--http-wait-timeout", str(args.http_wait_timeout)]
    pipeline_result = run_command(pipeline_command, cwd=repo, env=env, timeout=args.pipeline_timeout)
    receipt["steps"].append({"name": "RESUME_PIPELINE_V2", **pipeline_result})
    receipt["resolved_env"] = {"AAYS_IOD25_V2_CSV": str(iod_path), "AAYS_MPS_LSOA_CSV": str(mps_path)}
    if not pipeline_result["pass"]:
        return finish("BLOCKED_RESUME_PIPELINE", "RESUME_PIPELINE_V2_FAILED", int(pipeline_result.get("returncode") or 7))
    return finish("SOURCE_AWARE_PIPELINE_PASSED_AWAITING_PUBLISHER_READBACK", None, 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--slot-id")
    parser.add_argument("--target-branch")
    parser.add_argument("--source-timeout", type=int, default=300)
    parser.add_argument("--pipeline-timeout", type=int, default=5400)
    parser.add_argument("--port", type=int, default=8012)
    parser.add_argument("--sample-timeout", type=int, default=900)
    parser.add_argument("--batch-timeout", type=int, default=3600)
    parser.add_argument("--acceptance-timeout", type=int, default=300)
    parser.add_argument("--http-wait-timeout", type=int, default=30)
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({"slot_id": SLOT_ID, "carrier_version": "5.3-source-aware-resume-safe", "state": result.get("state"), "blocker": result.get("blocker"), "exit_code": result.get("exit_code"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(int(result.get("exit_code") or 0))
