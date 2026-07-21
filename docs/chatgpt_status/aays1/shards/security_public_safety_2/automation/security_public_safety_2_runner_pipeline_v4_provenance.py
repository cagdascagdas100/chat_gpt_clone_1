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
        return {"command": command, "returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:], "pass": completed.returncode == 0}
    except Exception as exc:
        return {"command": command, "returncode": None, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}:{exc}", "pass": False}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    shard = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2"
    out = shard / "runner_outputs"
    out.mkdir(parents=True, exist_ok=True)
    receipt_path = out / "security_public_safety_2_provenance_carrier_receipt_latest.json"
    receipt: dict[str, Any] = {"schema_version": 1, "slot_id": SLOT_ID, "carrier_version": "5.4-provenance-source-aware-resume-safe", "generated_at": utc_now(), "steps": [], "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}

    def finish(state: str, blocker: str | None, code: int) -> dict[str, Any]:
        receipt.update({"state": state, "blocker": blocker, "exit_code": code, "completed_at": utc_now()})
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt

    if slot != SLOT_ID or branch != TARGET_BRANCH:
        return finish("BLOCKED_CONTRACT", f"slot={slot};branch={branch}", 2)
    env = os.environ.copy()
    env.update({"AAYS_REPO_ROOT": str(repo), "AAYS_SLOT_ID": SLOT_ID, "AAYS_TARGET_BRANCH": TARGET_BRANCH})
    provenance = shard / "automation/security_public_safety_2_official_source_provenance.py"
    result = run_command([sys.executable, str(provenance), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--timeout", str(args.source_timeout)], repo, env, args.source_timeout + 120)
    receipt["steps"].append({"name": "OFFICIAL_SOURCE_PROVENANCE", **result})
    manifest_path = out / "security_public_safety_2_official_source_provenance_latest.json"
    if not result["pass"] or not manifest_path.is_file():
        return finish("BLOCKED_OFFICIAL_SOURCE_PROVENANCE", "PROVENANCE_COMMAND_FAILED_OR_MANIFEST_MISSING", 3)
    manifest = read_json(manifest_path)
    receipt["provenance_manifest"] = manifest
    if manifest.get("pass") is not True:
        return finish("BLOCKED_OFFICIAL_SOURCE_PROVENANCE_GATE", str(manifest.get("blocker")), 4)
    source_pipeline = shard / "automation/security_public_safety_2_runner_pipeline_v3_sources.py"
    result = run_command([sys.executable, str(source_pipeline), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--source-timeout", str(args.source_timeout), "--pipeline-timeout", str(args.pipeline_timeout), "--port", str(args.port), "--sample-timeout", str(args.sample_timeout), "--batch-timeout", str(args.batch_timeout), "--acceptance-timeout", str(args.acceptance_timeout), "--http-wait-timeout", str(args.http_wait_timeout)], repo, env, args.pipeline_timeout + args.source_timeout + 180)
    receipt["steps"].append({"name": "SOURCE_AWARE_PIPELINE_V3", **result})
    if not result["pass"]:
        return finish("BLOCKED_SOURCE_AWARE_PIPELINE", "SOURCE_AWARE_PIPELINE_V3_FAILED", int(result.get("returncode") or 5))
    return finish("PROVENANCE_PIPELINE_PASSED_AWAITING_PUBLISHER_READBACK", None, 0)


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
    payload = run(parse_args())
    print(json.dumps({"slot_id": SLOT_ID, "carrier_version": "5.4-provenance-source-aware-resume-safe", "state": payload.get("state"), "blocker": payload.get("blocker"), "exit_code": payload.get("exit_code"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(int(payload.get("exit_code") or 0))
