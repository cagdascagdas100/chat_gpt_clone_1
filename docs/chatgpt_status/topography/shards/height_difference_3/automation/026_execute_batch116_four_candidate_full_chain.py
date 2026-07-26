#!/usr/bin/env python3
"""Execute the four hardened height_difference_3 candidates end-to-end.

This wrapper is for the existing canonical single runner only. It chains the
already fail-closed source/matching/sampling components in a fixed order:

1. current HMLR Lambeth download + exact INSPIRE-ID boundary proof;
2. Environment Agency DTM 1m WCS acquisition for exact polygons;
3. current OS Terrain 50 GB ASCII Grid acquisition from the official API;
4. deterministic TQ26/TQ27 tile extraction and header validation;
5. EA polygon P95-P05 measurement + Terrain50 centroid cross-check;
6. verified-example publication only when all four rows are promoted.

No nearest/fuzzy parcel fill, second runner, queue submission, DB write,
migration or production deployment is performed here.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

EXPECTED_ROWS = [61536, 61537, 61538, 61539]
EXPECTED_TILES = {61536: "TQ26", 61537: "TQ27", 61538: "TQ27", 61539: "TQ27"}
ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM_HIGH"}
EXPECTED_METHOD = "EA_DTM_1M_POLYGON_P95_MINUS_P05"


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(stage: str, command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "stage": stage,
        "command": command,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-16000:],
        "stderr": proc.stderr[-16000:],
    }


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _terrain_gate(manifest_path: Path) -> dict[str, Any]:
    payload = _load(manifest_path)
    candidate_tiles = payload.get("candidate_tiles") or []
    records = payload.get("records") or []
    seen = {}
    for item in candidate_tiles:
        row = int(item["row_no"])
        seen[row] = str(item["tile_key"]).upper()
    exact_rows = sorted(seen) == EXPECTED_ROWS
    exact_tiles = exact_rows and all(seen[row] == EXPECTED_TILES[row] for row in EXPECTED_ROWS)
    record_keys = sorted(str(item.get("tile_key", "")).upper() for item in records)
    exact_record_keys = record_keys == ["TQ26", "TQ27"]
    schema_ok = True
    record_checks = []
    for item in records:
        header = item.get("header") or {}
        key = str(item.get("tile_key", "")).upper()
        ok = (
            int(float(header.get("ncols", -1))) == 200
            and int(float(header.get("nrows", -1))) == 200
            and math.isclose(float(header.get("cellsize", -1)), 50.0, rel_tol=0.0, abs_tol=1e-9)
        )
        schema_ok = schema_ok and ok
        record_checks.append({"tile_key": key, "schema_200x200_50m": ok, "sha256": item.get("sha256")})
    no_substitution = payload.get("nearest_or_neighbour_tile_substitution_used") is False
    passed = exact_tiles and exact_record_keys and schema_ok and no_substitution
    return {
        "passed": passed,
        "candidate_tiles": seen,
        "expected_tiles": EXPECTED_TILES,
        "record_keys": record_keys,
        "record_checks": record_checks,
        "no_neighbour_substitution": no_substitution,
    }


def _measurement_gate(path: Path) -> dict[str, Any]:
    payload = _load(path)
    measured = payload.get("measured_rows") or []
    results = payload.get("results") or []
    rows = sorted(int(item["row_no"]) for item in measured if item.get("row_no") is not None)
    checks = []
    for item in measured:
        row = int(item["row_no"])
        checks.append({
            "row_no": row,
            "parcel_id": item.get("parcel_id"),
            "method": item.get("height_difference_method"),
            "confidence": item.get("confidence"),
            "ea_valid_cell_count": item.get("ea_valid_cell_count"),
            "cross_source_absolute_difference_m": item.get("cross_source_absolute_difference_m"),
            "passed": (
                item.get("height_difference_method") == EXPECTED_METHOD
                and item.get("confidence") in ALLOWED_CONFIDENCE
                and int(item.get("ea_valid_cell_count") or 0) >= 4
                and float(item.get("cross_source_absolute_difference_m") or 1e9) <= 8.0
            ),
        })
    result_rows = sorted(int(item["row_no"]) for item in results if item.get("row_no") is not None)
    result_promoted = all(
        item.get("status") == "MEASURED_AND_CROSSCHECKED" and item.get("measured_value_promoted") is True
        for item in results
    ) if len(results) == 4 else False
    passed = rows == EXPECTED_ROWS and result_rows == EXPECTED_ROWS and len(checks) == 4 and all(x["passed"] for x in checks) and result_promoted
    return {
        "passed": passed,
        "measured_rows": rows,
        "result_rows": result_rows,
        "checks": checks,
        "all_results_promoted": result_promoted,
    }


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-manifest", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args(argv)

    script_dir = Path(__file__).resolve().parent
    scripts = {
        "hmlr": script_dir / "025_execute_batch115_hmlr_probe_and_exact_boundary_match.py",
        "ea": script_dir / "013_fetch_ea_dtm_wcs_for_matches.py",
        "os_download": script_dir / "021_download_os_terrain50_via_api.py",
        "os_tiles": script_dir / "014_prepare_os_terrain50_tiles.py",
        "sample": script_dir / "009_sample_ea_dtm_and_os_terrain50.py",
        "publish": script_dir / "010_publish_verified_height_difference_examples.py",
    }
    for path in scripts.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    candidate_manifest = args.candidate_manifest.resolve()
    if not candidate_manifest.is_file():
        raise FileNotFoundError(candidate_manifest)

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    hmlr_out = out / "01_hmlr"
    sources_out = out / "02_sources"
    terrain_download_out = out / "03_terrain50_download"
    measurement_path = out / "04_official_measurements.json"
    verified_json = out / "05_verified_examples.json"
    verified_geojson = out / "05_verified_examples.geojson"
    execution_path = out / "batch116_four_candidate_execution.json"
    stages: list[dict[str, Any]] = []
    gates: dict[str, Any] = {}
    status = "BLOCKED_NOT_STARTED"

    hmlr_cmd = [
        sys.executable, str(scripts["hmlr"]),
        "--candidate-manifest", str(candidate_manifest),
        "--output-dir", str(hmlr_out),
        "--timeout", str(args.timeout),
    ]
    stages.append(_run("HMLR_FRESH_EXACT_ID_AND_BOUNDARY", hmlr_cmd, script_dir))
    status = "BLOCKED_HMLR_FRESH_EXACT_ID_AND_BOUNDARY"
    matched_manifest = hmlr_out / "hmlr_exact_boundaries.json"

    if stages[-1]["exit_code"] == 0 and matched_manifest.is_file():
        hmlr_execution = _load(hmlr_out / "batch115_hmlr_probe_execution.json")
        gates["hmlr_strict_boundary_pass"] = bool(hmlr_execution.get("strict_boundary_pass"))
        if not gates["hmlr_strict_boundary_pass"]:
            raise ValueError("HMLR wrapper exited 0 without strict boundary pass")

        ea_cmd = [
            sys.executable, str(scripts["ea"]),
            "--matched-manifest", str(matched_manifest),
            "--output-dir", str(sources_out),
            "--timeout", str(args.timeout),
        ]
        stages.append(_run("EA_DTM1M_WCS_EXACT_POLYGONS", ea_cmd, script_dir))
        status = "BLOCKED_EA_DTM1M_WCS_EXACT_POLYGONS"

    if len(stages) == 2 and stages[-1]["exit_code"] == 0:
        os_download_cmd = [
            sys.executable, str(scripts["os_download"]),
            "--output-dir", str(terrain_download_out),
            "--timeout", str(args.timeout),
            "--max-cache-age-hours", "24",
        ]
        stages.append(_run("OS_TERRAIN50_CURRENT_OFFICIAL_API", os_download_cmd, script_dir))
        status = "BLOCKED_OS_TERRAIN50_CURRENT_OFFICIAL_API"

    archive = terrain_download_out / "OS_Terrain50_July_2026_GB_ASCII_Grid.zip"
    if len(stages) == 3 and stages[-1]["exit_code"] == 0 and archive.is_file():
        os_tiles_cmd = [
            sys.executable, str(scripts["os_tiles"]),
            "--matched-manifest", str(matched_manifest),
            "--source", str(archive),
            "--output-dir", str(sources_out),
        ]
        stages.append(_run("OS_TERRAIN50_EXACT_TQ26_TQ27", os_tiles_cmd, script_dir))
        status = "BLOCKED_OS_TERRAIN50_EXACT_TQ26_TQ27"
        if stages[-1]["exit_code"] == 0:
            terrain_manifest = sources_out / "terrain50_source_manifest.json"
            gates["terrain50"] = _terrain_gate(terrain_manifest)
            if not gates["terrain50"]["passed"]:
                status = "BLOCKED_TERRAIN50_DETERMINISTIC_TILE_GATE"

    terrain_ok = bool(gates.get("terrain50", {}).get("passed"))
    if len(stages) == 4 and stages[-1]["exit_code"] == 0 and terrain_ok:
        sample_cmd = [
            sys.executable, str(scripts["sample"]),
            "--matched-manifest", str(matched_manifest),
            "--ea-root", str(sources_out / "ea_dtm"),
            "--terrain50-root", str(sources_out / "terrain50"),
            "--minimum-ea-cells", "4",
            "--max-crosscheck-difference-m", "8.0",
            "--output", str(measurement_path),
        ]
        stages.append(_run("FOUR_PARCEL_EA_P95_P05_AND_TERRAIN50_CROSSCHECK", sample_cmd, script_dir))
        status = "BLOCKED_FOUR_PARCEL_MEASUREMENT"
        if measurement_path.is_file():
            gates["measurement"] = _measurement_gate(measurement_path)
            if stages[-1]["exit_code"] == 0 and not gates["measurement"]["passed"]:
                status = "BLOCKED_MEASUREMENT_PROMOTION_GATE"

    measurement_ok = bool(gates.get("measurement", {}).get("passed"))
    if len(stages) == 5 and stages[-1]["exit_code"] == 0 and measurement_ok:
        publish_cmd = [
            sys.executable, str(scripts["publish"]),
            "--measurement-manifest", str(measurement_path),
            "--output-json", str(verified_json),
            "--output-geojson", str(verified_geojson),
        ]
        stages.append(_run("VERIFIED_FOUR_PARCEL_PUBLICATION", publish_cmd, script_dir))
        status = "BLOCKED_VERIFIED_FOUR_PARCEL_PUBLICATION"

    published_count = 0
    if len(stages) == 6 and stages[-1]["exit_code"] == 0 and verified_json.is_file():
        published = _load(verified_json)
        published_count = int(published.get("published_example_count") or 0)
        published_rows = sorted(int(item["row_no"]) for item in (published.get("rows") or []))
        if published_count == 4 and published_rows == EXPECTED_ROWS:
            status = "FOUR_HARDENED_CANDIDATES_OFFICIAL_MEASURED_AND_PUBLISHED"
        else:
            status = "BLOCKED_PUBLICATION_ROW_SET_GATE"

    success = status == "FOUR_HARDENED_CANDIDATES_OFFICIAL_MEASURED_AND_PUBLISHED"
    execution = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "batch_id": 116,
        "status": status,
        "candidate_manifest": str(candidate_manifest),
        "expected_rows": EXPECTED_ROWS,
        "expected_terrain50_tiles": EXPECTED_TILES,
        "stages": stages,
        "gates": gates,
        "published_count": published_count,
        "outputs": {
            "hmlr_execution": str(hmlr_out / "batch115_hmlr_probe_execution.json"),
            "hmlr_exact_boundaries": str(matched_manifest),
            "ea_source_manifest": str(sources_out / "ea_dtm_source_manifest.json"),
            "terrain50_download_provenance": str(terrain_download_out / "terrain50_official_api_provenance.json"),
            "terrain50_source_manifest": str(sources_out / "terrain50_source_manifest.json"),
            "measurement_manifest": str(measurement_path),
            "verified_json": str(verified_json),
            "verified_geojson": str(verified_geojson),
        },
        "numeric_publish_allowed": success,
        "nearest_or_fuzzy_fill_forbidden": True,
        "single_shared_runner_only": True,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_submission": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    _write(execution_path, execution)
    print(json.dumps({"ok": success, "status": status, "execution": str(execution_path)}))
    return 0 if success else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
