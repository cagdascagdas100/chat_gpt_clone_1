#!/usr/bin/env python3
"""Extract and validate exact OS Terrain 50 ASCII tiles for matched parcels.

Only the deterministic BNG 10 km tile key is accepted. Archive members are read
with explicit size limits into an ephemeral staging directory. A canonical tile
is replaced only after the staged copy passes the full header/origin validation.
No nearest or neighbouring tile substitution is allowed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Iterable

MAX_ASCII_MEMBER_BYTES = 64 * 1024 * 1024
MAX_NESTED_ZIP_BYTES = 128 * 1024 * 1024
COPY_CHUNK_BYTES = 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(COPY_CHUNK_BYTES), b""):
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
    result: list[dict[str, Any]] = []
    for row in values:
        if not isinstance(row, dict) or row.get("status") != "MATCHED":
            raise ValueError("all candidates must be HMLR matched")
        result.append(dict(row))
    return result


def _header(path: Path) -> dict[str, float]:
    result: dict[str, float] = {}
    recognized = {
        "ncols",
        "nrows",
        "xllcorner",
        "xllcenter",
        "yllcorner",
        "yllcenter",
        "cellsize",
        "nodata_value",
    }
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
    if path.stat().st_size <= 0 or path.stat().st_size > MAX_ASCII_MEMBER_BYTES:
        raise ValueError(f"Terrain50 ASCII size outside safety bounds: {path}")
    header = _header(path)
    required = {"ncols", "nrows", "cellsize"}
    if not required.issubset(header):
        raise ValueError(f"ASCII grid missing required header fields: {path}")
    if (
        int(header["ncols"]) != 200
        or int(header["nrows"]) != 200
        or abs(header["cellsize"] - 50.0) > 1e-9
    ):
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
        raise ValueError(
            f"Terrain50 tile origin mismatch for {tile['key']}: "
            f"{(x_value, y_value)} vs {(expected_x, expected_y)}"
        )
    return header


def _safe_member_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    if normalized.startswith("/") or ".." in parts:
        raise ValueError(f"unsafe archive path: {name}")
    base = Path(normalized).name
    if not base:
        raise ValueError(f"empty archive member name: {name}")
    return base


def _bounded_member_bytes(
    archive: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    maximum: int,
) -> bytes:
    if info.file_size < 0 or info.file_size > maximum:
        raise ValueError(
            f"archive member size outside safety bounds: {info.filename}: "
            f"{info.file_size}"
        )
    with archive.open(info) as handle:
        payload = handle.read(maximum + 1)
    if len(payload) > maximum or len(payload) != info.file_size:
        raise ValueError(
            f"archive member size mismatch: {info.filename}: "
            f"declared={info.file_size} actual={len(payload)}"
        )
    return payload


def _stage_bytes(payload: bytes, temp_root: Path, identity: str, name: str) -> Path:
    if not payload or len(payload) > MAX_ASCII_MEMBER_BYTES:
        raise ValueError("staged Terrain50 ASCII payload outside safety bounds")
    target_dir = temp_root / hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / name
    if target.exists():
        raise ValueError(f"duplicate staged Terrain50 target: {target}")
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{name}_",
        suffix=".stage.tmp",
        dir=target_dir,
    )
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(target)
        return target
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _candidate_files(sources: list[Path], key: str, temp_root: Path) -> list[Path]:
    pattern = re.compile(
        rf"(^|[^a-z0-9]){re.escape(key.casefold())}([^a-z0-9]|$)"
    )
    found: list[Path] = []
    for source in sources:
        if source.is_dir():
            for path in source.rglob("*"):
                if (
                    path.is_file()
                    and path.suffix.casefold() == ".asc"
                    and pattern.search(path.stem.casefold())
                ):
                    found.append(path.resolve())
            continue
        if source.is_file() and source.suffix.casefold() == ".asc":
            if pattern.search(source.stem.casefold()):
                found.append(source.resolve())
            continue
        if not source.is_file():
            raise FileNotFoundError(source)
        if not zipfile.is_zipfile(source):
            raise ValueError(f"Terrain50 source is not an ASCII file or ZIP: {source}")

        with zipfile.ZipFile(source) as archive:
            seen_outer: set[str] = set()
            for info in archive.infolist():
                if info.is_dir():
                    continue
                member_name = _safe_member_name(info.filename)
                folded = info.filename.replace("\\", "/").casefold()
                if folded in seen_outer:
                    raise ValueError(f"duplicate outer archive member: {info.filename}")
                seen_outer.add(folded)
                suffix = Path(member_name).suffix.casefold()
                if suffix == ".asc" and pattern.search(Path(member_name).stem.casefold()):
                    payload = _bounded_member_bytes(
                        archive, info, MAX_ASCII_MEMBER_BYTES
                    )
                    found.append(
                        _stage_bytes(
                            payload,
                            temp_root,
                            f"{source.resolve()}!{info.filename}",
                            member_name,
                        )
                    )
                    continue
                if suffix != ".zip" or not pattern.search(
                    Path(member_name).stem.casefold()
                ):
                    continue

                nested_payload = _bounded_member_bytes(
                    archive, info, MAX_NESTED_ZIP_BYTES
                )
                with zipfile.ZipFile(io.BytesIO(nested_payload)) as nested:
                    seen_inner: set[str] = set()
                    for nested_info in nested.infolist():
                        if nested_info.is_dir():
                            continue
                        inner_name = _safe_member_name(nested_info.filename)
                        inner_folded = nested_info.filename.replace("\\", "/").casefold()
                        if inner_folded in seen_inner:
                            raise ValueError(
                                f"duplicate nested archive member: {nested_info.filename}"
                            )
                        seen_inner.add(inner_folded)
                        if Path(inner_name).suffix.casefold() != ".asc":
                            continue
                        if not pattern.search(Path(inner_name).stem.casefold()):
                            continue
                        payload = _bounded_member_bytes(
                            nested, nested_info, MAX_ASCII_MEMBER_BYTES
                        )
                        found.append(
                            _stage_bytes(
                                payload,
                                temp_root,
                                (
                                    f"{source.resolve()}!{info.filename}!"
                                    f"{nested_info.filename}"
                                ),
                                inner_name,
                            )
                        )

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in found:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def _materialize_atomic(
    source: Path,
    target: Path,
    tile: dict[str, Any],
) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}_",
        suffix=".materialize.tmp",
        dir=target.parent,
    )
    os.close(fd)
    temporary = Path(temp_name)
    total = 0
    try:
        with source.open("rb") as input_handle, temporary.open("wb") as output_handle:
            while chunk := input_handle.read(COPY_CHUNK_BYTES):
                total += len(chunk)
                if total > MAX_ASCII_MEMBER_BYTES:
                    raise ValueError("Terrain50 tile exceeds safety size limit")
                output_handle.write(chunk)
            output_handle.flush()
            os.fsync(output_handle.fileno())
        header = _validate(temporary, tile)
        temporary.replace(target)
        return header
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _write_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}_",
        suffix=".json.tmp",
        dir=path.parent,
    )
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matched-manifest", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    matches = _load_matches(args.matched_manifest)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    tile_rows: dict[str, dict[str, Any]] = {}
    candidate_records: list[dict[str, Any]] = []
    for row in matches:
        tile = _tile(float(row["bng_easting"]), float(row["bng_northing"]))
        tile_rows.setdefault(tile["key"], tile)
        candidate_records.append(
            {
                "row_no": row.get("row_no"),
                "parcel_id": row.get("parcel_id"),
                "tile_key": tile["key"],
            }
        )

    records: list[dict[str, Any]] = []
    raster_paths: list[str] = []
    with tempfile.TemporaryDirectory(
        prefix=".terrain50_candidate_stage_",
        dir=output_dir,
    ) as temp_name:
        temp_root = Path(temp_name)
        for key, tile in sorted(tile_rows.items()):
            candidates = _candidate_files(args.source, key, temp_root)
            valid: list[tuple[Path, dict[str, Any]]] = []
            errors: list[str] = []
            for path in candidates:
                try:
                    header = _validate(path, tile)
                    valid.append((path, header))
                except Exception as exc:
                    errors.append(f"{path}: {type(exc).__name__}: {exc}")
            if len(valid) != 1:
                raise ValueError(
                    f"expected exactly one valid Terrain50 tile {key}; "
                    f"valid={len(valid)} errors={errors}"
                )
            source_path, _ = valid[0]
            target = output_dir / "terrain50" / f"{key.casefold()}.asc"
            header = _materialize_atomic(source_path, target, tile)
            records.append(
                {
                    "tile_key": key,
                    "path": str(target),
                    "sha256": _sha256(target),
                    "size_bytes": target.stat().st_size,
                    "header": header,
                    "expected_bbox_epsg27700": [
                        tile["sw_e"],
                        tile["sw_n"],
                        tile["sw_e"] + 10000,
                        tile["sw_n"] + 10000,
                    ],
                    "atomic_materialization": True,
                }
            )
            raster_paths.append(str(target))

    manifest = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "status": "READY",
        "source_paths": [str(path) for path in args.source],
        "candidate_count": len(candidate_records),
        "unique_tile_count": len(records),
        "candidate_tiles": candidate_records,
        "records": records,
        "raster_paths": raster_paths,
        "nearest_or_neighbour_tile_substitution_used": False,
        "bounded_archive_member_reads": True,
        "ephemeral_candidate_extraction": True,
        "canonical_tile_validation_before_replace": True,
        "atomic_tile_materialization": True,
        "atomic_manifest_materialization": True,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    output = output_dir / "terrain50_source_manifest.json"
    _write_atomic(output, manifest)
    print(json.dumps({"ok": True, "manifest": str(output), "tiles": len(records)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}),
            file=sys.stderr,
        )
        raise
