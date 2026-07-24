#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import requests
import rasterio
from lxml import etree
from rasterio.io import MemoryFile
from rasterio.mask import mask
from shapely.geometry import Point, shape

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
SLOT = "height_difference_1"
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
PAYLOAD_REVISION = 12
ATTEMPT_ID = "official-source-batch-004-revision-12-direct-ea-pixel-center-resample"
IDEMPOTENCY_KEY = "height_difference_1-004-20260720"
SCRIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_1/automation/035_height_difference_1_revision_12_direct_ea_pixel_center_resample_20260721.py"

REV8_ENTRY = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/012_height_difference_1_revision_8_entry_20260721.py"
REV8_OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/010_geometry_datum_quality_gate_latest.json"
REV10_MODULE = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/027_height_difference_1_revision_10_explicit_identity_evidence_gate_20260721.py"
REV11_MODULE = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/032_height_difference_1_revision_11_pixel_center_sampling_provenance_20260721.py"

OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/014_revision_12_direct_ea_pixel_center_resample_latest.json"
WEB_OUT = REPO / "england_map_web/data/aays_21_slots/height_difference_1/revision_12_direct_ea_pixel_center_resample_latest.json"
SNAPSHOT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/014_revision_12_direct_ea_pixel_center_resample_manifest_latest.json"
REPORT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/reports/019_height_difference_1_revision_12_direct_ea_pixel_center_resample_result.md"

