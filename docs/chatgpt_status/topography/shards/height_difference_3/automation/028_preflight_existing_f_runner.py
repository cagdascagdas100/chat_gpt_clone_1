#!/usr/bin/env python3
"""Preflight the existing F portable runner before height_difference_3 real execution.

The check is read-only except for an atomic write/delete probe in the requested
output directory and optional status JSON files. It creates no runner, queue,
lease, parcel result, geometry, elevation or product row.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import py_compile
import shutil
import socket
import ssl
import sys
import tempfile
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REQUIRED_MODULES = ("requests", "pyproj", "fiona", "rasterio", "shapely", "numpy")
REQUIRED_SCRIPTS = (
    "004_prepare_three_real_sample_queries.py",
    "008_match_hmlr_inspire_gml.py",
    "009_sample_ea_dtm_and_os_terrain50.py",
    "010_publish_verified_height_difference_examples.py",
    "012_download_hmlr_inspire_sources.py",
    "013_fetch_ea_dtm_wcs_for_matches.py",
    "014_prepare_os_terrain50_tiles.py",
    "020_stream_extract_security_canonical.py",
    "023_download_os_terrain50_required_areas.py",
    "025_validate_resumable_targeted_sources.py",
    "026_execute_resumable_targeted_sources.py",
    "027_validate_resumable_alias_safe.py",
)
ENDPOINTS = {
    "HMLR_INSPIRE_DOWNLOAD_PAGE": "https://use-land-property-data.service.gov.uk/datasets/inspire/download",
    "OS_TERRAIN50_PRODUCT_API": "https://api.os.uk/downloads/v1/products/Terrain50",
    "EA_DTM_1M_WCS_CAPABILITIES": (
        "https://environment.data.gov.uk/spatialdata/"
        "lidar-composite-digital-terrain-model-dtm-1m/wcs"
        "?service=WCS&version=2.0.1&request=GetCapabilities"
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()  # nosec - Git object identity, not cryptographic authentication
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_python() -> dict[str, Any]:
    version = list(sys.version_info[:3])
    if tuple(version) < (3, 10, 0):
        raise RuntimeError(f"Python >=3.10 required, found {version}")
    return {"python_version": version, "executable": sys.executable}


def check_modules() -> dict[str, Any]:
    versions: dict[str, str] = {}
    for name in REQUIRED_MODULES:
        importlib.import_module(name)
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "importable_version_unknown"
    return {"module_count": len(versions), "versions": versions}


def check_scripts(script_dir: Path) -> dict[str, Any]:
    compiled = []
    for name in REQUIRED_SCRIPTS:
        path = script_dir / name
        if not path.is_file():
            raise FileNotFoundError(path)
        py_compile.compile(str(path), doraise=True)
        compiled.append(name)
    return {"script_count": len(compiled), "compiled": compiled}


def check_source(path: Path, expected_blob: str | None, min_bytes: int) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    size = path.stat().st_size
    if size < min_bytes:
        raise RuntimeError(f"canonical source too small: {size} < {min_bytes}")
    actual = git_blob_sha1(path)
    if expected_blob and actual.casefold() != expected_blob.casefold():
        raise RuntimeError(f"canonical Git blob SHA mismatch: {actual} != {expected_blob}")
    with path.open("rb") as handle:
        head = handle.read(256).lstrip()
    if not head.startswith(b"{"):
        raise RuntimeError("canonical source is not a JSON object")
    return {"path": str(path), "size_bytes": size, "git_blob_sha1": actual}


def check_output_dir(path: Path, min_free_bytes: int) -> dict[str, Any]:
    path.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(path)
    if usage.free < min_free_bytes:
        raise RuntimeError(f"insufficient free bytes: {usage.free} < {min_free_bytes}")
    fd, name = tempfile.mkstemp(prefix="height_difference_3_preflight_", suffix=".tmp", dir=path)
    probe = Path(name)
    try:
        with open(fd, "wb", closefd=True) as handle:
            handle.write(b"atomic-write-probe")
        final = probe.with_suffix(".ok")
        probe.replace(final)
        final.unlink()
    finally:
        probe.unlink(missing_ok=True)
    return {"path": str(path), "free_bytes": usage.free, "min_free_bytes": min_free_bytes, "atomic_write_rename": True}


def fetch_limited(url: str, timeout: int, max_bytes: int = 1024 * 1024) -> tuple[bytes, str, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "TerraYield-AAYS/height_difference_3-preflight", "Accept": "*/*"},
    )
    with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            body = body[:max_bytes]
        return body, response.geturl(), response.headers.get("content-type", "")


def check_endpoint(name: str, url: str, timeout: int) -> dict[str, Any]:
    host = urllib.parse.urlparse(url).hostname
    if not host:
        raise RuntimeError(f"endpoint has no host: {url}")
    addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
    body, resolved, content_type = fetch_limited(url, timeout)
    lower = body.lower()
    if name == "HMLR_INSPIRE_DOWNLOAD_PAGE":
        if b"inspire" not in lower or b"download" not in lower:
            raise RuntimeError("HMLR page signature not found")
    elif name == "OS_TERRAIN50_PRODUCT_API":
        payload = json.loads(body)
        if payload.get("id") != "Terrain50":
            raise RuntimeError("OS product API did not return Terrain50")
        version = str(payload.get("version") or "")
        if not version.endswith("-07"):
            raise RuntimeError(f"Terrain50 is not a July release: {version}")
    elif name == "EA_DTM_1M_WCS_CAPABILITIES":
        if b"coverage" not in lower or (b"wcs" not in lower and b"capabilities" not in lower):
            raise RuntimeError("EA WCS capabilities signature not found")
    return {
        "name": name,
        "url": url,
        "resolved_url": resolved,
        "content_type": content_type,
        "bytes_read": len(body),
        "dns_addresses": addresses,
    }


def run_check(name: str, function: Callable[[], dict[str, Any]], required: bool = True) -> dict[str, Any]:
    started = utc_now()
    try:
        evidence = function()
    except Exception as exc:
        return {
            "check": name,
            "required": required,
            "status": "blocked" if required else "warning",
            "started_at": started,
            "finished_at": utc_now(),
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "check": name,
        "required": required,
        "status": "completed",
        "started_at": started,
        "finished_at": utc_now(),
        "evidence": evidence,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    script_dir = args.script_dir.resolve()
    source = args.security_geojson.resolve()
    output_dir = args.output_dir.resolve()
    checks = [
        run_check("PYTHON_VERSION", check_python),
        run_check("REQUIRED_PYTHON_MODULES", check_modules),
        run_check("PIPELINE_SCRIPT_COMPILE", lambda: check_scripts(script_dir)),
        run_check(
            "CANONICAL_SOURCE_GIT_BLOB",
            lambda: check_source(source, args.expected_git_blob_sha1, args.min_source_bytes),
        ),
        run_check("OUTPUT_DISK_AND_ATOMIC_WRITE", lambda: check_output_dir(output_dir, args.min_free_bytes)),
    ]
    endpoint_items = list(ENDPOINTS.items())
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="height_difference_3_preflight") as pool:
        futures = [(name, pool.submit(check_endpoint, name, url, args.timeout)) for name, url in endpoint_items]
        for name, future in futures:
            checks.append(run_check(name, future.result))
    blocked = [item for item in checks if item["required"] and item["status"] != "completed"]
    status = "PREFLIGHT_READY_EXISTING_F_RUNNER_CAN_START_026" if not blocked else "BLOCKED_EXISTING_F_RUNNER_PREFLIGHT"
    operations = []
    number = args.operation_start
    for item in checks:
        operations.append({
            "operation_no": number,
            "stage": "PREFLIGHT",
            "check": item["check"],
            "status": item["status"],
            "details_summary": (
                "Required preflight check passed."
                if item["status"] == "completed"
                else item.get("error", "Required preflight check failed.")
            ),
            "evidence": item.get("evidence"),
        })
        number += 1
    return {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "updated_at": utc_now(),
        "status": status,
        "first_invalid_stage": None if not blocked else blocked[0]["check"],
        "check_count": len(checks),
        "passed_count": sum(item["status"] == "completed" for item in checks),
        "blocked_count": len(blocked),
        "checks": checks,
        "operation_count": len(operations),
        "operations": operations,
        "real_counts": {
            "canonical_shard_rows": 0,
            "candidates": 0,
            "hmlr_matches": 0,
            "ea_samples": 0,
            "terrain50_samples": 0,
            "published_examples": 0,
        },
        "next_command_allowed": not blocked,
        "single_shared_runner_only": True,
        "single_process_bounded_concurrency": True,
        "maximum_parallel_network_stages": 2,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_submission": False,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--security-geojson", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--script-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--report-output", type=Path)
    parser.add_argument("--web-runtime-status", type=Path)
    parser.add_argument("--expected-git-blob-sha1", default="8afd1d2bac414cf0f6b9484014e7878a4ceff877")
    parser.add_argument("--min-source-bytes", type=int, default=10 * 1024 * 1024)
    parser.add_argument("--min-free-bytes", type=int, default=4 * 1024 * 1024 * 1024)
    parser.add_argument("--operation-start", type=int, default=331)
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    if args.operation_start < 1 or args.timeout < 1 or args.min_source_bytes < 1 or args.min_free_bytes < 0:
        raise ValueError("invalid numeric preflight argument")
    report = build_report(args)
    output = args.report_output or args.output_dir / "preflight_latest.json"
    atomic_json(output.resolve(), report)
    if args.web_runtime_status:
        atomic_json(args.web_runtime_status.resolve(), report)
    print(json.dumps({
        "ok": report["next_command_allowed"],
        "status": report["status"],
        "passed": report["passed_count"],
        "blocked": report["blocked_count"],
        "report": str(output),
    }))
    return 0 if report["next_command_allowed"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
