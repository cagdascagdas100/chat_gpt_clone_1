#!/usr/bin/env python3
"""Fail-closed runtime environment gate for the strict height_difference_3 chain.

Runs only after exact branch/HEAD and fresh-host-heartbeat gates. It verifies the
actual Python, PowerShell, Git, geospatial libraries, GDAL drivers, PROJ/OSTN15
operation, official source endpoints and minimum free disk. Batch140 additionally
binds the completed preflight to a 15-minute TTL, exact local HEAD and canonical
current-task Git blob before invoking bootstrap 042. It never mutates the legacy
queue, starts a runner, publishes, or writes numeric parcel values.
"""
from __future__ import annotations

import json
import math
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BRANCH = "codex/aays-single-runner-v5-20260706"
TASK_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
BOOTSTRAP_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/042_run_batch135_fresh_origin_wiring_preflight.py"
OUTPUT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json"
GRID_NAME = "uk_os_OSTN15_NTv2_OSGBtoETRS.tif"
HMLR_URL = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
EA_WCS_URL = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
OS_CATALOG_URL = "https://api.os.uk/downloads/v1/products/Terrain50/downloads"
MIN_FREE_BYTES = 2 * 1024 * 1024 * 1024
PREFLIGHT_TTL_SECONDS = 900


def root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(name: str, condition: bool, detail: Any = None) -> dict[str, Any]:
    row = {"name": name, "passed": bool(condition), "detail": detail}
    if not condition:
        raise RuntimeError(f"ENVIRONMENT_GATE_FAILED:{name}:{detail}")
    return row


def resolve_executable(requested: str | None, fallback: str) -> str:
    token = str(requested or fallback).strip()
    found = shutil.which(token)
    if found:
        return str(Path(found).resolve())
    candidate = Path(token)
    if candidate.is_file():
        return str(candidate.resolve())
    raise RuntimeError(f"EXECUTABLE_NOT_FOUND:{token}")


