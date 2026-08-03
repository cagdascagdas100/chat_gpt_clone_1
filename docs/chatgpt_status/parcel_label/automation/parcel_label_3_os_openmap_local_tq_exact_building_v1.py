#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone

from pyproj import Transformer
from shapely.geometry import Point, Polygon, mapping
from shapely.ops import transform as shapely_transform, unary_union

INPUT = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json")
OUTPUTS = [
    pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/os_openmap_local_tq_exact_building_result_latest.json"),
    pathlib.Path("england_map_web/data/aays_21_slots/parcel_label_3/os_openmap_local_tq_exact_building_latest.json"),
]
LISTING_URL = "https://api.os.uk/downloads/v1/products/OpenMapLocal/downloads?area=TQ&format=GML"
DOC_URL = "https://docs.os.uk/os-downloads/products/maps-and-imagery-portfolio/os-openmap-local"
API_DOC_URL = "https://docs.os.uk/os-apis/accessing-os-apis/os-downloads-api/technical-specification/download-an-opendata-product"
BUILDING_SPEC_URL = "https://docs.os.uk/os-downloads/contextual-or-derived-mapping/os-openmap-local/os-openmap-local-technical-specification/feature-types/building"
LICENSE_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_LISTING_BYTES = 4 * 1024 * 1024
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_GML_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024
ALLOWED_DOWNLOAD_SUFFIXES = (".os.uk", ".amazonaws.com", ".blob.core.windows.net")
TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
TO_WGS84 = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        tmp = pathlib.Path(handle.name)
    tmp.replace(path)


def validate_https(url: str, *, listing: bool = False) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").casefold()
    if parsed.scheme.casefold() != "https" or parsed.username or parsed.password or parsed.fragment:
        raise RuntimeError(f"UNSAFE_URL:{url}")
    if listing:
        if host != "api.os.uk":
            raise RuntimeError(f"UNTRUSTED_LISTING_HOST:{host}")
    elif host != "api.os.uk" and not any(host.endswith(suffix) for suffix in ALLOWED_DOWNLOAD_SUFFIXES):
        raise RuntimeError(f"UNTRUSTED_DOWNLOAD_HOST:{host}")
    return url


def bounded_fetch(url: str, timeout: int, max_bytes: int, *, listing: bool = False) -> tuple[bytes, str, int]:
    validate_https(url, listing=listing)
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label-3/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        validate_https(final_url, listing=listing and urllib.parse.urlsplit(final_url).hostname == "api.os.uk")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(min(1024 * 1024, max_bytes - total + 1))
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError(f"RESPONSE_TOO_LARGE:{total}:{max_bytes}")
            chunks.append(chunk)
        return b"".join(chunks), final_url, int(getattr(response, "status", 200))


def load_rows() -> list[dict]:
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = payload.get("records", [])
    if len(rows) != 3:
        raise RuntimeError(f"EXPECTED_3_ROWS:{len(rows)}")
    required = {"parcel_id", "UPRN", "FULLADDRESS", "longitude", "latitude"}
    for row in rows:
        missing = sorted(required - set(row))
        if missing or not row.get("exact_uprn_bound"):
            raise RuntimeError(f"INVALID_INPUT_ROW:{row.get('parcel_id')}:{missing}")
        easting, northing = TO_BNG.transform(float(row["longitude"]), float(row["latitude"]))
        row["easting"] = float(easting)
        row["northing"] = float(northing)
        row["os_grid_100km"] = "TQ" if 500000 <= easting < 600000 and 100000 <= northing < 200000 else "OUTSIDE_TQ"
    if {row["os_grid_100km"] for row in rows} != {"TQ"}:
        raise RuntimeError("TARGETS_NOT_ALL_IN_TQ")
    return rows


def select_download(listing_bytes: bytes) -> dict:
    payload = json.loads(listing_bytes)
    if not isinstance(payload, list):
        raise RuntimeError("OS_DOWNLOAD_LIST_NOT_ARRAY")
    matches = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        area = str(item.get("area", "")).strip().upper()
        fmt = str(item.get("format", "")).strip().casefold()
        filename = str(item.get("fileName", "")).strip()
        url = str(item.get("url", "")).strip()
        if area == "TQ" and "gml" in fmt and filename and url:
            validate_https(url)
            matches.append({
                "area": area,
                "format": str(item.get("format", "")).strip(),
                "fileName": filename,
                "url": url,
                "size": item.get("size"),
                "md5": item.get("md5"),
                "version": item.get("version"),
            })
    unique = {(item["fileName"], item["url"]): item for item in matches}
    if len(unique) != 1:
        raise RuntimeError(f"OS_DOWNLOAD_AMBIGUOUS_OR_MISSING_TQ_GML:{len(unique)}")
    return next(iter(unique.values()))


