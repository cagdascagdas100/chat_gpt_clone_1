from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
SOURCE_BRANCH = "codex/aays-single-runner-v5-20260706"
SOURCE_PATH = "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
REQUIRED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
CORE_MODULE = "security_public_safety_2_batch_hydrate_v2"


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def blob_sha(repo: Path, path: Path) -> str | None:
    try:
        result = git(repo, "hash-object", str(path))
        return result.stdout.decode("ascii", errors="replace").strip() or None
    except Exception:
        return None


def materialize_exact_source(repo: Path) -> tuple[Path | None, dict[str, Any]]:
    local = repo / SOURCE_PATH
    attempts: list[dict[str, Any]] = []
    if local.is_file():
        observed = blob_sha(repo, local)
        attempts.append({"method": "working_tree", "path": str(local), "blob_sha": observed})
        if observed == REQUIRED_BLOB_SHA:
            return local, {
                "pass": True,
                "materialization_method": "working_tree_exact_blob",
                "required_blob_sha": REQUIRED_BLOB_SHA,
                "observed_blob_sha": observed,
                "source_branch": SOURCE_BRANCH,
                "source_path": SOURCE_PATH,
                "attempts": attempts,
            }

    temp_root = Path(tempfile.gettempdir()) / "aays_security_public_safety_2"
    temp_root.mkdir(parents=True, exist_ok=True)
    target = temp_root / f"{REQUIRED_BLOB_SHA}.geojson"
    refs = [f"origin/{SOURCE_BRANCH}:{SOURCE_PATH}", f"{SOURCE_BRANCH}:{SOURCE_PATH}"]
    for ref in refs:
        try:
            result = git(repo, "show", ref)
            target.write_bytes(result.stdout)
            observed = blob_sha(repo, target)
            attempts.append({"method": "git_show", "ref": ref, "path": str(target), "blob_sha": observed})
            if observed == REQUIRED_BLOB_SHA:
                return target, {
                    "pass": True,
                    "materialization_method": "git_show_exact_blob",
                    "required_blob_sha": REQUIRED_BLOB_SHA,
                    "observed_blob_sha": observed,
                    "source_branch": SOURCE_BRANCH,
                    "source_path": SOURCE_PATH,
                    "attempts": attempts,
                }
        except Exception as exc:
            attempts.append({"method": "git_show", "ref": ref, "error": f"{type(exc).__name__}:{exc}"})

    try:
        fetch = git(repo, "fetch", "--no-tags", "origin", SOURCE_BRANCH, check=False)
        attempts.append({
            "method": "git_fetch",
            "returncode": fetch.returncode,
            "stderr": fetch.stderr.decode("utf-8", errors="replace")[-1000:],
        })
        if fetch.returncode == 0:
            result = git(repo, "show", f"FETCH_HEAD:{SOURCE_PATH}")
            target.write_bytes(result.stdout)
            observed = blob_sha(repo, target)
            attempts.append({"method": "fetch_head_show", "path": str(target), "blob_sha": observed})
            if observed == REQUIRED_BLOB_SHA:
                return target, {
                    "pass": True,
                    "materialization_method": "fetch_head_exact_blob",
                    "required_blob_sha": REQUIRED_BLOB_SHA,
                    "observed_blob_sha": observed,
                    "source_branch": SOURCE_BRANCH,
                    "source_path": SOURCE_PATH,
                    "attempts": attempts,
                }
    except Exception as exc:
        attempts.append({"method": "git_fetch_or_show", "error": f"{type(exc).__name__}:{exc}"})

    return None, {
        "pass": False,
        "materialization_method": None,
        "required_blob_sha": REQUIRED_BLOB_SHA,
        "observed_blob_sha": None,
        "source_branch": SOURCE_BRANCH,
        "source_path": SOURCE_PATH,
        "attempts": attempts,
        "blocker": "EXACT_CANONICAL_GIT_BLOB_NOT_VERIFIED",
    }


def write_fail_closed(repo: Path, guard: dict[str, Any]) -> None:
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/security_public_safety_2_exact_blob_guard_latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "canonical_guard": guard,
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    repo = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main")).resolve()
    source, guard = materialize_exact_source(repo)
    if source is None or not guard.get("pass"):
        write_fail_closed(repo, guard)
        print(json.dumps({"slot_id": SLOT_ID, "canonical_guard": False, "final_ready": False}))
        return 2

    automation_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(automation_dir))
    core = __import__(CORE_MODULE)
    core.SOURCES = [source]
    result = core.run(core.args())
    result["canonical_guard"] = guard
    result["accuracy_4_guarded"] = True
    result["final_ready"] = False

    out_dir = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    web_dir = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    for path in [
        out_dir / "security_public_safety_2_hydrated_300_latest.json",
        web_dir / "hydrated_300_latest.json",
    ]:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    guard_path = out_dir / "security_public_safety_2_exact_blob_guard_latest.json"
    guard_path.write_text(json.dumps({"schema_version": 1, "slot_id": SLOT_ID, "canonical_guard": guard, "final_ready": False}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "slot_id": SLOT_ID,
        "canonical_guard": True,
        "canonical_rows": result.get("canonical_rows"),
        "accuracy_ge_3_count": result.get("accuracy_ge_3_count"),
        "accuracy_4_count": result.get("accuracy_4_count"),
        "final_ready": False,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