def git(git_executable: str, repo: Path, *args: str) -> str:
    proc = subprocess.run([git_executable, "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr[-1200:]}")
    return proc.stdout.strip()


def main() -> int:
    repo = root(Path(__file__).resolve())
    checks: list[dict[str, Any]] = []

    python_executable = str(Path(sys.executable).resolve())
    checks.append(require("python_executable_exists", Path(python_executable).is_file(), python_executable))
    checks.append(require("python_version_min_3_10", sys.version_info >= (3, 10), platform.python_version()))
    checks.append(require("python_64_bit", sys.maxsize > 2**32, {"machine": platform.machine(), "maxsize": sys.maxsize}))

    git_executable = resolve_executable(os.environ.get("AAYS_GIT_EXE"), "git")
    checks.append(require("git_executable_exists", Path(git_executable).is_file(), git_executable))
    git_version = subprocess.run([git_executable, "--version"], text=True, capture_output=True, check=False)
    checks.append(require("git_invocation_ok", git_version.returncode == 0 and "git version" in git_version.stdout.casefold(), {"exit": git_version.returncode, "stdout": git_version.stdout.strip(), "stderr": git_version.stderr[-500:]}))
    symbolic_branch = git(git_executable, repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    checks.append(require("canonical_symbolic_branch", symbolic_branch == BRANCH, symbolic_branch))

    try:
        import fiona
        import numpy as np
        import pyproj
        import rasterio
        import requests
        import shapely
        from pyproj import CRS, Transformer, datadir, network
        from pyproj.transformer import TransformerGroup
        from rasterio.mask import mask as rasterio_mask
        from shapely import make_valid
    except Exception as exc:
        raise RuntimeError(f"GEOSPATIAL_IMPORT_FAILED:{type(exc).__name__}:{exc}") from exc

    proj_data_dir = str(Path(datadir.get_data_dir()).resolve())
    checks.append(require("proj_data_dir_exists", Path(proj_data_dir).is_dir(), proj_data_dir))
    versions = {
        "python": platform.python_version(),
        "git": git_version.stdout.strip(),
        "numpy": np.__version__,
        "requests": requests.__version__,
        "fiona": fiona.__version__,
        "fiona_gdal": getattr(fiona, "__gdal_version__", None),
        "rasterio": rasterio.__version__,
        "rasterio_gdal": getattr(rasterio, "__gdal_version__", None),
        "shapely": shapely.__version__,
        "pyproj": pyproj.__version__,
        "proj": pyproj.proj_version_str,
    }
    checks.append(require("shapely_make_valid_available", callable(make_valid), versions["shapely"]))
    checks.append(require("rasterio_mask_available", callable(rasterio_mask), versions["rasterio"]))

    gml_mode = str((fiona.supported_drivers or {}).get("GML") or "").lower()
    checks.append(require("fiona_gml_read_driver", "r" in gml_mode, gml_mode))
    with rasterio.Env() as env:
        drivers = env.drivers()
    checks.append(require("rasterio_gtiff_driver", "GTiff" in drivers, drivers.get("GTiff")))
    checks.append(require("rasterio_aaigrid_driver", "AAIGrid" in drivers, drivers.get("AAIGrid")))

    source = CRS.from_epsg(27700)
    target = CRS.from_epsg(4326)
    checks.append(require("epsg_27700_resolves", source.to_epsg() == 27700, source.to_string()))
    checks.append(require("epsg_4326_resolves", target.to_epsg() == 4326, target.to_string()))

    network_before = bool(network.is_network_enabled())
    if not network_before:
        network.set_network_enabled(True)
    network_after = bool(network.is_network_enabled())
    checks.append(require("pyproj_network_enabled", network_after, {"before": network_before, "after": network_after}))

    group = TransformerGroup(source, target, always_xy=True, allow_ballpark=False)
    transformers = []
    for item in group.transformers:
        definition = str(item.definition or "")
        description = str(item.description or "")
        transformers.append({
            "description": description,
            "accuracy_m": item.accuracy,
            "uses_ostn15_grid": GRID_NAME in definition,
            "contains_ballpark": "ballpark" in description.casefold() or "ballpark" in definition.casefold(),
        })
    best = transformers[0] if transformers else None
    checks.append(require("proj_best_available", bool(group.best_available), best))
    checks.append(require("proj_best_uses_ostn15", bool(best and best["uses_ostn15_grid"]), best))
    checks.append(require("proj_best_no_ballpark", bool(best and not best["contains_ballpark"]), best))
    accuracy = float(best["accuracy_m"]) if best and best.get("accuracy_m") is not None else math.inf
    checks.append(require("proj_best_accuracy_le_1m", 0.0 <= accuracy <= 1.0, accuracy))
    transformer = Transformer.from_crs(source, target, always_xy=True, allow_ballpark=False, only_best=True)
    lon, lat = transformer.transform(529200.0, 170000.0)
    checks.append(require("proj_probe_finite", math.isfinite(lon) and math.isfinite(lat), {"lon": lon, "lat": lat}))

    powershell = resolve_executable(os.environ.get("AAYS_POWERSHELL_EXE"), "powershell")
    checks.append(require("windows_powershell_available", Path(powershell).is_file(), powershell))
    ps = subprocess.run([powershell, "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"], text=True, capture_output=True, check=False)
    checks.append(require("powershell_invocation_ok", ps.returncode == 0, {"exit": ps.returncode, "stdout": ps.stdout.strip(), "stderr": ps.stderr[-500:]}))

    disk = shutil.disk_usage(repo)
    checks.append(require("repo_drive_free_space_ge_2gib", disk.free >= MIN_FREE_BYTES, {"free_bytes": disk.free, "required_bytes": MIN_FREE_BYTES}))

    session = requests.Session()
    session.headers.update({"User-Agent": "TerraYield-AAYS/height_difference_3-batch140"})
    hmlr = session.get(HMLR_URL, timeout=30, allow_redirects=True)
    checks.append(require("hmlr_https_reachable", hmlr.status_code == 200, {"status": hmlr.status_code, "final_url": hmlr.url}))
    checks.append(require("hmlr_inspire_page_identity", "INSPIRE" in hmlr.text and "published" in hmlr.text.casefold(), hmlr.text[:300]))

    ea = session.get(EA_WCS_URL, params={"service": "WCS", "request": "GetCapabilities", "version": "2.0.1"}, timeout=30, allow_redirects=True)
    checks.append(require("ea_wcs_https_reachable", ea.status_code == 200, {"status": ea.status_code, "final_url": ea.url}))
    ea_text = ea.text[:200000]
    checks.append(require("ea_wcs_capabilities_identity", "Capabilities" in ea_text and ("CoverageId" in ea_text or "CoverageSummary" in ea_text), ea_text[:300]))

    osr = session.get(OS_CATALOG_URL, params={"area": "GB", "format": "ASCII Grid and GML (Grid)"}, timeout=30, allow_redirects=True)
    checks.append(require("os_terrain50_catalog_https_reachable", osr.status_code == 200, {"status": osr.status_code, "final_url": osr.url}))
    try:
        os_payload = osr.json()
    except Exception as exc:
        raise RuntimeError(f"OS_TERRAIN50_CATALOG_JSON_FAILED:{type(exc).__name__}:{exc}") from exc
    os_text = json.dumps(os_payload, ensure_ascii=False).casefold()
    checks.append(require("os_terrain50_catalog_identity", "terrain50" in os_text or "terrain 50" in os_text, os_text[:500]))
    checks.append(require("os_terrain50_ascii_grid_candidate", "ascii" in os_text and "grid" in os_text, os_text[:500]))

    bootstrap = repo / BOOTSTRAP_REL
    checks.append(require("bootstrap_042_exists", bootstrap.is_file(), str(bootstrap)))
    proc = subprocess.run([python_executable, str(bootstrap)], cwd=repo, text=True, capture_output=True, check=False)
    checks.append(require("bootstrap_042_passed", proc.returncode == 0, {"exit": proc.returncode, "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}))

    completed_at = datetime.now(timezone.utc)
    valid_until = completed_at + timedelta(seconds=PREFLIGHT_TTL_SECONDS)
    canonical_head = git(git_executable, repo, "rev-parse", "HEAD")
    current_task_blob = git(git_executable, repo, "rev-parse", f"HEAD:{TASK_REL}").lower()
    checks.append(require("canonical_head_sha", len(canonical_head) == 40, canonical_head))
    checks.append(require("current_task_blob_sha", len(current_task_blob) == 40, current_task_blob))

    payload = {
        "schema_version": 4,
        "slot_id": "height_difference_3",
        "canonical_branch": BRANCH,
        "purpose": "STRICT_RUNTIME_ENVIRONMENT_EXECUTABLE_IDENTITY_AND_TTL_BOUND_PREFLIGHT_NO_NUMERIC_MEASUREMENT",
        "generated_at_utc": completed_at.isoformat().replace("+00:00", "Z"),
        "valid_until_utc": valid_until.isoformat().replace("+00:00", "Z"),
        "preflight_ttl_seconds": PREFLIGHT_TTL_SECONDS,
        "canonical_head": canonical_head,
        "canonical_current_task_path": TASK_REL,
        "canonical_current_task_blob_sha": current_task_blob,
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "runtime_identity": {
            "python_executable": python_executable,
            "powershell_executable": powershell,
            "powershell_version": ps.stdout.strip(),
            "git_executable": git_executable,
            "git_version": git_version.stdout.strip(),
            "proj_data_dir": proj_data_dir,
            "versions": versions,
        },
        "versions": versions,
        "required_grid": GRID_NAME,
        "pyproj_network_before": network_before,
        "pyproj_network_after": network_after,
        "best_transformer": best,
        "powershell_path": powershell,
        "powershell_version": ps.stdout.strip(),
        "git_executable": git_executable,
        "git_version": git_version.stdout.strip(),
        "python_executable": python_executable,
        "proj_data_dir": proj_data_dir,
        "free_disk_bytes": disk.free,
        "official_endpoint_checks": {"hmlr_status": hmlr.status_code, "ea_wcs_status": ea.status_code, "os_catalog_status": osr.status_code},
        "bootstrap_042_executed": True,
        "bootstrap_042_exit_code": proc.returncode,
        "coordinator_action_performed": False,
        "queue_mutated": False,
        "runner_started": False,
        "numeric_values_written": 0,
        "final_ready": False,
        "fake_data": False,
    }
    out = repo / OUTPUT_REL
    write(out, payload)
    print(json.dumps({"ok": True, "checks": len(checks), "python": python_executable, "powershell": powershell, "git": git_executable, "head": canonical_head, "valid_until_utc": payload["valid_until_utc"], "output": str(out)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
