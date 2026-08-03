#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import pathlib
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from shapely.geometry import Point, mapping, shape

INPUT = pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json")
OUTPUTS = [
    pathlib.Path("docs/chatgpt_status/_shared/slots_21/parcel_label_3/microsoft_globalml_exact_building_result_latest.json"),
    pathlib.Path("england_map_web/data/aays_21_slots/parcel_label_3/microsoft_globalml_exact_building_latest.json"),
]
INDEX_URL = "https://bfppub.blob.core.windows.net/%24web/2026-07-24/dataset-links.csv"
DOC_URL = "https://github.com/microsoft/GlobalMLBuildingFootprints"
LICENSE_URL = "https://cdla.dev/permissive-2-0/"
ALLOWED_HOST = "bfppub.blob.core.windows.net"
ZOOM = 9
MAX_INDEX_BYTES = 24 * 1024 * 1024
MAX_TILE_BYTES = 64 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 256 * 1024 * 1024
TARGET_LOCATION_MARKERS = ("united kingdom", "great britain", "uk")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        tmp = pathlib.Path(handle.name)
    tmp.replace(path)


def quadkey(lon: float, lat: float, zoom: int = ZOOM) -> str:
    lat = max(min(float(lat), 85.05112878), -85.05112878)
    x = (float(lon) + 180.0) / 360.0
    sin_lat = math.sin(math.radians(lat))
    y = 0.5 - math.log((1.0 + sin_lat) / (1.0 - sin_lat)) / (4.0 * math.pi)
    scale = 1 << zoom
    tile_x = int(min(max(x * scale, 0), scale - 1))
    tile_y = int(min(max(y * scale, 0), scale - 1))
    digits: list[str] = []
    for level in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (level - 1)
        if tile_x & mask:
            digit += 1
        if tile_y & mask:
            digit += 2
        digits.append(str(digit))
    return "".join(digits)


def validate_https_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.casefold() != "https":
        raise RuntimeError("MICROSOFT_BUILDING_URL_NOT_HTTPS")
    if parsed.username or parsed.password or parsed.fragment:
        raise RuntimeError("MICROSOFT_BUILDING_URL_UNSAFE_COMPONENT")
    if (parsed.hostname or "").casefold() != ALLOWED_HOST:
        raise RuntimeError(f"MICROSOFT_BUILDING_URL_UNTRUSTED_HOST:{parsed.hostname}")
    return url


def bounded_fetch(url: str, timeout: int, max_bytes: int) -> tuple[bytes, str, int]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-parcel-label-3/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = validate_https_url(response.geturl())
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(min(1024 * 1024, max_bytes - total + 1))
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError(f"MICROSOFT_BUILDING_RESPONSE_TOO_LARGE:{total}:{max_bytes}")
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
        row["quadkey_l9"] = quadkey(float(row["longitude"]), float(row["latitude"]))
    return rows


def is_uk_location(value: str) -> bool:
    normalized = " ".join(value.casefold().replace("_", " ").split())
    return any(marker in normalized for marker in TARGET_LOCATION_MARKERS)


def select_index_rows(index_bytes: bytes, required_quadkeys: set[str]) -> dict[str, dict]:
    text = index_bytes.decode("utf-8-sig", errors="strict")
    reader = csv.DictReader(io.StringIO(text))
    required_columns = {"Location", "QuadKey", "Url"}
    if not reader.fieldnames or not required_columns.issubset(reader.fieldnames):
        raise RuntimeError(f"MICROSOFT_INDEX_SCHEMA_MISMATCH:{reader.fieldnames}")
    candidates: dict[str, list[dict]] = {key: [] for key in required_quadkeys}
    for row in reader:
        qk = str(row.get("QuadKey", "")).strip()
        if qk not in candidates:
            continue
        if not is_uk_location(str(row.get("Location", ""))):
            continue
        url = validate_https_url(str(row.get("Url", "")).strip())
        item = {
            "Location": str(row.get("Location", "")).strip(),
            "QuadKey": qk,
            "Url": url,
            "Size": str(row.get("Size", "")).strip() or None,
            "UploadDate": str(row.get("UploadDate", "")).strip() or None,
        }
        candidates[qk].append(item)
    selected: dict[str, dict] = {}
    for qk, items in candidates.items():
        if not items:
            raise RuntimeError(f"MICROSOFT_INDEX_NO_UK_ROW:{qk}")
        items.sort(key=lambda item: (item.get("UploadDate") or "", item["Url"]), reverse=True)
        top_date = items[0].get("UploadDate")
        same_top = [item for item in items if item.get("UploadDate") == top_date]
        unique_urls = {item["Url"] for item in same_top}
        if len(unique_urls) != 1:
            raise RuntimeError(f"MICROSOFT_INDEX_AMBIGUOUS_TOP_ROW:{qk}:{len(unique_urls)}")
        selected[qk] = items[0]
    return selected


def geometry_candidate(obj: dict) -> tuple[object | None, dict]:
    if obj.get("type") == "Feature":
        geometry_obj = obj.get("geometry")
        properties = obj.get("properties") or {}
    elif "geometry" in obj:
        geometry_obj = obj.get("geometry")
        properties = obj.get("properties") or {}
    else:
        geometry_obj = obj
        properties = {}
    if not isinstance(geometry_obj, dict):
        return None, properties
    if geometry_obj.get("type") not in {"Polygon", "MultiPolygon"}:
        return None, properties
    try:
        geom = shape(geometry_obj)
        if not geom.is_valid:
            geom = geom.buffer(0)
        if geom.is_empty:
            return None, properties
        return geom, properties
    except Exception:
        return None, properties


