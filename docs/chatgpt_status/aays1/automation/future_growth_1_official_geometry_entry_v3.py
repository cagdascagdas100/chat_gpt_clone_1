#!/usr/bin/env python3
"""Networked single-runner entrypoint for future_growth_1 attempt 3.

The entrypoint downloads official GLA Brownfield polygons, resolves and downloads
the current HM Land Registry Barking and Dagenham INSPIRE GML, and delegates all
matching and spatial relation work to the exact-ID v2 relation builder. It is
sequential, fail closed, and never emits a Future Growth score or DB write.
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
ATTEMPT_ID = "future-growth-1-20260721-003"
REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
RELATION_BUILDER = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/003_build_official_geometry_relations_v2.py"
HMLR_PREPARER = REPO / "docs/chatgpt_status/topography/shards/height_difference_2/automation/009_prepare_hmlr_inspire_sources.py"
CANONICAL = REPO / "england_map_web/data/program_layer_matrix/security.geojson"
CANDIDATES = REPO / "england_map_web/data/aays_21_slots/future_growth_1/candidates_latest.json"
RUN_ROOT = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/003_official_geometry_pipeline_v3_latest"
WEB_ROOT = REPO / "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_3"
RUNNER_STATUS = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/003_official_geometry_pipeline_v3_latest.json"
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
        "stdout": process.stdout[-16000:],
        "stderr": process.stderr[-16000:],
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
            "User-Agent": "AAYS-TerraYield/future_growth_1 exact-geometry-v3",
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
            declared = response.headers.get("Content-Length")
            if declared and int(declared) > MAX_GLA_BYTES:
                raise RuntimeError("GLA declared content exceeds safety budget")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_GLA_BYTES:
                    raise RuntimeError("GLA streamed content exceeds safety budget")
                handle.write(chunk)
                digest.update(chunk)
        payload = json.loads(destination.read_text(encoding="utf-8-sig"))
        features = payload.get("features") if isinstance(payload, dict) else None
        if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
            raise ValueError("GLA response is not a GeoJSON FeatureCollection")
        references = {
            str((feature.get("properties") or {}).get("sitereference") or "").strip() for feature in features
        }
        unexpected = references - set(SITE_REFS)
        missing_current = set(CURRENT_SITE_REFS) - references
        if unexpected:
            raise ValueError(f"unexpected GLA references: {sorted(unexpected)}")
        if missing_current:
            raise ValueError(f"missing current GLA references: {sorted(missing_current)}")
        if any(not feature.get("geometry") for feature in features):
            raise ValueError("GLA response contains missing geometry")
        return {
            "ok": True,
            "url": url,
            "http_status": status,
            "content_type": response.headers.get("Content-Type") if 'response' in locals() else None,
            "bytes": total,
            "sha256": digest.hexdigest(),
            "feature_count": len(features),
            "current_references_required": list(CURRENT_SITE_REFS),
            "current_references_present": sorted(set(CURRENT_SITE_REFS) & references),
            "optional_stale_references_present": sorted(set(OPTIONAL_STALE_SITE_REFS) & references),
            "optional_stale_references_missing": sorted(set(OPTIONAL_STALE_SITE_REFS) - references),
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
    return {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "canonical_scope": "LONDON_CANONICAL_92283_NOT_ALL_ENGLAND",
        "canonical_source_path": str(CANONICAL),
        "canonical_source_expected_blob_sha": "8afd1d2bac414cf0f6b9484014e7878a4ceff877",
        "candidates": [
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
        ],
        "candidate_count": 3,
        "row_order_inference_used": False,
        "nearest_fill_used": False,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def publish(payload: dict[str, Any]) -> None:
    write_json(RUNNER_STATUS, payload)
    write_json(WEB_STATUS, payload)


def blocked(result: dict[str, Any], status: str, blocker: str) -> int:
    result.update(state="BLOCKED", status=status, blocker=blocker, completed_at_epoch=time.time())
    publish(result)
    return 2


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    WEB_ROOT.mkdir(parents=True, exist_ok=True)
    starter_path = RUN_ROOT / "starter_manifest.json"
    write_json(starter_path, starter_manifest())

    result: dict[str, Any] = {
        "schema_version": 2,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "started_at_epoch": time.time(),
        "state": "RUNNING",
        "status": "RUNNING",
        "source_steps": {},
        "starter_manifest_path": str(starter_path),
        "candidate_json_path": str(CANDIDATES),
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    publish(result)

    required = [RELATION_BUILDER, HMLR_PREPARER, CANONICAL, CANDIDATES]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        result["missing_paths"] = missing
        return blocked(result, "BLOCKED_MISSING_REQUIRED_REPOSITORY_FILE", "REQUIRED_REPOSITORY_FILES_MISSING")

    gla_path = RUN_ROOT / "sources" / "gla_brownfield_target_sites.geojson"
    gla_result = fetch_gla(gla_path)
    result["source_steps"]["gla_brownfield"] = gla_result
    publish(result)
    if not gla_result.get("ok"):
        return blocked(result, "BLOCKED_GLA_OFFICIAL_POLYGON_FETCH", str(gla_result.get("error")))

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
    hmlr_manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig")) if manifest_path.is_file() else None
    result["source_steps"]["hmlr_source_manifest"] = hmlr_manifest
    publish(result)
    if hmlr_execution["exit_code"] != 0 or not isinstance(hmlr_manifest, dict):
        return blocked(result, "BLOCKED_HMLR_OFFICIAL_SOURCE_PREPARATION", "HMLR_PREPARER_DID_NOT_RETURN_READY_MANIFEST")
    if hmlr_manifest.get("status") != "READY_HMLR_GML_DOWNLOADED":
        return blocked(result, "BLOCKED_HMLR_OFFICIAL_SOURCE_PREPARATION", str(hmlr_manifest.get("status")))

    relation_output = WEB_ROOT / "verified"
    relation_execution = run(
        [
            sys.executable,
            str(RELATION_BUILDER),
            "--starter-manifest",
            str(starter_path),
            "--candidate-json",
            str(CANDIDATES),
            "--gla-geojson",
            str(gla_path),
            "--vector-root",
            str(hmlr_output),
            "--output-dir",
            str(relation_output),
        ]
    )
    result["source_steps"]["relation_builder_execution"] = relation_execution
    relation_path = relation_output / "official_geometry_relations_v2_latest.json"
    relation_result = json.loads(relation_path.read_text(encoding="utf-8-sig")) if relation_path.is_file() else None
    result["relation_result"] = relation_result
    publish(result)
    if relation_execution["exit_code"] != 0 or not isinstance(relation_result, dict):
        return blocked(result, "BLOCKED_EXACT_HMLR_GLA_RELATION_BUILDER", "RELATION_BUILDER_DID_NOT_PASS")

    counts = dict(relation_result.get("counts") or {})
    gates = dict(relation_result.get("quality_gates") or {})
    acceptance = {
        "exact_hmlr_parcel_polygons": counts.get("exact_hmlr_parcel_polygons") == 3,
        "current_gla_site_polygons": counts.get("current_gla_site_polygons") == 3,
        "current_polygon_relations_verified": counts.get("current_polygon_relations_verified") == 5,
        "stale_or_completed_rejections": counts.get("stale_or_completed_rejections") == 1,
        "nearest_polygon_fill_used": gates.get("nearest_polygon_fill_used") is False,
        "point_only_promotion_used": gates.get("point_only_promotion_used") is False,
        "scored_business_rows": counts.get("scored_business_rows") == 0,
        "actual_business_data_rows_written": counts.get("actual_business_data_rows_written") == 0,
    }
    result["acceptance"] = acceptance
    result["source_sha256"] = {
        "gla_geojson": sha256(gla_path),
        "relation_builder": sha256(RELATION_BUILDER),
        "candidate_json": sha256(CANDIDATES),
    }
    if not all(acceptance.values()):
        return blocked(result, "BLOCKED_ACCEPTANCE_CONTRACT", "ONE_OR_MORE_OFFICIAL_GEOMETRY_ACCEPTANCE_GATES_FAILED")

    result.update(
        state="COMPLETED_SOURCE_GEOMETRY_WAVE",
        status="COMPLETED_EXACT_OFFICIAL_GEOMETRY_WAVE_NO_SCORE",
        output_path=str(relation_path),
        output_geojson_path=str(relation_output / "official_geometry_relations_v2_latest.geojson"),
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
            "schema_version": 2,
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
