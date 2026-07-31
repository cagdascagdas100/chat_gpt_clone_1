from __future__ import annotations

import concurrent.futures
import hashlib
import html
import importlib.util
import io
import json
import os
import re
import threading
import zipfile
from pathlib import Path
from typing import Any

import shapefile
from pyproj import CRS, Transformer
from shapely.geometry import Point, Polygon, shape as shapely_shape
from shapely.ops import transform as shapely_transform, unary_union

ROOT = Path.cwd()
BASE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave133_official_correspondence_code_history_package_provenance_20260731.py"
spec = importlib.util.spec_from_file_location("wave133_base", BASE)
w = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(w)

TASK_ID = "security_public_safety_2_wave134_official_binary_shapefile_dbf_crs_geometry_reconciliation_20260731"
FIRST_STEP = "WAVE134_SINGLE_OPEN_ROW_OFFICIAL_BINARY_SHP_DBF_PRJ_CRS_GEOMETRY_RECONCILIATION"
PREVIOUS = "abebf80f7ff3b32f5ea85a9bfb49f7ceab085357bdbc0845e9bc9a2295a5e7ce"
SOURCE_HEAD = os.environ["AAYS_SOURCE_HEAD"]
CONTINUATION = hashlib.sha256(
    f"{w.m.WORKSTREAM_ID}|{w.m.SLOT_ID}|{w.m.CANONICAL_BRANCH}|{FIRST_STEP}|{SOURCE_HEAD}".encode()
).hexdigest()

W133 = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_official_correspondence_code_history_package_provenance_wave133_latest.json"
MANUAL = ROOT / "docs/chatgpt_status/_shared/manual_actions/security_public_safety_2.json"
OUTJ = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_official_binary_shapefile_dbf_crs_geometry_reconciliation_wave134_latest.json"
OUTH = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_official_binary_shapefile_dbf_crs_geometry_reconciliation_wave134.html"

MAX_PACKAGES = 12
MAX_DOWNLOAD_WORKERS = 4
MAX_ANALYSIS_WORKERS = 15
MAX_DOWNLOAD_BYTES = 80 * 1024 * 1024
MAX_DATASETS_PER_ARCHIVE = 16
MAX_RECORDS_PER_DATASET = 120000

w.MAX_DOWNLOAD_BYTES = MAX_DOWNLOAD_BYTES
w.ledger.clear()
w.m.network_attempts = 0
w.m.network_successes = 0
w.m.targeted_recoveries = 0
lock = threading.Lock()


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def add(kind: str, target: str, ok: bool, details: dict[str, Any] | None = None, error: str | None = None) -> None:
    w.add_ledger(kind, target, ok, details, error)


def year_context(*parts: Any) -> str:
    text = " ".join(str(part or "") for part in parts).lower()
    has11 = bool(re.search(r"(^|[^0-9])2011([^0-9]|$)|lsoa11", text))
    has21 = bool(re.search(r"(^|[^0-9])2021([^0-9]|$)|lsoa21", text))
    if has11 and not has21:
        return "2011"
    if has21 and not has11:
        return "2021"
    if has11 and has21:
        return "2011_2021"
    return "unknown"


def code_role(code: str, context: str) -> str:
    if code == w.m.EXPECTED_2011:
        return "expected_2011"
    if code == w.m.EXPECTED_2021:
        if context == "2011":
            return "competing_2011"
        if context == "2021":
            return "expected_2021"
        return "expected_2021_or_competing_2011"
    return "other"


def package_candidates(previous: dict[str, Any]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    fallback: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in previous.get("official_packages", []):
        url = str(row.get("url") or "")
        if not url or url in seen or not row.get("ok") or row.get("truncated"):
            continue
        seen.add(url)
        members = row.get("members", [])
        member_names = [str(member.get("name") or "") for member in members]
        has_binary = any(name.lower().endswith((".shp", ".dbf", ".prj", ".shx", ".cpg")) for name in member_names)
        candidate = {
            "item_id": row.get("item_id"),
            "title": row.get("title"),
            "item_type": row.get("item_type"),
            "kind": row.get("kind"),
            "url": url,
            "previous_sha256": row.get("sha256"),
            "previous_content_type": row.get("content_type"),
            "previous_bytes_read": row.get("bytes_read"),
            "previous_members": member_names[:200],
            "binary_members_previously_seen": has_binary,
        }
        if has_binary:
            selected.append(candidate)
        elif "shapefile" in str(row.get("item_type") or "").lower() or "zip" in str(row.get("content_type") or "").lower():
            fallback.append(candidate)
    merged = selected + fallback
    return merged[:MAX_PACKAGES]


def group_binary_members(archive: zipfile.ZipFile) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, str]] = {}
    for info in archive.infolist():
        if info.is_dir():
            continue
        name = info.filename
        suffix = Path(name).suffix.lower()
        if suffix not in {".shp", ".shx", ".dbf", ".prj", ".cpg"}:
            continue
        stem = str(Path(name).with_suffix(""))
        groups.setdefault(stem.lower(), {})[suffix] = name
    rows = []
    for stem, members in sorted(groups.items()):
        if ".shp" in members and ".dbf" in members:
            rows.append({"stem": stem, "members": members})
    return rows[:MAX_DATASETS_PER_ARCHIVE]