def scan_tile(tile_bytes: bytes, rows: list[dict], quadkey_value: str) -> tuple[dict[str, list[dict]], int]:
    targets = {
        str(row["UPRN"]): Point(float(row["longitude"]), float(row["latitude"]))
        for row in rows
        if row["quadkey_l9"] == quadkey_value
    }
    matches: dict[str, list[dict]] = {uprn: [] for uprn in targets}
    decompressed = 0
    line_number = 0
    with gzip.GzipFile(fileobj=io.BytesIO(tile_bytes), mode="rb") as stream:
        for raw_line in stream:
            line_number += 1
            decompressed += len(raw_line)
            if decompressed > MAX_UNCOMPRESSED_BYTES:
                raise RuntimeError(f"MICROSOFT_TILE_UNCOMPRESSED_TOO_LARGE:{decompressed}")
            if not raw_line.strip():
                continue
            try:
                obj = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            geom, properties = geometry_candidate(obj)
            if geom is None:
                continue
            for uprn, point in targets.items():
                if len(matches[uprn]) > 1:
                    continue
                if geom.contains(point) or geom.touches(point):
                    geometry_obj = mapping(geom)
                    geometry_text = json.dumps(geometry_obj, separators=(",", ":"), sort_keys=True)
                    evidence_properties = {
                        key: properties[key]
                        for key in ("height", "confidence", "source", "is_inner")
                        if key in properties
                    }
                    matches[uprn].append({
                        "tile_line_number": line_number,
                        "geometry": geometry_obj,
                        "geometry_sha256": hashlib.sha256(geometry_text.encode("utf-8")).hexdigest(),
                        "polygon_area_degrees2": round(float(geom.area), 12),
                        "properties": evidence_properties,
                    })
    return matches, decompressed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    rows = load_rows()
    quadkeys = sorted({row["quadkey_l9"] for row in rows})
    if args.validate_only:
        print(json.dumps({
            "valid": True,
            "input_count": len(rows),
            "quadkeys_l9": quadkeys,
            "resource_class": "geometry",
            "index_url": INDEX_URL,
            "write_paths": [str(path) for path in OUTPUTS],
            "max_index_bytes": MAX_INDEX_BYTES,
            "max_tile_bytes": MAX_TILE_BYTES,
        }, sort_keys=True))
        return 0

    accessed_at = utc_now()
    evidence: dict = {
        "documentation_url": DOC_URL,
        "license_url": LICENSE_URL,
        "index_url": INDEX_URL,
        "accessed_at": accessed_at,
        "quadkeys_l9": quadkeys,
    }
    records: list[dict] = []
    matched_count = 0
    try:
        index_bytes, final_index_url, index_status = bounded_fetch(INDEX_URL, args.timeout, MAX_INDEX_BYTES)
        evidence.update({
            "index_final_url": final_index_url,
            "index_http_status": index_status,
            "index_bytes": len(index_bytes),
            "index_content_sha256": sha256_bytes(index_bytes),
        })
        selected = select_index_rows(index_bytes, set(quadkeys))
        evidence["selected_index_rows"] = selected
        tile_results: dict[str, dict] = {}
        all_matches: dict[str, list[dict]] = {}
        for qk in quadkeys:
            tile_row = selected[qk]
            tile_bytes, final_tile_url, tile_status = bounded_fetch(tile_row["Url"], args.timeout, MAX_TILE_BYTES)
            matches, uncompressed_bytes = scan_tile(
                tile_bytes,
                [row for row in rows if row["quadkey_l9"] == qk],
                qk,
            )
            all_matches.update(matches)
            tile_results[qk] = {
                "url": final_tile_url,
                "http_status": tile_status,
                "compressed_bytes": len(tile_bytes),
                "compressed_content_sha256": sha256_bytes(tile_bytes),
                "uncompressed_bytes": uncompressed_bytes,
                "index_record": tile_row,
            }
        evidence["tiles"] = tile_results

        for row in rows:
            uprn = str(row["UPRN"])
            candidates = all_matches.get(uprn, [])
            record = {
                "parcel_id": row["parcel_id"],
                "UPRN": uprn,
                "FULLADDRESS": row["FULLADDRESS"],
                "longitude": float(row["longitude"]),
                "latitude": float(row["latitude"]),
                "quadkey_l9": row["quadkey_l9"],
                "source_url": selected[row["quadkey_l9"]]["Url"],
                "exact_uprn_bound": True,
                "inferred": False,
                "candidate_count": len(candidates),
            }
            if len(candidates) == 1:
                record.update({"state": "MATCHED_UNIQUE_POINT_CONTAINING_BUILDING", **candidates[0]})
                matched_count += 1
            elif len(candidates) > 1:
                record.update({"state": "NO_DATA", "reason": "AMBIGUOUS_MULTIPLE_POINT_CONTAINING_BUILDINGS"})
            else:
                record.update({"state": "NO_DATA", "reason": "NO_POINT_CONTAINING_BUILDING"})
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
                "quadkey_l9": row["quadkey_l9"],
                "source_url": INDEX_URL,
                "state": "NO_DATA",
                "reason": evidence["error"],
                "exact_uprn_bound": True,
                "inferred": False,
                "candidate_count": 0,
            })

    state = "PUBLISHED" if matched_count else "NO_DATA_CONTINUE"
    result = {
        "schema_version": 1,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "parcel_label_3",
        "task_id": "parcel-label-3-microsoft-globalml-exact-building-v1-20260803",
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
