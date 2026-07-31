from __future__ import annotations

import concurrent.futures
import importlib.util
import io
import os
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import fiona
from pyproj import CRS
from shapely.geometry import shape as shapely_shape

ROOT = Path.cwd()
REPAIR_PATH = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave134_official_binary_shapefile_repair_20260731.py"
spec = importlib.util.spec_from_file_location("wave134_repair_v2", REPAIR_PATH)
repair = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(repair)
core = repair.core

MAX_ARCHIVE_DEPTH = 2
MAX_NESTED_ARCHIVES = 24
MAX_GDB_ROOTS_PER_ARCHIVE = 8
MAX_GDB_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
MAX_ARCHIVE_MEMBER_ROWS = 600


def safe_member_parts(name: str) -> tuple[str, ...] | None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        return None
    return tuple(part for part in path.parts if part not in ("", "."))


def inspect_gdb_layer(gdb_path: Path, layer_name: str, candidate: dict[str, Any], archive_label: str) -> dict[str, Any]:
    target = f"{candidate['url']}#{archive_label}::{gdb_path.name}/{layer_name}"
    try:
        with fiona.open(str(gdb_path), layer=layer_name) as source:
            fields = list(source.schema.get("properties", {}).keys())
            context = core.year_context(candidate.get("title"), archive_label, gdb_path.name, layer_name, fields)
            source_crs = None
            crs_error = None
            try:
                if source.crs_wkt:
                    source_crs = CRS.from_wkt(source.crs_wkt)
                elif source.crs:
                    source_crs = CRS.from_user_input(source.crs)
            except Exception as exc:
                crs_error = str(exc)
            hits: list[dict[str, Any]] = []
            scanned = 0
            declared = len(source)
            for feature in source:
                scanned += 1
                if scanned > core.MAX_RECORDS_PER_DATASET:
                    break
                attrs = dict(feature.get("properties") or {})
                values = {str(value).strip() for value in attrs.values() if value is not None}
                matched = [code for code in (core.w.m.EXPECTED_2011, core.w.m.EXPECTED_2021) if code in values]
                if not matched:
                    continue
                geometry = None
                if feature.get("geometry"):
                    try:
                        geometry = shapely_shape(feature["geometry"])
                    except Exception:
                        geometry = None
                metrics = core.geometry_metrics(geometry, source_crs)
                matched_fields = {
                    name: str(value)
                    for name, value in attrs.items()
                    if str(value).strip() in {core.w.m.EXPECTED_2011, core.w.m.EXPECTED_2021}
                }
                for code in matched:
                    hits.append({
                        "source_kind": "official_binary_file_geodatabase",
                        "item_id": candidate.get("item_id"),
                        "title": candidate.get("title"),
                        "package_url": candidate.get("url"),
                        "dataset_stem": f"{archive_label}::{gdb_path.name}/{layer_name}",
                        "year_context": context,
                        "code": code,
                        "role": core.code_role(code, context),
                        "matched_fields": matched_fields,
                        "attributes_sha256": core.digest(attrs),
                        "record_index": scanned,
                        "shape_type": str(source.schema.get("geometry")),
                        "point_count": None,
                        "part_count": None,
                        **metrics,
                    })
            authority = source_crs.to_authority() if source_crs else None
            result = {
                "item_id": candidate.get("item_id"),
                "title": candidate.get("title"),
                "package_url": candidate.get("url"),
                "dataset_stem": f"{archive_label}::{gdb_path.name}/{layer_name}",
                "members": {"file_geodatabase": str(gdb_path), "layer": layer_name},
                "year_context": context,
                "encoding": None,
                "field_names": fields,
                "record_count_declared": declared,
                "records_scanned": scanned,
                "scan_truncated": scanned > core.MAX_RECORDS_PER_DATASET,
                "hit_count": len(hits),
                "hits": hits,
                "prj_present": bool(source_crs),
                "prj_sha256": None,
                "prj_wkt": source_crs.to_wkt() if source_crs else None,
                "crs_ok": source_crs is not None,
                "crs_authority": list(authority) if authority else None,
                "crs_name": source_crs.name if source_crs else None,
                "crs_error": crs_error,
                "shp_sha256": None,
                "dbf_sha256": None,
                "shx_sha256": None,
                "cpg_sha256": None,
                "gdb_layer": layer_name,
                "gdb_driver": source.driver,
                "ok": True,
                "error": None,
            }
            core.add("binary_gdb_layer_scan", target, True, {
                "driver": source.driver,
                "records_scanned": scanned,
                "hit_count": len(hits),
                "crs": result["crs_authority"] or result["crs_name"],
            })
            return result
    except Exception as exc:
        core.add("binary_gdb_layer_scan", target, False, {}, str(exc))
        return {
            "item_id": candidate.get("item_id"),
            "title": candidate.get("title"),
            "package_url": candidate.get("url"),
            "dataset_stem": f"{archive_label}::{gdb_path.name}/{layer_name}",
            "members": {"file_geodatabase": str(gdb_path), "layer": layer_name},
            "records_scanned": 0,
            "hit_count": 0,
            "hits": [],
            "ok": False,
            "error": str(exc),
        }