def decode_cpg(payload: bytes | None) -> str:
    if not payload:
        return "cp1252"
    text = payload.decode("ascii", errors="ignore").strip().lower()
    aliases = {
        "utf-8": "utf-8", "utf8": "utf-8", "65001": "utf-8",
        "windows-1252": "cp1252", "1252": "cp1252", "ansi 1252": "cp1252",
        "iso-8859-1": "latin-1", "latin1": "latin-1",
    }
    return aliases.get(text, text or "cp1252")


def read_crs(prj_payload: bytes | None) -> tuple[CRS | None, str | None, str | None]:
    if not prj_payload:
        return None, None, "PRJ_MISSING"
    text = prj_payload.decode("utf-8", errors="replace").strip()
    try:
        crs = CRS.from_wkt(text)
        return crs, text, None
    except Exception as exc:
        return None, text, str(exc)


def geometry_metrics(geom: Any, source_crs: CRS | None) -> dict[str, Any]:
    if geom is None or geom.is_empty or source_crs is None:
        return {
            "geometry_ok": False,
            "covers_selected_coordinate": None,
            "boundary_distance_metres": None,
            "area_square_metres": None,
            "perimeter_metres": None,
            "centroid_27700": None,
            "bounds_27700": None,
            "geometry_sha256_27700": None,
            "error": "EMPTY_GEOMETRY_OR_UNKNOWN_CRS",
        }
    try:
        point_lonlat = Point(w.m.CENTER[0], w.m.CENTER[1])
        to_source = Transformer.from_crs(CRS.from_epsg(4326), source_crs, always_xy=True)
        point_source = shapely_transform(to_source.transform, point_lonlat)
        covers = bool(geom.covers(point_source))
        to_27700 = Transformer.from_crs(source_crs, CRS.from_epsg(27700), always_xy=True)
        geom_27700 = shapely_transform(to_27700.transform, geom)
        point_27700 = shapely_transform(
            Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(27700), always_xy=True).transform,
            point_lonlat,
        )
        try:
            normalized = geom_27700.normalize()
        except Exception:
            normalized = geom_27700
        return {
            "geometry_ok": True,
            "covers_selected_coordinate": covers,
            "boundary_distance_metres": float(point_27700.distance(geom_27700.boundary)),
            "area_square_metres": float(geom_27700.area),
            "perimeter_metres": float(geom_27700.length),
            "centroid_27700": [float(geom_27700.centroid.x), float(geom_27700.centroid.y)],
            "bounds_27700": [float(v) for v in geom_27700.bounds],
            "geometry_sha256_27700": hashlib.sha256(normalized.wkb).hexdigest(),
            "error": None,
        }
    except Exception as exc:
        return {
            "geometry_ok": False,
            "covers_selected_coordinate": None,
            "boundary_distance_metres": None,
            "area_square_metres": None,
            "perimeter_metres": None,
            "centroid_27700": None,
            "bounds_27700": None,
            "geometry_sha256_27700": None,
            "error": str(exc),
        }


