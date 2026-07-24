#!/usr/bin/env python3
"""Safely sync the existing worktree, run the real pipeline, then transactional website acceptance."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def run(command: list[str]) -> dict[str, Any]:
    started = now()
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    return {
        "started_at": started,
        "finished_at": now(),
        "command": command,
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-16000:],
        "stderr_tail": proc.stderr[-16000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--security-geojson", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--web-runtime-status", required=True, type=Path)
    parser.add_argument("--web-operations-history", required=True, type=Path)
    parser.add_argument("--web-json", type=Path, default=Path("england_map_web/data/aays_18_slots/height_difference_3/verified_examples_latest.json"))
    parser.add_argument("--web-geojson", type=Path, default=Path("england_map_web/data/aays_18_slots/height_difference_3/verified_examples_latest.geojson"))
    parser.add_argument("--base-url", default="http://127.0.0.1:8012")
    parser.add_argument("--script-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--expected-branch", default="codex/aays-single-runner-v5-20260706")
    parser.add_argument("--minimum-commit", default="b0b8bd63d95d8193ce5b14ad19051bdc33201173")
    parser.add_argument("--remote-name", default="origin")
    parser.add_argument("--expected-remote-repository", default="cagdascagdas100/chat_gpt_clone_1")
    parser.add_argument("--git-timeout", type=int, default=120)
    parser.add_argument("--operation-start", type=int)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--preflight-timeout", type=int, default=30)
    parser.add_argument("--acceptance-timeout", type=int, default=30)
    parser.add_argument("--runtime-poll-seconds", type=float, default=0.5)
    parser.add_argument("--min-free-bytes", type=int, default=4 * 1024 * 1024 * 1024)
    parser.add_argument("--expected-git-blob-sha1", default="8afd1d2bac414cf0f6b9484014e7878a4ceff877")
    args = parser.parse_args()
    if min(args.timeout, args.preflight_timeout, args.acceptance_timeout, args.git_timeout) < 1:
        raise ValueError("timeouts must be positive")

    scripts = args.script_dir.resolve()
    syncer = scripts / "035_sync_existing_f_worktree_ff_only.py"
    bootstrap = scripts / "029_preflight_then_execute_resumable.py"
    acceptance = scripts / "031_publish_verify_three_examples_port8012.py"
    transaction = scripts / "033_transactional_website_acceptance.py"
    worktree_verifier = scripts / "034_verify_existing_f_worktree.py"
    for path in (syncer, bootstrap, acceptance, transaction, worktree_verifier):
        if not path.is_file():
            raise FileNotFoundError(path)

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "full_pipeline_and_website_acceptance_execution.json"
    state = {
        "schema_version": 5,
        "slot_id": "height_difference_3",
        "updated_at": now(),
        "status": "035_SAFE_FAST_FORWARD_SYNC_STARTING",
        "worktree_sync": None,
        "worktree_preflight": None,
        "pipeline": None,
        "website_acceptance_transaction": None,
        "single_shared_runner_only": True,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_submission": False,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    write(report_path, state)

    repo_root = args.repo_root.resolve()
    sync_command = [
        sys.executable,
        str(syncer),
        "--repo-root", str(repo_root),
        "--expected-branch", args.expected_branch,
        "--remote-name", args.remote_name,
        "--expected-remote-repository", args.expected_remote_repository,
        "--git-timeout", str(args.git_timeout),
        "--output", str(out / "worktree_sync_latest.json"),
    ]
    state["worktree_sync"] = run(sync_command)
    state["updated_at"] = now()
    if state["worktree_sync"]["exit_code"] != 0:
        state["status"] = "BLOCKED_035_SAFE_FAST_FORWARD_SYNC"
        write(report_path, state)
        return int(state["worktree_sync"]["exit_code"])

    scripts = args.script_dir.resolve()
    bootstrap = scripts / "029_preflight_then_execute_resumable.py"
    acceptance = scripts / "031_publish_verify_three_examples_port8012.py"
    transaction = scripts / "033_transactional_website_acceptance.py"
    worktree_verifier = scripts / "034_verify_existing_f_worktree.py"
    for path in (bootstrap, acceptance, transaction, worktree_verifier):
        if not path.is_file():
            raise FileNotFoundError(path)

    required_files = [
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/004_prepare_three_real_sample_queries.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/008_match_hmlr_inspire_gml.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/009_sample_ea_dtm_and_os_terrain50.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/010_publish_verified_height_difference_examples.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/012_download_hmlr_inspire_sources.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/013_fetch_ea_dtm_wcs_for_matches.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/014_prepare_os_terrain50_tiles.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/020_stream_extract_security_canonical.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/023_download_os_terrain50_required_areas.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/025_validate_resumable_targeted_sources.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/026_execute_resumable_targeted_sources.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/027_validate_resumable_alias_safe.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/028_preflight_existing_f_runner.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/029_preflight_then_execute_resumable.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/030_stream_combined_runtime.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/031_publish_verify_three_examples_port8012.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/032_run_full_pipeline_and_website_acceptance.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/033_transactional_website_acceptance.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/034_verify_existing_f_worktree.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/automation/035_sync_existing_f_worktree_ff_only.py",
        "docs/chatgpt_status/topography/shards/height_difference_3/runner_tasks/012_resumable_targeted_sources.task.json",
    ]
    state["status"] = "034_REMOTE_PARITY_WORKTREE_PREFLIGHT_STARTING"
    write(report_path, state)
    worktree_command = [
        sys.executable,
        str(worktree_verifier),
        "--repo-root", str(repo_root),
        "--expected-branch", args.expected_branch,
        "--minimum-commit", args.minimum_commit,
        "--remote-name", args.remote_name,
        "--expected-remote-repository", args.expected_remote_repository,
        "--git-timeout", str(args.git_timeout),
        "--output", str(out / "worktree_preflight_latest.json"),
    ]
    for required_file in required_files:
        worktree_command.extend(["--required-file", required_file])
    state["worktree_preflight"] = run(worktree_command)
    state["updated_at"] = now()
    if state["worktree_preflight"]["exit_code"] != 0:
        state["status"] = "BLOCKED_034_REMOTE_PARITY_OR_EXISTING_F_WORKTREE_PREFLIGHT"
        write(report_path, state)
        return int(state["worktree_preflight"]["exit_code"])

    state["status"] = "029_PIPELINE_STARTING"
    write(report_path, state)
    pipeline = [
        sys.executable,
        str(bootstrap),
        "--security-geojson", str(args.security_geojson.resolve()),
        "--output-dir", str(out),
        "--web-runtime-status", str(args.web_runtime_status.resolve()),
        "--web-operations-history", str(args.web_operations_history.resolve()),
        "--timeout", str(args.timeout),
        "--preflight-timeout", str(args.preflight_timeout),
        "--runtime-poll-seconds", str(args.runtime_poll_seconds),
        "--min-free-bytes", str(args.min_free_bytes),
        "--expected-git-blob-sha1", args.expected_git_blob_sha1,
    ]
    if args.operation_start is not None:
        pipeline.extend(["--operation-start", str(args.operation_start)])
    state["pipeline"] = run(pipeline)
    state["updated_at"] = now()
    if state["pipeline"]["exit_code"] != 0:
        state["status"] = "BLOCKED_029_PIPELINE_OR_PREFLIGHT"
        write(report_path, state)
        return int(state["pipeline"]["exit_code"])

    state["status"] = "033_TRANSACTIONAL_WEBSITE_ACCEPTANCE_RUNNING"
    write(report_path, state)
    command = [
        sys.executable,
        str(transaction),
        "--acceptance-script", str(acceptance),
        "--output-dir", str(out),
        "--web-json", str(args.web_json.resolve()),
        "--web-geojson", str(args.web_geojson.resolve()),
        "--web-runtime-status", str(args.web_runtime_status.resolve()),
        "--base-url", args.base_url,
        "--timeout", str(args.acceptance_timeout),
        "--acceptance-output", str(out / "website_acceptance_latest.json"),
        "--transaction-output", str(out / "website_acceptance_transaction_latest.json"),
    ]
    state["website_acceptance_transaction"] = run(command)
    state["updated_at"] = now()
    if state["website_acceptance_transaction"]["exit_code"] != 0:
        state["status"] = "BLOCKED_033_WEBSITE_ACCEPTANCE_TRANSACTION_ROLLED_BACK_OR_FAILED"
        write(report_path, state)
        return int(state["website_acceptance_transaction"]["exit_code"])

    state["status"] = "THREE_REAL_EXAMPLES_TRANSACTIONALLY_PUBLISHED_AND_PORT_8012_ACCEPTED"
    write(report_path, state)
    print(json.dumps({"ok": True, "status": state["status"], "report": str(report_path)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
