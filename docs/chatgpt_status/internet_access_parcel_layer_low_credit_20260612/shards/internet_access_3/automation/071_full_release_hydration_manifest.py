#!/usr/bin/env python3
"""Hydrate current OS and ONS UPRN release packages with resumable downloads.

This worker is source-evidence only. It does not write business rows, promote parcel
relations, or infer parcel-to-address links.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
DEFAULT_OS_RESOLUTION = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/041_os_opendata_download_resolution_latest.json"
DEFAULT_ONS_DISCOVERY = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/015_ons_uprn_arcgis_release_discovery_latest.json"
DEFAULT_REGISTRY = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/013_full_release_hydration_uprn_join_registry_latest.json"
DEFAULT_RUNNER_OUTPUT = "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/050_full_release_hydration_manifest_latest.json"
DEFAULT_WEB_OUTPUT = "england_map_web/data/aays_21_slots/internet_access_3/full_release_hydration_manifest_latest.json"
ARCGIS_DATA = "https://www.arcgis.com/sharing/rest/content/items/{item_id}/data"
HEX32 = re.compile(r"^[0-9a-fA-F]{32}$")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--os-resolution", default=DEFAULT_OS_RESOLUTION)
    p.add_argument("--ons-discovery", default=DEFAULT_ONS_DISCOVERY)
    p.add_argument("--registry", default=DEFAULT_REGISTRY)
    p.add_argument("--runner-output", default=DEFAULT_RUNNER_OUTPUT)
    p.add_argument("--web-output", default=DEFAULT_WEB_OUTPUT)
    p.add_argument("--cache-dir", type=Path, default=Path(tempfile.gettempdir()) / "aays_internet_access_3_release_cache")
    p.add_argument("--chunk-size", type=int, default=8 * 1024 * 1024)
    p.add_argument("--timeout", type=int, default=180)
    p.add_argument("--retries", type=int, default=4)
    return p.parse_args()


def repo_root(explicit: Path | None) -> Path:
    if explicit:
        root = explicit.expanduser().resolve()
        if not (root / "docs").exists() or not (root / "england_map_web").exists():
            raise FileNotFoundError(f"invalid repo root: {root}")
        return root
    for candidate in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (candidate / "docs").exists() and (candidate / "england_map_web").exists():
            return candidate
    raise FileNotFoundError("repository root not found")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return cleaned[:180] or "package"


def file_hash(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_package(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        prefix = handle.read(8)
    if prefix.startswith(b"PK") and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as archive:
            bad = archive.testzip()
            members = [item for item in archive.infolist() if not item.is_dir()]
            return {
                "media_type": "application/zip",
                "zip_integrity_passed": bad is None,
                "zip_bad_member": bad,
                "zip_member_count": len(members),
                "zip_uncompressed_bytes": sum(int(item.file_size) for item in members),
                "zip_csv_member_count": sum(1 for item in members if item.filename.lower().endswith(".csv")),
            }
    text_like = not prefix.startswith((b"\x00", b"\x1f\x8b"))
    return {
        "media_type": "text/csv-or-text" if text_like else "application/octet-stream",
        "zip_integrity_passed": None,
        "zip_bad_member": None,
        "zip_member_count": 0,
        "zip_uncompressed_bytes": 0,
        "zip_csv_member_count": 0,
    }


def build_packages(os_resolution: dict[str, Any], ons_discovery: dict[str, Any]) -> list[dict[str, Any]]:
    blockers: list[str] = []
    if os_resolution.get("state") != "resolved":
        blockers.append("OS_DOWNLOAD_RESOLUTION_NOT_RESOLVED")
    if ons_discovery.get("state") != "runtime_validation_passed":
        blockers.append("ONS_RELEASE_DISCOVERY_NOT_RESOLVED")
    if blockers:
        raise ValueError(";".join(blockers))
    selected = os_resolution.get("selected") or {}
    os_specs = [
        ("os_open_uprn", selected.get("open_uprn")),
        ("os_lids_uprn_topographic_area", selected.get("uprn_topographic_area")),
    ]
    packages: list[dict[str, Any]] = []
    for package_id, item in os_specs:
        if not isinstance(item, dict):
            raise ValueError(f"missing OS package: {package_id}")
        md5 = str(item.get("md5") or "").lower()
        if not HEX32.fullmatch(md5):
            raise ValueError(f"invalid OS md5: {package_id}")
        packages.append({
            "package_id": package_id,
            "authority": "Ordnance Survey",
            "product_id": "OpenUPRN" if package_id == "os_open_uprn" else "LIDS",
            "title": item.get("fileName") or package_id,
            "download_url": item.get("url"),
            "expected_size": int(item.get("size") or 0),
            "expected_md5": md5,
            "release_label": "June 2026",
        })
    products = ons_discovery.get("products") or []
    by_product = {str(item.get("product_id")): item for item in products if isinstance(item, dict)}
    for product_id in ("nsul", "onsud"):
        product = by_product.get(product_id) or {}
        item = product.get("selected") or {}
        item_id = str(item.get("id") or "")
        if not item_id:
            raise ValueError(f"missing ONS selected item: {product_id}")
        packages.append({
            "package_id": product_id,
            "authority": "Office for National Statistics",
            "product_id": product_id.upper(),
            "title": item.get("title") or product_id,
            "download_url": ARCGIS_DATA.format(item_id=item_id),
            "expected_size": int(item.get("size") or 0),
            "expected_md5": None,
            "release_label": ons_discovery.get("release_label") or "May 2026",
            "arcgis_item_id": item_id,
        })
    if len(packages) != 4:
        raise ValueError(f"release package count mismatch: {len(packages)}")
    return packages


def download_resumable(spec: dict[str, Any], cache_dir: Path, chunk_size: int, timeout: int, retries: int) -> dict[str, Any]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    extension = ".zip" if spec["package_id"].startswith("os_") else ".download"
    final_path = cache_dir / (safe_name(f"{spec['package_id']}_{spec['release_label']}") + extension)
    partial_path = final_path.with_suffix(final_path.suffix + ".part")
    expected_size = int(spec.get("expected_size") or 0)
    if final_path.exists() and (not expected_size or final_path.stat().st_size == expected_size):
        cache_hit = True
    else:
        cache_hit = False
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            current = partial_path.stat().st_size if partial_path.exists() else 0
            headers = {"User-Agent": "TerraYield-AAYS-internet-access-3/15", "Accept": "*/*"}
            if current:
                headers["Range"] = f"bytes={current}-"
            request = urllib.request.Request(str(spec["download_url"]), headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    status = int(getattr(response, "status", response.getcode()))
                    content_range = response.headers.get("Content-Range")
                    append = current > 0 and status == 206 and bool(content_range and content_range.startswith(f"bytes {current}-"))
                    mode = "ab" if append else "wb"
                    with partial_path.open(mode) as handle:
                        while True:
                            block = response.read(max(64 * 1024, chunk_size))
                            if not block:
                                break
                            handle.write(block)
                if expected_size and partial_path.stat().st_size != expected_size:
                    raise IOError(f"size mismatch {partial_path.stat().st_size}!={expected_size}")
                os.replace(partial_path, final_path)
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                time.sleep(min(2 ** (attempt - 1), 8))
        if last_error is not None:
            raise last_error
    actual_size = final_path.stat().st_size
    md5 = file_hash(final_path, "md5")
    sha256 = file_hash(final_path, "sha256")
    expected_md5 = spec.get("expected_md5")
    md5_ok = expected_md5 is None or md5.lower() == str(expected_md5).lower()
    size_ok = expected_size <= 0 or actual_size == expected_size
    inspection = inspect_package(final_path)
    return {
        **spec,
        "cache_path": str(final_path),
        "cache_hit": cache_hit,
        "bytes_hydrated": actual_size,
        "actual_md5": md5,
        "actual_sha256": sha256,
        "size_verified": size_ok,
        "md5_verified": md5_ok,
        **inspection,
    }


def main() -> int:
    options = parse_args()
    root = repo_root(options.repo_root)
    registry = load_json(root / options.registry)
    os_resolution = load_json(root / options.os_resolution)
    ons_discovery = load_json(root / options.ons_discovery)
    packages = build_packages(os_resolution, ons_discovery)
    hydrated: list[dict[str, Any]] = []
    blockers: list[str] = []
    for spec in packages:
        try:
            result = download_resumable(spec, options.cache_dir.expanduser().resolve(), options.chunk_size, options.timeout, options.retries)
            hydrated.append(result)
            if not result["size_verified"]:
                blockers.append(f"{spec['package_id'].upper()}_SIZE_MISMATCH")
            if not result["md5_verified"]:
                blockers.append(f"{spec['package_id'].upper()}_MD5_MISMATCH")
            if result["media_type"] == "application/zip" and not result["zip_integrity_passed"]:
                blockers.append(f"{spec['package_id'].upper()}_ZIP_INTEGRITY_FAILED")
        except Exception as exc:
            blockers.append(f"{spec['package_id'].upper()}_HYDRATION_ERROR:{type(exc).__name__}:{exc}")
    complete = len(hydrated) == 4 and not blockers
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    summary = {
        "schema_version": 1,
        "task_id": "aays1-internet-access-3-full-release-hydration-20260722",
        "slot_id": SLOT_ID,
        "state": "runtime_validation_passed" if complete else "blocked",
        "updated_at": now,
        "release_contract_sha256": hashlib.sha256(json.dumps(registry.get("release_contract"), sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "packages_expected": 4,
        "packages_hydrated": len(hydrated),
        "packages": hydrated,
        "download_bytes_hydrated": sum(int(item.get("bytes_hydrated") or 0) for item in hydrated),
        "source_checks_executed": 8,
        "validation": {"passed": complete, "blockers": blockers},
        "parcel_relations_promoted": 0,
        "confidence_uplifts": 0,
        "actual_business_data_rows_written": 0,
        "output_semantics": "FULL_OFFICIAL_RELEASE_BYTE_HYDRATION_AND_CHECKSUM_MANIFEST_ONLY",
        "first_unverified_step_after_run": "STREAM_OS_OPEN_UPRN_AND_NSUL_ONSUD_THEN_VALIDATE_EXACT_SAME_UPRN_POSTCODE_JOINS",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    atomic_json(root / options.runner_output, summary)
    atomic_json(root / options.web_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if complete else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id": SLOT_ID, "state": "exception", "error_type": type(exc).__name__, "error": str(exc), "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}, ensure_ascii=False, indent=2), file=__import__("sys").stderr)
        raise
