from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_3"
REPO_TOKEN = "cagdascagdas100/chat_gpt_clone_1"

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

def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp = Path(tmp.name)
    os.replace(temp, path)

def run(cmd: list[str], cwd: Path, timeout: int = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, check=False, env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"})
        return {"command": cmd, "exit_code": completed.returncode, "stdout": completed.stdout[-8000:], "stderr": completed.stderr[-8000:], "timed_out": False, "passed": completed.returncode == 0}
    except subprocess.TimeoutExpired as exc:
        return {"command": cmd, "exit_code": None, "stdout": (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "", "stderr": (exc.stderr or "")[-8000:] if isinstance(exc.stderr, str) else "", "timed_out": True, "passed": False}

def normalize_origin(value: str) -> str:
    value = value.strip().replace("\\", "/").lower()
    return value[:-4] if value.endswith(".git") else value

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--website-output", required=True)
    args = parser.parse_args()
    started = utc_now()
    blockers: list[str] = []
    checks: list[dict[str, Any]] = []
    repo = Path(args.repo_root).resolve()
    manifest_path = Path(args.manifest).resolve()
    try:
        manifest = strict_load(manifest_path)
    except Exception as exc:
        manifest = {}
        blockers.append(f"MANIFEST_STRICT_JSON_FAILED:{type(exc).__name__}:{exc}")
    if manifest.get("slot_id") != SLOT_ID:
        blockers.append("MANIFEST_SLOT_MISMATCH")
    if manifest.get("repo_token") != REPO_TOKEN:
        blockers.append("MANIFEST_REPO_TOKEN_MISMATCH")
    git = shutil.which("git")
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    python_executable = str(Path(sys.executable).resolve())
    command_map = {"git": git, "powershell": powershell, "python": python_executable}
    required_commands = set(manifest.get("required_commands", ["git", "powershell", "python"]))
    for name, resolved in command_map.items():
        available = bool(resolved)
        required = name in required_commands
        checks.append({"check": f"command_{name}", "passed": available or not required, "available": available, "required": required, "value": resolved})
        if required and not available:
            blockers.append(f"COMMAND_NOT_AVAILABLE:{name}")
    min_python = tuple(manifest.get("minimum_python", [3, 10]))
    python_ok = sys.version_info[:2] >= min_python
    checks.append({"check": "minimum_python", "passed": python_ok, "value": list(sys.version_info[:3]), "required": list(min_python)})
    if not python_ok:
        blockers.append("PYTHON_VERSION_BELOW_MINIMUM")
    repo_exists = repo.is_dir()
    git_dir_exists = (repo / ".git").exists()
    checks.extend([{"check": "repo_root_exists", "passed": repo_exists, "value": str(repo)}, {"check": "git_metadata_exists", "passed": git_dir_exists, "value": str(repo / ".git")}])
    if not repo_exists:
        blockers.append("REPO_ROOT_NOT_FOUND")
    if not git_dir_exists:
        blockers.append("REPO_ROOT_NOT_GIT_WORKTREE")
    disk = shutil.disk_usage(repo if repo_exists else manifest_path.parent)
    min_free = int(manifest.get("minimum_free_bytes", 2147483648))
    disk_ok = disk.free >= min_free
    checks.append({"check": "minimum_free_bytes", "passed": disk_ok, "free": disk.free, "required": min_free})
    if not disk_ok:
        blockers.append("FREE_DISK_SPACE_BELOW_MINIMUM")
    task_id = os.environ.get("AAYS_TASK_ID", "")
    expected_task_id = manifest.get("expected_task_id")
    task_ok = task_id == expected_task_id
    checks.append({"check": "task_identity", "passed": task_ok, "value": task_id, "required": expected_task_id})
    if not task_ok:
        blockers.append("AAYS_TASK_ID_MISMATCH")
    git_results: dict[str, Any] = {}
    if git and repo_exists and git_dir_exists:
        top = run([git, "rev-parse", "--show-toplevel"], repo)
        git_results["show_toplevel"] = top
        resolved_top = Path(top["stdout"].strip()).resolve() if top["passed"] and top["stdout"].strip() else None
        top_ok = resolved_top == repo
        checks.append({"check": "git_toplevel_exact", "passed": top_ok, "value": str(resolved_top) if resolved_top else None})
        if not top_ok:
            blockers.append("GIT_TOPLEVEL_MISMATCH")
        origin = run([git, "remote", "get-url", "origin"], repo)
        git_results["origin"] = origin
        normalized_origin = normalize_origin(origin["stdout"]) if origin["passed"] else ""
        origin_ok = REPO_TOKEN in normalized_origin
        checks.append({"check": "origin_repository_identity", "passed": origin_ok, "value": normalized_origin})
        if not origin_ok:
            blockers.append("ORIGIN_REPOSITORY_MISMATCH")
        branch = run([git, "rev-parse", "--abbrev-ref", "HEAD"], repo)
        git_results["branch"] = branch
        current_branch = branch["stdout"].strip() if branch["passed"] else ""
        allowed_branches = list(manifest.get("allowed_current_branches", []))
        branch_ok = current_branch in allowed_branches or current_branch == "HEAD"
        checks.append({"check": "allowed_current_branch", "passed": branch_ok, "value": current_branch, "allowed": allowed_branches + ["HEAD"]})
        if not branch_ok:
            blockers.append("CURRENT_BRANCH_NOT_ALLOWED")
        status = run([git, "status", "--porcelain=v1", "-uno"], repo)
        git_results["status"] = status
        checks.append({"check": "git_status_readable", "passed": status["passed"], "value": status["stdout"].splitlines()[:100]})
        if not status["passed"]:
            blockers.append("GIT_STATUS_UNREADABLE")
        for item in manifest.get("required_files", []):
            rel = str(item.get("path", ""))
            expected_sha = str(item.get("sha", ""))
            path = repo / rel
            exists = path.is_file()
            actual_sha = None
            if exists:
                result = run([git, "hash-object", "--", rel], repo)
                if result["passed"]:
                    actual_sha = result["stdout"].strip()
            passed = exists and actual_sha == expected_sha
            checks.append({"check": "required_file_blob", "path": rel, "passed": passed, "expected_sha": expected_sha, "actual_sha": actual_sha})
            if not passed:
                blockers.append(f"REQUIRED_FILE_BLOB_MISMATCH:{rel}")
        for sha in manifest.get("required_object_shas", []):
            result = run([git, "cat-file", "-e", f"{sha}^{{blob}}"], repo)
            checks.append({"check": "required_blob_object", "sha": sha, "passed": result["passed"]})
            if not result["passed"]:
                blockers.append(f"REQUIRED_BLOB_OBJECT_MISSING:{sha}")
    blockers = list(dict.fromkeys(blockers))
    report = {"schema_version": 1, "slot_id": SLOT_ID, "task_id": expected_task_id, "started_at": started, "completed_at": utc_now(), "accepted": not blockers, "check_count": len(checks), "passed_check_count": sum(1 for row in checks if row.get("passed") is True), "failed_check_count": sum(1 for row in checks if row.get("passed") is not True), "checks": checks, "git_results": git_results, "blockers": blockers, "repo_root": str(repo), "python_executable": python_executable, "python_version": list(sys.version_info[:3]), "free_bytes": disk.free, "network_access_attempted": False, "actual_business_data_rows_written": 0, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "final_ready": False, "output_semantics": "SLOT_ONLY_LOCAL_ENVIRONMENT_AND_EXACT_BLOB_PREFLIGHT_NONFINAL"}
    atomic_json(Path(args.output), report)
    atomic_json(Path(args.website_output), report)
    print(f"HEIGHT_DIFFERENCE_3_PREFLIGHT_ACCEPTED={str(report['accepted']).lower()}")
    print(f"HEIGHT_DIFFERENCE_3_PREFLIGHT_FAILED_CHECKS={report['failed_check_count']}")
    print("FINAL_READY=false")
    return 0 if report["accepted"] else 4

if __name__ == "__main__":
    raise SystemExit(main())
