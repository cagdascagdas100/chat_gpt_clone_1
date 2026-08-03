#!/usr/bin/env python3
"""Wave353: bounded DuckDB/httpfs direct official Overture S3 bbox query gate.

The script installs DuckDB only into a temporary directory, resolves the latest
Overture release through the official STAC catalog, and—only when both gates
succeed—runs three isolated bbox queries. Geometry is never selected and at
most 25 candidate IDs/bboxes are retained per query. Candidate features are
not parcel bindings without independent exact identity proof.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request
from typing import Any

STAC_URL = "https://stac.overturemaps.org/catalog.json"
S3_TEMPLATE = "s3://overturemaps-us-west-2/release/{release}/theme=buildings/type=building/*.parquet"
PACKAGE_SPEC = "duckdb>=1.1.0"
MAX_STAC_BYTES = 200_000
MAX_CANDIDATES_PER_BBOX = 25


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as tmp:
        tmp.write(encoded)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bounded_get_json(url: str, timeout: int, max_bytes: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-Wave353/1.0"})
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError(f"response_exceeded_{max_bytes}_bytes")
            return {"ok": True, "url": url, "status": getattr(response, "status", None), "bytes_read": len(data), "content_sha256": sha256_bytes(data), "json": json.loads(data.decode("utf-8")), "duration_seconds": round(time.monotonic() - started, 3)}
    except Exception as exc:
        return {"ok": False, "url": url, "bytes_read": 0, "error": f"{type(exc).__name__}:{exc}", "duration_seconds": round(time.monotonic() - started, 3)}


def extract_latest_release(catalog: dict[str, Any]) -> str | None:
    for key in ("latest", "release", "id"):
        value = catalog.get(key)
        if isinstance(value, str) and value[:4].isdigit() and "." in value:
            return value
    links = catalog.get("links")
    if isinstance(links, list):
        for link in links:
            if isinstance(link, dict) and link.get("rel") == "latest":
                href = str(link.get("href", ""))
                for part in reversed(href.rstrip("/").split("/")):
                    if part[:4].isdigit() and "." in part:
                        return part.removesuffix(".json")
    return None


def install_duckdb(temp_target: Path, timeout: int) -> dict[str, Any]:
    command = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-cache-dir", "--target", str(temp_target), PACKAGE_SPEC]
    started = time.monotonic()
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        combined = (completed.stdout or "") + (completed.stderr or "")
        return {"attempted": True, "returncode": completed.returncode, "installed": completed.returncode == 0 and (temp_target / "duckdb").exists(), "timed_out": False, "duration_seconds": round(time.monotonic() - started, 3), "log_bytes": len(combined.encode("utf-8", errors="replace")), "log_sha256": sha256_bytes(combined.encode("utf-8", errors="replace")), "log_excerpt": combined[-2000:], "temporary_target_only": True, "package_spec": PACKAGE_SPEC}
    except subprocess.TimeoutExpired as exc:
        combined = ((exc.stdout or "") if isinstance(exc.stdout, str) else "") + ((exc.stderr or "") if isinstance(exc.stderr, str) else "")
        return {"attempted": True, "returncode": None, "installed": False, "timed_out": True, "duration_seconds": round(time.monotonic() - started, 3), "log_bytes": len(combined.encode("utf-8", errors="replace")), "log_sha256": sha256_bytes(combined.encode("utf-8", errors="replace")), "log_excerpt": combined[-2000:], "temporary_target_only": True, "package_spec": PACKAGE_SPEC}


def bbox_for_point(lon: float, lat: float, delta: float = 0.00035) -> list[float]:
    return [round(lon - delta, 7), round(lat - delta, 7), round(lon + delta, 7), round(lat + delta, 7)]


def run_bbox_query(temp_target: Path, release: str, parcel_id: str, bbox: list[float], timeout: int) -> dict[str, Any]:
    s3_path = S3_TEMPLATE.format(release=release)
    child = '''
import json, os, sys
sys.path.insert(0, os.environ["AAYS_DUCKDB_TARGET"])
import duckdb
bbox = json.loads(os.environ["AAYS_BBOX"])
path = os.environ["AAYS_S3_PATH"]
con = duckdb.connect(database=":memory:")
con.execute("INSTALL httpfs")
con.execute("LOAD httpfs")
con.execute("SET s3_region='us-west-2'")
query = """
SELECT id, bbox.xmin AS xmin, bbox.ymin AS ymin, bbox.xmax AS xmax, bbox.ymax AS ymax
FROM read_parquet(?, filename=true, hive_partitioning=1)
WHERE bbox.xmin < ? AND bbox.xmax > ? AND bbox.ymin < ? AND bbox.ymax > ?
LIMIT 25
"""
rows = con.execute(query, [path, bbox[2], bbox[0], bbox[3], bbox[1]]).fetchall()
print(json.dumps({"rows": rows}, separators=(",", ":")))
'''
    env = os.environ.copy()
    env.update({"AAYS_DUCKDB_TARGET": str(temp_target), "AAYS_BBOX": json.dumps(bbox, separators=(",", ":")), "AAYS_S3_PATH": s3_path})
    started = time.monotonic()
    try:
        completed = subprocess.run([sys.executable, "-c", child], capture_output=True, text=True, timeout=timeout, env=env, check=False)
        stdout, stderr = completed.stdout or "", completed.stderr or ""
        rows, parse_error = [], None
        if completed.returncode == 0:
            try:
                rows = json.loads(stdout).get("rows", [])
            except Exception as exc:
                parse_error = f"{type(exc).__name__}:{exc}"
        return {"parcel_id": parcel_id, "bbox": bbox, "attempted": True, "returncode": completed.returncode, "timed_out": False, "success": completed.returncode == 0 and parse_error is None, "row_count": len(rows), "rows": rows[:MAX_CANDIDATES_PER_BBOX], "stdout_sha256": sha256_bytes(stdout.encode("utf-8", errors="replace")), "stderr_sha256": sha256_bytes(stderr.encode("utf-8", errors="replace")), "stderr_excerpt": stderr[-2000:], "parse_error": parse_error, "duration_seconds": round(time.monotonic() - started, 3), "geometry_selected": False, "max_candidates": MAX_CANDIDATES_PER_BBOX}
    except subprocess.TimeoutExpired as exc:
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        return {"parcel_id": parcel_id, "bbox": bbox, "attempted": True, "returncode": None, "timed_out": True, "success": False, "row_count": 0, "rows": [], "stderr_sha256": sha256_bytes(stderr.encode("utf-8", errors="replace")), "stderr_excerpt": stderr[-2000:], "duration_seconds": round(time.monotonic() - started, 3), "geometry_selected": False, "max_candidates": MAX_CANDIDATES_PER_BBOX}


def self_test() -> int:
    assert bbox_for_point(-0.0407406, 51.6769078) == [-0.0410906, 51.6765578, -0.0403906, 51.6772578]
    assert extract_latest_release({"latest": "2026-06-17.0"}) == "2026-06-17.0"
    assert extract_latest_release({"links": [{"rel": "latest", "href": "https://x/releases/2026-06-17.0/catalog.json"}]}) == "2026-06-17.0"
    print("SELF_TEST_PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--install-timeout", type=int, default=120)
    parser.add_argument("--stac-timeout", type=int, default=30)
    parser.add_argument("--accessed-at", required=False)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.canonical or not args.fixture or not args.output:
        parser.error("--canonical, --fixture and --output are required")
    canonical, fixture = load_json(Path(args.canonical)), load_json(Path(args.fixture))
    assessments = []
    for row in canonical.get("rows", [])[:3]:
        props = row.get("properties", {})
        lon, lat = float(props["hmlr_lon"]), float(props["hmlr_lat"])
        assessments.append({"parcel_id": props["parcel_id"], "hmlr_inspire_id": props["hmlr_inspire_id"], "longitude": lon, "latitude": lat, "london_authority": props.get("london_authority"), "geometry_type": row.get("geometry_type"), "bbox": bbox_for_point(lon, lat)})
    stac_receipt = bounded_get_json(STAC_URL, args.stac_timeout, MAX_STAC_BYTES)
    release = extract_latest_release(stac_receipt.get("json", {})) if stac_receipt.get("ok") else None
    duckdb_preinstalled = importlib.util.find_spec("duckdb") is not None
    bbox_results = []
    with tempfile.TemporaryDirectory(prefix="aays_wave353_duckdb_") as temp_dir:
        temp_target = Path(temp_dir) / "site-packages"
        temp_target.mkdir()
        install_receipt = {"attempted": False, "returncode": 0, "installed": True, "timed_out": False, "temporary_target_only": True, "package_spec": "preinstalled duckdb"} if duckdb_preinstalled else install_duckdb(temp_target, args.install_timeout)
        runnable = bool(install_receipt.get("installed") and release)
        if runnable:
            for assessment in assessments:
                bbox_results.append(run_bbox_query(temp_target, release, assessment["parcel_id"], assessment["bbox"], args.timeout))
        else:
            reason = ";".join((["DUCKDB_NOT_INSTALLED"] if not install_receipt.get("installed") else []) + (["LATEST_RELEASE_NOT_RESOLVED"] if not release else []))
            bbox_results = [{"parcel_id": a["parcel_id"], "bbox": a["bbox"], "attempted": False, "success": False, "row_count": 0, "rows": [], "reason": reason, "geometry_selected": False, "max_candidates": MAX_CANDIDATES_PER_BBOX} for a in assessments]
    successful = sum(1 for item in bbox_results if item.get("success"))
    candidate_count = sum(int(item.get("row_count", 0)) for item in bbox_results)
    blocker_parts = []
    if not stac_receipt.get("ok"): blocker_parts.append("OVERTURE_STAC_LATEST_RELEASE_NOT_LIVE_ACQUIRED")
    elif not release: blocker_parts.append("OVERTURE_STAC_LATEST_RELEASE_NOT_PARSED")
    if not install_receipt.get("installed"): blocker_parts.append("DUCKDB_NOT_INSTALLABLE_FROM_CONFIGURED_PACKAGE_INDEX")
    if successful < 3: blocker_parts.append("THREE_BOUNDED_DUCKDB_HTTPFS_OVERTURE_S3_BBOX_QUERIES_NOT_COMPLETED")
    if candidate_count == 0: blocker_parts.append("THREE_EXACT_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED")
    blocker_parts.extend(["THREE_EXACT_UPRNS_NOT_ACQUIRED", "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"])
    runtime_excerpt = f"stac_ok={stac_receipt.get('ok')}; release={release}; duckdb_preinstalled={duckdb_preinstalled}; install_returncode={install_receipt.get('returncode')}; installed={install_receipt.get('installed')}; successful_bbox_query_count={successful}; candidate_feature_count={candidate_count}"
    runtime_evidence = {"source_url": STAC_URL, "accessed_at": args.accessed_at, "content_sha256": sha256_bytes(runtime_excerpt.encode("utf-8")), "hash_scope": "stac_duckdb_install_and_three_bbox_query_receipts", "record_scope": "Official STAC latest-release resolution, temporary DuckDB install, and up to three isolated httpfs S3 bbox queries.", "relevant_record_ids_or_excerpt": runtime_excerpt, "supports_fields": ["latest_release", "duckdb_installability", "httpfs", "three_bounded_bbox_queries", "candidate_count", "no_geometry_selection", "no_exact_binding_claim"], "license_or_terms_url": "https://docs.overturemaps.org/attribution/"}
    payload = {"schema_version": 1, "architecture_version": 3, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": "gas_emissions_2", "wave": 353, "accessed_at": args.accessed_at, "canonical_sample_rows_in_scope": len(assessments), "assessments": assessments, "stac_receipt": {k: v for k, v in stac_receipt.items() if k != "json"}, "resolved_release": release, "s3_path": S3_TEMPLATE.format(release=release) if release else None, "duckdb_preinstalled": duckdb_preinstalled, "temporary_duckdb_install": install_receipt, "bbox_query_count": 3, "bbox_query_results": bbox_results, "successful_bbox_query_count": successful, "candidate_feature_count": candidate_count, "geoparquet_body_downloaded": False, "geometry_selected": False, "business_rows_produced": 0, "parcel_rows_bound": 0, "completed_count": 0, "target_count": 30761, "previous_percent": 0.0, "current_percent": 0.0, "percent_increase": 0.0, "decision": "DUCKDB_HTTPFS_DIRECT_OVERTURE_S3_THREE_BBOX_QUERY_GATE_ASSESSED", "state": "NO_DATA_CONTINUE", "blocker": ";".join(blocker_parts), "first_unverified_step": "ASSESS_OVERTURE_EXPLORER_VISIBLE_GEOJSON_THREE_POINT_BUILDING_CANDIDATE_GATE_OR_NO_DATA_CONTINUE", "source_evidence_manifest": fixture.get("source_evidence_manifest", []), "runtime_source_evidence": [runtime_evidence], "fake_data": False, "final_ready": False}
    atomic_write_json(Path(args.output), payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
