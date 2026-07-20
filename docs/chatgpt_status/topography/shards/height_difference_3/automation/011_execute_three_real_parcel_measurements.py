#!/usr/bin/env python3
"""Execute the official three-parcel boundary, DTM and publication pipeline.

This orchestrator is for the existing single shared runner. It does not search
for or invent candidates; it starts from a validated starter manifest and
fails closed at the first missing evidence gate.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_many(command: list[str], flag: str, paths: list[Path]) -> None:
    for path in paths:
        command.extend([flag, str(path)])


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
    parser.add_argument("--starter-manifest", type=Path, required=True)
    parser.add_argument("--hmlr-vector", type=Path, action="append", default=[])
    parser.add_argument("--hmlr-root", type=Path, action="append", default=[])
    parser.add_argument("--ea-raster", type=Path, action="append", default=[])
    parser.add_argument("--ea-root", type=Path, action="append", default=[])
    parser.add_argument("--terrain50-raster", type=Path, action="append", default=[])
    parser.add_argument("--terrain50-root", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-files", type=int, default=500)
    parser.add_argument("--minimum-ea-cells", type=int, default=4)
    parser.add_argument("--max-crosscheck-difference-m", type=float, default=8.0)
    args = parser.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    matcher = script_dir / "008_match_hmlr_inspire_gml.py"
    sampler = script_dir / "009_sample_ea_dtm_and_os_terrain50.py"
    publisher = script_dir / "010_publish_verified_height_difference_examples.py"
    for script in (matcher, sampler, publisher):
        if not script.is_file():
            raise FileNotFoundError(script)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    matched = output_dir / "hmlr_matches.json"
    measured = output_dir / "official_measurements.json"
    site_json = output_dir / "verified_examples.json"
    site_geojson = output_dir / "verified_examples.geojson"
    execution_path = output_dir / "pipeline_execution.json"

    matcher_cmd = [
        sys.executable,
        str(matcher),
        "--starter-manifest",
        str(args.starter_manifest),
        "--output",
        str(matched),
        "--max-files",
        str(args.max_files),
    ]
    _append_many(matcher_cmd, "--vector", args.hmlr_vector)
    _append_many(matcher_cmd, "--vector-root", args.hmlr_root)

    sampler_cmd = [
        sys.executable,
        str(sampler),
        "--matched-manifest",
        str(matched),
        "--output",
        str(measured),
        "--max-files",
        str(args.max_files),
        "--minimum-ea-cells",
        str(args.minimum_ea_cells),
        "--max-crosscheck-difference-m",
        str(args.max_crosscheck_difference_m),
    ]
    _append_many(sampler_cmd, "--ea-raster", args.ea_raster)
    _append_many(sampler_cmd, "--ea-root", args.ea_root)
    _append_many(sampler_cmd, "--terrain50-raster", args.terrain50_raster)
    _append_many(sampler_cmd, "--terrain50-root", args.terrain50_root)

    publisher_cmd = [
        sys.executable,
        str(publisher),
        "--measurement-manifest",
        str(measured),
        "--output-json",
        str(site_json),
        "--output-geojson",
        str(site_geojson),
    ]

    stages: list[dict[str, Any]] = []
    status = "BLOCKED"
    for stage_name, command in (
        ("HMLR_BOUNDARY_MATCH", matcher_cmd),
        ("EA_DTM_AND_OS_TERRAIN50_SAMPLE", sampler_cmd),
        ("WEBSITE_VERIFIED_EXAMPLE_PUBLICATION", publisher_cmd),
    ):
        result = _run(command, script_dir)
        result["stage"] = stage_name
        stages.append(result)
        if result["exit_code"] != 0:
            status = f"BLOCKED_{stage_name}"
            break
    else:
        status = "THREE_REAL_PARCELS_MEASURED_AND_PUBLISHED"

    execution = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "single_shared_runner_only": True,
        "starter_manifest": str(args.starter_manifest),
        "status": status,
        "stages": stages,
        "outputs": {
            "hmlr_matches": str(matched),
            "official_measurements": str(measured),
            "website_json": str(site_json),
            "website_geojson": str(site_geojson),
        },
        "nearest_fill_forbidden": True,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    _write(execution_path, execution)
    print(json.dumps({"ok": status == "THREE_REAL_PARCELS_MEASURED_AND_PUBLISHED", "status": status}))
    return 0 if status == "THREE_REAL_PARCELS_MEASURED_AND_PUBLISHED" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
