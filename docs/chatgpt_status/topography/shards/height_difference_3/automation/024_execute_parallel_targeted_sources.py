#!/usr/bin/env python3
"""Execute the height_difference_3 source chain with bounded in-process concurrency.

This uses one existing runner process. HMLR and OS downloads run concurrently;
after the boundary match, EA WCS retrieval and exact Terrain50 tile extraction
run concurrently. No new runner, queue, lease or synthetic value is created.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(name: str, command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {"stage": name, "command": command, "exit_code": proc.returncode, "stdout": proc.stdout[-12000:], "stderr": proc.stderr[-12000:]}


def _parallel(commands: list[tuple[str, list[str]]], cwd: Path) -> list[dict[str, Any]]:
    with ThreadPoolExecutor(max_workers=len(commands), thread_name_prefix="height_difference_3_source") as pool:
        futures = [pool.submit(_run, name, command, cwd) for name, command in commands]
        return [future.result() for future in futures]


def _require_success(results: list[dict[str, Any]], group: str) -> None:
    failed = [result for result in results if result["exit_code"] != 0]
    if failed:
        raise RuntimeError(f"{group} failed: {[result['stage'] for result in failed]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--security-geojson", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--script-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--no-network-query-preparer", action="store_true")
    args = parser.parse_args()

    script_dir = args.script_dir.resolve()
    scripts = {
        "extract": script_dir / "020_stream_extract_security_canonical.py",
        "query": script_dir / "004_prepare_three_real_sample_queries.py",
        "hmlr_download": script_dir / "012_download_hmlr_inspire_sources.py",
        "terrain_area_download": script_dir / "023_download_os_terrain50_required_areas.py",
        "hmlr_match": script_dir / "008_match_hmlr_inspire_gml.py",
        "ea_wcs": script_dir / "013_fetch_ea_dtm_wcs_for_matches.py",
        "terrain_tile": script_dir / "014_prepare_os_terrain50_tiles.py",
        "sample": script_dir / "009_sample_ea_dtm_and_os_terrain50.py",
        "publish": script_dir / "010_publish_verified_height_difference_examples.py",
    }
    for path in scripts.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    source = args.security_geojson.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    out = args.output_dir.resolve()
    canonical = out / "canonical"
    sources = out / "sources"
    terrain_areas = sources / "os_terrain50_areas"
    matches = out / "hmlr_matches.json"
    measurements = out / "official_measurements.json"
    website_json = out / "verified_examples.json"
    website_geojson = out / "verified_examples.geojson"
    execution_path = out / "parallel_targeted_source_execution.json"
    out.mkdir(parents=True, exist_ok=True)

    stages: list[dict[str, Any]] = []
    status = "BLOCKED_CANONICAL_STREAM_EXTRACT_AND_PREPARE_THREE"
    try:
        extract_cmd = [sys.executable, str(scripts["extract"]), "--source-geojson", str(source), "--output-dir", str(canonical), "--query-preparer", str(scripts["query"])]
        if args.no_network_query_preparer:
            extract_cmd.append("--no-network")
        first = _run("CANONICAL_STREAM_EXTRACT_AND_PREPARE_THREE", extract_cmd, script_dir)
        stages.append(first)
        _require_success([first], "canonical extraction")

        starter = canonical / "starter_three_query_manifest.json"
        group2 = _parallel([
            ("HMLR_SOURCE_PREPARATION", [sys.executable, str(scripts["hmlr_download"]), "--starter-manifest", str(starter), "--output-dir", str(sources), "--timeout", str(args.timeout)]),
            ("TERRAIN50_REQUIRED_AREA_ACQUISITION", [sys.executable, str(scripts["terrain_area_download"]), "--starter-manifest", str(starter), "--output-dir", str(terrain_areas), "--timeout", str(args.timeout)]),
        ], script_dir)
        stages.extend(group2)
        status = "BLOCKED_PARALLEL_HMLR_AND_TERRAIN50_AREA_ACQUISITION"
        _require_success(group2, "parallel source acquisition")

        hmlr = _run("HMLR_BOUNDARY_MATCH", [sys.executable, str(scripts["hmlr_match"]), "--starter-manifest", str(starter), "--vector-root", str(sources / "hmlr"), "--output", str(matches)], script_dir)
        stages.append(hmlr)
        status = "BLOCKED_HMLR_BOUNDARY_MATCH"
        _require_success([hmlr], "HMLR boundary match")

        area_manifest = json.loads((terrain_areas / "terrain50_required_areas_manifest.json").read_text(encoding="utf-8-sig"))
        archives = [Path(record["archive_path"]) for record in area_manifest.get("archives") or []]
        if not archives:
            raise ValueError("Terrain50 required-area manifest has no archives")
        terrain_cmd = [sys.executable, str(scripts["terrain_tile"]), "--matched-manifest", str(matches), "--output-dir", str(sources)]
        for archive in archives:
            terrain_cmd.extend(["--source", str(archive)])
        group4 = _parallel([
            ("EA_DTM_WCS_PREPARATION", [sys.executable, str(scripts["ea_wcs"]), "--matched-manifest", str(matches), "--output-dir", str(sources), "--timeout", str(args.timeout)]),
            ("TERRAIN50_EXACT_TILE_PREPARATION", terrain_cmd),
        ], script_dir)
        stages.extend(group4)
        status = "BLOCKED_PARALLEL_EA_AND_TERRAIN50_TILE_PREPARATION"
        _require_success(group4, "parallel raster preparation")

        sample = _run("EA_DTM_AND_TERRAIN50_SAMPLE", [sys.executable, str(scripts["sample"]), "--matched-manifest", str(matches), "--ea-root", str(sources / "ea_dtm"), "--terrain50-root", str(sources / "terrain50"), "--output", str(measurements)], script_dir)
        stages.append(sample)
        status = "BLOCKED_EA_DTM_AND_TERRAIN50_SAMPLE"
        _require_success([sample], "official sampling")

        publish = _run("VERIFIED_WEBSITE_PUBLICATION", [sys.executable, str(scripts["publish"]), "--measurement-manifest", str(measurements), "--output-json", str(website_json), "--output-geojson", str(website_geojson)], script_dir)
        stages.append(publish)
        status = "BLOCKED_VERIFIED_WEBSITE_PUBLICATION"
        _require_success([publish], "website publication")
        status = "THREE_REAL_SHARD_ROWS_OFFICIAL_CROSSCHECKED_AND_PUBLISHED"
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
    else:
        failure = None

    execution = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "single_shared_runner_only": True,
        "single_process_bounded_concurrency": True,
        "maximum_parallel_network_stages": 2,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_submission": False,
        "status": status,
        "failure": failure,
        "stages": stages,
        "outputs": {
            "canonical_shard": str(canonical / "canonical_shard_61523_92283.jsonl"),
            "starter_manifest": str(canonical / "starter_three_query_manifest.json"),
            "terrain50_area_manifest": str(terrain_areas / "terrain50_required_areas_manifest.json"),
            "hmlr_matches": str(matches),
            "official_measurements": str(measurements),
            "verified_json": str(website_json),
            "verified_geojson": str(website_geojson),
        },
        "nearest_fill_forbidden": True,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    _write(execution_path, execution)
    ok = status.startswith("THREE_REAL")
    print(json.dumps({"ok": ok, "status": status, "execution": str(execution_path)}))
    return 0 if ok else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