def parse_poslist(text: str, dimension: int = 2) -> list[tuple[float, float]]:
    values = [float(value) for value in text.split()]
    if dimension < 2 or len(values) < dimension * 4 or len(values) % dimension:
        return []
    coords = [(values[i], values[i + 1]) for i in range(0, len(values), dimension)]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    return coords


def first_poslist(element: ET.Element) -> list[tuple[float, float]]:
    for node in element.iter():
        if local_name(node.tag) == "posList" and node.text:
            dimension = int(node.attrib.get("srsDimension", "2"))
            coords = parse_poslist(node.text, dimension)
            if coords:
                return coords
    return []


def building_geometry(building: ET.Element):
    polygons = []
    candidates = [
        node for node in building.iter()
        if local_name(node.tag) in {"Polygon", "PolygonPatch"}
    ]
    for polygon_node in candidates:
        exterior = []
        holes = []
        for child in polygon_node.iter():
            name = local_name(child.tag)
            if name == "exterior" and not exterior:
                exterior = first_poslist(child)
            elif name == "interior":
                ring = first_poslist(child)
                if ring:
                    holes.append(ring)
        if not exterior:
            exterior = first_poslist(polygon_node)
        if len(exterior) >= 4:
            try:
                polygon = Polygon(exterior, holes)
                if not polygon.is_valid:
                    polygon = polygon.buffer(0)
                if not polygon.is_empty:
                    polygons.append(polygon)
            except Exception:
                continue
    if not polygons:
        return None
    geometry = unary_union(polygons)
    if not geometry.is_valid:
        geometry = geometry.buffer(0)
    return None if geometry.is_empty else geometry


