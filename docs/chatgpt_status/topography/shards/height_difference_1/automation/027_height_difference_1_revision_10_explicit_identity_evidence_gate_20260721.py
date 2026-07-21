#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
SLOT = "height_difference_1"
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
PAYLOAD_REVISION = 10
ATTEMPT_ID = "official-source-batch-004-revision-10-explicit-identity-evidence-gate"
IDEMPOTENCY_KEY = "height_difference_1-004-20260720"
SCRIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_1/automation/027_height_difference_1_revision_10_explicit_identity_evidence_gate_20260721.py"
REV8_ENTRY = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/012_height_difference_1_revision_8_entry_20260721.py"
REV8_OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/010_geometry_datum_quality_gate_latest.json"
OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/012_revision_10_explicit_identity_evidence_gate_latest.json"
WEB_OUT = REPO / "england_map_web/data/aays_21_slots/height_difference_1/revision_10_explicit_identity_evidence_gate_latest.json"
SNAPSHOT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/012_revision_10_explicit_identity_evidence_manifest_latest.json"
REPORT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/reports/017_height_difference_1_revision_10_explicit_identity_evidence_result.md"

EA_VERTICAL_RMSE_M = 0.15
RANGE_ENDPOINT_RSS_RMSE_M = round(math.sqrt(2.0) * EA_VERTICAL_RMSE_M, 3)
MIN_VALID_PIXELS = 3
MAX_EA_OS_ABSOLUTE_DIFFERENCE_M = 8.0
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")
ALLOWED_AUTHORITIES = {"LONDON BOROUGH OF BARNET", "LONDON BOROUGH OF ENFIELD"}


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def first_value(mapping: Any, *keys: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        if mapping.get(key) is not None:
            return mapping.get(key)
    return None


def nested(mapping: Any, *path: str) -> Any:
    value = mapping
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def valid_digest(value: Any, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and bool(pattern.fullmatch(value.strip()))


def source_text(boundary: Any) -> str:
    if not isinstance(boundary, dict):
        return ""
    parts: list[str] = []
    for key in ("source", "authority", "method", "provider", "source_type"):
        if boundary.get(key) is not None:
            parts.append(str(boundary[key]))
    for key in ("bulk_match", "gml_match", "monthly_gml"):
        child = boundary.get(key)
        if isinstance(child, dict):
            parts.extend(str(child.get(name, "")) for name in ("source", "authority", "method", "provider"))
    return " ".join(parts).upper()


def flatten_ring(value: Any) -> list[list[float]]:
    if isinstance(value, dict):
        value = value.get("coordinates")
    while isinstance(value, list) and value and isinstance(value[0], list) and value[0] and isinstance(value[0][0], list):
        value = value[0]
    ring: list[list[float]] = []
    if isinstance(value, list):
        for point in value:
            if isinstance(point, (list, tuple)) and len(point) >= 2 and finite_number(point[0]) and finite_number(point[1]):
                ring.append([float(point[0]), float(point[1])])
    if len(ring) >= 3 and ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def point_in_polygon(x: float, y: float, ring: list[list[float]]) -> bool:
    if len(ring) < 4:
        return False
    inside = False
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        if min(y1, y2) <= y <= max(y1, y2) and min(x1, x2) <= x <= max(x1, x2):
            cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
            if abs(cross) <= 1e-8:
                return True
        if (y1 > y) != (y2 > y):
            intersect_x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < intersect_x:
                inside = not inside
    return inside


def candidate_bng(row: dict[str, Any]) -> tuple[float, float] | None:
    candidates = [row.get("centroid_epsg27700"), row.get("candidate_epsg27700"), row.get("candidate_bng"), row.get("centroid_bng"), row]
    for item in candidates:
        if not isinstance(item, dict):
            continue
        east = first_value(item, "easting", "x", "bng_easting")
        north = first_value(item, "northing", "y", "bng_northing")
        if finite_number(east) and finite_number(north):
            e, n = float(east), float(north)
            if 0 <= e <= 700000 and 0 <= n <= 1300000:
                return e, n
    return None


def boundary_evidence(row: dict[str, Any]) -> dict[str, Any]:
    boundary = row.get("boundary")
    if not isinstance(boundary, dict):
        return {"ok": False, "reasons": ["BOUNDARY_NOT_OBJECT"]}
    child = first_value(boundary, "bulk_match", "gml_match", "monthly_gml")
    reasons: list[str] = []
    text = source_text(boundary)
    if not any(token in text for token in ("HMLR_INSPIRE_GML", "MONTHLY_GML", "BULK_GML")):
        reasons.append("HMLR_MONTHLY_GML_MARKER_MISSING")
    digest = first_value(boundary, "source_sha256", "gml_sha256", "bulk_sha256")
    if digest is None and isinstance(child, dict):
        digest = first_value(child, "source_sha256", "gml_sha256", "bulk_sha256")
    if not valid_digest(digest, SHA256_RE):
        reasons.append("HMLR_SOURCE_SHA256_INVALID")
    match_flag = first_value(boundary, "match", "matched", "found")
    if match_flag is None and isinstance(child, dict):
        match_flag = first_value(child, "match", "matched", "found")
    if match_flag is not True:
        reasons.append("HMLR_MATCH_FLAG_NOT_TRUE")
    authority = str(first_value(boundary, "authority", "local_authority", "localAuthority") or "").strip().upper()
    if not authority and isinstance(child, dict):
        authority = str(first_value(child, "authority", "local_authority", "localAuthority") or "").strip().upper()
    if authority not in ALLOWED_AUTHORITIES:
        reasons.append("HMLR_AUTHORITY_NOT_BARNET_OR_ENFIELD")
    inspire_id = first_value(boundary, "inspire_id", "inspireId", "local_id", "localId", "cadastral_id", "national_cadastral_reference")
    if inspire_id is None and isinstance(child, dict):
        inspire_id = first_value(child, "inspire_id", "inspireId", "local_id", "localId", "cadastral_id", "national_cadastral_reference")
    if not str(inspire_id or "").strip():
        reasons.append("HMLR_INSPIRE_IDENTIFIER_MISSING")
    geometry = first_value(boundary, "ring", "polygon", "coordinates")
    if geometry is None and isinstance(child, dict):
        geometry = first_value(child, "ring", "polygon", "coordinates")
    ring = flatten_ring(geometry)
    if len(ring) < 4:
        reasons.append("HMLR_GEOMETRY_INVALID")
    coords = candidate_bng(row)
    explicit_inside = first_value(boundary, "point_inside_polygon", "centroid_inside_polygon", "candidate_inside_polygon", "inside_polygon")
    if explicit_inside is None and isinstance(child, dict):
        explicit_inside = first_value(child, "point_inside_polygon", "centroid_inside_polygon", "candidate_inside_polygon", "inside_polygon")
    recomputed_inside = bool(coords and ring and point_in_polygon(coords[0], coords[1], ring))
    if explicit_inside is not True and not recomputed_inside:
        reasons.append("HMLR_CANDIDATE_POINT_NOT_PROVEN_INSIDE")
    crs = str(first_value(boundary, "crs", "horizontal_crs", "srs_name", "srsName") or "").upper()
    if not crs and isinstance(child, dict):
        crs = str(first_value(child, "crs", "horizontal_crs", "srs_name", "srsName") or "").upper()
    if "27700" not in crs:
        reasons.append("HMLR_HORIZONTAL_CRS_NOT_EPSG27700")
    return {"ok": not reasons, "reasons": reasons, "authority": authority, "inspire_id": str(inspire_id or ""), "source_sha256": str(digest or ""), "horizontal_crs": "EPSG:27700", "candidate_bng": {"easting": coords[0], "northing": coords[1]} if coords else None, "candidate_inside_polygon_recomputed": recomputed_inside}


def resolution_pair(stats: dict[str, Any]) -> tuple[float, float] | None:
    resolution = first_value(stats, "resolution", "pixel_size", "cell_size")
    if finite_number(resolution):
        return float(resolution), float(resolution)
    if isinstance(resolution, (list, tuple)) and len(resolution) >= 2 and finite_number(resolution[0]) and finite_number(resolution[1]):
        return abs(float(resolution[0])), abs(float(resolution[1]))
    x = first_value(stats, "resolution_x", "pixel_size_x", "cell_size_x")
    y = first_value(stats, "resolution_y", "pixel_size_y", "cell_size_y")
    if finite_number(x) and finite_number(y):
        return abs(float(x)), abs(float(y))
    transform = stats.get("transform")
    if isinstance(transform, (list, tuple)) and len(transform) >= 6 and finite_number(transform[0]) and finite_number(transform[4]):
        return abs(float(transform[0])), abs(float(transform[4]))
    return None


def range_from_stats(stats: Any) -> dict[str, Any]:
    if not isinstance(stats, dict) or not bool(stats.get("ok")):
        return {"ok": False, "error": "EA_POLYGON_STATISTICS_MISSING"}
    aliases = {"min_m": ("min_m", "min", "minimum_m", "minimum"), "max_m": ("max_m", "max", "maximum_m", "maximum"), "median_m": ("median_m", "median"), "iqr_m": ("iqr_m", "iqr"), "pixel_count": ("pixel_count", "valid_pixel_count", "count")}
    values = {name: first_value(stats, *keys) for name, keys in aliases.items()}
    if not all(finite_number(values[name]) for name in aliases):
        return {"ok": False, "error": "EA_POLYGON_STATISTICS_NON_NUMERIC"}
    minimum, maximum = float(values["min_m"]), float(values["max_m"])
    median, iqr, pixel_count = float(values["median_m"]), float(values["iqr_m"]), int(values["pixel_count"])
    if not (minimum <= median <= maximum and 0.0 <= iqr <= maximum - minimum):
        return {"ok": False, "error": "EA_POLYGON_STATISTICS_ORDER_INVALID"}
    if pixel_count < MIN_VALID_PIXELS:
        return {"ok": False, "error": "EA_POLYGON_PIXEL_COUNT_BELOW_3", "pixel_count": pixel_count}
    crs = str(first_value(stats, "crs", "horizontal_crs", "srs", "srs_name") or "").upper()
    if "27700" not in crs:
        return {"ok": False, "error": "EA_HORIZONTAL_CRS_NOT_EPSG27700"}
    vertical = str(first_value(stats, "vertical_crs", "vertical_reference", "datum") or "").upper()
    if not ("5701" in vertical or "ORDNANCE DATUM NEWLYN" in vertical or vertical == "ODN"):
        return {"ok": False, "error": "EA_VERTICAL_REFERENCE_NOT_ODN"}
    resolution = resolution_pair(stats)
    if resolution is None or not (0 < resolution[0] <= 1.10 and 0 < resolution[1] <= 1.10):
        return {"ok": False, "error": "EA_RESOLUTION_NOT_1M_CLASS"}
    return {"ok": True, "minimum_elevation_m_odn": round(minimum, 3), "maximum_elevation_m_odn": round(maximum, 3), "median_elevation_m_odn": round(median, 3), "height_difference_m": round(maximum - minimum, 3), "iqr_m": round(iqr, 3), "pixel_count": pixel_count, "resolution_m": [round(resolution[0], 6), round(resolution[1], 6)], "source_vertical_rmse_m": EA_VERTICAL_RMSE_M, "range_endpoint_rss_rmse_m": RANGE_ENDPOINT_RSS_RMSE_M, "horizontal_crs": "EPSG:27700", "vertical_crs": "EPSG:5701", "vertical_reference": "Ordnance Datum Newlyn", "metric_definition": "maximum_minus_minimum_EA_DTM_1m_pixels_inside_official_HMLR_polygon"}


def os_evidence(row: dict[str, Any]) -> dict[str, Any]:
    sample = row.get("os_terrain50")
    if not isinstance(sample, dict) or not bool(sample.get("ok")):
        return {"ok": False, "reasons": ["OS_TERRAIN50_NOT_OK"]}
    reasons: list[str] = []
    elevation = first_value(sample, "elevation_m", "height_m", "value_m", "value")
    if not finite_number(elevation):
        reasons.append("OS_TERRAIN50_ELEVATION_NON_NUMERIC")
    crs = str(first_value(sample, "crs", "horizontal_crs", "srs", "srs_name") or "").upper()
    if "27700" not in crs:
        reasons.append("OS_HORIZONTAL_CRS_NOT_EPSG27700")
    vertical = str(first_value(sample, "vertical_crs", "vertical_reference", "datum") or "").upper()
    if not ("5701" in vertical or "ORDNANCE DATUM NEWLYN" in vertical or vertical == "ODN"):
        reasons.append("OS_VERTICAL_REFERENCE_NOT_ODN")
    header_candidates = [sample.get("header"), row.get("os_terrain50_header"), nested(row, "source_results", "os_terrain50", "header"), nested(row, "source_results", "os", "header")]
    header = next((item for item in header_candidates if isinstance(item, dict)), {})
    ncols, nrows = first_value(header, "ncols", "columns"), first_value(header, "nrows", "rows")
    cellsize = first_value(header, "cellsize", "cell_size", "resolution")
    if not (finite_number(ncols) and int(ncols) == 200 and finite_number(nrows) and int(nrows) == 200):
        reasons.append("OS_GRID_HEADER_NOT_200_BY_200")
    if not finite_number(cellsize) or abs(float(cellsize) - 50.0) > 1e-9:
        reasons.append("OS_GRID_CELLSIZE_NOT_50M")
    row_index, col_index = first_value(sample, "row", "row_index"), first_value(sample, "col", "column", "col_index")
    if not (finite_number(row_index) and 0 <= int(row_index) < 200 and finite_number(col_index) and 0 <= int(col_index) < 200):
        reasons.append("OS_GRID_INDEX_OUT_OF_RANGE")
    nodata_value = first_value(header, "NODATA_value", "nodata_value", "nodata")
    if bool(sample.get("nodata") or sample.get("is_nodata")) or (finite_number(nodata_value) and finite_number(elevation) and float(elevation) == float(nodata_value)):
        reasons.append("OS_TERRAIN50_NODATA")
    expected_md5 = first_value(sample, "expected_md5", "official_md5", "md5_expected")
    actual_md5 = first_value(sample, "actual_md5", "download_md5", "md5")
    if expected_md5 is not None:
        if not (valid_digest(expected_md5, MD5_RE) and valid_digest(actual_md5, MD5_RE) and str(expected_md5).lower() == str(actual_md5).lower()):
            reasons.append("OS_MD5_NOT_VERIFIED")
    return {"ok": not reasons, "reasons": reasons, "elevation_m_odn": round(float(elevation), 3) if finite_number(elevation) else None, "header": {"ncols": ncols, "nrows": nrows, "cellsize": cellsize}, "grid_index": {"row": row_index, "col": col_index}, "horizontal_crs": "EPSG:27700", "vertical_crs": "EPSG:5701", "vertical_reference": "Ordnance Datum Newlyn", "role": "independent_absolute_elevation_and_datum_crosscheck_not_parcel_range"}


def apply_gate(result: dict[str, Any]) -> dict[str, Any]:
    rows = result.get("rows") if isinstance(result.get("rows"), list) else []
    accepted, valid_ranges, conflict_rows = 0, 0, 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        boundary = boundary_evidence(row)
        metric = range_from_stats(row.get("ea_dtm_1m_polygon"))
        os_check = os_evidence(row)
        upstream_accept = bool(row.get("accepted_measured_row"))
        declared_conflict = bool(row.get("human_review_required") or row.get("hmlr_bulk_wfs_conflict"))
        ea_os_difference = None
        if metric.get("ok") and os_check.get("ok"):
            ea_os_difference = round(abs(float(metric["median_elevation_m_odn"]) - float(os_check["elevation_m_odn"])), 3)
        numeric_conflict = ea_os_difference is not None and ea_os_difference > MAX_EA_OS_ABSOLUTE_DIFFERENCE_M
        conflict = declared_conflict or numeric_conflict
        if conflict:
            conflict_rows += 1
        accepted_row = upstream_accept and boundary["ok"] and metric["ok"] and os_check["ok"] and not conflict
        row["revision_10_evidence_gate"] = {"upstream_revision_8_accepted": upstream_accept, "boundary": boundary, "ea_height_difference": metric, "os_independent_crosscheck": os_check, "ea_os_median_absolute_difference_m": ea_os_difference, "maximum_allowed_ea_os_difference_m": MAX_EA_OS_ABSOLUTE_DIFFERENCE_M, "conflict_free": not conflict, "accepted": accepted_row}
        row["height_difference"] = metric
        row["human_review_required"] = conflict
        row["accepted_measured_row"] = accepted_row
        row["metric_name"] = "parcel_ground_height_difference"
        row["metric_unit"] = "metre"
        row["independent_os_role"] = "absolute_elevation_and_vertical_datum_crosscheck_not_parcel_range_measurement"
        row["same_provider_resolution_checks_role"] = "EA_2m_and_10m_are_consistency_checks_not_independent_sources"
        if metric.get("ok"):
            valid_ranges += 1
        if accepted_row:
            accepted += 1
            row["output_semantics"] = "MEASURED_OFFICIAL_PARCEL_GROUND_HEIGHT_DIFFERENCE"
            row["accuracy_score_4"] = "3.5/4"
        elif conflict:
            row["output_semantics"] = "HUMAN_REVIEW_REQUIRED_NOT_MEASURED"
            row["accuracy_score_4"] = "2.5/4 not_measured"
        else:
            row["output_semantics"] = "NO_DATA_NOT_INFERRED"
            row["accuracy_score_4"] = "2.5/4 fallback"

    digest = script_sha256()
    counts = result.setdefault("counts", {})
    counts.update({"candidate_rows": len(rows), "ea_1m_valid_height_difference_rows": valid_ranges, "official_three_source_height_difference_rows": accepted, "official_three_source_measured_rows": accepted, "human_review_rows": conflict_rows})
    result.update({"schema_version": max(int(result.get("schema_version", 0) or 0), 10), "slot_id": SLOT, "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "attempt_id": ATTEMPT_ID, "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL, "script_sha256": digest, "status": "MEASURED_OFFICIAL_HEIGHT_DIFFERENCE_ROWS_AVAILABLE" if accepted else "NO_DATA_NOT_INFERRED", "metric_contract": {"layer_key": "height_difference", "metric_name": "parcel_ground_height_difference", "definition": "maximum minus minimum EA DTM 1m elevation among valid pixels inside the official HMLR parcel polygon", "unit": "metre", "primary_numeric_source": "Environment Agency LIDAR Composite DTM 1m", "independent_source": "OS Terrain 50", "independent_source_role": "absolute elevation and shared ODN datum crosscheck; 50m grid is not parcel-range measurement", "minimum_valid_ea_pixels": MIN_VALID_PIXELS, "maximum_ea_os_absolute_difference_m": MAX_EA_OS_ABSOLUTE_DIFFERENCE_M, "ea_source_vertical_rmse_m": EA_VERTICAL_RMSE_M, "indicative_range_endpoint_rss_rmse_m": RANGE_ENDPOINT_RSS_RMSE_M, "horizontal_crs": "EPSG:27700", "vertical_crs": "EPSG:5701", "vertical_reference": "Ordnance Datum Newlyn", "no_data_policy": "NO_DATA_NOT_INFERRED"}, "acceptance": {"upstream_revision_8_quality_gate_required": True, "official_monthly_hmlr_bulk_gml_required": True, "hmlr_candidate_point_inside_polygon_required": True, "minimum_valid_ea_1m_pixels": MIN_VALID_PIXELS, "ea_height_difference_definition": "max_minus_min", "os_terrain50_parcel_range_promotion_forbidden": True, "ea_os_difference_over_8m_requires_human_review": True, "unresolved_conflict_promotion_forbidden": True}, "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False})
    return result


def main() -> int:
    if not REV8_ENTRY.exists():
        raise SystemExit(f"revision_8_entry_missing:{REV8_ENTRY}")
    completed = subprocess.run([sys.executable, str(REV8_ENTRY)], cwd=str(REPO), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    if not REV8_OUT.exists():
        raise SystemExit(f"revision_8_output_missing:{REV8_OUT}")
    source = json.loads(REV8_OUT.read_text(encoding="utf-8-sig"))
    if not isinstance(source, dict):
        raise SystemExit("revision_8_output_root_not_object")
    result = apply_gate(source)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    for path in (OUT, WEB_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    output_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    snapshot = {"schema_version": 2, "slot_id": SLOT, "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "attempt_id": ATTEMPT_ID, "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL, "script_sha256": result["script_sha256"], "runner_web_output_sha256": output_sha, "metric_contract": result["metric_contract"], "candidate_rows": result.get("counts", {}).get("candidate_rows", 0), "valid_height_difference_rows": result.get("counts", {}).get("ea_1m_valid_height_difference_rows", 0), "accepted_official_height_difference_rows": result.get("counts", {}).get("official_three_source_height_difference_rows", 0), "human_review_rows": result.get("counts", {}).get("human_review_rows", 0), "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("# Height Difference 1 revision 10 explicit identity and evidence gate\n\n" f"- Candidate rows: `{snapshot['candidate_rows']}`\n" f"- Valid EA 1m height-difference rows: `{snapshot['valid_height_difference_rows']}`\n" f"- Accepted official height-difference rows: `{snapshot['accepted_official_height_difference_rows']}`\n" f"- Human-review rows: `{snapshot['human_review_rows']}`\n" f"- Script SHA-256: `{snapshot['script_sha256']}`\n" f"- Runner/web output SHA-256: `{snapshot['runner_web_output_sha256']}`\n" "- Explicit task/revision/attempt/idempotency/script identity is embedded in output.\n" "- HMLR point-in-polygon, EA 1m resolution/statistics, OS 200x200/50m/ODN and >8m conflict gates are revalidated.\n" "- `final_ready=false`\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result.get("counts", {}), "output": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
