#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable

ASCII_SUFFIXES = {".asc", ".txt"}
SIDECAR_SUFFIXES = {".prj"}
MAX_MEMBER_BYTES = 20_000_000
MAX_SIDECAR_BYTES = 1_000_000
MAX_NESTED_ARCHIVE_BYTES = 50_000_000
MAX_EXTRACTED_BYTES = 600_000_000
MAX_NESTING_DEPTH = 2
OS_TERRAIN50_GRID_RMSE_M = 4.0
EA_LIDAR_DTM_RMSE_M = 0.15
CONSERVATIVE_ONE_RMSE_SUM_M = round(OS_TERRAIN50_GRID_RMSE_M + EA_LIDAR_DTM_RMSE_M, 2)
CONSERVATIVE_TWO_RMSE_SUM_M = round(2.0 * (OS_TERRAIN50_GRID_RMSE_M + EA_LIDAR_DTM_RMSE_M), 2)


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {"command": command, "exit_code": process.returncode, "stdout": process.stdout[-8000:], "stderr": process.stderr[-8000:]}


def _member_tile(name: str) -> str | None:
    stem = Path(name).stem.casefold()
    matches = re.findall(r"(?<![a-z])([a-z]{2}\d{2})(?!\d)", stem)
    return matches[-1] if matches else None


def _safe_member_path(name: str) -> Path:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe Terrain50 archive member: {name}")
    return path


def _safe_extract_zip(
    zf: zipfile.ZipFile,
    root: Path,
    *,
    prefix: str,
    depth: int,
    total: list[int],
    container_tile: str | None,
) -> list[str]:
    written: list[str] = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        path = _safe_member_path(info.filename)
        suffix = path.suffix.casefold()
        member_tile = _member_tile(path.name) or container_tile
        if suffix in ASCII_SUFFIXES | SIDECAR_SUFFIXES:
            if member_tile is None:
                continue
            limit = MAX_MEMBER_BYTES if suffix in ASCII_SUFFIXES else MAX_SIDECAR_BYTES
            if info.file_size <= 0 or info.file_size > limit:
                raise ValueError(f"Terrain50 member size invalid: {info.filename}")
            total[0] += info.file_size
            if total[0] > MAX_EXTRACTED_BYTES:
                raise ValueError("Terrain50 extracted data exceeds safety limit")
            target = root / f"{prefix}_{path.name}"
            if target.exists():
                raise ValueError(f"Terrain50 extraction target collision: {target.name}")
            with zf.open(info) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination, length=1024 * 1024)
            if suffix in ASCII_SUFFIXES:
                written.append(str(target))
            continue
        if suffix != ".zip":
            continue
        nested_tile = _member_tile(path.name) or container_tile
        if depth >= MAX_NESTING_DEPTH:
            raise ValueError(f"Terrain50 nested archive depth exceeds limit: {info.filename}")
        if info.file_size <= 0 or info.file_size > MAX_NESTED_ARCHIVE_BYTES:
            raise ValueError(f"Terrain50 nested archive size invalid: {info.filename}")
        with zf.open(info) as source:
            payload = source.read(MAX_NESTED_ARCHIVE_BYTES + 1)
        if len(payload) != info.file_size or len(payload) > MAX_NESTED_ARCHIVE_BYTES:
            raise ValueError(f"Terrain50 nested archive read invalid: {info.filename}")
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as nested:
                written.extend(
                    _safe_extract_zip(
                        nested,
                        root,
                        prefix=f"{prefix}_{path.stem}",
                        depth=depth + 1,
                        total=total,
                        container_tile=nested_tile,
                    )
                )
        except zipfile.BadZipFile as exc:
            raise ValueError(f"Terrain50 nested archive invalid: {info.filename}") from exc
    return written


def _safe_extract_archives(archives: list[Path], root: Path) -> list[str]:
    root.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    total = [0]
    for archive_index, archive in enumerate(archives, start=1):
        if not archive.is_file() or not zipfile.is_zipfile(archive):
            raise ValueError(f"Terrain50 archive invalid: {archive}")
        with zipfile.ZipFile(archive) as zf:
            written.extend(
                _safe_extract_zip(
                    zf,
                    root,
                    prefix=f"a{archive_index}",
                    depth=0,
                    total=total,
                    container_tile=None,
                )
            )
    if not written:
        raise ValueError("no Terrain50 ASCII grid files extracted")
    return written


