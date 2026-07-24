#!/usr/bin/env python3
"""Sequential single-runner entrypoint for future_growth_1 geometry wave 2.

Downloads official GLA Brownfield polygons and the current HM Land Registry
INSPIRE authority GML, then runs the fail-closed spatial relation pipeline for
canonical rows 1-3. It never emits Future Growth scores or writes to the DB.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SLOT_ID = "future_growth_1"
TASK_ID = "aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID = "future-growth-1-20260721-002"
REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
PIPELINE = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/002_fetch_official_geometry_and_build_sample_matrix.py"
HMLR_PREPARER = REPO / "docs/chatgpt_status/topography/shards/height_difference_2/automation/009_prepare_hmlr_inspire_sources.py"
CANONICAL = REPO / "england_map_web/data/program_layer_matrix/security.geojson"
RUN_ROOT = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/002_official_geometry_pipeline_latest"
WEB_ROOT = REPO / "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_2"
RUNNER_STATUS = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/002_official_geometry_pipeline_latest.json"
WEB_STATUS = REPO / "england_map_web/data/aays_21_slots/future_growth_1/geometry_runner_status_latest.json"
GLA_QUERY = "https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/FeatureServer/101/query"
CURRENT_SITE_REFS = ("LBBD49/XJ", "LBBD72/ZZ", "LBBD91/DI")
OPTIONAL_STALE_SITE_REFS = ("LBBD23",)
SITE_REFS = CURRENT_SITE_REFS + OPTIONAL_STALE_SITE_REFS
TIMEOUT_SECONDS = 180
MAX_GLA_BYTES = 25 * 1024 * 1024


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> dict[str, Any]:
    started = time.time()
    process = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "exit_code": process.returncode,
        "stdout": process.stdout[-12000:],
        "stderr": process.stderr[-12000:],
        "elapsed_seconds": round(time.time() - started, 3),
    }


def fetch_gla(destination: Path) -> dict[str, Any]:
    quoted = ",".join("'" + ref.replace("'", "''") + "'" for ref in SITE_REFS)
    params = {
        "where": f"sitereference IN ({quoted})",
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    url = GLA_QUERY + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AAYS-TerraYield/future_growth_1 official-geometry-only",
            "Accept": "application/geo+json,application/json",
        },
    )
    started = time.time()
    total = 0
    digest = hashlib.sha256()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response, destination.open("wb") as handle:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"HTTP {status}")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_GLA_BYTES:
                    raise RuntimeError("GLA payload exceeds safety budget")
                handle.write(chunk)
                digest.update(chunk)
        payload = json.loads(destination.read_text(encoding="utf-8-sig"))
        features = payload.get("features") if isinstance(payload, dict) else None
        if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
            raise ValueError("GLA response is not a GeoJSON FeatureCollection")
        refs = {str((feature.get("properties") or {}).get("sitereference") or "").strip() for feature in features}
        unexpected = refs - set(SITE_REFS)
        if unexpected:
            raise ValueError(f"GLA response contains unexpected references: {sorted(unexpected)}")
        missing_current = set(CURRENT_SITE_REFS) - refs
        if missing_current:
            raise ValueError(f"GLA response missing current references: {sorted(missing_current)}")
        if any(not feature.get("geometry") for feature in features):
            raise ValueError("GLA response contains missing geometry")
        return {
            "ok": True,
            "url": url,
            "http_status": status,
            "bytes": total,
            "sha256": digest.hexdigest(),
            "feature_count": len(features),
            "current_site_references_required": list(CURRENT_SITE_REFS),
            "optional_stale_site_references": list(OPTIONAL_STALE_SITE_REFS),
            "site_references_returned": sorted(refs),
            "optional_stale_references_missing": sorted(set(OPTIONAL_STALE_SITE_REFS) - refs),
            "path": str(destination),
            "elapsed_seconds": round(time.time() - started, 3),
        }
    except Exception as exc:
        destination.unlink(missing_ok=True)
        return {
            "ok": False,
            "url": url,
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": round(time.time() - started, 3),
        }


def starter_manifest() -> dict[str, Any]:
    candidates = [
        {
            "row_no": 1,
            "parcel_id": "parcel_1",
            "hmlr_inspire_id": "39729785",
            "longitude": 0.1615694,
            "latitude": 51.528344,
            "local_authority_name": "London Borough of Barking and Dagenham",
        },
        {
            "row_no": 2,
            "parcel_id": "parcel_2",
            "hmlr_inspire_id": "39724273",
            "longitude": 0.1603329,
            "latitude": 51.5284149,
            "local_authority_name": "London Borough of Barking and Dagenham",
        },
        {
            "row_no": 3,
            "parcel_id": "parcel_3",
            "hmlr_inspire_id": "60116682",
            "longitude": 0.1158854,
            "latitude": 51.5455174,
            "local_authority_name": "London Borough of Barking and Dagenham",
        },
    ]
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "canonical_scope": "LONDON_CANONICAL_92283_NOT_ALL_ENGLAND",
        "canonical_source_path": str(CANONICAL),
        "canonical_source_expected_blob_sha": "8afd1d2bac414cf0f6b9484014e7878a4ceff877",
        "candidates": candidates,
        "candidate_count": 3,
        "row_order_inference_used": False,
        "nearest_fill_used": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def publish(payload: dict[str, Any]) -> None:
    write_json(RUNNER_STATUS, payload)
    write_json(WEB_STATUS, payload)


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    WEB_ROOT.mkdir(parents=True, exist_ok=True)
    starter_path = RUN_ROOT / "starter_manifest.json"
    write_json(starter_path, starter_manifest())

    result: dict[str, Any] = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "started_at_epoch": time.time(),
        "state": "RUNNING",
        "status": "RUNNING",
        "starter_manifest_path": str(starter_path),
        "source_steps": {},
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    publish(result)

    if not PIPELINE.is_file() or not HMLR_PREPARER.is_file() or not CANONICAL.is_file():
        result.update(
            state="BLOCKED",
            status="BLOCKED_MISSING_REQUIRED_REPOSITORY_FILE",
            blocker="PIPELINE_HMLR_PREPARER_OR_CANONICAL_SOURCE_MISSING",
        )
        publish(result)
        return 2

    gla_path = RUN_ROOT / "sources" / "gla_brownfield_target_sites.geojson"
    gla_result = fetch_gla(gla_path)
    result["source_steps"]["gla_brownfield"] = gla_result
    publish(result)
    if not gla_result.get("ok"):
        result.update(state="BLOCKED", status="BLOCKED_GLA_OFFICIAL_POLYGON_FETCH", blocker=gla_result.get("error"))
        publish(result)
        return 2

    hmlr_output = RUN_ROOT / "sources" / "hmlr"
    hmlr_execution = run(
        [
            sys.executable,
            str(HMLR_PREPARER),
            "--starter-manifest",
            str(starter_path),
            "--output-dir",
            str(hmlr_output),
            "--timeout",
            str(TIMEOUT_SECONDS),
        ]
    )
    result["source_steps"]["hmlr_preparer_execution"] = hmlr_execution
    manifest_path = hmlr_output / "hmlr_source_manifest.json"
    if manifest_path.is_file():
        hmlr_manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        result["source_steps"]["hmlr_source_manifest"] = hmlr_manifest
    else:
        hmlr_manifest = None
    publish(result)
    if hmlr_execution["exit_code"] != 0 or not isinstance(hmlr_manifest, dict):
        result.update(state="BLOCKED", status="BLOCKED_HMLR_OFFICIAL_SOURCE_PREPARATION", blocker="HMLR_PREPARER_DID_NOT_RETURN_READY_MANIFEST")
        publish(result)
        return 2

    vectors = [Path(value) for value in hmlr_manifest.get("vector_paths") or []]
    vectors = [path for path in vectors if path.is_file()]
    if not vectors:
        result.update(
            state="BLOCKED",
            status="BLOCKED_HMLR_VECTOR_SELECTION",
            blocker="NO_AUTHORITY_VECTOR_RETURNED",
            hmlr_vector_paths=[],
        )
        publish(result)
        return 2

    pipeline_attempts: list[dict[str, Any]] = []
    selected_vector: Path | None = None
    geometry_result: dict[str, Any] | None = None
    geometry_output: Path | None = None
    for index, vector in enumerate(vectors, start=1):
        attempt_output = WEB_ROOT / "verified" / f"vector_{index}"
        execution = run(
            [
                sys.executable,
                str(PIPELINE),
                "--repo-root",
                str(REPO),
                "--canonical-geojson",
                str(CANONICAL),
                "--gla-geojson",
                str(gla_path),
                "--hmlr-gml",
                str(vector),
                "--output-dir",
                str(attempt_output),
            ]
        )
        candidate_path = attempt_output / "official_geometry_verification_latest.json"
        candidate_result = json.loads(candidate_path.read_text(encoding="utf-8-sig")) if candidate_path.is_file() else None
        attempt = {
            "vector_path": str(vector),
            "vector_sha256": sha256(vector),
            "execution": execution,
            "result_path": str(candidate_path),
            "result_available": isinstance(candidate_result, dict),
        }
        pipeline_attempts.append(attempt)
        if execution["exit_code"] == 0 and isinstance(candidate_result, dict):
            selected_vector = vector
            geometry_result = candidate_result
            geometry_output = attempt_output
            break

    result["source_steps"]["geometry_pipeline_attempts"] = pipeline_attempts
    result["geometry_result"] = geometry_result
    if selected_vector is not None:
        result["selected_hmlr_vector"] = {
            "path": str(selected_vector),
            "sha256": sha256(selected_vector),
        }
    result["source_sha256"] = {"gla_geojson": sha256(gla_path)}
    if geometry_result is None or selected_vector is None or geometry_output is None:
        result.update(state="BLOCKED", status="BLOCKED_OFFICIAL_GEOMETRY_PIPELINE", blocker="NO_HMLR_VECTOR_PASSED_EXACT_ID_FAIL_CLOSED_VALIDATOR")
        publish(result)
        return 2

    verified = int((geometry_result.get("counts") or {}).get("parcel_polygon_relations_verified") or 0)
    result.update(
        state="COMPLETED_SOURCE_GEOMETRY_WAVE",
        status="COMPLETED_OFFICIAL_GEOMETRY_WAVE_NO_SCORE",
        official_polygon_relations_verified=verified,
        selected_geometry_output=str(geometry_output),
        next_unverified_step="BUILD_30761_ROW_FULL_FACTOR_MATRIX_THEN_SCORE_WITH_CONFIDENCE",
        completed_at_epoch=time.time(),
    )
    publish(result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "state": "BLOCKED",
            "status": "BLOCKED_UNHANDLED_EXCEPTION",
            "blocker": f"{type(exc).__name__}: {exc}",
            "actual_business_data_rows_written": 0,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        publish(payload)
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        raise
