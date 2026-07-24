#!/usr/bin/env python3
"""Extract and validate exact OS Terrain 50 ASCII tiles for matched parcels.

Only the deterministic BNG 10km tile key is accepted. The ASCII header must be
200x200 with 50m cells and southwest coordinates matching the tile. No nearest
or neighbouring tile substitution is allowed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid_letters(easting: float, northing: float) -> str:
    e100k = int(easting) // 100000
    n100k = int(northing) // 100000
    if not (0 <= e100k <= 6 and 0 <= n100k <= 12):
        raise ValueError("coordinate outside British National Grid letter extent")
    l1 = (19 - n100k) - (19 - n100k) % 5 + (e100k + 10) // 5
    l2 = (19 - n100k) * 5 % 25 + e100k % 5
    if l1 > 7:
        l1 += 1
    if l2 > 7:
        l2 += 1
    return chr(l1 + 65) + chr(l2 + 65)


def _tile(easting: float, northing: float) -> dict[str, Any]:
    letters = _grid_letters(easting, northing)
    e10 = (int(easting) % 100000) // 10000
    n10 = (int(northing) % 100000) // 10000
    sw_e = (int(easting) // 10000) * 10000
    sw_n = (int(northing) // 10000) * 10000
    return {"key": f"{letters}{e10}{n10}", "sw_e": sw_e, "sw_n": sw_n}


def _load_matches(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    values = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(values, list) or not values:
        raise ValueError("matched manifest has no results")
    result = []
    for row in values:
        if row.get("status") != "MATCHED":
            raise ValueError("all candidates must be HMLR matched")
        result.append(dict(row))
    return result


def _header(path: Path) -> dict[str, float]:
    result: dict[str, float] = {}
    recognized = {"ncols", "nrows", "xllcorner", "xllcenter", "yllcorner", "yllcenter", "cellsize", "nodata_value"}
    with path.open("r", encoding="utf-8-sig", errors="strict") as handle:
        for _ in range(8):
            line = handle.readline()
            if not line:
                break
            parts = line.split()
            if len(parts) < 2 or parts[0].casefold() not in recognized:
                break
            result[parts[0].casefold()] = float(parts[1])
    return result


def _validate(path: Path, tile: dict[str, Any]) -> dict[str, Any]:
    header = _header(path)
    required = {"ncols", "nrows", "cellsize"}
    if not required.issubset(header):
        raise ValueError(f"ASCII grid missing required header fields: {path}")
    if int(header["ncols"]) != 200 or int(header["nrows"]) != 200 or abs(header["cellsize"] - 50.0) > 1e-9:
        raise ValueError(f"Terrain50 grid schema mismatch: {header}")
    x_value = header.get("xllcorner", header.get("xllcenter"))
    y_value = header.get("yllcorner", header.get("yllcenter"))
    if x_value is None or y_value is None:
        raise ValueError("ASCII grid lacks southwest origin")
    expected_x = float(tile["sw_e"])
    expected_y = float(tile["sw_n"])
    if "xllcenter" in header:
        expected_x += 25.0
    if "yllcenter" in header:
        expected_y += 25.0
    if abs(x_value - expected_x) > 0.01 or abs(y_value - expected_y) > 0.01:
        raise ValueError(f"Terrain50 tile origin mismatch for {tile['key']}: {(x_value, y_value)} vs {(expected_x, expected_y)}")
    return header


def _candidate_files(sources: list[Path], key: str, temp_root: Path) -> list[Path]:
    pattern = re.compile(rf"(^|[^a-z0-9]){re.escape(key.casefold())}([^a-z0-9]|$)")
    found: list[Path] = []
    for source in sources:
        if source.is_dir():
            for path in source.rglob("*"):
                if path.is_file() and path.suffix.casefold() == ".asc" and pattern.search(path.stem.casefold()):
                    found.append(path.resolve())
        elif source.is_file() and source.suffix.casefold() == ".asc":
            if pattern.search(source.stem.casefold()):
                found.append(source.resolve())
        elif source.is_file() and zipfile.is_zipfile(source):
            with zipfile.ZipFile(source) as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    suffix = Path(info.filename).suffix.casefold()
                    if suffix == ".asc" and pattern.search(Path(info.filename).stem.casefold()):
                        target_dir = temp_root / hashlib.sha256(str(source).encode()).hexdigest()[:12]
                        target_dir.mkdir(parents=True, exist_ok=True)
                        target = target_dir / Path(info.filename).name
                        with archive.open(info) as input_handle, target.open("wb") as output_handle:
                            while chunk := input_handle.read(1024 * 1024):
                                output_handle.write(chunk)
                        found.append(target)
                        continue
                    if suffix != ".zip" or not pattern.search(Path(info.filename).stem.casefold()):
                        continue
                    # Official GB Terrain50 is an outer ZIP of per-tile ZIPs.
                    # Open only the exact deterministic BNG tile candidate.
                    with archive.open(info) as nested_handle:
                        nested_payload = nested_handle.read()
                    with zipfile.ZipFile(io.BytesIO(nested_payload)) as nested:
                        for nested_info in nested.infolist():
                            if nested_info.is_dir() or Path(nested_info.filename).suffix.casefold() != ".asc":
                                continue
                            if not pattern.search(Path(nested_info.filename).stem.casefold()):
                                continue
                            target_dir = temp_root / hashlib.sha256(
                                f"{source}!{info.filename}".encode()
                            ).hexdigest()[:12]
                            target_dir.mkdir(parents=True, exist_ok=True)
                            target = target_dir / Path(nested_info.filename).name
                            with nested.open(nested_info) as input_handle, target.open("wb") as output_handle:
                                while chunk := input_handle.read(1024 * 1024):
                                    output_handle.write(chunk)
                            found.append(target)
        else:
            raise FileNotFoundError(source)
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in found:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matched-manifest", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    matches = _load_matches(args.matched_manifest)
    temp_root = args.output_dir / "_extracted"
    tile_rows: dict[str, dict[str, Any]] = {}
    candidate_records = []
    for row in matches:
        tile = _tile(float(row["bng_easting"]), float(row["bng_northing"]))
        tile_rows.setdefault(tile["key"], tile)
        candidate_records.append({"row_no": row.get("row_no"), "parcel_id": row.get("parcel_id"), "tile_key": tile["key"]})

    records = []
    raster_paths = []
    for key, tile in sorted(tile_rows.items()):
        candidates = _candidate_files(args.source, key, temp_root)
        valid = []
        errors = []
        for path in candidates:
            try:
                header = _validate(path, tile)
                valid.append((path, header))
            except Exception as exc:
                errors.append(f"{path}: {type(exc).__name__}: {exc}")
        if len(valid) != 1:
            raise ValueError(f"expected exactly one valid Terrain50 tile {key}; valid={len(valid)} errors={errors}")
        source_path, header = valid[0]
        target = args.output_dir / "terrain50" / f"{key.casefold()}.asc"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source_path.read_bytes())
        records.append(
            {
                "tile_key": key,
                "path": str(target),
                "sha256": _sha256(target),
                "size_bytes": target.stat().st_size,
                "header": header,
                "expected_bbox_epsg27700": [tile["sw_e"], tile["sw_n"], tile["sw_e"] + 10000, tile["sw_n"] + 10000],
            }
        )
        raster_paths.append(str(target))

    manifest = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "status": "READY",
        "source_paths": [str(path) for path in args.source],
        "candidate_count": len(candidate_records),
        "unique_tile_count": len(records),
        "candidate_tiles": candidate_records,
        "records": records,
        "raster_paths": raster_paths,
        "nearest_or_neighbour_tile_substitution_used": False,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    output = args.output_dir / "terrain50_source_manifest.json"
    _write(output, manifest)
    print(json.dumps({"ok": True, "manifest": str(output), "tiles": len(records)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