def _apply_accuracy_screening(payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    crosschecks = payload.get("crosschecks")
    if payload.get("status") != "THREE_OS_TERRAIN50_CROSSCHECKS_READY" or not isinstance(crosschecks, list) or len(crosschecks) != 3:
        return payload, False
    exact_rows = sorted(int(row.get("row_no", -1)) for row in crosschecks)
    if exact_rows != [30762, 46142, 61522]:
        raise ValueError(f"Terrain50 crosscheck exact row set mismatch: {exact_rows}")

    outside_two = []
    for row in crosschecks:
        delta = float(row["absolute_crosscheck_difference_m"])
        if delta <= CONSERVATIVE_ONE_RMSE_SUM_M:
            tier = "WITHIN_CONSERVATIVE_ONE_RMSE_SUM"
        elif delta <= CONSERVATIVE_TWO_RMSE_SUM_M:
            tier = "OUTSIDE_ONE_WITHIN_TWO_RMSE_SUM_REVIEW"
        else:
            tier = "OUTSIDE_CONSERVATIVE_TWO_RMSE_SUM_BLOCK"
            outside_two.append(int(row["row_no"]))
        row["accuracy_screening_tier"] = tier
        row["os_terrain50_grid_rmse_m"] = OS_TERRAIN50_GRID_RMSE_M
        row["ea_lidar_dtm_rmse_m"] = EA_LIDAR_DTM_RMSE_M
        row["conservative_one_rmse_sum_m"] = CONSERVATIVE_ONE_RMSE_SUM_M
        row["conservative_two_rmse_sum_m"] = CONSERVATIVE_TWO_RMSE_SUM_M
        row["screening_is_not_confidence_interval"] = True

    payload["accuracy_screening_contract"] = {
        "os_terrain50_grid_rmse_m": OS_TERRAIN50_GRID_RMSE_M,
        "ea_lidar_dtm_rmse_m": EA_LIDAR_DTM_RMSE_M,
        "conservative_one_rmse_sum_m": CONSERVATIVE_ONE_RMSE_SUM_M,
        "conservative_two_rmse_sum_m": CONSERVATIVE_TWO_RMSE_SUM_M,
        "method": "linear_sum_of_publisher_RMSE_values_for_conservative_screening",
        "statistical_independence_assumed": False,
        "confidence_interval_claimed": False,
        "automatic_ready_requires_all_rows_within_two_rmse_sum": True,
        "primary_source_remains_ea_dtm1m": True,
        "terrain50_is_secondary_coarse_crosscheck": True,
    }
    payload["accuracy_screening_outside_two_rmse_rows"] = outside_two
    payload["accuracy_screening_passed"] = not outside_two
    payload["human_review_required_for_difference"] = True
    if outside_two:
        payload["status"] = "BLOCKED_TERRAIN50_CROSSCHECK_OUTSIDE_CONSERVATIVE_TWO_RMSE_SUM"
        return payload, False
    payload["status"] = "THREE_OS_TERRAIN50_CROSSCHECKS_READY"
    return payload, True


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--hmlr-exact-matches", type=Path, required=True)
    parser.add_argument("--ea-samples", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--terrain50-archive", type=Path)
    parser.add_argument("--terrain50-root", type=Path)
    args = parser.parse_args(argv)
    stages: list[dict[str, Any]] = []
    try:
        repo_root = args.repo_root.resolve()
        automation = repo_root / "docs/chatgpt_status/topography/shards/height_difference_2/automation"
        resolver = automation / "015_resolve_os_terrain50_downloads.py"
        crosschecker = automation / "013_crosscheck_os_terrain50.py"
        if not resolver.is_file() or not crosschecker.is_file():
            raise FileNotFoundError("Terrain50 resolver or crosschecker missing")
        archive = args.terrain50_archive or (Path(os.environ["AAYS_TERRAIN50_ARCHIVE"]) if os.environ.get("AAYS_TERRAIN50_ARCHIVE") else None)
        root = args.terrain50_root or (Path(os.environ["AAYS_TERRAIN50_ROOT"]) if os.environ.get("AAYS_TERRAIN50_ROOT") else None)
        if archive:
            source_kind, source_value = "configured_archive", archive
        elif root:
            source_kind, source_value = "configured_root", root
        else:
            resolver_output_dir = args.output_dir / "downloads"
            resolver_manifest = args.output_dir / "terrain50_download_manifest.json"
            resolver_stage = _run([sys.executable, str(resolver), "--hmlr-exact-matches", str(args.hmlr_exact_matches), "--output-dir", str(resolver_output_dir), "--output", str(resolver_manifest)], repo_root)
            resolver_stage["stage"] = "OS_DOWNLOADS_API_TERRAIN50_RESOLUTION"
            stages.append(resolver_stage)
            if resolver_stage["exit_code"] != 0:
                raise RuntimeError("OS Downloads API Terrain50 resolution failed")
            manifest = json.loads(resolver_manifest.read_text(encoding="utf-8-sig"))
            archives = [Path(value) for value in manifest.get("archive_paths", [])]
            if not archives:
                raise ValueError("Terrain50 resolver returned no archives")
            extracted_root = args.output_dir / "resolved_ascii_root"
            extracted = _safe_extract_archives(archives, extracted_root)
            stages.append({"stage": "TERRAIN50_MULTI_ARCHIVE_SAFE_EXTRACTION", "exit_code": 0, "archive_count": len(archives), "ascii_grid_file_count": len(extracted), "root": str(extracted_root), "nested_zip_supported": True, "prj_sidecars_preserved": True})
            source_kind, source_value = "os_downloads_api_resolved_root", extracted_root
        command = [sys.executable, str(crosschecker), "--hmlr-exact-matches", str(args.hmlr_exact_matches), "--ea-samples", str(args.ea_samples), "--work-dir", str(args.output_dir / "crosscheck_work"), "--output", str(args.output)]
        if source_kind == "configured_archive":
            command.extend(["--terrain50-archive", str(source_value)])
        else:
            command.extend(["--terrain50-root", str(source_value)])
        crosscheck_stage = _run(command, repo_root)
        crosscheck_stage["stage"] = "OS_TERRAIN50_POLYGON_CROSSCHECK"
        stages.append(crosscheck_stage)
        if crosscheck_stage["exit_code"] != 0:
            raise RuntimeError("OS Terrain50 polygon crosscheck failed")
        payload = json.loads(args.output.read_text(encoding="utf-8-sig"))
        payload, screening_passed = _apply_accuracy_screening(payload)
        payload["source_resolution_kind"] = source_kind
        payload["preparation_stages"] = stages
        payload["os_downloads_api_used"] = source_kind == "os_downloads_api_resolved_root"
        _write(args.output, payload)
        code = 0 if screening_passed else 2
    except Exception as exc:
        payload = {"schema_version": 2, "slot_id": "height_difference_2", "status": "BLOCKED_TERRAIN50_PREPARATION_OR_CROSSCHECK", "error": f"{type(exc).__name__}: {exc}", "preparation_stages": stages, "crosscheck_count": 0, "accuracy_screening_passed": False, "accuracy_screening_contract": {"os_terrain50_grid_rmse_m": OS_TERRAIN50_GRID_RMSE_M, "ea_lidar_dtm_rmse_m": EA_LIDAR_DTM_RMSE_M, "conservative_one_rmse_sum_m": CONSERVATIVE_ONE_RMSE_SUM_M, "conservative_two_rmse_sum_m": CONSERVATIVE_TWO_RMSE_SUM_M, "statistical_independence_assumed": False, "confidence_interval_claimed": False}, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
        _write(args.output, payload)
        code = 2
    print(json.dumps({"ok": code == 0, "status": payload.get("status"), "crosschecks": payload.get("crosscheck_count", 0), "accuracy_screening_passed": payload.get("accuracy_screening_passed", False), "two_rmse_sum_m": CONSERVATIVE_TWO_RMSE_SUM_M}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
