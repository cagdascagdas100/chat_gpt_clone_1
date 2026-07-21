from __future__ import annotations

import argparse
import hashlib
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


def parse_time(value: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve_repo_root(explicit: str | None) -> Path:
    candidates: list[Path] = []
    for value in (explicit, os.environ.get("AAYS_REPO_ROOT")):
        if value:
            candidates.append(Path(value).expanduser())
    for probe in (Path.cwd(), Path(__file__).resolve().parent):
        try:
            completed = subprocess.run(["git", "-C", str(probe), "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            if completed.returncode == 0 and completed.stdout.strip():
                candidates.append(Path(completed.stdout.strip()))
        except Exception:
            pass
    candidates.extend(Path(__file__).resolve().parents)
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate.absolute()
        key = os.path.normcase(str(resolved))
        if key in seen:
            continue
        seen.add(key)
        if (resolved / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation").is_dir():
            return resolved
    raise RuntimeError("AAYS_REPO_ROOT_NOT_RESOLVED")


def run_command(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, cwd=str(cwd), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"command": command, "returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:], "pass": completed.returncode == 0, "timed_out": False}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {"command": command, "returncode": None, "stdout_tail": stdout[-4000:], "stderr_tail": stderr[-4000:], "pass": False, "timed_out": True, "error": "TIMEOUT"}
    except Exception as exc:
        return {"command": command, "returncode": None, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}:{exc}", "pass": False, "timed_out": False, "error": "EXECUTION_EXCEPTION"}


def validate_fresh_receipt(payload: dict[str, Any], *, started_at: datetime, expected_state: str) -> dict[str, Any]:
    generated = parse_time(payload.get("generated_at"))
    completed = parse_time(payload.get("completed_at"))
    checks = {
        "slot_exact": payload.get("slot_id") == SLOT_ID,
        "state_exact": payload.get("state") == expected_state,
        "pass_true": payload.get("pass") is True,
        "exit_code_present": "exit_code" in payload,
        "exit_zero": payload.get("exit_code") == 0,
        "fresh_generated": bool(generated and generated >= started_at),
        "fresh_completed": bool(completed and completed >= started_at),
        "business_rows_present": "actual_business_rows_written" in payload,
        "business_rows_zero": payload.get("actual_business_rows_written") == 0,
        "fake_false": payload.get("fake_data") is False,
        "final_false": payload.get("final_ready") is False,
    }
    return {"pass": all(checks.values()), "checks": checks, "passed": sum(checks.values()), "total": len(checks), "blocker": None if all(checks.values()) else "RECEIPT_NOT_FRESH_OR_EXACT"}


def remove_stale(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    item = {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
    path.unlink()
    return item


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo = resolve_repo_root(args.repo_root)
    slot = args.slot_id or os.environ.get("AAYS_SLOT_ID") or ""
    branch = args.target_branch or os.environ.get("AAYS_TARGET_BRANCH") or ""
    shard = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2"
    out = shard / "runner_outputs"
    out.mkdir(parents=True, exist_ok=True)
    output = out / "security_public_safety_2_pipeline_v6_receipt_latest.json"
    receipt: dict[str, Any] = {"schema_version": 1, "slot_id": SLOT_ID, "pipeline_version": "6.0-source-bound-artifact-integrity", "generated_at": utc_now(), "steps": [], "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}

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
    receipt["stale_attestation_removed"] = remove_stale(attestation_output)
    attestation_started = datetime.now(timezone.utc)
    result = run_command([sys.executable, str(attestation_script), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--timeout", str(args.source_timeout)], repo, env, args.source_timeout * 4 + 300)
    receipt["steps"].append({"name": "LIVE_SOURCE_ATTESTATION", **result})
    if not result["pass"] or not attestation_output.is_file():
        return finish("BLOCKED_LIVE_SOURCE_ATTESTATION", "COMMAND_FAILED_OR_FRESH_RECEIPT_MISSING", 3)
    try:
        attestation = read_json(attestation_output)
    except Exception as exc:
        return finish("BLOCKED_LIVE_SOURCE_ATTESTATION", f"READ:{type(exc).__name__}:{exc}", 4)
    attestation_validation = validate_fresh_receipt(attestation, started_at=attestation_started, expected_state="LIVE_SOURCE_ATTESTATION_PASSED")
    receipt["attestation"] = attestation
    receipt["attestation_validation"] = attestation_validation
    if not attestation_validation["pass"]:
        return finish("BLOCKED_LIVE_SOURCE_ATTESTATION_GATE", attestation_validation.get("blocker"), 5)

    source_bound_script = shard / "automation/security_public_safety_2_runner_pipeline_v4_source_bound.py"
    source_bound_output = out / "security_public_safety_2_source_bound_resume_receipt_latest.json"
    receipt["stale_source_bound_receipt_removed"] = remove_stale(source_bound_output)
    source_bound_started = datetime.now(timezone.utc)
    command = [sys.executable, str(source_bound_script), "--repo-root", str(repo), "--slot-id", SLOT_ID, "--target-branch", TARGET_BRANCH, "--port", str(args.port), "--pipeline-timeout", str(args.pipeline_timeout), "--sample-timeout", str(args.sample_timeout), "--batch-timeout", str(args.batch_timeout), "--acceptance-timeout", str(args.acceptance_timeout), "--http-wait-timeout", str(args.http_wait_timeout)]
    result = run_command(command, repo, env, args.pipeline_timeout + 300)
    receipt["steps"].append({"name": "SOURCE_BOUND_RESUME", **result})
    if not result["pass"] or not source_bound_output.is_file():
        return finish("BLOCKED_SOURCE_BOUND_RESUME", "COMMAND_FAILED_OR_FRESH_RECEIPT_MISSING", 6)
    try:
        source_bound = read_json(source_bound_output)
    except Exception as exc:
        return finish("BLOCKED_SOURCE_BOUND_RESUME", f"READ:{type(exc).__name__}:{exc}", 7)
    source_bound_validation = validate_fresh_receipt(source_bound, started_at=source_bound_started, expected_state="SOURCE_BOUND_ACCEPTANCE_PASSED_AWAITING_PUBLISHER_READBACK")
    receipt["source_bound_resume"] = source_bound
    receipt["source_bound_validation"] = source_bound_validation
    if not source_bound_validation["pass"]:
        return finish("BLOCKED_SOURCE_BOUND_RESUME_GATE", source_bound_validation.get("blocker"), 8)
    return finish("PIPELINE_V6_PASSED_AWAITING_PUBLISHER_COMMIT_READBACK", None, 0)


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
    print(json.dumps({"slot_id": SLOT_ID, "pipeline_version": "6.0-source-bound-artifact-integrity", "state": result.get("state"), "pass": result.get("pass"), "exit_code": result.get("exit_code"), "actual_business_rows_written": 0, "final_ready": False}))
    raise SystemExit(int(result.get("exit_code") or 0))