DEFAULT_WCS = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
MAX_RESPONSE_BYTES = 250_000_000
NODATA_FLOOR = -1.0e30
MIN_VALID_PIXELS = 3


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def first_value(mapping: Any, *keys: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        if mapping.get(key) is not None:
            return mapping.get(key)
    return None


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def script_sha256() -> str:
    return sha256_bytes(Path(__file__).read_bytes())


def load_module(path: Path, name: str):
    if not path.is_file():
        raise FileNotFoundError(f"module_missing:{path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module_spec_failed:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def xml_root(content: bytes) -> etree._Element:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)
    return etree.fromstring(content, parser=parser)


def get(session: requests.Session, url: str, params: dict[str, Any], timeout: int) -> requests.Response:
    response = session.get(url, params=params, timeout=timeout, allow_redirects=True, stream=False)
    response.raise_for_status()
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("EA_WCS_RESPONSE_EXCEEDS_SAFETY_LIMIT")
    return response


def discover_coverage(session: requests.Session, base_url: str, timeout: int, override: str | None) -> tuple[str, dict[str, Any]]:
    response = get(session, base_url, {"service": "WCS", "version": "2.0.1", "request": "GetCapabilities"}, timeout)
    root = xml_root(response.content)
    coverage_ids = list(dict.fromkeys((node.text or "").strip() for node in root.xpath("//*[local-name()='CoverageId']") if (node.text or "").strip()))
    if override:
        if override not in coverage_ids:
            raise ValueError("CONFIGURED_COVERAGE_ID_ABSENT_FROM_CAPABILITIES")
        selected = override
    else:
        ranked = [value for value in coverage_ids if re.search(r"dtm", value, re.I) and re.search(r"(^|[^0-9])1\s*m([^0-9]|$)|1m", value, re.I)]
        if len(ranked) != 1:
            raise ValueError(f"UNIQUE_DTM_1M_COVERAGE_ID_NOT_FOUND:{ranked!r}")
        selected = ranked[0]
    return selected, {"capabilities_url": response.url, "capabilities_sha256": sha256_bytes(response.content), "coverage_ids_seen": coverage_ids}


def describe_coverage(session: requests.Session, base_url: str, timeout: int, coverage_id: str) -> dict[str, Any]:
    response = get(session, base_url, {"service": "WCS", "version": "2.0.1", "request": "DescribeCoverage", "coverageId": coverage_id}, timeout)
    root = xml_root(response.content)
    axis_values: list[str] = []
    for node in root.xpath("//*[@axisLabels]"):
        axis_values.extend(str(node.attrib.get("axisLabels", "")).split())
    axis_values = [value for value in axis_values if value]
    if len(axis_values) < 2:
        axis_values = ["E", "N"]
    return {"describe_url": response.url, "describe_sha256": sha256_bytes(response.content), "axis_labels": axis_values[:2]}


def download_geotiff(session: requests.Session, base_url: str, timeout: int, coverage_id: str, axis_labels: list[str], bounds: tuple[float, float, float, float], padding_m: float) -> tuple[bytes, str]:
    minx, miny, maxx, maxy = bounds
    params: list[tuple[str, str]] = [
        ("service", "WCS"), ("version", "2.0.1"), ("request", "GetCoverage"), ("coverageId", coverage_id), ("format", "image/tiff"),
        ("subsettingCrs", "http://www.opengis.net/def/crs/EPSG/0/27700"), ("outputCrs", "http://www.opengis.net/def/crs/EPSG/0/27700"),
        ("subset", f"{axis_labels[0]}({minx - padding_m:.3f},{maxx + padding_m:.3f})"), ("subset", f"{axis_labels[1]}({miny - padding_m:.3f},{maxy + padding_m:.3f})"),
    ]
    response = session.get(base_url, params=params, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    content = response.content
    if not content or len(content) > MAX_RESPONSE_BYTES:
        raise ValueError("EA_WCS_GETCOVERAGE_EMPTY_OR_OVERSIZED")
    content_type = response.headers.get("content-type", "").lower()
    head = content[:512].lstrip().lower()
    if b"exceptionreport" in head or b"serviceexception" in head or head.startswith(b"<"):
        raise ValueError("EA_WCS_GETCOVERAGE_RETURNED_XML_ERROR")
    if "tiff" not in content_type and not content.startswith((b"II*\x00", b"MM\x00*")):
        raise ValueError(f"EA_WCS_RESPONSE_NOT_GEOTIFF:{content_type!r}")
    return content, response.url


def extract_boundary_geometry(row: dict[str, Any]) -> dict[str, Any]:
    boundary = row.get("boundary")
    if not isinstance(boundary, dict):
        raise ValueError("BOUNDARY_NOT_OBJECT")
    child = first_value(boundary, "bulk_match", "gml_match", "monthly_gml")
    candidates = [first_value(boundary, "geometry_geojson_epsg27700", "geometry", "polygon", "coordinates", "ring")]
    if isinstance(child, dict):
        candidates.append(first_value(child, "geometry_geojson_epsg27700", "geometry", "polygon", "coordinates", "ring"))
    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, dict) and candidate.get("type") in {"Polygon", "MultiPolygon"}:
            geom = candidate
        else:
            coords = candidate.get("coordinates") if isinstance(candidate, dict) else candidate
            if not isinstance(coords, list) or not coords:
                continue
            def coordinate_depth(value: Any) -> int:
                depth = 0
                while isinstance(value, list) and value:
                    depth += 1
                    value = value[0]
                return depth
            depth = coordinate_depth(coords)
            if depth == 2:
                geom = {"type": "Polygon", "coordinates": [coords]}
            elif depth == 3:
                geom = {"type": "Polygon", "coordinates": coords}
            elif depth == 4:
                geom = {"type": "MultiPolygon", "coordinates": coords}
            else:
                continue
        shaped = shape(geom)
        if shaped.is_empty or shaped.geom_type not in {"Polygon", "MultiPolygon"} or not shaped.is_valid:
            continue
        return geom
    raise ValueError("OFFICIAL_HMLR_GEOMETRY_NOT_EXTRACTABLE")


def sampling_mask_sha256(valid_mask: np.ndarray, transform: rasterio.Affine) -> str:
    header = json.dumps({"shape": [int(valid_mask.shape[0]), int(valid_mask.shape[1])], "transform": [float(value) for value in transform[:6]], "bit_order": "row_major_packbits_big"}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    packed = np.packbits(valid_mask.astype(np.uint8).ravel(order="C"), bitorder="big").tobytes()
    return sha256_bytes(header + b"\n" + packed)


def selected_centers_sha256(xs: list[float], ys: list[float]) -> str:
    digest = hashlib.sha256()
    for x, y in zip(xs, ys):
        digest.update(f"{x:.6f},{y:.6f}\n".encode("ascii"))
    return digest.hexdigest()


def sample_polygon(content: bytes, geometry: dict[str, Any]) -> dict[str, Any]:
    official_polygon = shape(geometry)
    if official_polygon.is_empty or not official_polygon.is_valid:
        raise ValueError("OFFICIAL_HMLR_POLYGON_INVALID_FOR_SAMPLING")
    with MemoryFile(content) as memfile:
        with memfile.open() as dataset:
            epsg = dataset.crs.to_epsg() if dataset.crs else None
            if epsg != 27700:
                raise ValueError(f"EA_RASTER_CRS_NOT_EPSG27700:{dataset.crs}")
            data, out_transform = mask(dataset, [geometry], crop=True, all_touched=False, filled=False)
            band = np.ma.asarray(data[0], dtype="float64")
            array = np.asarray(band.filled(np.nan), dtype="float64")
            valid = (~np.ma.getmaskarray(band)) & np.isfinite(array) & (array > NODATA_FLOOR)
            rows, cols = np.nonzero(valid)
            if rows.size < MIN_VALID_PIXELS:
                raise ValueError(f"EA_DTM_VALID_PIXEL_COUNT_BELOW_{MIN_VALID_PIXELS}:{rows.size}")
            xs_raw, ys_raw = rasterio.transform.xy(out_transform, rows.tolist(), cols.tolist(), offset="center")
            xs = [float(value) for value in xs_raw]
            ys = [float(value) for value in ys_raw]
            centers_inside = all(official_polygon.covers(Point(x, y)) for x, y in zip(xs, ys))
            if not centers_inside:
                raise ValueError("RASTERIO_MASK_SELECTED_CENTER_OUTSIDE_OFFICIAL_POLYGON")
            values = array[valid]
            q1, median, q3 = np.quantile(values, [0.25, 0.5, 0.75])
            area = float(official_polygon.area)
            resolution = [abs(float(dataset.transform.a)), abs(float(dataset.transform.e))]
            return {
                "ok": True, "min_m": round(float(values.min()), 3), "max_m": round(float(values.max()), 3), "median_m": round(float(median), 3),
                "q1_m": round(float(q1), 3), "q3_m": round(float(q3), 3), "iqr_m": round(float(q3 - q1), 3), "pixel_count": int(values.size),
                "resolution": resolution, "horizontal_crs": "EPSG:27700", "vertical_crs": "EPSG:5701", "vertical_reference": "Ordnance Datum Newlyn",
                "raster_width": int(dataset.width), "raster_height": int(dataset.height), "raster_nodata": dataset.nodata,
                "sampling_provenance": {
                    "pixel_inclusion_policy": "pixel_center_inside_official_hmlr_polygon", "all_touched": False, "pixel_centers_inside_polygon": True,
                    "valid_pixel_count": int(values.size), "mask_sha256": sampling_mask_sha256(valid, out_transform),
                    "selected_pixel_centers_sha256": selected_centers_sha256(xs, ys), "polygon_area_m2": area,
                    "raster_mask_shape": [int(valid.shape[0]), int(valid.shape[1])], "cropped_transform": [float(value) for value in out_transform[:6]],
                    "reference_implementation": "rasterio.mask(all_touched=False,filled=False,crop=True)",
                },
            }


def main() -> int:
    timeout = int(os.environ.get("AAYS_EA_WCS_TIMEOUT_SECONDS", "120"))
    padding_m = float(os.environ.get("AAYS_EA_WCS_PADDING_M", "2.0"))
    coverage_override = os.environ.get("AAYS_EA_DTM1M_COVERAGE_ID") or None
    wcs_url = os.environ.get("AAYS_EA_DTM1M_WCS_URL", DEFAULT_WCS)
    if not REV8_ENTRY.is_file():
        raise SystemExit(f"revision_8_entry_missing:{REV8_ENTRY}")
    completed = subprocess.run([sys.executable, str(REV8_ENTRY)], cwd=str(REPO), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    if not REV8_OUT.is_file():
        raise SystemExit(f"revision_8_output_missing:{REV8_OUT}")
    result = json.loads(REV8_OUT.read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise SystemExit("revision_8_output_root_not_object")
    rows = result.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("revision_8_rows_not_list")
    rev10 = load_module(REV10_MODULE, "height_difference_1_rev10")
    rev11 = load_module(REV11_MODULE, "height_difference_1_rev11")
    session = requests.Session()
    session.headers.update({"User-Agent": "TerraYield-AAYS/height_difference_1-revision-12"})
    coverage_id, capabilities = discover_coverage(session, wcs_url, timeout, coverage_override)
    description = describe_coverage(session, wcs_url, timeout, coverage_id)
    direct_sample_rows = 0
    direct_sample_errors = 0
    direct_sample_error_details: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            boundary_check = rev10.boundary_evidence(row)
            if not boundary_check.get("ok"):
                raise ValueError("REVISION_10_BOUNDARY_EVIDENCE_NOT_ACCEPTED")
            geometry = extract_boundary_geometry(row)
            shaped = shape(geometry)
            content, resolved_url = download_geotiff(session, wcs_url, timeout, coverage_id, description["axis_labels"], shaped.bounds, padding_m)
            sample = sample_polygon(content, geometry)
            sample.update({
                "source": "Environment Agency LIDAR Composite DTM 1m WCS", "coverage_id": coverage_id,
                "resolved_getcoverage_url": resolved_url, "geotiff_sha256": sha256_bytes(content),
                "capabilities_sha256": capabilities["capabilities_sha256"], "describe_coverage_sha256": description["describe_sha256"],
                "geometry_source": "official HMLR INSPIRE polygon EPSG:27700", "centroid_fallback_used": False,
            })
            row["ea_dtm_1m_polygon"] = sample
            row["revision_12_direct_ea_resample"] = {"ok": True, "error": None}
            direct_sample_rows += 1
        except Exception as exc:
            row["ea_dtm_1m_polygon"] = {"ok": False, "error": f"{type(exc).__name__}:{exc}"}
            row["revision_12_direct_ea_resample"] = {"ok": False, "error": f"{type(exc).__name__}:{exc}"}
            row["accepted_measured_row"] = False
            row["output_semantics"] = "NO_DATA_NOT_INFERRED_DIRECT_EA_RESAMPLE_FAILED"
            direct_sample_errors += 1
            direct_sample_error_details.append({"parcel_id": str(row.get("parcel_id") or row.get("parcel_ref") or ""), "error": f"{type(exc).__name__}:{exc}"})
    result = rev10.apply_gate(result)
    result = rev11.apply_gate(result)
    digest = script_sha256()
    counts = result.setdefault("counts", {})
    counts["revision_12_direct_ea_resample_rows"] = direct_sample_rows
    counts["revision_12_direct_ea_resample_error_rows"] = direct_sample_errors
    result.update({
        "schema_version": max(int(result.get("schema_version", 0) or 0), 12), "slot_id": SLOT, "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION,
        "attempt_id": ATTEMPT_ID, "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL, "script_sha256": digest,
        "ea_wcs_source_contract": {"base_url": wcs_url, "service": "WCS", "version": "2.0.1", "coverage_id": coverage_id,
            "capabilities_url": capabilities["capabilities_url"], "capabilities_sha256": capabilities["capabilities_sha256"],
            "describe_url": description["describe_url"], "describe_sha256": description["describe_sha256"], "axis_labels": description["axis_labels"],
            "horizontal_crs": "EPSG:27700", "vertical_crs": "EPSG:5701", "vertical_reference": "Ordnance Datum Newlyn"},
        "direct_ea_resample_errors": direct_sample_error_details,
        "direct_sampling_contract": {"official_hmlr_geometry_required": True, "centroid_fallback_forbidden": True, "all_touched": False,
            "pixel_center_verification_required": True, "sampling_mask_sha256_required": True, "selected_pixel_centers_sha256_required": True,
            "minimum_valid_pixels": MIN_VALID_PIXELS},
        "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False,
    })
    accepted = int(counts.get("official_three_source_height_difference_rows", 0) or 0)
    if direct_sample_errors:
        result["status"] = "BLOCKED_DIRECT_EA_PIXEL_CENTER_RESAMPLE"
    else:
        result["status"] = "MEASURED_OFFICIAL_HEIGHT_DIFFERENCE_ROWS_AVAILABLE" if accepted else "NO_DATA_NOT_INFERRED"
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    for path in (OUT, WEB_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    output_sha = sha256_bytes(text.encode("utf-8"))
    snapshot = {"schema_version": 1, "slot_id": SLOT, "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "attempt_id": ATTEMPT_ID,
        "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL, "script_sha256": digest, "runner_web_output_sha256": output_sha,
        "candidate_rows": counts.get("candidate_rows", 0), "direct_ea_resample_rows": direct_sample_rows,
        "direct_ea_resample_error_rows": direct_sample_errors, "pixel_center_sampling_provenance_rows": counts.get("pixel_center_sampling_provenance_rows", 0),
        "accepted_official_height_difference_rows": accepted, "ea_wcs_source_contract": result["ea_wcs_source_contract"],
        "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("# Height Difference 1 revision 12 direct EA pixel-center resample\n\n" f"- Candidate rows: `{snapshot['candidate_rows']}`\n" f"- Direct EA WCS resample rows: `{direct_sample_rows}`\n" f"- Direct EA WCS resample errors: `{direct_sample_errors}`\n" f"- Pixel-center provenance rows: `{snapshot['pixel_center_sampling_provenance_rows']}`\n" f"- Accepted official height-difference rows: `{accepted}`\n" f"- Script SHA-256: `{digest}`\n" f"- Runner/web output SHA-256: `{output_sha}`\n" "- Sampling is performed directly from the official EA DTM 1m WCS against the official HMLR polygon.\n" "- `all_touched=false`; every selected pixel center is rechecked with the polygon; mask and center-list SHA-256 values are recorded.\n" "- `final_ready=false`\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": counts, "output": str(OUT)}))
    return 2 if direct_sample_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
