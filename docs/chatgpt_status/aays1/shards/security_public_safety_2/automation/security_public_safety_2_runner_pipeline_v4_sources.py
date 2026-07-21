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


def validate_manifest(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if manifest.get("pass") is not True:
        failures.append("MANIFEST_PASS_FALSE")
    if manifest.get("slot_id") != SLOT_ID:
        failures.append("WRONG_SLOT")
    if (manifest.get("contract") or {}).get("branch") != TARGET_BRANCH:
        failures.append("WRONG_BRANCH")
    if manifest.get("actual_business_rows_written") != 0:
        failures.append("BOOTSTRAP_WROTE_BUSINESS_ROWS")
    if manifest.get("fake_data") is not False or manifest.get("final_ready") is not False:
        failures.append("BOOTSTRAP_TERMINAL_FLAGS_INVALID")
    provenance = manifest.get("provenance") or {}
    for key in ("police_latest", "iod25_file7_v2", "mps_lsoa"):
        if (provenance.get(key) or {}).get("pass") is not True:
            failures.append(f"PROVENANCE_{key.upper()}_FAILED")
    for key in ("iod25_file7_v2", "mps_lsoa"):
        item = provenance.get(key) or {}
        if not item.get("sha256"):
            failures.append(f"PROVENANCE_{key.upper()}_SHA_MISSING")
        if (item.get("url_guard") or {}).get("pass") is not True:
            failures.append(f"PROVENANCE_{key.upper()}_URL_GUARD_FAILED")
    if (manifest.get("freshness_gate") or {}).get("pass") is not True:
        failures.append("SOURCE_FRESHNESS_GATE_FAILED")
    resolved = manifest.get("resolved_env") or {}
    if not resolved.get("AAYS_IOD25_V2_CSV") or not resolved.get("AAYS_MPS_LSOA_CSV"):
        failures.append("RESOLVED_SOURCE_PATH_MISSING")
    return not failures, failures


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = Path(args.repo_root or os.environ.get("AAYS_REPO_ROOT") or r"F:\chatgpt\chat_gpt_clone_1_main").resolve()
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    shard = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2"
    out = shard / "runner_outputs"
    out.mkdir(parents=True, exist_ok=True)
    receipt_path = out / "security_public_safety_2_source_aware_carrier_receipt_latest.json"
    receipt: dict[str, Any] = {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "carrier_version": "5.4-source-provenance-resume-safe",
        "generated_at": utc_now(),
        "steps": [],
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }

    def finish(state: str, blocker: str | None, exit_code: int) -> dict[str, Any]:
        receipt.update({"state": state, "blocker": blocker, "exit_code": exit_code, "completed_at": utc_now()})
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return receipt

    if slot != SLOT_ID or branch != TARGET_BRANCH:
        return finish("BLOCKED_CONTRACT", f"slot={slot};branch={branch}", 2)

    env = os.environ.copy()
    env.update({"AAYS_REPO_ROOT": str(repo), "AAYS_SLOT_ID": SLOT_ID, "AAYS_TARGET_BRANCH": TARGET_BRANCH})
    bootstrap = shard / "automation/security_public_safety_2_official_source_bootstrap_v2.py"
    bootstrap_command = [sys.executable, str(bootstrap), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--timeout", str(args.source_timeout)]
    source_result = run_command(bootstrap_command, cwd=repo, env=env, timeout=args.source_timeout + 180)
    receipt["steps"].append({"name": "OFFICIAL_SOURCE_BOOTSTRAP_V2", **source_result})
    manifest_path = out / "security_public_safety_2_official_source_manifest_latest.json"
    if not source_result["pass"] or not manifest_path.is_file():
        return finish("BLOCKED_OFFICIAL_SOURCE_BOOTSTRAP", "SOURCE_BOOTSTRAP_V2_FAILED_OR_MANIFEST_MISSING", 3)
    try:
        manifest = read_json(manifest_path)
    except Exception as exc:
        return finish("BLOCKED_OFFICIAL_SOURCE_MANIFEST", f"MANIFEST_READ:{type(exc).__name__}:{exc}", 4)
    manifest_ok, manifest_failures = validate_manifest(manifest)
    receipt["source_manifest"] = manifest
    receipt["steps"].append({"name": "OFFICIAL_SOURCE_PROVENANCE_GATE", "pass": manifest_ok, "failures": manifest_failures})
    if not manifest_ok:
        return finish("BLOCKED_OFFICIAL_SOURCE_PROVENANCE", ";".join(manifest_failures), 5)
    resolved = manifest.get("resolved_env") or {}
    env["AAYS_IOD25_V2_CSV"] = str(resolved["AAYS_IOD25_V2_CSV"])
    env["AAYS_MPS_LSOA_CSV"] = str(resolved["AAYS_MPS_LSOA_CSV"])

    pipeline = shard / "automation/security_public_safety_2_runner_pipeline_v2_resume.py"
    pipeline_command = [
        sys.executable, str(pipeline), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH,
        "--port", str(args.port), "--sample-timeout", str(args.sample_timeout), "--batch-timeout", str(args.batch_timeout),
        "--acceptance-timeout", str(args.acceptance_timeout), "--http-wait-timeout", str(args.http_wait_timeout),
    ]
    pipeline_result = run_command(pipeline_command, cwd=repo, env=env, timeout=args.pipeline_timeout)
    receipt["steps"].append({"name": "RESUME_PIPELINE_V2", **pipeline_result})
    receipt["resolved_env"] = {
        "AAYS_IOD25_V2_CSV": str(resolved["AAYS_IOD25_V2_CSV"]),
        "AAYS_MPS_LSOA_CSV": str(resolved["AAYS_MPS_LSOA_CSV"]),
    }
    if not pipeline_result["pass"]:
        return finish("BLOCKED_RESUME_PIPELINE", "RESUME_PIPELINE_V2_FAILED", int(pipeline_result.get("returncode") or 7))
    return finish("SOURCE_PROVENANCE_PIPELINE_PASSED_AWAITING_PUBLISHER_READBACK", None, 0)


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
    print(json.dumps({
        "slot_id": SLOT_ID,
        "carrier_version": "5.4-source-provenance-resume-safe",
        "state": payload.get("state"),
        "blocker": payload.get("blocker"),
        "exit_code": payload.get("exit_code"),
        "actual_business_rows_written": 0,
        "final_ready": False,
    }))
    raise SystemExit(int(payload.get("exit_code") or 0))
