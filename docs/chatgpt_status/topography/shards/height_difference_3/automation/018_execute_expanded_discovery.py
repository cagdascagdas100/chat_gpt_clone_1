#!/usr/bin/env python3
"""Run expanded canonical discovery and official source preparation in one runner.

The existing shared runner remains the only executor. This script performs no
lease, queue, runner creation, database write, migration, or deployment.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from typing import Any, Iterable

def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "exit_code": process.returncode,
        "stdout": process.stdout[-8000:],
        "stderr": process.stderr[-8000:],
    }

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repository", default="cagdascagdas100/chat_gpt_clone_1")
    parser.add_argument("--ref", default="codex/aays-single-runner-v5-20260706")
    parser.add_argument("--github-api-base", default="https://api.github.com")
    parser.add_argument("--terrain50-har", type=Path, action="append", default=[])
    parser.add_argument("--terrain50-url", action="append", default=[])
    parser.add_argument("--download-terrain50", action="store_true")
    args = parser.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    github_discovery = script_dir / "016_discover_canonical_via_github_tree.py"
    terrain_capture = script_dir / "017_capture_validate_os_terrain50_download.py"
    for script in (github_discovery, terrain_capture):
        if not script.is_file():
            raise FileNotFoundError(script)

    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    stages = []

    github_cmd = [
        sys.executable, str(github_discovery),
        "--repository", args.repository,
        "--ref", args.ref,
        "--api-base", args.github_api_base,
        "--output-dir", str(output / "github_discovery"),
    ]
    github_result = _run(github_cmd, script_dir)
    github_result["stage"] = "GITHUB_TREE_CANONICAL_DISCOVERY"
    stages.append(github_result)

    terrain_cmd = [
        sys.executable, str(terrain_capture),
        "--output-dir", str(output / "terrain50"),
    ]
    for path in args.terrain50_har:
        terrain_cmd.extend(["--har", str(path)])
    for url in args.terrain50_url:
        terrain_cmd.extend(["--url", url])
    if args.download_terrain50:
        terrain_cmd.append("--download")
    terrain_result = _run(terrain_cmd, script_dir)
    terrain_result["stage"] = "OS_TERRAIN50_DOWNLOAD_CAPTURE_AND_VALIDATION"
    stages.append(terrain_result)

    canonical_ready = github_result["exit_code"] == 0
    terrain_ready = terrain_result["exit_code"] == 0 and (
        args.download_terrain50 or bool(args.terrain50_har) or bool(args.terrain50_url)
    )
    if canonical_ready and terrain_ready:
        status = "DISCOVERY_AND_TERRAIN50_INPUTS_READY_FOR_EXISTING_PIPELINE"
        code = 0
    else:
        blockers = []
        if not canonical_ready:
            blockers.append("CANONICAL_8012_MATRIX_SHARD_EXPORT_REQUIRED")
        if not terrain_ready:
            blockers.append("OS_TERRAIN50_DOWNLOAD_URL_OR_ARCHIVE_REQUIRED")
        status = "BLOCKED_" + "_AND_".join(blockers)
        code = 2

    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "single_shared_runner_only": True,
        "status": status,
        "stages": stages,
        "next_pipeline": "015_execute_auto_source_and_measurement_pipeline.py",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    _write(output / "expanded_discovery_execution.json", payload)
    print(json.dumps({"ok": code == 0, "status": status}))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