def inspect_gdb_roots(
    archive: zipfile.ZipFile,
    infos: list[zipfile.ZipInfo],
    candidate: dict[str, Any],
    archive_label: str,
) -> list[dict[str, Any]]:
    roots: dict[str, list[zipfile.ZipInfo]] = {}
    for info in infos:
        parts = safe_member_parts(info.filename)
        if not parts:
            continue
        for index, part in enumerate(parts):
            if part.lower().endswith(".gdb"):
                root = "/".join(parts[: index + 1])
                roots.setdefault(root, []).append(info)
                break
    datasets: list[dict[str, Any]] = []
    for root, root_infos in list(sorted(roots.items()))[:MAX_GDB_ROOTS_PER_ARCHIVE]:
        total = sum(max(0, int(info.file_size)) for info in root_infos)
        target = f"{candidate['url']}#{archive_label}::{root}"
        if total <= 0 or total > MAX_GDB_UNCOMPRESSED_BYTES:
            core.add("binary_gdb_extract", target, False, {"uncompressed_bytes": total}, "GDB_SIZE_LIMIT")
            continue
        try:
            with tempfile.TemporaryDirectory(prefix="aays_wave134_gdb_") as temp_name:
                temp = Path(temp_name)
                for info in root_infos:
                    parts = safe_member_parts(info.filename)
                    if not parts or info.is_dir():
                        continue
                    destination = temp.joinpath(*parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(info))
                gdb_path = temp.joinpath(*PurePosixPath(root).parts)
                layers = list(fiona.listlayers(str(gdb_path)))[: core.MAX_DATASETS_PER_ARCHIVE]
                core.add("binary_gdb_extract", target, bool(layers), {
                    "uncompressed_bytes": total,
                    "layers": layers,
                    "layer_count": len(layers),
                }, None if layers else "NO_GDB_LAYERS")
                for layer_name in layers:
                    datasets.append(inspect_gdb_layer(gdb_path, layer_name, candidate, archive_label))
        except Exception as exc:
            core.add("binary_gdb_extract", target, False, {"uncompressed_bytes": total}, str(exc))
    return datasets


def scan_archive(
    payload: bytes,
    candidate: dict[str, Any],
    archive_label: str,
    depth: int,
    state: dict[str, Any],
) -> None:
    if depth > MAX_ARCHIVE_DEPTH or state["nested_archives"] > MAX_NESTED_ARCHIVES:
        return
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        state["archives_opened"] += 1
        infos = [info for info in archive.infolist() if not info.is_dir()]
        for info in infos:
            if len(state["members"]) >= MAX_ARCHIVE_MEMBER_ROWS:
                break
            state["members"].append({
                "archive": archive_label,
                "depth": depth,
                "name": info.filename,
                "size": info.file_size,
                "crc": info.CRC,
                "compressed_size": info.compress_size,
            })

        for group in core.group_binary_members(archive):
            scoped = {"stem": f"{archive_label}::{group['stem']}", "members": group["members"]}
            state["datasets"].append(core.inspect_dataset(archive, candidate, scoped))

        state["datasets"].extend(inspect_gdb_roots(archive, infos, candidate, archive_label))

        if depth >= MAX_ARCHIVE_DEPTH:
            return
        for info in infos:
            if state["nested_archives"] >= MAX_NESTED_ARCHIVES:
                break
            if info.file_size <= 0 or info.file_size > core.MAX_DOWNLOAD_BYTES:
                continue
            lower = info.filename.lower()
            if not lower.endswith((".zip", ".sd", ".mpk", ".mpkx", ".ppkx", ".lpk", ".lpkx")):
                continue
            try:
                child = archive.read(info)
                if not zipfile.is_zipfile(io.BytesIO(child)):
                    continue
                state["nested_archives"] += 1
                child_label = f"{archive_label}!{info.filename}"
                core.add("binary_nested_archive_open", child_label, True, {
                    "depth": depth + 1,
                    "bytes": len(child),
                    "parent": archive_label,
                })
                scan_archive(child, candidate, child_label, depth + 1, state)
            except Exception as exc:
                core.add("binary_nested_archive_open", f"{archive_label}!{info.filename}", False, {
                    "depth": depth + 1,
                    "parent": archive_label,
                }, str(exc))


