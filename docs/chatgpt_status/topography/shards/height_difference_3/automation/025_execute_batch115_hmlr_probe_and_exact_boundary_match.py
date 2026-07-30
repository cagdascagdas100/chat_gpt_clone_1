#!/usr/bin/env python3
"""Prepare exact HMLR INSPIRE boundaries for the four hardened candidates.

The wrapper reuses the current authority downloader and strict matcher already present
in the canonical task read-set. Candidate identity, dependency byte identity and all
derived manifests are hash-bound. Execution evidence is atomically materialized and
no elevation or height-difference value is created.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

EXPECTED_ROWS = [61536, 61537, 61538, 61539]
EXPECTED_SOURCE_BLOB = "f89aea9d3e89a3037194129498b281e380a92c0f"
EXPECTED_MATCHER_BLOB = "5240a20ea0d65fa99af845d15e8219daf1287cf2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_blob_sha1(path: Path) -> str:
    data_size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {data_size}\0".encode("ascii"))
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


def _validate_candidates(path: Path) -> tuple[list[dict[str, Any]], str]:
    payload = _load(path)
    values = payload.get("candidates")
    if not isinstance(values, list):
        raise ValueError("candidate manifest lacks candidates list")
    rows: list[dict[str, Any]] = []
    seen_parcels: set[str] = set()
    seen_ids: set[str] = set()
    for index, raw in enumerate(values, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"candidate {index} is not an object")
        item = dict(raw)
        row_no = int(item.get("row_no"))
        parcel_id = str(item.get("parcel_id") or "").strip()
        inspire_id = str(
            item.get("hmlr_inspire_id")
            or item.get("national_cadastral_reference")
            or item.get("parcel_registry_id")
            or ""
        ).strip()
        easting = float(item.get("bng_easting"))
        northing = float(item.get("bng_northing"))
        if not parcel_id or not inspire_id:
            raise ValueError(f"candidate {row_no} lacks parcel or INSPIRE identity")
        if parcel_id in seen_parcels or inspire_id.casefold() in seen_ids:
            raise ValueError(f"duplicate candidate identity at row {row_no}")
        if not (math.isfinite(easting) and math.isfinite(northing)):
            raise ValueError(f"candidate {row_no} has non-finite BNG coordinates")
        if not (0 <= easting <= 700000 and 0 <= northing <= 1300000):
            raise ValueError(f"candidate {row_no} lies outside accepted BNG extent")
        if item.get("existing_verified_height_value") not in (None, "", "null", "None"):
            raise ValueError(f"candidate {row_no} unexpectedly contains a height value")
        seen_parcels.add(parcel_id)
        seen_ids.add(inspire_id.casefold())
        rows.append(item)
    actual_rows = [int(item["row_no"]) for item in rows]
    if actual_rows != EXPECTED_ROWS:
        raise ValueError(f"candidate row set/order mismatch: {actual_rows}")
    return rows, _sha256(path)


def _validate_boundary(path: Path, candidate_sha: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = _load(path)
    if int(payload.get("schema_version") or 0) < 3:
        raise ValueError("HMLR matcher output schema is too old")
    if payload.get("target_crs") != "EPSG:27700":
        raise ValueError("HMLR matcher output CRS mismatch")
    if payload.get("exact_identifier_requires_point_consistency") is not True:
        raise ValueError("HMLR point-consistency gate missing")
    if payload.get("equivalent_boundary_duplicate_geometry_deduplication") is not True:
        raise ValueError("HMLR equivalent-boundary deduplication gate missing")
    if payload.get("nearest_polygon_fill_forbidden") is not True:
        raise ValueError("nearest HMLR fill is not forbidden")
    if int(payload.get("measurement_values_written") or 0) != 0:
        raise ValueError("HMLR matcher wrote a measurement")
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("HMLR matcher results are invalid")
    rows = [int(item.get("row_no")) for item in results]
    if rows != EXPECTED_ROWS:
        raise ValueError(f"HMLR boundary row set/order mismatch: {rows}")
    checks: list[dict[str, Any]] = []
    for item in results:
        row_no = int(item["row_no"])
        method = str(item.get("match_method") or "")
        match = item.get("match") or {}
        official_ids = [str(v).strip() for v in (item.get("candidate_official_ids") or []) if str(v).strip()]
        passed = (
            item.get("status") == "MATCHED"
            and method.startswith("EXACT_OFFICIAL_ID")
            and int(item.get("exact_match_count") or 0) == 1
            and bool(official_ids)
            and match.get("point_inside") is True
            and not bool(item.get("nearest_polygon_fill_used"))
            and item.get("measured_value_promoted") is False
        )
        checks.append(
            {
                "row_no": row_no,
                "parcel_id": item.get("parcel_id"),
                "match_method": method,
                "exact_match_count": item.get("exact_match_count"),
                "point_inside": match.get("point_inside"),
                "candidate_official_ids": official_ids,
                "passed": passed,
            }
        )
    if not all(item["passed"] for item in checks):
        raise ValueError("one or more candidates lack one exact point-consistent HMLR boundary")
    payload["candidate_manifest_sha256_checked_by_wrapper"] = candidate_sha
    return payload, checks


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--source-script", type=Path)
    parser.add_argument("--matcher-script", type=Path)
    args = parser.parse_args(argv)
    if args.timeout < 1 or args.timeout > 900:
        raise ValueError("timeout must be between 1 and 900 seconds")

    script_dir = Path(__file__).resolve().parent
    source_script = (args.source_script or script_dir / "012_download_hmlr_inspire_sources.py").resolve()
    matcher_script = (args.matcher_script or script_dir / "008_match_hmlr_inspire_gml.py").resolve()
    candidate_manifest = args.candidate_manifest.resolve()
    for label, path in (
        ("candidate manifest", candidate_manifest),
        ("HMLR source script", source_script),
        ("HMLR matcher script", matcher_script),
    ):
        if not path.is_file() or path.stat().st_size <= 0:
            raise FileNotFoundError(f"{label} missing or empty: {path}")

    candidates, candidate_sha_before = _validate_candidates(candidate_manifest)
    source_blob_before = _git_blob_sha1(source_script)
    matcher_blob_before = _git_blob_sha1(matcher_script)
    if args.source_script is None and source_blob_before != EXPECTED_SOURCE_BLOB:
        raise RuntimeError(f"tracked HMLR source script blob mismatch: {source_blob_before}")
    if args.matcher_script is None and matcher_blob_before != EXPECTED_MATCHER_BLOB:
        raise RuntimeError(f"tracked HMLR matcher script blob mismatch: {matcher_blob_before}")

    output_dir = args.output_dir.resolve()
    source_out = output_dir / "hmlr_source"
    boundary_out = output_dir / "hmlr_exact_boundaries.json"
    execution_out = output_dir / "batch115_hmlr_probe_execution.json"
    stages: list[dict[str, Any]] = []

    source_cmd = [
        sys.executable,
        str(source_script),
        "--starter-manifest",
        str(candidate_manifest),
        "--output-dir",
        str(source_out),
        "--timeout",
        str(args.timeout),
    ]
    source_result = _run("CURRENT_OFFICIAL_HMLR_AUTHORITY_SOURCE", source_cmd, script_dir)
    stages.append(source_result)
    if source_result["exit_code"] != 0:
        raise RuntimeError(f"HMLR source preparation failed: {source_result['stderr'][-2400:]}")

    source_manifest_path = source_out / "hmlr_source_manifest.json"
    if not source_manifest_path.is_file():
        raise FileNotFoundError(source_manifest_path)
    source_manifest = _load(source_manifest_path)
    if (
        int(source_manifest.get("schema_version") or 0) < 4
        or source_manifest.get("status") != "READY"
        or int(source_manifest.get("candidate_count") or 0) != len(candidates)
        or int(source_manifest.get("prepared_authority_count") or 0) != int(source_manifest.get("authority_count") or -1)
        or source_manifest.get("nearest_or_fuzzy_authority_match_used") is not False
        or source_manifest.get("archive_tree_transactional_publish") is not True
        or source_manifest.get("manifest_atomic_materialization") is not True
    ):
        raise ValueError("HMLR source manifest is not strict-ready")
    if not (source_manifest.get("vector_paths") or []):
        raise ValueError("HMLR source manifest contains no vectors")

    matcher_cmd = [
        sys.executable,
        str(matcher_script),
        "--starter-manifest",
        str(candidate_manifest),
        "--vector-root",
        str(source_out / "hmlr"),
        "--output",
        str(boundary_out),
    ]
    matcher_result = _run("STRICT_EXACT_HMLR_BOUNDARY_MATCH", matcher_cmd, script_dir)
    stages.append(matcher_result)
    if matcher_result["exit_code"] != 0 or not boundary_out.is_file():
        raise RuntimeError(f"HMLR exact boundary matching failed: {matcher_result['stderr'][-2400:]}")

    boundary_payload, strict_checks = _validate_boundary(boundary_out, candidate_sha_before)
    candidate_sha_after = _sha256(candidate_manifest)
    source_blob_after = _git_blob_sha1(source_script)
    matcher_blob_after = _git_blob_sha1(matcher_script)
    if candidate_sha_after != candidate_sha_before:
        raise RuntimeError("candidate manifest changed during HMLR preparation")
    if source_blob_after != source_blob_before or matcher_blob_after != matcher_blob_before:
        raise RuntimeError("HMLR dependency script changed during execution")

    source_manifest_sha = _sha256(source_manifest_path)
    boundary_sha = _sha256(boundary_out)
    execution = {
        "schema_version": 3,
        "slot_id": "height_difference_3",
        "batch_id": 115,
        "status": "FOUR_HARDENED_CANDIDATES_EXACT_HMLR_BOUNDARIES_READY",
        "candidate_manifest": str(candidate_manifest),
        "candidate_manifest_sha256": candidate_sha_before,
        "expected_rows": EXPECTED_ROWS,
        "candidate_count": len(candidates),
        "source_script": str(source_script),
        "source_script_git_blob_sha1": source_blob_before,
        "matcher_script": str(matcher_script),
        "matcher_script_git_blob_sha1": matcher_blob_before,
        "source_manifest": str(source_manifest_path),
        "source_manifest_sha256": source_manifest_sha,
        "boundary_manifest": str(boundary_out),
        "boundary_manifest_sha256": boundary_sha,
        "stages": stages,
        "strict_boundary_checks": strict_checks,
        "strict_boundary_pass": True,
        "exact_match_count_required_per_row": 1,
        "exact_identifier_point_consistency_required": True,
        "candidate_input_hash_stable": True,
        "dependency_script_hashes_stable": True,
        "execution_manifest_atomic_materialization": True,
        "next_step_only_if_pass": "EA_DTM1M_AND_TERRAIN50_SAME_POINT_MEASUREMENT_CHAIN",
        "candidate_promotion_allowed": False,
        "numeric_publish_allowed": False,
        "measurement_values_written": 0,
        "nearest_fill_forbidden": True,
        "single_shared_runner_only": True,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "final_ready": False,
        "fake_data": False,
    }
    _atomic_json(execution_out, execution)
    print(
        json.dumps(
            {
                "ok": True,
                "status": execution["status"],
                "candidate_sha256": candidate_sha_before,
                "boundary_sha256": boundary_sha,
                "execution": str(execution_out),
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
