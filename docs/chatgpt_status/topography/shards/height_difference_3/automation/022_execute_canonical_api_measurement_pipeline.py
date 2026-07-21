#!/usr/bin/env python3
"""Run the complete height_difference_3 canonical-to-publication chain on the existing runner.

Stages:
1. stream-validate security.geojson and export rows 61523..92283
2. select the first three explicit source-backed rows via existing 004
3. acquire/validate OS Terrain 50 through the official Downloads API
4. run HMLR + EA DTM + Terrain50 measurement and verified website publication via existing 015

No runner, queue, lease or synthetic measurement is created.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(stage: str, command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "stage": stage,
        "command": command,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-12000:],
        "stderr": proc.stderr[-12000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--security-geojson", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--terrain50-archive", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--script-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--no-network-query-preparer", action="store_true")
    args = parser.parse_args()

    script_dir = args.script_dir.resolve()
    scripts = {
        "extractor": script_dir / "020_stream_extract_security_canonical.py",
        "query_preparer": script_dir / "004_prepare_three_real_sample_queries.py",
        "terrain_api": script_dir / "021_download_os_terrain50_via_api.py",
        "measurement": script_dir / "015_execute_auto_source_and_measurement_pipeline.py",
    }
    for path in scripts.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    source = args.security_geojson.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    canonical_out = out / "canonical"
    terrain_out = out / "terrain50"
    measurement_out = out / "measurement"
    execution_path = out / "canonical_api_measurement_execution.json"

    stages: list[dict[str, Any]] = []
    extract_cmd = [
        sys.executable,
        str(scripts["extractor"]),
        "--source-geojson",
        str(source),
        "--output-dir",
        str(canonical_out),
        "--query-preparer",
        str(scripts["query_preparer"]),
    ]
    if args.no_network_query_preparer:
        extract_cmd.append("--no-network")
    stages.append(run("CANONICAL_STREAM_EXTRACT_AND_PREPARE_THREE", extract_cmd, script_dir))
    status = "BLOCKED_CANONICAL_STREAM_EXTRACT_AND_PREPARE_THREE"

    terrain_archive: Path | None = None
    if stages[-1]["exit_code"] == 0:
        terrain_cmd = [
            sys.executable,
            str(scripts["terrain_api"]),
            "--output-dir",
            str(terrain_out),
            "--timeout",
            str(args.timeout),
        ]
        if args.terrain50_archive:
            terrain_archive = args.terrain50_archive.resolve()
            terrain_cmd += ["--archive", str(terrain_archive)]
        else:
            terrain_archive = terrain_out / "OS_Terrain50_July_2026_GB_ASCII_Grid.zip"
        stages.append(run("OS_TERRAIN50_OFFICIAL_API_ACQUISITION", terrain_cmd, script_dir))
        status = "BLOCKED_OS_TERRAIN50_OFFICIAL_API_ACQUISITION"

    if len(stages) == 2 and stages[-1]["exit_code"] == 0 and terrain_archive is not None:
        starter = canonical_out / "starter_three_query_manifest.json"
        measure_cmd = [
            sys.executable,
            str(scripts["measurement"]),
            "--starter-manifest",
            str(starter),
            "--terrain50-source",
            str(terrain_archive),
            "--output-dir",
            str(measurement_out),
            "--timeout",
            str(args.timeout),
        ]
        stages.append(run("OFFICIAL_HMLR_EA_OS_MEASURE_AND_PUBLISH", measure_cmd, script_dir))
        status = "BLOCKED_OFFICIAL_HMLR_EA_OS_MEASURE_AND_PUBLISH"

    if len(stages) == 3 and stages[-1]["exit_code"] == 0:
        status = "THREE_REAL_SHARD_ROWS_OFFICIAL_CROSSCHECKED_AND_PUBLISHED"

    execution = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "single_shared_runner_only": True,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_submission": False,
        "security_geojson": str(source),
        "status": status,
        "stages": stages,
        "outputs": {
            "canonical_manifest": str(canonical_out / "stream_extraction_manifest.json"),
            "canonical_shard": str(canonical_out / "canonical_shard_61523_92283.jsonl"),
            "first_three_candidates": str(canonical_out / "first_three_canonical_candidates.json"),
            "starter_manifest": str(canonical_out / "starter_three_query_manifest.json"),
            "terrain50_provenance": str(terrain_out / "terrain50_official_api_provenance.json"),
            "measurement_execution": str(measurement_out / "auto_source_pipeline_execution.json"),
            "verified_json": str(measurement_out / "verified_examples.json"),
            "verified_geojson": str(measurement_out / "verified_examples.geojson"),
        },
        "nearest_fill_forbidden": True,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    write_json(execution_path, execution)
    ok = status.startswith("THREE_REAL")
    print(json.dumps({"ok": ok, "status": status, "execution": str(execution_path)}))
    return 0 if ok else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
