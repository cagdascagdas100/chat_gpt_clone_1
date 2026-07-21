from __future__ import annotations

import argparse
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


def repo_has_contract(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / ".git").exists()
        and (path / "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation").is_dir()
    )


def resolve_repo_root() -> Path:
    candidates: list[Path] = []
    explicit = os.environ.get("AAYS_REPO_ROOT")
    if explicit:
        candidates.append(Path(explicit).expanduser())

    for probe in (Path.cwd(), Path(__file__).resolve().parent):
        try:
            completed = subprocess.run(
                ["git", "-C", str(probe), "rev-parse", "--show-toplevel"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if completed.returncode == 0 and completed.stdout.strip():
                candidates.append(Path(completed.stdout.strip()))
        except Exception:
            pass

    script_path = Path(__file__).resolve()
    candidates.extend(script_path.parents)
    candidates.append(Path(r"F:\chatgpt\chat_gpt_clone_1_main"))

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
        if repo_has_contract(resolved):
            return resolved
    raise RuntimeError("AAYS_REPO_ROOT_NOT_RESOLVED")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def git_show_to_file(repo: Path, ref: str, target: Path) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    with temporary.open("wb") as output:
        completed = subprocess.run(
            ["git", "-C", str(repo), "show", ref],
            stdout=output,
            stderr=subprocess.PIPE,
            check=False,
        )
    stderr = completed.stderr.decode("utf-8", errors="replace")[-2000:]
    if completed.returncode == 0:
        os.replace(temporary, target)
    else:
        temporary.unlink(missing_ok=True)
    return {
        "method": "git_show_stream",
        "ref": ref,
        "returncode": completed.returncode,
        "stderr": stderr,
        "bytes": target.stat().st_size if completed.returncode == 0 and target.is_file() else 0,
    }


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
        attempt = git_show_to_file(repo, ref, target)
        observed = blob_sha(repo, target) if attempt["returncode"] == 0 else None
        attempt.update({"path": str(target), "blob_sha": observed})
        attempts.append(attempt)
        if observed == REQUIRED_BLOB_SHA:
            return target, {
                "pass": True,
                "materialization_method": "git_show_stream_exact_blob",
                "required_blob_sha": REQUIRED_BLOB_SHA,
                "observed_blob_sha": observed,
                "source_branch": SOURCE_BRANCH,
                "source_path": SOURCE_PATH,
                "attempts": attempts,
            }

    try:
        fetch = git(repo, "fetch", "--no-tags", "origin", SOURCE_BRANCH, check=False)
        attempts.append({
            "method": "git_fetch",
            "returncode": fetch.returncode,
            "stderr": fetch.stderr.decode("utf-8", errors="replace")[-2000:],
        })
        if fetch.returncode == 0:
            attempt = git_show_to_file(repo, f"FETCH_HEAD:{SOURCE_PATH}", target)
            observed = blob_sha(repo, target) if attempt["returncode"] == 0 else None
            attempt.update({"path": str(target), "blob_sha": observed})
            attempts.append(attempt)
            if observed == REQUIRED_BLOB_SHA:
                return target, {
                    "pass": True,
                    "materialization_method": "fetch_head_stream_exact_blob",
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


def output_paths(repo: Path) -> list[Path]:
    out_dir = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    web_dir = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    return [
        out_dir / "security_public_safety_2_hydrated_300_latest.json",
        out_dir / "security_public_safety_2_hydrated_300_latest.csv",
        out_dir / "security_public_safety_2_hydrated_300_latest.geojson",
        web_dir / "hydrated_300_latest.json",
    ]


def clear_hydrated_outputs(repo: Path) -> None:
    for path in output_paths(repo):
        path.unlink(missing_ok=True)


def write_fail_closed(repo: Path, guard: dict[str, Any], blocker: str | None = None) -> None:
    clear_hydrated_outputs(repo)
    out = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs/security_public_safety_2_exact_blob_guard_latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "canonical_guard": guard,
        "blocker": blocker or guard.get("blocker"),
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--repo-root")
    known, remaining = parser.parse_known_args()
    known.core_argv = remaining
    return known


def main() -> int:
    own_args = parse_args()
    if own_args.repo_root:
        os.environ["AAYS_REPO_ROOT"] = own_args.repo_root
    try:
        repo = resolve_repo_root()
    except Exception as exc:
        print(json.dumps({"slot_id": SLOT_ID, "state": "BLOCKED_REPO_ROOT", "error": f"{type(exc).__name__}:{exc}", "final_ready": False}))
        return 2

    os.environ["AAYS_REPO_ROOT"] = str(repo)
    source, guard = materialize_exact_source(repo)
    if source is None or not guard.get("pass"):
        write_fail_closed(repo, guard)
        print(json.dumps({"slot_id": SLOT_ID, "canonical_guard": False, "final_ready": False}))
        return 3

    os.environ["AAYS_CANONICAL_SOURCE_PATH"] = str(source)
    automation_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(automation_dir))
    sys.modules.pop(CORE_MODULE, None)
    core = __import__(CORE_MODULE)

    original_load_base = core.load_base

    def load_base_exact() -> Any:
        base = original_load_base()
        base.SOURCES = [source]
        return base

    core.load_base = load_base_exact
    old_argv = sys.argv[:]
    try:
        sys.argv = [old_argv[0], *own_args.core_argv]
        arguments = core.parse_args()
        result = core.run(arguments)
    except Exception as exc:
        guard["execution_error"] = f"{type(exc).__name__}:{exc}"
        write_fail_closed(repo, guard, "GUARDED_CORE_EXECUTION_FAILED")
        print(json.dumps({"slot_id": SLOT_ID, "state": "BLOCKED_CORE_EXECUTION", "error": guard["execution_error"], "final_ready": False}))
        return 4
    finally:
        sys.argv = old_argv

    observed_source = Path(str(result.get("source_file") or "")).resolve() if result.get("source_file") else None
    source_override_observed = observed_source == source.resolve()
    guard["source_override_observed"] = source_override_observed
    guard["observed_runtime_source"] = str(observed_source) if observed_source else None
    if not source_override_observed:
        write_fail_closed(repo, guard, "EXACT_SOURCE_OVERRIDE_NOT_OBSERVED")
        print(json.dumps({"slot_id": SLOT_ID, "state": "BLOCKED_SOURCE_OVERRIDE", "final_ready": False}))
        return 5

    result["canonical_guard"] = guard
    result["accuracy_4_guarded"] = True
    result["final_ready"] = False

    out_dir = repo / "docs/chatgpt_status/aays1/shards/security_public_safety_2/runner_outputs"
    web_dir = repo / "england_map_web/data/aays_18_slots/security_public_safety_2"
    out_dir.mkdir(parents=True, exist_ok=True)
    web_dir.mkdir(parents=True, exist_ok=True)
    for path in [
        out_dir / "security_public_safety_2_hydrated_300_latest.json",
        web_dir / "hydrated_300_latest.json",
    ]:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    guard_path = out_dir / "security_public_safety_2_exact_blob_guard_latest.json"
    guard_path.write_text(json.dumps({
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "canonical_guard": guard,
        "actual_business_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "slot_id": SLOT_ID,
        "canonical_guard": True,
        "source_override_observed": True,
        "canonical_rows": result.get("canonical_rows"),
        "accuracy_ge_3_count": result.get("accuracy_ge_3_count"),
        "accuracy_4_count": result.get("accuracy_4_count"),
        "final_ready": False,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