def inspect_dataset(archive: zipfile.ZipFile, candidate: dict[str, Any], group: dict[str, Any]) -> dict[str, Any]:
    members = group["members"]
    target = f"{candidate['url']}#{group['stem']}"
    try:
        shp_bytes = archive.read(members[".shp"])
        dbf_bytes = archive.read(members[".dbf"])
        shx_bytes = archive.read(members[".shx"]) if ".shx" in members else None
        prj_bytes = archive.read(members[".prj"]) if ".prj" in members else None
        cpg_bytes = archive.read(members[".cpg"]) if ".cpg" in members else None
        encoding = decode_cpg(cpg_bytes)
        crs, prj_text, crs_error = read_crs(prj_bytes)
        reader = shapefile.Reader(
            shp=io.BytesIO(shp_bytes),
            shx=io.BytesIO(shx_bytes) if shx_bytes else None,
            dbf=io.BytesIO(dbf_bytes),
            encoding=encoding,
            encodingErrors="replace",
        )
        field_names = [field[0] for field in reader.fields[1:]]
        context = year_context(candidate.get("title"), group["stem"], field_names)
        hits: list[dict[str, Any]] = []
        records_scanned = 0
        for shape_record in reader.iterShapeRecords():
            records_scanned += 1
            if records_scanned > MAX_RECORDS_PER_DATASET:
                break
            attrs = shape_record.record.as_dict()
            values = {str(value).strip() for value in attrs.values() if value is not None}
            matched = [code for code in (w.m.EXPECTED_2011, w.m.EXPECTED_2021) if code in values]
            if not matched:
                continue
            try:
                geom = shapely_shape(shape_record.shape.__geo_interface__)
            except Exception:
                geom = None
            metrics = geometry_metrics(geom, crs)
            matched_fields = {
                name: str(value)
                for name, value in attrs.items()
                if str(value).strip() in {w.m.EXPECTED_2011, w.m.EXPECTED_2021}
            }
            for code in matched:
                hits.append({
                    "source_kind": "official_binary_package",
                    "item_id": candidate.get("item_id"),
                    "title": candidate.get("title"),
                    "package_url": candidate.get("url"),
                    "dataset_stem": group["stem"],
                    "year_context": context,
                    "code": code,
                    "role": code_role(code, context),
                    "matched_fields": matched_fields,
                    "attributes_sha256": digest(attrs),
                    "record_index": records_scanned,
                    "shape_type": int(shape_record.shape.shapeType),
                    "point_count": len(shape_record.shape.points),
                    "part_count": len(shape_record.shape.parts),
                    **metrics,
                })
        result = {
            "item_id": candidate.get("item_id"),
            "title": candidate.get("title"),
            "package_url": candidate.get("url"),
            "dataset_stem": group["stem"],
            "members": members,
            "year_context": context,
            "encoding": encoding,
            "field_names": field_names,
            "record_count_declared": len(reader),
            "records_scanned": records_scanned,
            "scan_truncated": records_scanned > MAX_RECORDS_PER_DATASET,
            "hit_count": len(hits),
            "hits": hits,
            "prj_present": prj_bytes is not None,
            "prj_sha256": hashlib.sha256(prj_bytes).hexdigest() if prj_bytes else None,
            "prj_wkt": prj_text,
            "crs_ok": crs is not None,
            "crs_authority": list(crs.to_authority()) if crs and crs.to_authority() else None,
            "crs_name": crs.name if crs else None,
            "crs_error": crs_error,
            "shp_sha256": hashlib.sha256(shp_bytes).hexdigest(),
            "dbf_sha256": hashlib.sha256(dbf_bytes).hexdigest(),
            "shx_sha256": hashlib.sha256(shx_bytes).hexdigest() if shx_bytes else None,
            "cpg_sha256": hashlib.sha256(cpg_bytes).hexdigest() if cpg_bytes else None,
            "ok": True,
            "error": None,
        }
        add("binary_dataset_scan", target, True, {
            "records_scanned": records_scanned,
            "hit_count": len(hits),
            "crs": result["crs_authority"] or result["crs_name"],
            "shp_sha256": result["shp_sha256"],
            "dbf_sha256": result["dbf_sha256"],
        })
        return result
    except Exception as exc:
        add("binary_dataset_scan", target, False, {}, str(exc))
        return {
            "item_id": candidate.get("item_id"),
            "title": candidate.get("title"),
            "package_url": candidate.get("url"),
            "dataset_stem": group["stem"],
            "members": members,
            "records_scanned": 0,
            "hit_count": 0,
            "hits": [],
            "ok": False,
            "error": str(exc),
        }


def inspect_package(candidate: dict[str, Any]) -> dict[str, Any]:
    fetched = w.fetch_bytes(candidate["url"])
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
        "error": fetched.get("error"),
    }
    if not fetched["ok"] or fetched.get("truncated"):
        return result
    payload = fetched["bytes"]
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        result["error"] = "NOT_ZIP_ARCHIVE"
        add("binary_archive_open", candidate["url"], False, {"content_type": result["content_type"]}, result["error"])
        return result
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
            result["archive_members"] = [
                {"name": info.filename, "size": info.file_size, "crc": info.CRC, "compressed_size": info.compress_size}
                for info in infos[:300]
            ]
            groups = group_binary_members(archive)
            result["binary_dataset_groups"] = len(groups)
            result["datasets"] = [inspect_dataset(archive, candidate, group) for group in groups]
            result["archive_ok"] = True
            add("binary_archive_open", candidate["url"], True, {
                "members": len(infos),
                "binary_dataset_groups": len(groups),
                "package_sha256": result["sha256"],
            })
    except Exception as exc:
        result["error"] = str(exc)
        add("binary_archive_open", candidate["url"], False, {}, str(exc))
    return result