def scan_archive(archive_bytes: bytes, rows: list[dict]) -> tuple[dict[str, list[dict]], dict]:
    targets = {
        str(row["UPRN"]): Point(row["easting"], row["northing"])
        for row in rows
    }
    matches: dict[str, list[dict]] = {uprn: [] for uprn in targets}
    stats = {"gml_entries": [], "building_features_scanned": 0, "uncompressed_bytes": 0}
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        entries = [name for name in archive.namelist() if name.casefold().endswith((".gml", ".xml"))]
        if not entries:
            raise RuntimeError("OS_ARCHIVE_HAS_NO_GML")
        for entry_name in sorted(entries):
            info = archive.getinfo(entry_name)
            stats["uncompressed_bytes"] += int(info.file_size)
            if stats["uncompressed_bytes"] > MAX_GML_UNCOMPRESSED_BYTES:
                raise RuntimeError(f"OS_GML_UNCOMPRESSED_TOO_LARGE:{stats['uncompressed_bytes']}")
            stats["gml_entries"].append({"name": entry_name, "size": int(info.file_size)})
            with archive.open(entry_name) as stream:
                context = ET.iterparse(stream, events=("end",))
                for _event, element in context:
                    if local_name(element.tag) != "Building":
                        continue
                    stats["building_features_scanned"] += 1
                    geometry = building_geometry(element)
                    if geometry is not None:
                        feature_id = next(
                            (value for key, value in element.attrib.items() if local_name(key) == "id"),
                            None,
                        )
                        for uprn, point in targets.items():
                            if len(matches[uprn]) > 1:
                                continue
                            if geometry.covers(point):
                                wgs84 = shapely_transform(TO_WGS84.transform, geometry)
                                geometry_obj = mapping(wgs84)
                                geometry_text = json.dumps(geometry_obj, separators=(",", ":"), sort_keys=True)
                                matches[uprn].append({
                                    "gml_id": feature_id,
                                    "gml_entry": entry_name,
                                    "feature_scan_index": stats["building_features_scanned"],
                                    "geometry": geometry_obj,
                                    "geometry_sha256": hashlib.sha256(geometry_text.encode("utf-8")).hexdigest(),
                                    "area_m2": round(float(geometry.area), 3),
                                })
                    element.clear()
    return matches, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    rows = load_rows()
    if args.validate_only:
        print(json.dumps({
            "valid": True,
            "input_count": len(rows),
            "os_grid_100km": sorted({row["os_grid_100km"] for row in rows}),
            "resource_class": "geometry",
            "listing_url": LISTING_URL,
            "write_paths": [str(path) for path in OUTPUTS],
            "max_listing_bytes": MAX_LISTING_BYTES,
            "max_archive_bytes": MAX_ARCHIVE_BYTES,
        }, sort_keys=True))
        return 0

    evidence = {
        "listing_url": LISTING_URL,
        "documentation_url": DOC_URL,
        "api_documentation_url": API_DOC_URL,
        "building_specification_url": BUILDING_SPEC_URL,
        "license_url": LICENSE_URL,
        "accessed_at": utc_now(),
        "target_area": "TQ",
    }
    records = []
    matched_count = 0
    try:
        listing_bytes, listing_final_url, listing_status = bounded_fetch(
            LISTING_URL, args.timeout, MAX_LISTING_BYTES, listing=True
        )
        evidence.update({
            "listing_final_url": listing_final_url,
            "listing_http_status": listing_status,
            "listing_bytes": len(listing_bytes),
            "listing_content_sha256": sha256_bytes(listing_bytes),
        })
        selected = select_download(listing_bytes)
        evidence["selected_download_record"] = selected
        archive_bytes, archive_final_url, archive_status = bounded_fetch(
            selected["url"], args.timeout, MAX_ARCHIVE_BYTES
        )
        matches, scan_stats = scan_archive(archive_bytes, rows)
        evidence.update({
            "archive_final_url": archive_final_url,
            "archive_http_status": archive_status,
            "archive_bytes": len(archive_bytes),
            "archive_content_sha256": sha256_bytes(archive_bytes),
            "scan_stats": scan_stats,
        })
        for row in rows:
            uprn = str(row["UPRN"])
            candidates = matches.get(uprn, [])
            record = {
                "parcel_id": row["parcel_id"],
                "UPRN": uprn,
                "FULLADDRESS": row["FULLADDRESS"],
                "longitude": float(row["longitude"]),
                "latitude": float(row["latitude"]),
                "easting": round(row["easting"], 3),
                "northing": round(row["northing"], 3),
                "os_grid_100km": row["os_grid_100km"],
                "source_url": archive_final_url,
                "candidate_count": len(candidates),
                "exact_uprn_bound": True,
                "inferred": False,
            }
            if len(candidates) == 1:
                record.update({"state": "MATCHED_UNIQUE_POINT_CONTAINING_OS_BUILDING", **candidates[0]})
                matched_count += 1
            elif len(candidates) > 1:
                record.update({"state": "NO_DATA", "reason": "AMBIGUOUS_MULTIPLE_POINT_CONTAINING_OS_BUILDINGS"})
            else:
                record.update({"state": "NO_DATA", "reason": "NO_POINT_CONTAINING_OS_BUILDING"})
            records.append(record)
    except Exception as exc:
        evidence["error"] = f"{type(exc).__name__}:{exc}"
        for row in rows:
            records.append({
                "parcel_id": row["parcel_id"],
                "UPRN": str(row["UPRN"]),
                "FULLADDRESS": row["FULLADDRESS"],
                "longitude": float(row["longitude"]),
                "latitude": float(row["latitude"]),
                "easting": round(row["easting"], 3),
                "northing": round(row["northing"], 3),
                "os_grid_100km": row["os_grid_100km"],
                "source_url": LISTING_URL,
                "candidate_count": 0,
                "state": "NO_DATA",
                "reason": evidence["error"],
                "exact_uprn_bound": True,
                "inferred": False,
            })

    state = "PUBLISHED" if matched_count else "NO_DATA_CONTINUE"
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": "parcel-label-3-os-openmap-local-tq-exact-building-v1-20260803",
        "state": state,
        "panel_status": "PUBLISHED",
        "completed_count": len(records),
        "target_count": 3,
        "previous_percent": 0.0,
        "progress_percent": round(len(records) / 3 * 100, 6),
        "percent_increase": round(len(records) / 3 * 100, 6),
        "matched_exact_building_rows": matched_count,
        "evidence_records": len(records),
        "source_evidence": evidence,
        "records": records,
        "large_raw_files_committed": False,
        "fake_data": False,
        "generated_at": utc_now(),
    }
    text = json.dumps(result, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    for output in OUTPUTS:
        atomic_write(output, text)
    print(json.dumps({
        "completed_count": len(records),
        "target_count": 3,
        "matched_exact_building_rows": matched_count,
        "state": state,
        "output_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
