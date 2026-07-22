#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import io
import json
import math
import os
import platform
import re
import stat
import sys
import tempfile
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

MAX_COMPRESSION_RATIO = 200.0
MAX_TOTAL_COMPRESSION_RATIO = 100.0
MAX_SINGLE_FILE_BYTES = 512 * 1024 * 1024
ALLOWED_ZIP_METHODS = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
TIFF_MAGICS = {b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"}
FORBIDDEN_EXECUTABLE_SUFFIXES = {
    ".exe", ".dll", ".com", ".bat", ".cmd", ".ps1", ".sh", ".py", ".js", ".jar", ".msi", ".scr"
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def is_tiff_magic(data: bytes) -> bool:
    return len(data) >= 4 and data[:4] in TIFF_MAGICS


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temp:
        json.dump(payload, temp, ensure_ascii=False, indent=2, sort_keys=True)
        temp.write("\n")
        temp.flush()
        os.fsync(temp.fileno())
        temp_path = Path(temp.name)
    os.replace(temp_path, path)


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def runtime_report(wrapper_path: Path, base_path: Path) -> dict[str, Any]:
    values: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "report_kind": "OFFICIAL_INPUT_MANIFEST_HARDENED_RUNTIME",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {name: package_version(name) for name in ("requests", "rasterio", "fiona", "shapely", "pyproj", "numpy")},
        "wrapper_sha256": sha256_file(wrapper_path),
        "base_manifest_sha256": sha256_file(base_path),
        "gdal_georef_sources": "INTERNAL",
        "security_gates": [
            "redirect_chain_https_and_final_host_allowlist",
            "role_specific_content_magic",
            "archive_path_duplicate_encryption_and_special_file_rejection",
            "archive_per_file_total_size_and_compression_ratio_limits",
            "archive_crc_test_after_resource_limits",
            "single_tiff_and_georeferencing_sidecar_rejection",
            "internal_geotiff_georeferencing_only",
            "north_up_no_rotation_square_supported_pixel_size",
            "single_numeric_band_finite_nodata_unit_scale_zero_offset",
            "target_point_cell_readable_finite_and_unmasked",
            "dtm_dsm_shared_lineage_fields_must_not_conflict",
        ],
        "actual_business_data_rows_written": 0,
        "fake_data": False,
        "final_ready": False,
    }
    try:
        import rasterio
        values["gdal_version"] = getattr(rasterio, "__gdal_version__", None)
        values["rasterio_proj_version"] = getattr(rasterio, "__proj_version__", None)
    except Exception as exc:
        values["rasterio_import_error"] = type(exc).__name__ + ":" + str(exc)
    try:
        import pyproj
        values["pyproj_proj_version"] = getattr(pyproj, "proj_version_str", None)
        values["pyproj_database_version"] = pyproj.database.get_database_metadata("EPSG.VERSION")
    except Exception as exc:
        values["pyproj_import_error"] = type(exc).__name__ + ":" + str(exc)
    return values


def load_base_module(base_path: Path):
    spec = importlib.util.spec_from_file_location("height_difference_3_official_input_manifest_base", base_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("BASE_MANIFEST_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def normalised_archive_name(name: str) -> str:
    if "\x00" in name:
        raise RuntimeError("ARCHIVE_MEMBER_NUL")
    if "\\" in name:
        raise RuntimeError("ARCHIVE_MEMBER_BACKSLASH")
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        raise RuntimeError("ARCHIVE_MEMBER_ABSOLUTE")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError("ARCHIVE_MEMBER_PATH_INVALID")
    return path.as_posix()


def zip_member_type(info: zipfile.ZipInfo) -> str:
    mode = (info.external_attr >> 16) & 0xFFFF
    kind = stat.S_IFMT(mode)
    if info.is_dir() or kind == stat.S_IFDIR:
        return "directory"
    if kind in (0, stat.S_IFREG):
        return "file"
    if kind == stat.S_IFLNK:
        raise RuntimeError("ARCHIVE_SYMLINK_REJECTED")
    raise RuntimeError("ARCHIVE_SPECIAL_FILE_REJECTED")


def hardened_safe_extract_factory(base):
    def safe_extract_single_tiff(data: bytes, directory: str | Path) -> Path:
        if not zipfile.is_zipfile(io.BytesIO(data)):
            raise base.GateError("ARCHIVE_MAGIC_OR_DIRECTORY_INVALID")
        root = Path(directory).resolve()
        root.mkdir(parents=True, exist_ok=True)
        try:
            archive = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile as exc:
            raise base.GateError("ARCHIVE_BAD_ZIP") from exc
        with archive:
            infos = archive.infolist()
            if not infos:
                raise base.GateError("ARCHIVE_EMPTY")
            if len(infos) > base.MAX_ARCHIVE_FILES:
                raise base.GateError("ARCHIVE_TOO_MANY_FILES")
            seen: set[str] = set()
            total_uncompressed = 0
            total_compressed = 0
            file_infos: list[tuple[zipfile.ZipInfo, str]] = []
            tiff_names: list[str] = []
            all_names: list[str] = []
            for info in infos:
                try:
                    name = normalised_archive_name(info.filename)
                    member_type = zip_member_type(info)
                except RuntimeError as exc:
                    raise base.GateError(str(exc)) from exc
                folded = name.casefold()
                if folded in seen:
                    raise base.GateError("ARCHIVE_DUPLICATE_MEMBER_NAME")
                seen.add(folded)
                all_names.append(folded)
                if info.flag_bits & 0x1:
                    raise base.GateError("ARCHIVE_ENCRYPTED_MEMBER")
                if info.compress_type not in ALLOWED_ZIP_METHODS:
                    raise base.GateError("ARCHIVE_COMPRESSION_METHOD_REJECTED")
                if info.file_size < 0 or info.compress_size < 0:
                    raise base.GateError("ARCHIVE_NEGATIVE_SIZE")
                if info.file_size > MAX_SINGLE_FILE_BYTES:
                    raise base.GateError("ARCHIVE_SINGLE_FILE_TOO_LARGE")
                if info.file_size and info.compress_size == 0:
                    raise base.GateError("ARCHIVE_ZERO_COMPRESSED_NONEMPTY")
                if info.file_size / max(info.compress_size, 1) > MAX_COMPRESSION_RATIO:
                    raise base.GateError("ARCHIVE_MEMBER_COMPRESSION_RATIO_TOO_HIGH")
                total_uncompressed += info.file_size
                total_compressed += info.compress_size
                if total_uncompressed > base.MAX_EXTRACTED_BYTES:
                    raise base.GateError("ARCHIVE_UNCOMPRESSED_TOO_LARGE")
                if member_type == "directory":
                    continue
                suffix = Path(name).suffix.casefold()
                if suffix in FORBIDDEN_EXECUTABLE_SUFFIXES:
                    raise base.GateError("ARCHIVE_EXECUTABLE_MEMBER_REJECTED")
                file_infos.append((info, name))
                if suffix in {".tif", ".tiff"}:
                    tiff_names.append(name)
            if total_uncompressed / max(total_compressed, 1) > MAX_TOTAL_COMPRESSION_RATIO:
                raise base.GateError("ARCHIVE_TOTAL_COMPRESSION_RATIO_TOO_HIGH")
            if len(tiff_names) != 1:
                raise base.GateError(f"ARCHIVE_TIFF_COUNT_{len(tiff_names)}")
            tiff_name = tiff_names[0]
            tiff_stem = PurePosixPath(tiff_name).with_suffix("").as_posix().casefold()
            forbidden_sidecars = {
                tiff_name.casefold() + ".aux.xml", tiff_stem + ".tfw", tiff_stem + ".tifw",
                tiff_stem + ".tiffw", tiff_stem + ".wld", tiff_stem + ".tab",
                tiff_stem + ".vrt", tiff_stem + ".ovr", tiff_stem + ".xml",
            }
            if any(name in forbidden_sidecars for name in all_names):
                raise base.GateError("ARCHIVE_GEOREFERENCE_SIDECAR_REJECTED")
            bad_crc = archive.testzip()
            if bad_crc is not None:
                raise base.GateError("ARCHIVE_CRC_FAILED")
            tiff_path: Path | None = None
            actual_total = 0
            for info, name in file_infos:
                destination = (root / Path(*PurePosixPath(name).parts)).resolve()
                if root != destination and root not in destination.parents:
                    raise base.GateError("ARCHIVE_PATH_TRAVERSAL")
                destination.parent.mkdir(parents=True, exist_ok=True)
                written = 0
                try:
                    with archive.open(info) as source, destination.open("xb") as target:
                        while chunk := source.read(1024 * 1024):
                            written += len(chunk)
                            actual_total += len(chunk)
                            if written > info.file_size or written > MAX_SINGLE_FILE_BYTES:
                                raise base.GateError("ARCHIVE_MEMBER_ACTUAL_SIZE_EXCEEDED")
                            if actual_total > base.MAX_EXTRACTED_BYTES:
                                raise base.GateError("ARCHIVE_ACTUAL_TOTAL_TOO_LARGE")
                            target.write(chunk)
                except FileExistsError as exc:
                    raise base.GateError("ARCHIVE_DESTINATION_ALREADY_EXISTS") from exc
                if written != info.file_size:
                    raise base.GateError("ARCHIVE_MEMBER_SIZE_MISMATCH")
                if name == tiff_name:
                    tiff_path = destination
            if tiff_path is None:
                raise base.GateError("ARCHIVE_TIFF_NOT_EXTRACTED")
            with tiff_path.open("rb") as handle:
                if not is_tiff_magic(handle.read(4)):
                    raise base.GateError("TIFF_MAGIC_INVALID")
            return tiff_path
    return safe_extract_single_tiff


def hardened_download_factory(base):
    def download_bounded(session, url: str, *, allowed_hosts: set[str] | None = None) -> bytes:
        parsed = urllib.parse.urlparse(url)
        allowed = {host.casefold() for host in allowed_hosts} if allowed_hosts is not None else None
        if parsed.scheme != "https" or not parsed.hostname:
            raise base.GateError("DOWNLOAD_URL_NOT_HTTPS")
        if allowed is not None and parsed.hostname.casefold() not in allowed:
            raise base.GateError("DOWNLOAD_HOST_NOT_ALLOWED")
        response = session.get(url, timeout=base.TIMEOUT, stream=True, allow_redirects=True)
        response.raise_for_status()
        chain = list(getattr(response, "history", []) or []) + [response]
        if len(chain) > 6:
            raise base.GateError("DOWNLOAD_TOO_MANY_REDIRECTS")
        for hop in chain:
            hop_url = urllib.parse.urlparse(str(getattr(hop, "url", "")))
            if hop_url.scheme != "https" or not hop_url.hostname:
                raise base.GateError("DOWNLOAD_REDIRECT_NOT_HTTPS")
        final = urllib.parse.urlparse(str(response.url))
        if allowed is not None and final.hostname.casefold() not in allowed:
            raise base.GateError("DOWNLOAD_FINAL_HOST_NOT_ALLOWED")
        declared = response.headers.get("Content-Length")
        if declared:
            try:
                declared_size = int(declared)
            except ValueError as exc:
                raise base.GateError("DOWNLOAD_CONTENT_LENGTH_INVALID") from exc
            if declared_size < 0 or declared_size > base.MAX_HTTP_BYTES:
                raise base.GateError("DOWNLOAD_DECLARED_TOO_LARGE")
        out = bytearray()
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                out.extend(chunk)
                if len(out) > base.MAX_HTTP_BYTES:
                    raise base.GateError("DOWNLOAD_STREAM_TOO_LARGE")
        if not out:
            raise base.GateError("DOWNLOAD_EMPTY")
        data = bytes(out)
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
        final_path = final.path.casefold()
        prefix = data[:256].lstrip().lower()
        if final_path.endswith(".gml"):
            if not prefix.startswith(b"<") or prefix.startswith((b"<html", b"<!doctype html")):
                raise base.GateError("HMLR_GML_CONTENT_MAGIC_INVALID")
            if content_type and not any(token in content_type for token in ("xml", "gml", "octet-stream", "text/plain")):
                raise base.GateError("HMLR_GML_CONTENT_TYPE_INVALID")
        elif allowed == {host.casefold() for host in base.EA_ALLOWED_HOSTS}:
            if not (data.startswith(b"PK") or is_tiff_magic(data)):
                raise base.GateError("EA_RASTER_CONTENT_MAGIC_INVALID")
            if content_type and not any(token in content_type for token in ("zip", "tiff", "octet-stream")):
                raise base.GateError("EA_RASTER_CONTENT_TYPE_INVALID")
        elif final.geturl().rstrip("/") == base.HMLR_DOWNLOAD_PAGE.rstrip("/"):
            if not (prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html")):
                raise base.GateError("HMLR_INDEX_HTML_MAGIC_INVALID")
        return data
    return download_bounded


def get_selected(layer: Any) -> dict[str, Any] | None:
    if not isinstance(layer, dict):
        return None
    selected = layer.get("selected_candidate") or layer.get("selected")
    if isinstance(selected, dict):
        return selected
    candidates = layer.get("candidates")
    if isinstance(candidates, list) and len(candidates) == 1 and isinstance(candidates[0], dict):
        return candidates[0]
    return None


def compare_shared_field(base, dtm: dict[str, Any], dsm: dict[str, Any], keys: tuple[str, ...], code: str) -> None:
    left = next((dtm.get(key) for key in keys if dtm.get(key) not in (None, "")), None)
    right = next((dsm.get(key) for key in keys if dsm.get(key) not in (None, "")), None)
    if left is not None and right is not None and str(left).strip().casefold() != str(right).strip().casefold():
        raise base.GateError(code)


def hardened_selected_candidate_factory(base, original):
    def selected_dtm_candidate(discovery_row: dict[str, Any]) -> dict[str, Any]:
        selected = original(discovery_row)
        layers = discovery_row.get("layers")
        dsm = get_selected(layers.get("dsm")) if isinstance(layers, dict) else None
        if dsm is not None:
            compare_shared_field(base, selected, dsm, ("to_date", "survey_date", "latest_survey"), "DTM_DSM_SURVEY_DATE_MISMATCH")
            compare_shared_field(base, selected, dsm, ("resolution", "resolution_m", "pixel_size"), "DTM_DSM_RESOLUTION_MISMATCH")
            compare_shared_field(base, selected, dsm, ("tile_name", "tile_ref", "tile_id", "name"), "DTM_DSM_TILE_MISMATCH")
        return selected
    return selected_dtm_candidate


def suspicious_sidecars(path: Path) -> list[str]:
    stem = path.with_suffix("").name.casefold()
    names = {child.name.casefold() for child in path.parent.iterdir() if child.is_file()}
    candidates = {
        path.name.casefold() + ".aux.xml", stem + ".tfw", stem + ".tifw", stem + ".tiffw",
        stem + ".wld", stem + ".tab", stem + ".vrt", stem + ".ovr", stem + ".xml",
    }
    return sorted(names & candidates)


def hardened_validate_raster_factory(base, original):
    def validate_raster(path: str | Path, candidate: dict[str, Any], easting: float, northing: float) -> dict[str, Any]:
        import numpy as np
        import rasterio
        raster_path = Path(path)
        if suspicious_sidecars(raster_path):
            raise base.GateError("DTM_GEOREFERENCE_SIDECAR_PRESENT")
        with raster_path.open("rb") as handle:
            if not is_tiff_magic(handle.read(4)):
                raise base.GateError("DTM_TIFF_MAGIC_INVALID")
        with rasterio.Env(GDAL_GEOREF_SOURCES="INTERNAL"):
            with rasterio.open(raster_path) as dataset:
                if dataset.driver != "GTiff":
                    raise base.GateError("DTM_DRIVER_NOT_GTIFF")
                if dataset.count != 1 or not dataset.crs or dataset.crs.to_epsg() != 27700:
                    raise base.GateError("DTM_DATASET_STRUCTURE_OR_CRS_INVALID")
                transform = dataset.transform
                if abs(transform.b) > 1e-12 or abs(transform.d) > 1e-12 or transform.a <= 0 or transform.e >= 0:
                    raise base.GateError("DTM_ROTATED_OR_NON_NORTH_UP")
                xres, yres = abs(transform.a), abs(transform.e)
                if abs(xres - yres) > 1e-6 or round(xres, 6) not in {0.25, 0.5, 1.0, 2.0}:
                    raise base.GateError("DTM_PIXEL_SIZE_UNSUPPORTED")
                dtype = np.dtype(dataset.dtypes[0])
                if dtype.kind not in {"i", "u", "f"}:
                    raise base.GateError("DTM_DTYPE_NOT_REAL_NUMERIC")
                if dataset.nodata is None or not math.isfinite(float(dataset.nodata)):
                    raise base.GateError("DTM_NODATA_MISSING_OR_NONFINITE")
                if len(dataset.scales) != 1 or not math.isclose(float(dataset.scales[0]), 1.0, abs_tol=1e-12):
                    raise base.GateError("DTM_SCALE_NOT_UNIT")
                if len(dataset.offsets) != 1 or not math.isclose(float(dataset.offsets[0]), 0.0, abs_tol=1e-12):
                    raise base.GateError("DTM_OFFSET_NOT_ZERO")
                if not (dataset.bounds.left <= easting < dataset.bounds.right and dataset.bounds.bottom < northing <= dataset.bounds.top):
                    raise base.GateError("DTM_POINT_OUTSIDE_BOUNDS")
                row, col = dataset.index(easting, northing)
                if not (0 <= row < dataset.height and 0 <= col < dataset.width):
                    raise base.GateError("DTM_POINT_INDEX_OUTSIDE")
                cell = dataset.read(1, window=((row, row + 1), (col, col + 1)), masked=True)
                if cell.size != 1 or bool(np.ma.getmaskarray(cell).reshape(-1)[0]):
                    raise base.GateError("DTM_POINT_CELL_MASKED_OR_NODATA")
                value = float(np.asarray(cell).reshape(-1)[0])
                if not math.isfinite(value):
                    raise base.GateError("DTM_POINT_CELL_NONFINITE")
        metadata = original(raster_path, candidate, easting, northing)
        metadata.update({
            "driver": "GTiff", "georeferencing_source_policy": "INTERNAL_ONLY", "sidecar_conflicts": [],
            "band_dtype": str(dtype), "scale": 1.0, "offset": 0.0,
            "target_point_cell_readable": True, "target_point_cell_value_preview_nonfinal": value,
        })
        return metadata
    return validate_raster


def main() -> int:
    raw_root = os.environ.get("AAYS_REPO_ROOT")
    if not raw_root:
        raise SystemExit("AAYS_REPO_ROOT_REQUIRED")
    repo_root = Path(raw_root).resolve()
    wrapper_path = Path(__file__).resolve()
    base_path = wrapper_path.with_name("height_difference_3_official_input_manifest_v1.py")
    if not base_path.is_file():
        raise SystemExit("BASE_MANIFEST_SCRIPT_NOT_FOUND")
    base = load_base_module(base_path)
    original_validate = base.validate_raster
    original_selected = base.selected_dtm_candidate
    base.download_bounded = hardened_download_factory(base)
    base.safe_extract_single_tiff = hardened_safe_extract_factory(base)
    base.selected_dtm_candidate = hardened_selected_candidate_factory(base, original_selected)
    base.validate_raster = hardened_validate_raster_factory(base, original_validate)
    report = runtime_report(wrapper_path, base_path)
    atomic_json(repo_root / "docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_runtime_environment_latest.json", report)
    atomic_json(repo_root / "england_map_web/data/height_difference/height_difference_3_runtime_environment_latest.json", report)
    return int(base.main())


if __name__ == "__main__":
    raise SystemExit(main())
