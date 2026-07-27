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
import re
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


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _clean_id(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip()).casefold()


def _starter_by_row(path: Path) -> dict[int, dict[str, Any]]:
    payload = _load_json(path)
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("starter manifest has no candidates")
    result: dict[int, dict[str, Any]] = {}
    for raw in candidates:
        if not isinstance(raw, dict):
            raise ValueError("starter candidate is not an object")
        row_no = int(raw["row_no"])
        if row_no in result:
            raise ValueError(f"duplicate starter row: {row_no}")
        result[row_no] = dict(raw)
    return result


def _exact_hmlr_matches_only(matches_path: Path, starter_path: Path) -> tuple[bool, list[dict[str, Any]]]:
    payload = _load_json(matches_path)
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("HMLR match manifest has no results")
    candidates = _starter_by_row(starter_path)
    failures: list[dict[str, Any]] = []
    for row in results:
        row_no = int(row.get("row_no"))
        method = str(row.get("match_method") or "")
        status = str(row.get("status") or "")
        candidate = candidates.get(row_no)
        expected_inspire_id = _clean_id((candidate or {}).get("hmlr_inspire_id"))
        match = row.get("match") if isinstance(row.get("match"), dict) else {}
        matched_values = {_clean_id(value) for value in (match.get("matched_identifier_values") or []) if _clean_id(value)}
        inspire_id_value_matched = bool(expected_inspire_id) and expected_inspire_id in matched_values
        if status != "MATCHED" or not method.startswith("EXACT_OFFICIAL_ID") or not inspire_id_value_matched:
            failures.append({
                "row_no": row_no,
                "parcel_id": row.get("parcel_id"),
                "status": status,
                "match_method": method or None,
                "expected_hmlr_inspire_id": expected_inspire_id or None,
                "matched_identifier_values": sorted(matched_values),
                "candidate_hmlr_inspire_id_matched": inspire_id_value_matched,
            })
    return not failures, failures


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starter-manifest", type=Path, required=True)
    parser.add_argument("--terrain50-source", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--hmlr-download-page", default="https://use-land-property-data.service.gov.uk/datasets/inspire/download")
    parser.add_argument("--ea-wcs-base", default="https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--maximum-crosscheck-difference-m", type=float, default=8.0)
    parser.add_argument("--require-exact-official-id", action="store_true")
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
    exact_hmlr_gate = {
        "required": bool(args.require_exact_official_id),
        "checked": False,
        "passed": None,
        "candidate_hmlr_inspire_id_value_required": bool(args.require_exact_official_id),
        "failures": [],
    }
    for name, command in commands:
        result = _run(command, script_dir)
        result["stage"] = name
        stages.append(result)
        if result["exit_code"] != 0:
            status = f"BLOCKED_{name}"
            break
        if name == "HMLR_BOUNDARY_MATCH" and args.require_exact_official_id:
            exact_hmlr_gate["checked"] = True
            passed, failures = _exact_hmlr_matches_only(matches, args.starter_manifest)
            exact_hmlr_gate["passed"] = passed
            exact_hmlr_gate["failures"] = failures
            if not passed:
                status = "BLOCKED_HMLR_EXACT_INSPIRE_ID_VALUE_REQUIRED"
                break
    else:
        status = "THREE_REAL_PARCELS_OFFICIAL_SOURCES_PREPARED_MEASURED_AND_PUBLISHED"

    execution = {
        "schema_version": 3,
        "slot_id": "height_difference_3",
        "single_shared_runner_only": True,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "starter_manifest": str(args.starter_manifest),
        "status": status,
        "stages": stages,
        "exact_hmlr_official_id_gate": exact_hmlr_gate,
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
