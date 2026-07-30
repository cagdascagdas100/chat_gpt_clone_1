#!/usr/bin/env python3
"""Run the four hardened candidates through the official HMLR/EA/OS chain.

All stage outputs are created under an isolated staging tree. The canonical output
directory is replaced only after source, same-point measurement and JSON/GeoJSON
publication gates all pass. Failed reruns preserve the previous valid output tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

EXPECTED_ROWS = [61536, 61537, 61538, 61539]
EXPECTED_TILES = {61536: "TQ26", 61537: "TQ27", 61538: "TQ27", 61539: "TQ27"}
ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM_HIGH"}
EXPECTED_METHOD = "EA_DTM_1M_POLYGON_P95_MINUS_P05"
EXPECTED_CONTRACT = "EA_DTM_POLYGON_P95_P05_OS_T50_SAME_POINT_V2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}_", suffix=".json.tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with temp.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def _run(stage: str, command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "stage": stage,
        "command": command,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-16000:],
        "stderr": proc.stderr[-16000:],
    }


def _finite(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} is non-finite: {value!r}")
    return number


def _validate_candidate_manifest(path: Path) -> tuple[list[dict[str, Any]], str]:
    payload = _load(path)
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidate manifest lacks candidates list")
    actual_rows = [int(item.get("row_no")) for item in candidates]
    if actual_rows != EXPECTED_ROWS:
        raise ValueError(f"candidate row set/order mismatch: {actual_rows}")
    seen_parcels: set[str] = set()
    seen_ids: set[str] = set()
    for item in candidates:
        row_no = int(item["row_no"])
        parcel = str(item.get("parcel_id") or "").strip()
        inspire = str(
            item.get("hmlr_inspire_id")
            or item.get("national_cadastral_reference")
            or item.get("parcel_registry_id")
            or ""
        ).strip()
        if not parcel or not inspire:
            raise ValueError(f"candidate {row_no} lacks parcel or INSPIRE identity")
        if parcel in seen_parcels or inspire.casefold() in seen_ids:
            raise ValueError(f"duplicate candidate identity at row {row_no}")
        _finite(item.get("bng_easting"), f"row {row_no} easting")
        _finite(item.get("bng_northing"), f"row {row_no} northing")
        if item.get("existing_verified_height_value") not in (None, "", "null", "None"):
            raise ValueError(f"candidate {row_no} unexpectedly contains a height value")
        seen_parcels.add(parcel)
        seen_ids.add(inspire.casefold())
    return candidates, _sha256(path)


def _validate_hmlr_execution(path: Path, candidate_sha: str) -> dict[str, Any]:
    payload = _load(path)
    if int(payload.get("schema_version") or 0) < 3:
        raise ValueError("HMLR execution schema is too old")
    if payload.get("status") != "FOUR_HARDENED_CANDIDATES_EXACT_HMLR_BOUNDARIES_READY":
        raise ValueError("HMLR exact boundary execution did not pass")
    if payload.get("candidate_manifest_sha256") != candidate_sha:
        raise ValueError("HMLR execution candidate SHA mismatch")
    if [int(v) for v in (payload.get("expected_rows") or [])] != EXPECTED_ROWS:
        raise ValueError("HMLR execution row set mismatch")
    if payload.get("strict_boundary_pass") is not True:
        raise ValueError("HMLR strict boundary gate is false")
    if payload.get("candidate_input_hash_stable") is not True:
        raise ValueError("HMLR candidate input was not hash-stable")
    if payload.get("dependency_script_hashes_stable") is not True:
        raise ValueError("HMLR dependencies were not hash-stable")
    if int(payload.get("measurement_values_written") or 0) != 0:
        raise ValueError("HMLR stage wrote a numeric measurement")
    return payload


def _validate_ea_source(path: Path) -> dict[str, Any]:
    payload = _load(path)
    if int(payload.get("schema_version") or 0) < 2 or payload.get("status") != "READY":
        raise ValueError("EA source manifest is not strict-ready")
    if payload.get("official_host") != "environment.data.gov.uk" or payload.get("official_host_only") is not True:
        raise ValueError("EA official host gate missing")
    if payload.get("axis_labels_inferred") is not False:
        raise ValueError("EA WCS axis labels were inferred")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != 4:
        raise ValueError("EA source manifest must contain exactly four records")
    rows = [int(item.get("row_no")) for item in records]
    if rows != EXPECTED_ROWS:
        raise ValueError(f"EA source rows mismatch: {rows}")
    for item in records:
        row_no = int(item["row_no"])
        if not str(item.get("sha256") or "").strip() or len(str(item.get("sha256"))) != 64:
            raise ValueError(f"EA row {row_no} lacks SHA-256")
        if Path(str(item.get("path") or "")).name != f"row_{row_no}_ea_dtm_1m.tif":
            raise ValueError(f"EA row {row_no} is not bound to its own raster")
    return payload


def _validate_terrain_download(path: Path, archive: Path) -> dict[str, Any]:
    payload = _load(path)
    if payload.get("official_catalog_verified") is not True:
        raise ValueError("Terrain50 official catalog verification missing")
    if payload.get("product_id") != "Terrain50" or payload.get("area") != "GB":
        raise ValueError("Terrain50 product identity mismatch")
    if not archive.is_file() or archive.stat().st_size <= 0:
        raise FileNotFoundError(archive)
    expected_hash = str(payload.get("archive_sha256") or "").lower()
    if len(expected_hash) != 64 or _sha256(archive) != expected_hash:
        raise ValueError("Terrain50 archive SHA-256 mismatch")
    if int(payload.get("archive_size_bytes") or -1) != archive.stat().st_size:
        raise ValueError("Terrain50 archive size mismatch")
    if payload.get("cache_reused") is True and payload.get("cache_provenance_verified") is not True:
        raise ValueError("Terrain50 cache reuse lacks provenance verification")
    return payload


def _validate_terrain_source(path: Path) -> dict[str, Any]:
    payload = _load(path)
    if payload.get("status") != "READY":
        raise ValueError("Terrain50 extracted source manifest is not ready")
    if payload.get("nearest_or_neighbour_tile_substitution_used") is not False:
        raise ValueError("Terrain50 neighbour substitution was used")
    candidate_tiles = payload.get("candidate_tiles")
    records = payload.get("records")
    if not isinstance(candidate_tiles, list) or not isinstance(records, list):
        raise ValueError("Terrain50 source arrays are invalid")
    candidate_map: dict[int, str] = {}
    for item in candidate_tiles:
        row_no = int(item["row_no"])
        if row_no in candidate_map:
            raise ValueError(f"duplicate Terrain50 candidate row {row_no}")
        candidate_map[row_no] = str(item.get("tile_key") or "").upper()
    if candidate_map != EXPECTED_TILES:
        raise ValueError(f"Terrain50 candidate tile mapping mismatch: {candidate_map}")
    record_keys = sorted(str(item.get("tile_key") or "").upper() for item in records)
    if record_keys != ["TQ26", "TQ27"]:
        raise ValueError(f"Terrain50 extracted tile keys mismatch: {record_keys}")
    for item in records:
        header = item.get("header") or {}
        key = str(item.get("tile_key") or "").upper()
        if (
            int(float(header.get("ncols", -1))) != 200
            or int(float(header.get("nrows", -1))) != 200
            or not math.isclose(float(header.get("cellsize", -1)), 50.0, rel_tol=0.0, abs_tol=1e-9)
        ):
            raise ValueError(f"Terrain50 tile {key} header mismatch")
        if len(str(item.get("sha256") or "")) != 64:
            raise ValueError(f"Terrain50 tile {key} lacks SHA-256")
    return payload


def _source_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        raise ValueError(f"{label} must contain exactly one source raster")
    if len(str(value[0].get("sha256") or "")) != 64:
        raise ValueError(f"{label} source raster lacks SHA-256")
    return value


def _validate_measurements(path: Path) -> dict[str, Any]:
    payload = _load(path)
    if int(payload.get("schema_version") or 0) < 2:
        raise ValueError("measurement manifest schema is too old")
    if payload.get("measurement_contract_version") != EXPECTED_CONTRACT:
        raise ValueError("measurement contract mismatch")
    if payload.get("target_crs") != "EPSG:27700":
        raise ValueError("measurement CRS mismatch")
    if payload.get("atomic_output_materialization") is not True:
        raise ValueError("measurement output is not atomically materialized")
    if payload.get("unique_ea_coverage_required") is not True or payload.get("unique_terrain50_tile_required") is not True:
        raise ValueError("unique source coverage/tile gates missing")
    if payload.get("source_errors_forbid_promotion") is not True:
        raise ValueError("source errors do not forbid promotion")
    if payload.get("strict_crs_resolution_gate") is not True:
        raise ValueError("strict CRS/resolution gate missing")
    results = payload.get("results")
    measured = payload.get("measured_rows")
    if not isinstance(results, list) or not isinstance(measured, list):
        raise ValueError("measurement arrays are invalid")
    if int(payload.get("candidate_count") or 0) != 4:
        raise ValueError("measurement candidate count is not four")
    if int(payload.get("promoted_measurement_count") or 0) != 4 or int(payload.get("blocked_measurement_count", -1)) != 0:
        raise ValueError("all four measurements were not promoted")
    if [int(item["row_no"]) for item in results] != EXPECTED_ROWS:
        raise ValueError("measurement result rows mismatch")
    if [int(item["row_no"]) for item in measured] != EXPECTED_ROWS:
        raise ValueError("promoted measurement rows mismatch")

    result_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    for item in results:
        row_no = int(item["row_no"])
        parcel_id = str(item.get("parcel_id") or "").strip()
        key = (row_no, parcel_id)
        if not parcel_id or key in result_by_key:
            raise ValueError(f"duplicate or empty measurement key: {key}")
        if item.get("status") != "MEASURED_AND_CROSSCHECKED" or item.get("measured_value_promoted") is not True:
            raise ValueError(f"row {row_no} is not promoted")
        if item.get("gate_reasons") not in ([], None) or item.get("measurement_errors") not in ([], None):
            raise ValueError(f"row {row_no} contains gate or measurement errors")
        if not str(item.get("hmlr_match_method") or "").startswith("EXACT_OFFICIAL_ID"):
            raise ValueError(f"row {row_no} lacks exact HMLR match")
        if item.get("nearest_point_fill_used") is not False:
            raise ValueError(f"row {row_no} used nearest fill")
        ea = item.get("ea_dtm") or {}
        terrain = item.get("os_terrain50") or {}
        _source_list(ea.get("source_rasters"), f"row {row_no} EA")
        _source_list(terrain.get("source_rasters"), f"row {row_no} Terrain50")
        if ea.get("errors") not in ([], None) or terrain.get("errors") not in ([], None):
            raise ValueError(f"row {row_no} contains source errors")
        ea_point = _finite(ea.get("point_elevation_m"), f"row {row_no} EA point")
        terrain_point = _finite(terrain.get("point_elevation_m"), f"row {row_no} Terrain50 point")
        cross = _finite(item.get("cross_source_same_point_absolute_difference_m"), f"row {row_no} same-point difference")
        threshold = _finite(item.get("crosscheck_threshold_m"), f"row {row_no} threshold")
        if not math.isclose(abs(ea_point - terrain_point), cross, rel_tol=0.0, abs_tol=0.002):
            raise ValueError(f"row {row_no} cross-source arithmetic mismatch")
        if not 0 <= cross <= threshold <= 8.0:
            raise ValueError(f"row {row_no} exceeds same-point crosscheck threshold")
        result_by_key[key] = item

    for item in measured:
        row_no = int(item["row_no"])
        parcel_id = str(item.get("parcel_id") or "").strip()
        key = (row_no, parcel_id)
        if key not in result_by_key:
            raise ValueError(f"row {row_no} lacks detailed result")
        if item.get("height_difference_method") != EXPECTED_METHOD:
            raise ValueError(f"row {row_no} method mismatch")
        if item.get("confidence") not in ALLOWED_CONFIDENCE:
            raise ValueError(f"row {row_no} confidence is not approved")
        if not str(item.get("boundary_match_method") or "").startswith("EXACT_OFFICIAL_ID"):
            raise ValueError(f"row {row_no} lacks exact boundary method")
        if item.get("data_status") != "official_sources_crosschecked_same_point":
            raise ValueError(f"row {row_no} data status is not same-point crosschecked")
        if int(item.get("ea_valid_cell_count") or 0) < 4:
            raise ValueError(f"row {row_no} has insufficient EA cells")
        _finite(item.get("height_difference_m"), f"row {row_no} height difference")
        ea_point = _finite(item.get("ea_sample_point_elevation_m"), f"row {row_no} promoted EA point")
        terrain_point = _finite(item.get("os_terrain50_sample_point_elevation_m"), f"row {row_no} promoted Terrain50 point")
        cross = _finite(item.get("cross_source_same_point_absolute_difference_m"), f"row {row_no} promoted crosscheck")
        if not math.isclose(abs(ea_point - terrain_point), cross, rel_tol=0.0, abs_tol=0.002):
            raise ValueError(f"row {row_no} promoted crosscheck arithmetic mismatch")
    return payload


def _validate_publication(json_path: Path, geojson_path: Path, measurement_path: Path) -> dict[str, Any]:
    summary = _load(json_path)
    geojson = _load(geojson_path)
    measurement_sha = _sha256(measurement_path)
    if int(summary.get("schema_version") or 0) < 2:
        raise ValueError("verified JSON schema is too old")
    if summary.get("status") != "VERIFIED_EXAMPLES_PUBLISHED":
        raise ValueError("verified JSON status is not published")
    if summary.get("atomic_json_geojson_bundle") is not True:
        raise ValueError("verified JSON/GeoJSON bundle is not atomic")
    if summary.get("measurement_manifest_sha256") != measurement_sha:
        raise ValueError("verified JSON measurement SHA mismatch")
    rows = summary.get("rows")
    if not isinstance(rows, list) or [int(item["row_no"]) for item in rows] != EXPECTED_ROWS:
        raise ValueError("verified JSON row set mismatch")
    if int(summary.get("published_example_count") or 0) != 4:
        raise ValueError("verified JSON count is not four")
    by_key = {(int(item["row_no"]), str(item.get("parcel_id") or "")): item for item in rows}
    if len(by_key) != 4:
        raise ValueError("verified JSON contains duplicate identities")

    if geojson.get("type") != "FeatureCollection" or geojson.get("atomic_json_geojson_bundle") is not True:
        raise ValueError("verified GeoJSON contract mismatch")
    if geojson.get("measurement_manifest_sha256") != measurement_sha:
        raise ValueError("verified GeoJSON measurement SHA mismatch")
    features = geojson.get("features")
    if not isinstance(features, list) or len(features) != 4 or int(geojson.get("feature_count") or 0) != 4:
        raise ValueError("verified GeoJSON feature count mismatch")
    feature_rows: list[int] = []
    feature_ids: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError("GeoJSON feature is not an object")
        properties = feature.get("properties") or {}
        row_no = int(properties["row_no"])
        parcel_id = str(properties.get("parcel_id") or "")
        key = (row_no, parcel_id)
        feature_rows.append(row_no)
        if key not in by_key or properties != by_key[key]:
            raise ValueError(f"GeoJSON properties mismatch at row {row_no}")
        feature_id = str(feature.get("id") or "")
        if feature_id != parcel_id or feature_id in feature_ids:
            raise ValueError(f"GeoJSON feature identity mismatch at row {row_no}")
        feature_ids.add(feature_id)
        geometry = feature.get("geometry") or {}
        if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"GeoJSON geometry mismatch at row {row_no}")
    if feature_rows != EXPECTED_ROWS:
        raise ValueError("verified GeoJSON row set mismatch")
    return {
        "measurement_sha256": measurement_sha,
        "verified_json_sha256": _sha256(json_path),
        "verified_geojson_sha256": _sha256(geojson_path),
    }


def _transactional_directory_swap(stage: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.parent / f".{target.name}.backup"
    if backup.exists():
        shutil.rmtree(backup)
    previous_moved = False
    published = False
    try:
        if target.exists():
            target.replace(backup)
            previous_moved = True
        try:
            stage.replace(target)
            published = True
        except Exception:
            if previous_moved and backup.exists():
                backup.replace(target)
                previous_moved = False
            raise
        if backup.exists():
            shutil.rmtree(backup)
            previous_moved = False
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if backup.exists():
            if previous_moved and not target.exists():
                backup.replace(target)
            else:
                shutil.rmtree(backup, ignore_errors=True)
        if not published and target.exists() and target.is_dir():
            pass


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--hmlr-script", type=Path)
    parser.add_argument("--ea-script", type=Path)
    parser.add_argument("--os-download-script", type=Path)
    parser.add_argument("--os-tiles-script", type=Path)
    parser.add_argument("--sample-script", type=Path)
    parser.add_argument("--publish-script", type=Path)
    args = parser.parse_args(argv)
    if args.timeout < 1 or args.timeout > 900:
        raise ValueError("timeout must be between 1 and 900 seconds")

    script_dir = Path(__file__).resolve().parent
    scripts = {
        "hmlr": (args.hmlr_script or script_dir / "025_execute_batch115_hmlr_probe_and_exact_boundary_match.py").resolve(),
        "ea": (args.ea_script or script_dir / "013_fetch_ea_dtm_wcs_for_matches.py").resolve(),
        "os_download": (args.os_download_script or script_dir / "021_download_os_terrain50_via_api.py").resolve(),
        "os_tiles": (args.os_tiles_script or script_dir / "014_prepare_os_terrain50_tiles.py").resolve(),
        "sample": (args.sample_script or script_dir / "009_sample_ea_dtm_and_os_terrain50.py").resolve(),
        "publish": (args.publish_script or script_dir / "010_publish_verified_height_difference_examples.py").resolve(),
    }
    for name, path in scripts.items():
        if not path.is_file() or path.stat().st_size <= 0:
            raise FileNotFoundError(f"{name} script missing or empty: {path}")
    candidate_manifest = args.candidate_manifest.resolve()
    if not candidate_manifest.is_file() or candidate_manifest.stat().st_size <= 0:
        raise FileNotFoundError(candidate_manifest)
    candidates, candidate_sha_before = _validate_candidate_manifest(candidate_manifest)
    script_hashes_before = {name: _sha256(path) for name, path in scripts.items()}

    target = args.output_dir.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    stage_root = Path(tempfile.mkdtemp(prefix=f".{target.name}_", suffix=".stage", dir=target.parent))
    stages: list[dict[str, Any]] = []
    gates: dict[str, Any] = {}
    try:
        hmlr_out = stage_root / "01_hmlr"
        sources_out = stage_root / "02_sources"
        terrain_download_out = stage_root / "03_terrain50_download"
        measurement_path = stage_root / "04_official_measurements.json"
        verified_json = stage_root / "05_verified_examples.json"
        verified_geojson = stage_root / "05_verified_examples.geojson"

        hmlr_cmd = [
            sys.executable,
            str(scripts["hmlr"]),
            "--candidate-manifest",
            str(candidate_manifest),
            "--output-dir",
            str(hmlr_out),
            "--timeout",
            str(args.timeout),
        ]
        result = _run("HMLR_EXACT_ID_POINT_CONSISTENT_BOUNDARIES", hmlr_cmd, script_dir)
        stages.append(result)
        if result["exit_code"] != 0:
            raise RuntimeError(f"HMLR stage failed: {result['stderr'][-2400:]}")
        hmlr_execution_path = hmlr_out / "batch115_hmlr_probe_execution.json"
        hmlr_execution = _validate_hmlr_execution(hmlr_execution_path, candidate_sha_before)
        matched_manifest = hmlr_out / "hmlr_exact_boundaries.json"
        if hmlr_execution.get("boundary_manifest_sha256") != _sha256(matched_manifest):
            raise ValueError("HMLR boundary manifest SHA mismatch")
        gates["hmlr"] = {"passed": True, "execution_sha256": _sha256(hmlr_execution_path), "boundary_sha256": _sha256(matched_manifest)}

        ea_cmd = [
            sys.executable,
            str(scripts["ea"]),
            "--matched-manifest",
            str(matched_manifest),
            "--output-dir",
            str(sources_out),
            "--timeout",
            str(args.timeout),
        ]
        result = _run("EA_DTM1M_WCS_EXACT_POLYGONS", ea_cmd, script_dir)
        stages.append(result)
        if result["exit_code"] != 0:
            raise RuntimeError(f"EA source stage failed: {result['stderr'][-2400:]}")
        ea_manifest_path = sources_out / "ea_dtm_source_manifest.json"
        _validate_ea_source(ea_manifest_path)
        gates["ea_source"] = {"passed": True, "manifest_sha256": _sha256(ea_manifest_path)}

        os_download_cmd = [
            sys.executable,
            str(scripts["os_download"]),
            "--output-dir",
            str(terrain_download_out),
            "--timeout",
            str(args.timeout),
            "--max-cache-age-hours",
            "24",
        ]
        result = _run("OS_TERRAIN50_OFFICIAL_API", os_download_cmd, script_dir)
        stages.append(result)
        if result["exit_code"] != 0:
            raise RuntimeError(f"Terrain50 download stage failed: {result['stderr'][-2400:]}")
        archive = terrain_download_out / "OS_Terrain50_July_2026_GB_ASCII_Grid.zip"
        terrain_provenance_path = terrain_download_out / "terrain50_official_api_provenance.json"
        _validate_terrain_download(terrain_provenance_path, archive)
        gates["terrain_download"] = {
            "passed": True,
            "archive_sha256": _sha256(archive),
            "provenance_sha256": _sha256(terrain_provenance_path),
        }

        os_tiles_cmd = [
            sys.executable,
            str(scripts["os_tiles"]),
            "--matched-manifest",
            str(matched_manifest),
            "--source",
            str(archive),
            "--output-dir",
            str(sources_out),
        ]
        result = _run("OS_TERRAIN50_EXACT_TQ26_TQ27", os_tiles_cmd, script_dir)
        stages.append(result)
        if result["exit_code"] != 0:
            raise RuntimeError(f"Terrain50 tile stage failed: {result['stderr'][-2400:]}")
        terrain_manifest_path = sources_out / "terrain50_source_manifest.json"
        _validate_terrain_source(terrain_manifest_path)
        gates["terrain_source"] = {"passed": True, "manifest_sha256": _sha256(terrain_manifest_path)}

        sample_cmd = [
            sys.executable,
            str(scripts["sample"]),
            "--matched-manifest",
            str(matched_manifest),
            "--ea-root",
            str(sources_out / "ea_dtm"),
            "--terrain50-root",
            str(sources_out / "terrain50"),
            "--minimum-ea-cells",
            "4",
            "--max-crosscheck-difference-m",
            "8.0",
            "--output",
            str(measurement_path),
        ]
        result = _run("FOUR_PARCEL_EA_P95_P05_TERRAIN50_SAME_POINT", sample_cmd, script_dir)
        stages.append(result)
        if result["exit_code"] != 0:
            raise RuntimeError(f"measurement stage failed: {result['stderr'][-2400:]}")
        _validate_measurements(measurement_path)
        gates["measurement"] = {"passed": True, "manifest_sha256": _sha256(measurement_path), "contract": EXPECTED_CONTRACT}

        publish_cmd = [
            sys.executable,
            str(scripts["publish"]),
            "--measurement-manifest",
            str(measurement_path),
            "--output-json",
            str(verified_json),
            "--output-geojson",
            str(verified_geojson),
        ]
        result = _run("VERIFIED_FOUR_PARCEL_TRANSACTIONAL_PUBLICATION", publish_cmd, script_dir)
        stages.append(result)
        if result["exit_code"] != 0:
            raise RuntimeError(f"publication stage failed: {result['stderr'][-2400:]}")
        publication_hashes = _validate_publication(verified_json, verified_geojson, measurement_path)
        gates["publication"] = {"passed": True, **publication_hashes}

        candidate_sha_after = _sha256(candidate_manifest)
        script_hashes_after = {name: _sha256(path) for name, path in scripts.items()}
        if candidate_sha_after != candidate_sha_before:
            raise RuntimeError("candidate manifest changed during four-candidate chain")
        if script_hashes_after != script_hashes_before:
            raise RuntimeError("one or more dependency scripts changed during four-candidate chain")

        execution_path = stage_root / "batch116_four_candidate_execution.json"
        execution = {
            "schema_version": 4,
            "slot_id": "height_difference_3",
            "batch_id": 116,
            "status": "FOUR_HARDENED_CANDIDATES_OFFICIAL_SAME_POINT_MEASURED_AND_PUBLISHED",
            "candidate_manifest": str(candidate_manifest),
            "candidate_manifest_sha256": candidate_sha_before,
            "expected_rows": EXPECTED_ROWS,
            "expected_terrain50_tiles": EXPECTED_TILES,
            "dependency_script_sha256": script_hashes_before,
            "candidate_input_hash_stable": True,
            "dependency_script_hashes_stable": True,
            "stages": stages,
            "gates": gates,
            "published_count": 4,
            "measurement_contract_version": EXPECTED_CONTRACT,
            "same_point_crosscheck_required": True,
            "source_errors_forbid_promotion": True,
            "all_outputs_staged_before_publish": True,
            "transactional_output_tree": True,
            "previous_valid_output_tree_preserved_on_failure": True,
            "outputs": {
                "hmlr_execution": "01_hmlr/batch115_hmlr_probe_execution.json",
                "hmlr_exact_boundaries": "01_hmlr/hmlr_exact_boundaries.json",
                "ea_source_manifest": "02_sources/ea_dtm_source_manifest.json",
                "terrain50_download_provenance": "03_terrain50_download/terrain50_official_api_provenance.json",
                "terrain50_source_manifest": "02_sources/terrain50_source_manifest.json",
                "measurement_manifest": "04_official_measurements.json",
                "verified_json": "05_verified_examples.json",
                "verified_geojson": "05_verified_examples.geojson",
            },
            "numeric_publish_allowed": True,
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
        _atomic_json(execution_path, execution)
        _transactional_directory_swap(stage_root, target)
        stage_root = target
        print(
            json.dumps(
                {
                    "ok": True,
                    "status": execution["status"],
                    "candidate_sha256": candidate_sha_before,
                    "measurement_sha256": gates["measurement"]["manifest_sha256"],
                    "verified_json_sha256": publication_hashes["verified_json_sha256"],
                    "verified_geojson_sha256": publication_hashes["verified_geojson_sha256"],
                    "execution": str(target / "batch116_four_candidate_execution.json"),
                }
            )
        )
        return 0
    finally:
        if stage_root.exists() and stage_root != target:
            shutil.rmtree(stage_root, ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