def inspect_package_recursive(candidate: dict[str, Any]) -> dict[str, Any]:
    fetched = core.w.fetch_bytes(candidate["url"])
    result = {
        **candidate,
        "download_ok": fetched["ok"],
        "status": fetched.get("status"),
        "content_type": fetched.get("content_type"),
        "content_length": fetched.get("content_length"),
        "bytes_read": fetched.get("bytes_read", 0),
        "truncated": fetched.get("truncated", False),
        "sha256": fetched.get("sha256"),
        "previous_sha256_matches": fetched.get("sha256") == candidate.get("previous_sha256") if fetched.get("sha256") else False,
        "archive_ok": False,
        "archive_members": [],
        "binary_dataset_groups": 0,
        "datasets": [],
        "nested_archives_opened": 0,
        "total_archives_opened": 0,
        "error": fetched.get("error"),
    }
    if not fetched["ok"] or fetched.get("truncated"):
        return result
    payload = fetched["bytes"]
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        result["error"] = "NOT_ZIP_ARCHIVE"
        core.add("binary_archive_open", candidate["url"], False, {"content_type": result["content_type"]}, result["error"])
        return result
    state: dict[str, Any] = {"members": [], "datasets": [], "nested_archives": 0, "archives_opened": 0}
    try:
        scan_archive(payload, candidate, "root", 0, state)
        result["archive_ok"] = True
        result["archive_members"] = state["members"]
        result["datasets"] = state["datasets"]
        result["binary_dataset_groups"] = len(state["datasets"])
        result["nested_archives_opened"] = state["nested_archives"]
        result["total_archives_opened"] = state["archives_opened"]
        core.add("binary_archive_open", candidate["url"], True, {
            "archive_member_rows": len(state["members"]),
            "binary_dataset_groups": len(state["datasets"]),
            "nested_archives_opened": state["nested_archives"],
            "total_archives_opened": state["archives_opened"],
            "package_sha256": result["sha256"],
        })
    except Exception as exc:
        result["error"] = str(exc)
        core.add("binary_archive_open", candidate["url"], False, {}, str(exc))
    return result


def inspect_services_direct(previous: dict[str, Any]) -> list[dict[str, Any]]:
    layers: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item_id in repair.KNOWN_BOUNDARY_SERVICE_ITEMS:
        meta = repair.fetch_meta(item_id)
        if not meta:
            continue
        url = str(meta.get("url") or "").rstrip("/")
        if "/FeatureServer" not in url:
            continue
        root = __import__("re").sub(r"/FeatureServer/\d+$", "/FeatureServer", url, flags=__import__("re").I)
        root_result = core.w.safe_json("wave134_direct_service_root", root, {"f": "json"})
        if not root_result["ok"]:
            continue
        requested_ids: list[str]
        match = __import__("re").search(r"/FeatureServer/(\d+)$", url, __import__("re").I)
        if match:
            requested_ids = [match.group(1)]
        else:
            requested_ids = [str(row.get("id")) for row in root_result["data"].get("layers", [])[:10]]
        for layer_id in requested_ids:
            layer_url = f"{root}/{layer_id}"
            if layer_url in seen:
                continue
            seen.add(layer_url)
            layer_meta = core.w.safe_json("wave134_direct_service_layer", layer_url, {"f": "json"})
            if not layer_meta["ok"]:
                continue
            fields = core.w.detect_code_fields(layer_meta["data"])
            core.add("wave134_direct_service_layer_summary", layer_url, True, {
                "item_id": item_id,
                "name": layer_meta["data"].get("name"),
                "code_fields": fields,
            })
            if fields:
                layers.append({
                    "item_id": item_id,
                    "layer_url": layer_url,
                    "metadata_name": layer_meta["data"].get("name") or meta.get("title"),
                    "code_fields": fields,
                })
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=core.MAX_ANALYSIS_WORKERS) as pool:
        for row in pool.map(core.inspect_service_layer, layers):
            rows.append(row)
    rows.sort(key=lambda row: str(row.get("layer_url")))
    return rows


core.inspect_package = inspect_package_recursive
core.inspect_services = inspect_services_direct

if __name__ == "__main__":
    core.main()