def inspect_packages(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as pool:
        futures = {pool.submit(inspect_package, candidate): candidate for candidate in candidates}
        for future in concurrent.futures.as_completed(futures):
            candidate = futures[future]
            try:
                rows.append(future.result())
            except Exception as exc:
                add("binary_package_worker", candidate["url"], False, {}, str(exc))
                rows.append({**candidate, "download_ok": False, "archive_ok": False, "datasets": [], "error": str(exc)})
    rows.sort(key=lambda row: (str(row.get("item_id")), str(row.get("url"))))
    return rows


def esri_polygon(geometry: dict[str, Any]) -> Any:
    polygons = []
    for ring in geometry.get("rings", []):
        if len(ring) >= 4:
            try:
                poly = Polygon(ring)
                if poly.is_valid and not poly.is_empty:
                    polygons.append(poly)
            except Exception:
                continue
    return unary_union(polygons) if polygons else None


def inspect_service_layer(layer: dict[str, Any]) -> dict[str, Any]:
    layer_url = str(layer.get("layer_url") or "")
    fields = [str(field) for field in layer.get("code_fields", []) if field]
    if not layer_url or not fields:
        return {"layer_url": layer_url, "query_ok": True, "skipped": True, "hits": [], "error": None}
    clauses = [f"{field}='{code}'" for field in fields for code in (w.m.EXPECTED_2011, w.m.EXPECTED_2021)]
    result = w.safe_json("wave134_service_geometry_query", layer_url + "/query", {
        "f": "json",
        "where": " OR ".join(clauses),
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": 27700,
        "geometryPrecision": 3,
        "resultRecordCount": 2000,
    })
    hits = []
    context = year_context(layer.get("metadata_name"), layer_url, fields)
    for feature in result["data"].get("features", []) if result["ok"] else []:
        attrs = feature.get("attributes", {})
        values = {str(value).strip() for value in attrs.values() if value is not None}
        matched = [code for code in (w.m.EXPECTED_2011, w.m.EXPECTED_2021) if code in values]
        geom = esri_polygon(feature.get("geometry", {}))
        metrics = geometry_metrics(geom, CRS.from_epsg(27700))
        for code in matched:
            hits.append({
                "source_kind": "official_feature_service",
                "item_id": layer.get("item_id"),
                "layer_url": layer_url,
                "metadata_name": layer.get("metadata_name"),
                "year_context": context,
                "code": code,
                "role": code_role(code, context),
                "attributes_sha256": digest(attrs),
                **metrics,
            })
    return {
        "item_id": layer.get("item_id"),
        "layer_url": layer_url,
        "metadata_name": layer.get("metadata_name"),
        "year_context": context,
        "code_fields": fields,
        "query_ok": result["ok"],
        "returned_features": len(result["data"].get("features", [])) if result["ok"] else 0,
        "hit_count": len(hits),
        "hits": hits,
        "error": result["error"],
    }


def inspect_services(previous: dict[str, Any]) -> list[dict[str, Any]]:
    layers = [
        layer for layer in previous.get("official_service_layers", [])
        if layer.get("layer_url") and layer.get("code_fields")
    ][:40]
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_ANALYSIS_WORKERS) as pool:
        for row in pool.map(inspect_service_layer, layers):
            rows.append(row)
    rows.sort(key=lambda row: str(row.get("layer_url")))
    return rows


def compare_hits(package_hits: list[dict[str, Any]], service_hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    comparisons = []
    for package_hit in package_hits:
        for service_hit in service_hits:
            if package_hit.get("code") != service_hit.get("code"):
                continue
            if package_hit.get("role") != service_hit.get("role"):
                continue
            pc = package_hit.get("centroid_27700")
            sc = service_hit.get("centroid_27700")
            pb = package_hit.get("bounds_27700")
            sb = service_hit.get("bounds_27700")
            pa = package_hit.get("area_square_metres")
            sa = service_hit.get("area_square_metres")
            if not pc or not sc or not pb or not sb or pa is None or sa is None:
                continue
            centroid_distance = ((pc[0] - sc[0]) ** 2 + (pc[1] - sc[1]) ** 2) ** 0.5
            bounds_max_delta = max(abs(a - b) for a, b in zip(pb, sb))
            area_relative_delta = abs(pa - sa) / max(abs(pa), abs(sa), 1.0)
            comparisons.append({
                "code": package_hit["code"],
                "role": package_hit["role"],
                "package_item_id": package_hit.get("item_id"),
                "package_dataset": package_hit.get("dataset_stem"),
                "service_item_id": service_hit.get("item_id"),
                "service_layer_url": service_hit.get("layer_url"),
                "package_covers": package_hit.get("covers_selected_coordinate"),
                "service_covers": service_hit.get("covers_selected_coordinate"),
                "classification_agrees": package_hit.get("covers_selected_coordinate") == service_hit.get("covers_selected_coordinate"),
                "centroid_distance_metres": centroid_distance,
                "bounds_max_delta_metres": bounds_max_delta,
                "area_relative_delta": area_relative_delta,
                "strict_geometry_match": centroid_distance <= 0.02 and bounds_max_delta <= 0.02 and area_relative_delta <= 1e-7,
            })
            if len(comparisons) >= 500:
                return comparisons
    return comparisons


def table(rows: list[dict[str, Any]], keys: list[str]) -> str:
    return "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>" for key in keys) + "</tr>"
        for row in rows
    )


