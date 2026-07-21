#!/usr/bin/env python3
"""Portable no-argument entrypoint for the existing height_difference_3 pipeline."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("PUBLISHER_REPO_ROOT_NOT_FOUND")


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo = find_repo_root(script_dir)
    orchestrator = script_dir / "022_execute_canonical_api_measurement_pipeline.py"
    security_geojson = repo / "england_map_web" / "data" / "program_layer_matrix" / "security.geojson"
    output_dir = (
        repo
        / "docs"
        / "chatgpt_status"
        / "topography"
        / "shards"
        / "height_difference_3"
        / "runner_outputs"
        / "010_canonical_api_measurement"
    )
    if not orchestrator.is_file():
        raise FileNotFoundError(orchestrator)
    if not security_geojson.is_file():
        raise FileNotFoundError(security_geojson)
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(orchestrator),
        "--security-geojson",
        str(security_geojson),
        "--output-dir",
        str(output_dir),
        "--timeout",
        os.environ.get("AAYS_OFFICIAL_SOURCE_TIMEOUT_SECONDS", "180"),
    ]
    completed = subprocess.run(command, cwd=repo, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
