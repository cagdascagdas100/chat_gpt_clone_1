#!/usr/bin/env python3
"""Prepare official files and execute the existing three-parcel pipeline.

This is an idempotent extension for the existing single shared runner. It does
not discover or invent parcel candidates. It begins with a validated starter
manifest, downloads exact HMLR sources, matches boundaries, retrieves bounded
EA WCS coverages, validates exact Terrain50 tiles, samples and publishes.
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
    parser.add_argument("--terrain50-source", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--hmlr-download-page", default="https://use-land-property-data.service.gov.uk/datasets/inspire/download")
    parser.add_argument("--ea-wcs-base", default="https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--maximum-crosscheck-difference-m", type=float, default=8.0)
    args = parser.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    scripts = {
        "HMLR_SOURCE_PREPARATION": script_dir / "012_download_hmlr_inspire_sources.py",
        "HMLR_BOUNDARY_MATCH": script_dir / "008_match_hmlr_inspire_gml.py",
        "EA_DTM_WCS_PREPARATION": script_dir / "013_fetch_ea_dtm_wcs_for_matches.py",
        "TERRAIN50_SOURCE_PREPARATION": script_dir / "014_prepare_os_terrain50_tiles.py",
        "EA_DTM_AND_TERRAIN50_SAMPLE": script_dir / "009_sample_ea_dtm_and_os_terrain50.py",
        "WEBSITE_PUBLICATION": script_dir / "010_publish_verified_height_difference_examples.py",
    }
    for path in scripts.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    output_root = args.output_dir.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    hmlr_source = output_root / "sources" / "hmlr_source_manifest.json"
    matches = output_root / "hmlr_matches.json"
    ea_source = output_root / "sources" / "ea_dtm_source_manifest.json"
    terrain_source = output_root / "sources" / "terrain50_source_manifest.json"
    measurements = output_root / "official_measurements.json"
    site_json = output_root / "verified_examples.json"
    site_geojson = output_root / "verified_examples.geojson"
    execution_path = output_root / "auto_source_pipeline_execution.json"

    commands: list[tuple[str, list[str]]] = []
    commands.append(("HMLR_SOURCE_PREPARATION", [
        sys.executable, str(scripts["HMLR_SOURCE_PREPARATION"]),
        "--starter-manifest", str(args.starter_manifest),
        "--output-dir", str(output_root / "sources"),
        "--download-page", args.hmlr_download_page,
        "--timeout", str(args.timeout),
    ]))
    commands.append(("HMLR_BOUNDARY_MATCH", [
        sys.executable, str(scripts["HMLR_BOUNDARY_MATCH"]),
        "--starter-manifest", str(args.starter_manifest),
        "--vector-root", str(output_root / "sources" / "hmlr"),
        "--output", str(matches),
    ]))
    commands.append(("EA_DTM_WCS_PREPARATION", [
        sys.executable, str(scripts["EA_DTM_WCS_PREPARATION"]),
        "--matched-manifest", str(matches),
        "--output-dir", str(output_root / "sources"),
        "--wcs-base", args.ea_wcs_base,
        "--timeout", str(args.timeout),
    ]))
    terrain_command = [
        sys.executable, str(scripts["TERRAIN50_SOURCE_PREPARATION"]),
        "--matched-manifest", str(matches),
        "--output-dir", str(output_root / "sources"),
    ]
    for source in args.terrain50_source:
        terrain_command.extend(["--source", str(source)])
    commands.append(("TERRAIN50_SOURCE_PREPARATION", terrain_command))
    commands.append(("EA_DTM_AND_TERRAIN50_SAMPLE", [
        sys.executable, str(scripts["EA_DTM_AND_TERRAIN50_SAMPLE"]),
        "--matched-manifest", str(matches),
        "--ea-root", str(output_root / "sources" / "ea_dtm"),
        "--terrain50-root", str(output_root / "sources" / "terrain50"),
        "--max-crosscheck-difference-m", str(args.maximum_crosscheck_difference_m),
        "--output", str(measurements),
    ]))
    commands.append(("WEBSITE_PUBLICATION", [
        sys.executable, str(scripts["WEBSITE_PUBLICATION"]),
        "--measurement-manifest", str(measurements),
        "--output-json", str(site_json),
        "--output-geojson", str(site_geojson),
    ]))

    stages = []
    status = "BLOCKED"
    for name, command in commands:
        result = _run(command, script_dir)
        result["stage"] = name
        stages.append(result)
        if result["exit_code"] != 0:
            status = f"BLOCKED_{name}"
            break
    else:
        status = "THREE_REAL_PARCELS_OFFICIAL_SOURCES_PREPARED_MEASURED_AND_PUBLISHED"

    execution = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "single_shared_runner_only": True,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "starter_manifest": str(args.starter_manifest),
        "status": status,
        "stages": stages,
        "outputs": {
            "hmlr_source_manifest": str(hmlr_source),
            "hmlr_matches": str(matches),
            "ea_source_manifest": str(ea_source),
            "terrain50_source_manifest": str(terrain_source),
            "official_measurements": str(measurements),
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
    print(json.dumps({"ok": status.startswith("THREE_REAL"), "status": status, "execution": str(execution_path)}))
    return 0 if status.startswith("THREE_REAL") else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