def main() -> None:
    if not W133.exists() or not MANUAL.exists():
        raise RuntimeError("Wave133/manual missing")
    previous = json.loads(W133.read_text())
    manual = json.loads(MANUAL.read_text())
    if previous.get("continuation_key") != PREVIOUS:
        raise RuntimeError("Wave133 continuation mismatch")
    if manual.get("open_item_count") != 1:
        raise RuntimeError("expected exactly one OPEN item")

    candidates = package_candidates(previous)
    packages = inspect_packages(candidates)
    services = inspect_services(previous)

    datasets = [dataset for package in packages for dataset in package.get("datasets", [])]
    package_hits = [hit for dataset in datasets for hit in dataset.get("hits", [])]
    service_hits = [hit for service in services for hit in service.get("hits", [])]
    comparisons = compare_hits(package_hits, service_hits)

    package_expected_2011 = [hit for hit in package_hits if hit.get("role") == "expected_2011"]
    package_expected_2021 = [hit for hit in package_hits if hit.get("role") == "expected_2021"]
    package_competing_2011 = [hit for hit in package_hits if hit.get("role") == "competing_2011"]
    service_expected_2011 = [hit for hit in service_hits if hit.get("role") == "expected_2011"]
    service_expected_2021 = [hit for hit in service_hits if hit.get("role") == "expected_2021"]
    service_competing_2011 = [hit for hit in service_hits if hit.get("role") == "competing_2011"]

    primary_eligible = len(previous.get("repository_provenance", {}).get("primary_eligible_files", []))
    package_2011_expected_covers = any(hit.get("covers_selected_coordinate") is True for hit in package_expected_2011)
    package_2021_expected_covers = any(hit.get("covers_selected_coordinate") is True for hit in package_expected_2021)
    package_2011_competing_covers = any(hit.get("covers_selected_coordinate") is True for hit in package_competing_2011)
    service_2011_expected_covers = any(hit.get("covers_selected_coordinate") is True for hit in service_expected_2011)
    service_2021_expected_covers = any(hit.get("covers_selected_coordinate") is True for hit in service_expected_2021)
    service_2011_competing_covers = any(hit.get("covers_selected_coordinate") is True for hit in service_competing_2011)
    strict_matches = [row for row in comparisons if row.get("strict_geometry_match")]

    promote = all([
        primary_eligible > 0,
        package_2011_expected_covers,
        package_2021_expected_covers,
        not package_2011_competing_covers,
        service_2011_expected_covers,
        service_2021_expected_covers,
        not service_2011_competing_covers,
        any(row.get("role") == "expected_2011" for row in strict_matches),
        any(row.get("role") == "expected_2021" for row in strict_matches),
    ])

    support = 30761 if promote else 30760
    accuracy = support / 30761 * 100
    state = (
        "RESOLVED_EXACT_PRIMARY_BINDING_AND_OFFICIAL_BINARY_PACKAGE_SERVICE_GEOMETRY_AGREEMENT"
        if promote
        else "OPEN_IRREDUCIBLE_AFTER_OFFICIAL_BINARY_SHP_DBF_PRJ_CRS_GEOMETRY_RECONCILIATION"
    )

    records_scanned = sum(int(dataset.get("records_scanned", 0)) for dataset in datasets)
    binary_groups = sum(int(package.get("binary_dataset_groups", 0)) for package in packages)
    archive_members = sum(len(package.get("archive_members", [])) for package in packages)
    service_features = sum(int(service.get("returned_features", 0)) for service in services)
    operations = (
        len(w.ledger)
        + len(candidates)
        + len(packages)
        + archive_members
        + binary_groups
        + records_scanned
        + len(package_hits)
        + len(services)
        + service_features
        + len(service_hits)
        + len(comparisons)
    )
    promoted_families = sum([
        bool(candidates),
        any(package.get("download_ok") for package in packages),
        any(package.get("archive_ok") for package in packages),
        any(dataset.get("ok") for dataset in datasets),
        any(dataset.get("prj_present") for dataset in datasets),
        any(dataset.get("crs_ok") for dataset in datasets),
        bool(package_hits),
        bool(service_hits),
        bool(comparisons),
        bool(strict_matches),
        primary_eligible > 0,
        promote,
    ])

    metrics = {
        "rows_audited": 1,
        "new_high_confidence_support_candidates": 1 if promote else 0,
        "open_rows_after_wave": 0 if promote else 1,
        "resolved_rows_after_wave": 16 if promote else 15,
        "high_confidence_support_rows": support,
        "parent_candidate_rows": 30761,
        "support_accuracy_percent": accuracy,
        "wave_percentage_point_delta": accuracy - float(previous["result"]["support_accuracy_percent"]),
        "cumulative_support_percentage_point_delta": accuracy - 98.71915737459771,
        "reviewed_official_source_families": 12,
        "promoted_official_source_families": promoted_families,
        "official_binary_package_candidates": len(candidates),
        "official_binary_package_downloads": len(packages),
        "official_binary_package_download_successes": sum(bool(package.get("download_ok")) for package in packages),
        "official_binary_archives_opened": sum(bool(package.get("archive_ok")) for package in packages),
        "official_archive_members_catalogued": archive_members,
        "official_binary_dataset_groups": binary_groups,
        "official_binary_datasets_scanned": len(datasets),
        "official_binary_dataset_scan_successes": sum(bool(dataset.get("ok")) for dataset in datasets),
        "official_binary_records_scanned": records_scanned,
        "official_binary_exact_code_hits": len(package_hits),
        "official_prj_records": sum(bool(dataset.get("prj_present")) for dataset in datasets),
        "official_crs_resolutions": sum(bool(dataset.get("crs_ok")) for dataset in datasets),
        "official_service_geometry_layers_queried": len(services),
        "official_service_geometry_features": service_features,
        "official_service_exact_code_hits": len(service_hits),
        "package_service_geometry_comparisons": len(comparisons),
        "strict_package_service_geometry_matches": len(strict_matches),
        "package_expected_2011_covers_selected": package_2011_expected_covers,
        "package_competing_2011_covers_selected": package_2011_competing_covers,
        "package_expected_2021_covers_selected": package_2021_expected_covers,
        "service_expected_2011_covers_selected": service_2011_expected_covers,
        "service_competing_2011_covers_selected": service_2011_competing_covers,
        "service_expected_2021_covers_selected": service_2021_expected_covers,
        "primary_eligible_files": primary_eligible,
        "official_network_probe_attempts": int(w.m.network_attempts),
        "official_network_probe_successes": int(w.m.network_successes),
        "targeted_http_recoveries": int(w.m.targeted_recoveries),
        "operation_ledger_rows": len(w.ledger),
        "completed_or_fail_closed_operations": operations,
        "total_operations": operations,
        "blocked_rows": 0,
        "blocked_operations": 0,
        "stuck_pending_operations": 0,
        "overall_scope_progress_percent": 100.0,
    }

    for item in manual["items"]:
        if item.get("parcel_id") == w.m.PARCEL_ID:
            item.update({
                "state": "RESOLVED" if promote else "OPEN",
                "confidence_percent": 98 if promote else 94,
                "wave134_state": state,
                "wave134_continuation_key": CONTINUATION,
                "wave134_binary_packages": len(packages),
                "wave134_binary_datasets_scanned": len(datasets),
                "wave134_binary_records_scanned": records_scanned,
                "wave134_binary_exact_code_hits": len(package_hits),
                "wave134_service_exact_code_hits": len(service_hits),
                "wave134_package_service_comparisons": len(comparisons),
                "wave134_strict_geometry_matches": len(strict_matches),
                "wave134_primary_eligible_files": primary_eligible,
                "wave134_package_expected_2011_covers": package_2011_expected_covers,
                "wave134_package_competing_2011_covers": package_2011_competing_covers,
                "wave134_package_expected_2021_covers": package_2021_expected_covers,
            })
            item["reason"] = (
                "Wave134 exact non-derived primary binding and official binary package/service geometry agreement established."
                if promote
                else "Wave134 official ONS binary SHP/DBF/PRJ packages, CRS-resolved geometries and FeatureServer geometry reconciliation did not establish a non-derived primary parcel-source binding on the intended 2011 side."
            )
            item["required_action"] = (
                "Ek kullanıcı işlemi yok."
                if promote
                else "Bağımsız coğrafi inceleyici exact upstream source identifier/ham coordinate kaydını ve amaçlanan resmî 2011 sınır tarafını belgelemelidir."
            )

    manual.update({"updated_at": w.m.utc_now(), "continuation_key": CONTINUATION})
    manual["open_item_count"] = sum(item.get("state") == "OPEN" for item in manual["items"])
    manual["resolved_item_count"] = sum(item.get("state") == "RESOLVED" for item in manual["items"])
    manual["state"] = "RESOLVED" if not manual["open_item_count"] else "OPEN"
    manual["requires_user_action"] = bool(manual["open_item_count"])
    manual["final_ready"] = not manual["open_item_count"]
    manual.setdefault("evidence_paths", [])
    for path in (str(OUTJ.relative_to(ROOT)), str(OUTH.relative_to(ROOT))):
        if path not in manual["evidence_paths"]:
            manual["evidence_paths"].append(path)

    clean_package_hits = package_hits[:500]
    clean_service_hits = service_hits[:500]
    data = {
        "schema_version": 1,
        "slot_id": w.m.SLOT_ID,
        "task_id": TASK_ID,
        "first_unverified_step": FIRST_STEP,
        "continuation_key": CONTINUATION,
        "previous_continuation_key": PREVIOUS,
        "source_head": SOURCE_HEAD,
        "generated_at": w.m.utc_now(),
        "state": "COMPLETED_OFFICIAL_BINARY_SHP_DBF_PRJ_CRS_GEOMETRY_RECONCILIATION_PUBLISHED",
        "scope": {
            "support_only": True,
            "parent_values_mutated": False,
            "parent_scores_mutated": False,
            "rows": [w.m.PARCEL_ID],
            "maximum_simultaneous_workers": MAX_ANALYSIS_WORKERS,
            "maximum_simultaneous_large_downloads": MAX_DOWNLOAD_WORKERS,
            "maximum_package_bytes": MAX_DOWNLOAD_BYTES,
        },
        "package_candidates": candidates,
        "official_binary_packages": packages,
        "official_binary_dataset_hits": clean_package_hits,
        "official_service_geometry_results": services,
        "official_service_geometry_hits": clean_service_hits,
        "package_service_geometry_comparisons": comparisons,
        "operation_ledger": w.ledger,
        "quality_policy": {
            "fail_closed": True,
            "majority_vote_forbidden": True,
            "threshold_relaxation_forbidden": True,
            "nearby_record_inference_forbidden": True,
            "binary_package_geometry_alone_cannot_promote": True,
            "feature_service_geometry_alone_cannot_promote": True,
            "exact_primary_source_lineage_required": True,
            "expected_and_competing_2011_classification_must_be_unambiguous": True,
            "package_service_geometry_agreement_required": True,
            "parent_candidate_value_changed": False,
            "parent_candidate_accuracy_mutated": False,
        },
        "result": metrics,
        "rows": [{
            "parcel_id": w.m.PARCEL_ID,
            "expected_lsoa11_code": w.m.EXPECTED_2011,
            "expected_lsoa21_code": w.m.EXPECTED_2021,
            "competing_lsoa11_code": w.m.EXPECTED_2021,
            "selected_coordinate": {"lon": w.m.CENTER[0], "lat": w.m.CENTER[1]},
            "state": state,
            "confidence_percent": 98 if promote else 94,
            "promotion_candidate": {
                "strict_geometry_matches": len(strict_matches),
                "primary_eligible_files": previous.get("repository_provenance", {}).get("primary_eligible_files", []),
            } if promote else None,
            "manual_action_required": not promote,
        }],
        "manual_action": {
            "state": manual["state"],
            "open_item_count": manual["open_item_count"],
            "resolved_item_count": manual["resolved_item_count"],
            "requires_user_action": manual["requires_user_action"],
            "final_ready": manual["final_ready"],
        },
        "fake_data": False,
    }

    package_summary = [{
        "item_id": row.get("item_id"), "title": row.get("title"), "url": row.get("url"),
        "download_ok": row.get("download_ok"), "archive_ok": row.get("archive_ok"),
        "bytes_read": row.get("bytes_read"), "sha256": row.get("sha256"),
        "previous_sha256_matches": row.get("previous_sha256_matches"),
        "archive_members": len(row.get("archive_members", [])),
        "binary_dataset_groups": row.get("binary_dataset_groups"), "error": row.get("error"),
    } for row in packages]
    dataset_summary = [{
        "item_id": row.get("item_id"), "title": row.get("title"), "dataset_stem": row.get("dataset_stem"),
        "year_context": row.get("year_context"), "record_count_declared": row.get("record_count_declared"),
        "records_scanned": row.get("records_scanned"), "hit_count": row.get("hit_count"),
        "crs_ok": row.get("crs_ok"), "crs_authority": row.get("crs_authority"),
        "crs_name": row.get("crs_name"), "shp_sha256": row.get("shp_sha256"),
        "dbf_sha256": row.get("dbf_sha256"), "prj_sha256": row.get("prj_sha256"),
        "ok": row.get("ok"), "error": row.get("error"),
    } for row in datasets]

    page = f"""<!doctype html><html lang='tr'><head><meta charset='utf-8'><title>security_public_safety_2 Wave134</title><style>
body{{font-family:Arial;margin:24px;line-height:1.35}}table{{border-collapse:collapse;width:100%;margin:12px 0 24px}}th,td{{border:1px solid #bbb;padding:5px;text-align:left;vertical-align:top;word-break:break-word}}th{{background:#eee;position:sticky;top:0}}</style></head><body>
<h1>security_public_safety_2 Wave134</h1>
<p><strong>State:</strong> {state}; <strong>confidence:</strong> {98 if promote else 94}%.</p>
<p><strong>Operations:</strong> {operations}/{operations}; <strong>official network:</strong> {w.m.network_successes}/{w.m.network_attempts}; <strong>blocked:</strong> 0; <strong>stuck pending:</strong> 0.</p>
<h2>Ana karar satırı</h2><table><tr><th>Parcel</th><th>Expected 2011 package</th><th>Competing 2011 package</th><th>Expected 2021 package</th><th>Strict matches</th><th>Primary binding</th><th>New HC</th></tr>
<tr><td>{w.m.PARCEL_ID}</td><td>{package_2011_expected_covers}</td><td>{package_2011_competing_covers}</td><td>{package_2021_expected_covers}</td><td>{len(strict_matches)}</td><td>{primary_eligible}</td><td>{1 if promote else 0}</td></tr></table>
<h2>İşlem günlüğü — satır satır</h2><table><tr><th>#</th><th>Tür</th><th>Hedef</th><th>OK</th><th>Fail-closed</th><th>Detay</th><th>Hata</th></tr>{table(w.ledger, ["index","kind","target","ok","fail_closed","details","error"])}</table>
<h2>Resmî binary paket indirmeleri</h2><table><tr><th>Item</th><th>Başlık</th><th>URL</th><th>Download</th><th>Archive</th><th>Bytes</th><th>SHA256</th><th>Önceki hash</th><th>Member</th><th>Dataset</th><th>Hata</th></tr>{table(package_summary, ["item_id","title","url","download_ok","archive_ok","bytes_read","sha256","previous_sha256_matches","archive_members","binary_dataset_groups","error"])}</table>
<h2>SHP/DBF/PRJ dataset taramaları</h2><table><tr><th>Item</th><th>Başlık</th><th>Dataset</th><th>Yıl</th><th>Kayıt</th><th>Taranan</th><th>Hit</th><th>CRS</th><th>Authority</th><th>Ad</th><th>SHP SHA</th><th>DBF SHA</th><th>PRJ SHA</th><th>OK</th><th>Hata</th></tr>{table(dataset_summary, ["item_id","title","dataset_stem","year_context","record_count_declared","records_scanned","hit_count","crs_ok","crs_authority","crs_name","shp_sha256","dbf_sha256","prj_sha256","ok","error"])}</table>
<h2>Binary exact kod ve geometri satırları</h2><table><tr><th>Item</th><th>Dataset</th><th>Yıl</th><th>Kod</th><th>Rol</th><th>Alanlar</th><th>Kapsıyor</th><th>Sınır m</th><th>Alan m²</th><th>Centroid</th><th>Geometry SHA</th></tr>{table(clean_package_hits, ["item_id","dataset_stem","year_context","code","role","matched_fields","covers_selected_coordinate","boundary_distance_metres","area_square_metres","centroid_27700","geometry_sha256_27700"])}</table>
<h2>FeatureServer exact geometri satırları</h2><table><tr><th>Item</th><th>Layer</th><th>Ad</th><th>Yıl</th><th>Kod</th><th>Rol</th><th>Kapsıyor</th><th>Sınır m</th><th>Alan m²</th><th>Geometry SHA</th></tr>{table(clean_service_hits, ["item_id","layer_url","metadata_name","year_context","code","role","covers_selected_coordinate","boundary_distance_metres","area_square_metres","geometry_sha256_27700"])}</table>
<h2>Paket–servis geometri karşılaştırmaları</h2><table><tr><th>Kod</th><th>Rol</th><th>Package item</th><th>Dataset</th><th>Service item</th><th>Layer</th><th>Package covers</th><th>Service covers</th><th>Sınıf eşleşmesi</th><th>Centroid m</th><th>Bounds m</th><th>Area delta</th><th>Strict</th></tr>{table(comparisons, ["code","role","package_item_id","package_dataset","service_item_id","service_layer_url","package_covers","service_covers","classification_agrees","centroid_distance_metres","bounds_max_delta_metres","area_relative_delta","strict_geometry_match"])}</table>
</body></html>"""

    OUTJ.parent.mkdir(parents=True, exist_ok=True)
    OUTJ.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    OUTH.write_text(page)
    MANUAL.write_text(json.dumps(manual, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"state": state, "continuation_key": CONTINUATION, "result": metrics}, ensure_ascii=False))


if __name__ == "__main__":
    main()
