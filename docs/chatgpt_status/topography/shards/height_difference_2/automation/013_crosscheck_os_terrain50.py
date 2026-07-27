#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import shape

GRID_LETTERS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
ASC_SUFFIXES = {".asc", ".txt"}
SIDECAR_SUFFIXES = {".prj"}
MAX_MEMBER_BYTES = 10_000_000
MAX_SIDECAR_BYTES = 1_000_000
MAX_NESTED_ARCHIVE_BYTES = 50_000_000
MAX_EXTRACTED_BYTES = 200_000_000
MAX_NESTING_DEPTH = 2


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid_100km_letters(easting: float, northing: float) -> str:
    e100k = int(math.floor(easting / 100000))
    n100k = int(math.floor(northing / 100000))
    if not (0 <= e100k <= 6 and 0 <= n100k <= 12):
        raise ValueError("coordinate outside British National Grid")
    l1 = (19 - n100k) - ((19 - n100k) % 5) + ((e100k + 10) // 5)
    l2 = ((19 - n100k) * 5) % 25 + (e100k % 5)
    if not (0 <= l1 < 25 and 0 <= l2 < 25):
        raise ValueError("invalid OS grid letter index")
    return GRID_LETTERS[l1] + GRID_LETTERS[l2]


def _tile_10km(easting: float, northing: float) -> str:
    letters = _grid_100km_letters(easting, northing)
    e10 = int(math.floor((easting % 100000) / 10000))
    n10 = int(math.floor((northing % 100000) / 10000))
    return f"{letters}{e10}{n10}".lower()


def _tiles_for_bounds(bounds: list[float]) -> set[str]:
    minx, miny, maxx, maxy = bounds
    if maxx <= minx or maxy <= miny:
        raise ValueError("invalid polygon bounds")
    start_e = int(math.floor(minx / 10000) * 10000)
    end_e = int(math.floor((maxx - 1e-9) / 10000) * 10000)
    start_n = int(math.floor(miny / 10000) * 10000)
    end_n = int(math.floor((maxy - 1e-9) / 10000) * 10000)
    tiles = set()
    for easting in range(start_e, end_e + 1, 10000):
        for northing in range(start_n, end_n + 1, 10000):
            tiles.add(_tile_10km(easting + 1, northing + 1))
    return tiles


def _load_inputs(hmlr_path: Path, ea_path: Path) -> list[dict[str, Any]]:
    hmlr = json.loads(hmlr_path.read_text(encoding="utf-8-sig"))
    ea = json.loads(ea_path.read_text(encoding="utf-8-sig"))
    if hmlr.get("status") != "THREE_HMLR_EXACT_POLYGONS_MATCHED":
        raise ValueError("HMLR polygon gate incomplete")
    if ea.get("status") != "THREE_EA_DTM1M_POLYGON_SAMPLES_READY":
        raise ValueError("EA DTM 1m gate incomplete")
    ea_rows = {int(row["row_no"]): row for row in ea.get("samples", [])}
    rows = []
    for hmlr_row in hmlr.get("results", []):
        if hmlr_row.get("status") != "MATCHED_EXACT_ID_AND_POINT_INSIDE":
            continue
        match_row = hmlr_row.get("match") or {}
        geometry = match_row.get("geometry_geojson_epsg27700")
        if not isinstance(geometry, dict):
            raise ValueError("HMLR exact match lacks EPSG:27700 geometry")
        row_no = int(hmlr_row["row_no"])
        ea_row = ea_rows.get(row_no)
        if not ea_row:
            raise ValueError(f"EA sample missing for row {row_no}")
        geom = shape(geometry)
        rows.append({
            "row_no": row_no,
            "parcel_id": str(hmlr_row["parcel_id"]),
            "hmlr_inspire_id": str(hmlr_row["hmlr_inspire_id"]),
            "geometry": geometry,
            "bounds": list(map(float, geom.bounds)),
            "ea_median_m_odn": float(ea_row["median_m_odn"]),
        })
    if len(rows) != 3:
        raise ValueError("exactly three joined HMLR/EA rows required")
    return rows


def _member_tile(name: str) -> str | None:
    stem = Path(name).stem.casefold()
    matches = re.findall(r"(?<![a-z])([a-z]{2}\d{2})(?!\d)", stem)
    return matches[-1] if matches else None


def _safe_member_path(name: str) -> Path:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe Terrain50 archive member: {name}")
    return path


def _extract_needed_zip(
    zf: zipfile.ZipFile,
    needed: set[str],
    output_dir: Path,
    found: dict[str, list[Path]],
    *,
    prefix: str,
    container_tile: str | None,
    depth: int,
    total: list[int],
) -> None:
    for info in zf.infolist():
        if info.is_dir():
            continue
        path = _safe_member_path(info.filename)
        suffix = path.suffix.casefold()
        member_tile = _member_tile(path.name) or container_tile
        if suffix == ".zip":
            nested_tile = _member_tile(path.name) or container_tile
            if nested_tile is not None and nested_tile not in needed:
                continue
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
                    _extract_needed_zip(
                        nested,
                        needed,
                        output_dir,
                        found,
                        prefix=f"{prefix}_{path.stem}",
                        container_tile=nested_tile,
                        depth=depth + 1,
                        total=total,
                    )
            except zipfile.BadZipFile as exc:
                raise ValueError(f"Terrain50 nested archive invalid: {info.filename}") from exc
            continue
        if suffix not in ASC_SUFFIXES | SIDECAR_SUFFIXES or member_tile not in needed:
            continue
        limit = MAX_MEMBER_BYTES if suffix in ASC_SUFFIXES else MAX_SIDECAR_BYTES
        if info.file_size <= 0 or info.file_size > limit:
            raise ValueError(f"Terrain50 member size invalid: {info.filename}")
        total[0] += info.file_size
        if total[0] > MAX_EXTRACTED_BYTES:
            raise ValueError("Terrain50 extraction exceeds safety limit")
        target = output_dir / f"{prefix}_{path.name}"
        if target.exists():
            raise ValueError(f"Terrain50 extraction target collision: {target.name}")
        with zf.open(info) as source, target.open("wb") as destination:
            shutil.copyfileobj(source, destination, length=1024 * 1024)
        if suffix in ASC_SUFFIXES:
            found[member_tile].append(target)


def _extract_needed_archive(archive: Path, needed: set[str], output_dir: Path) -> dict[str, list[Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    found: dict[str, list[Path]] = {tile: [] for tile in needed}
    total = [0]
    with zipfile.ZipFile(archive) as zf:
        _extract_needed_zip(
            zf,
            needed,
            output_dir,
            found,
            prefix="outer",
            container_tile=None,
            depth=0,
            total=total,
        )
    missing = sorted(tile for tile, paths in found.items() if not paths)
    if missing:
        raise ValueError(f"Terrain50 archive lacks required 10km tiles: {missing}")
    return found


def _discover_needed_root(root: Path, needed: set[str]) -> dict[str, list[Path]]:
    if not root.is_dir():
        raise NotADirectoryError(root)
    found: dict[str, list[Path]] = {tile: [] for tile in needed}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in ASC_SUFFIXES:
            continue
        tile = _member_tile(path.name)
        if tile in needed:
            found[tile].append(path)
    missing = sorted(tile for tile, paths in found.items() if not paths)
    if missing:
        raise ValueError(f"Terrain50 root lacks required 10km tiles: {missing}")
    return found


def _sample_tiles(paths: list[Path], geometry: dict[str, Any]) -> tuple[np.ndarray, list[dict[str, Any]]]:
    values_parts = []
    files = []
    for path in paths:
        with rasterio.open(path) as dataset:
            if not dataset.crs or dataset.crs.to_epsg() != 27700:
                raise ValueError(f"Terrain50 tile CRS is not EPSG:27700: {path}")
            data, _ = mask(dataset, [geometry], crop=True, all_touched=True, filled=False)
            band = np.ma.asarray(data[0], dtype="float64")
            values = band.compressed()
            values = values[np.isfinite(values)]
            if dataset.nodata is not None:
                values = values[values != float(dataset.nodata)]
            if values.size:
                values_parts.append(values)
            files.append({
                "path": str(path),
                "sha256": _sha256(path),
                "resolution_m": [abs(float(dataset.transform.a)), abs(float(dataset.transform.e))],
            })
    if not values_parts:
        raise ValueError("OS Terrain50 has no all-touched grid values for polygon")
    return np.concatenate(values_parts), files


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hmlr-exact-matches", type=Path, required=True)
    parser.add_argument("--ea-samples", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--terrain50-archive", type=Path)
    source.add_argument("--terrain50-root", type=Path)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        rows = _load_inputs(args.hmlr_exact_matches, args.ea_samples)
        required_tiles = set()
        for row in rows:
            row["required_tiles"] = sorted(_tiles_for_bounds(row["bounds"]))
            required_tiles.update(row["required_tiles"])
        if args.terrain50_archive:
            if not args.terrain50_archive.is_file() or not zipfile.is_zipfile(args.terrain50_archive):
                raise ValueError("Terrain50 archive is missing or not ZIP")
            source_sha256 = _sha256(args.terrain50_archive)
            tile_paths = _extract_needed_archive(
                args.terrain50_archive, required_tiles, args.work_dir / "tiles"
            )
            source_kind = "zip_archive"
            source_path = args.terrain50_archive
        else:
            tile_paths = _discover_needed_root(args.terrain50_root, required_tiles)
            source_sha256 = None
            source_kind = "directory"
            source_path = args.terrain50_root
        results = []
        for row in rows:
            paths = []
            for tile in row["required_tiles"]:
                paths.extend(tile_paths[tile])
            values, files = _sample_tiles(paths, row["geometry"])
            q1, median, q3 = np.quantile(values, [0.25, 0.5, 0.75])
            difference = float(median) - row["ea_median_m_odn"]
            results.append({
                "row_no": row["row_no"],
                "parcel_id": row["parcel_id"],
                "hmlr_inspire_id": row["hmlr_inspire_id"],
                "required_10km_tiles": row["required_tiles"],
                "terrain50_valid_pixel_count_all_touched": int(values.size),
                "terrain50_q1_m_odn": round(float(q1), 3),
                "terrain50_median_m_odn": round(float(median), 3),
                "terrain50_q3_m_odn": round(float(q3), 3),
                "ea_dtm1m_median_m_odn": round(row["ea_median_m_odn"], 3),
                "terrain50_minus_ea_median_m": round(difference, 3),
                "absolute_crosscheck_difference_m": round(abs(difference), 3),
                "crosscheck_role": "secondary coarse 50m grid; no replacement of EA DTM 1m",
                "sampling_method": "polygon all_touched on OS Terrain50 50m grid",
                "source_files": files,
            })
        status = "THREE_OS_TERRAIN50_CROSSCHECKS_READY" if len(results) == 3 else "BLOCKED_THREE_TERRAIN50_CROSSCHECKS_NOT_READY"
        code = 0 if len(results) == 3 else 2
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": status,
            "processing_crs": "EPSG:27700",
            "source_kind": source_kind,
            "source_path": str(source_path),
            "source_archive_sha256": source_sha256,
            "required_10km_tiles": sorted(required_tiles),
            "crosscheck_count": len(results),
            "crosschecks": results,
            "nested_zip_supported": True,
            "prj_sidecars_preserved": True,
            "acceptance_threshold_applied": False,
            "human_review_required_for_difference": True,
            "primary_numeric_source": "Environment Agency LiDAR Composite DTM 1m",
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": "BLOCKED_OS_TERRAIN50_CROSSCHECK",
            "error": f"{type(exc).__name__}: {exc}",
            "crosscheck_count": 0,
            "acceptance_threshold_applied": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 2
    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"], "crosschecks": payload.get("crosscheck_count", 0)}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
