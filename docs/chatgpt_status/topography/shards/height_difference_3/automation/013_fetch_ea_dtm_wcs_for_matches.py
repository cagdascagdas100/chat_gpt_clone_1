#!/usr/bin/env python3
"""Fetch bounded EA DTM 1m GeoTIFF coverages for HMLR-matched parcels.

The WCS coverage identifier and axis labels are discovered at runtime. Each
response is restricted to the official Environment Agency host and checked with
Rasterio for CRS, finite dimensions, resolution and intersection with the
matched parcel. Missing axis metadata and HTML/error responses fail closed.
Canonical raster paths are materialized only after full download and validation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse
import requests
import rasterio
from pyproj import CRS
from shapely import wkt
from shapely.geometry import box
DEFAULT_WCS = 'https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs'
EA_HOST = 'environment.data.gov.uk'
TARGET_CRS = CRS.from_epsg(27700)
MAX_RESPONSE_BYTES = 500000000

def _local(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]

def _official_ea(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == 'https' and parsed.hostname == EA_HOST

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def _load_matches(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding='utf-8-sig'))
    values = payload.get('results') if isinstance(payload, dict) else None
    if not isinstance(values, list) or not values:
        raise ValueError('matched manifest has no results')
    matched = [dict(value) for value in values if value.get('status') == 'MATCHED' and isinstance(value.get('match'), dict)]
    if len(matched) != len(values):
        raise ValueError('all candidates must have a unique HMLR match before EA WCS download')
    return matched

def _request_xml(session: requests.Session, base: str, params: list[tuple[str, str]], timeout: int) -> tuple[ET.Element, bytes, str]:
    if not _official_ea(base):
        raise ValueError('EA WCS base is not the pinned official host')
    response = session.get(base, params=params, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    if not _official_ea(response.url):
        raise ValueError(f'EA WCS XML request redirected off official host: {response.url}')
    body = response.content
    if not body:
        raise ValueError('WCS XML response is empty')
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise ValueError(f"WCS did not return XML: {response.headers.get('content-type')}") from exc
    return (root, body, response.url)

def _coverage_ids(root: ET.Element) -> list[str]:
    values = []
    for element in root.iter():
        if _local(element.tag) in {'CoverageId', 'Identifier'} and element.text:
            value = element.text.strip()
            if value and value not in values:
                values.append(value)
    return values

def _select_coverage(ids: list[str]) -> str:
    if not ids:
        raise ValueError('WCS GetCapabilities exposed no coverage identifier')
    if len(ids) == 1:
        return ids[0]

    def tokens(value: str) -> set[str]:
        return set(filter(None, re.split('[^a-z0-9]+', value.casefold())))
    preferred = [value for value in ids if 'dtm' in tokens(value) and {'1m', '1'} & tokens(value) and ('elevation' in tokens(value)) and ('hillshade' not in tokens(value))]
    if len(preferred) == 1:
        return preferred[0]
    non_hillshade_dtm = [value for value in ids if 'dtm' in tokens(value) and {'1m', '1'} & tokens(value) and ('hillshade' not in tokens(value))]
    if len(non_hillshade_dtm) == 1:
        return non_hillshade_dtm[0]
    raise ValueError(f'WCS coverage identifier is ambiguous: {ids}')

def _axis_labels(root: ET.Element) -> tuple[str, str]:
    candidates: list[tuple[str, str]] = []
    for element in root.iter():
        if _local(element.tag) in {'Envelope', 'RectifiedGrid'}:
            labels = element.attrib.get('axisLabels')
            if labels:
                parts = labels.split()
                if len(parts) >= 2:
                    pair = (parts[0], parts[1])
                    if pair not in candidates:
                        candidates.append(pair)
    if not candidates:
        raise ValueError('WCS DescribeCoverage exposed no axisLabels; refusing inferred E/N order')
    if len(candidates) > 1:
        normalized = {(a.casefold(), b.casefold()) for a, b in candidates}
        if len(normalized) > 1:
            raise ValueError(f'WCS DescribeCoverage exposed ambiguous axisLabels: {candidates}')
    axis_x, axis_y = candidates[0]
    if axis_x.casefold() not in {'e', 'x', 'easting'} or axis_y.casefold() not in {'n', 'y', 'northing'}:
        raise ValueError(f'unexpected EA WCS axis labels for EPSG:27700: {(axis_x, axis_y)}')
    return (axis_x, axis_y)

def _stream_get(session: requests.Session, base: str, params: list[tuple[str, str]], output: Path, timeout: int) -> dict[str, Any]:
    """Stream one WCS response to a caller-owned temporary file.

    The caller must validate the GeoTIFF and atomically replace the canonical
    destination. A failed network transfer never writes the final path.
    """
    if not _official_ea(base):
        raise ValueError('EA WCS base is not the pinned official host')
    output.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    resolved_url = ''
    content_type = ''
    try:
        with session.get(base, params=params, timeout=timeout, stream=True, allow_redirects=True) as response:
            response.raise_for_status()
            if not _official_ea(response.url):
                raise ValueError(f'EA WCS coverage request redirected off official host: {response.url}')
            resolved_url = response.url
            content_type = response.headers.get('content-type', '')
            with output.open('wb') as handle:
                for chunk in response.iter_content(1024 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_RESPONSE_BYTES:
                        raise ValueError('EA WCS response exceeds safety size limit')
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        if total == 0:
            raise ValueError('EA WCS coverage response is empty')
        with output.open('rb') as handle:
            head = handle.read(512).lstrip().lower()
        if head.startswith(b'<') and (b'exception' in head or b'html' in head):
            raise ValueError('EA WCS returned XML/HTML exception instead of GeoTIFF')
        return {'resolved_url': resolved_url, 'content_type': content_type, 'size_bytes': total}
    except Exception:
        output.unlink(missing_ok=True)
        raise

def _write(path: Path, payload: Any) -> None:
    """Write JSON with destination-local fsync and atomic replacement."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f'.{path.name}_', suffix='.json.tmp', dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with temp.open('w', encoding='utf-8', newline='\n') as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise

def main(argv: Iterable[str] | None=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--matched-manifest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--wcs-base', default=DEFAULT_WCS)
    parser.add_argument('--buffer-m', type=float, default=5.0)
    parser.add_argument('--timeout', type=int, default=120)
    args = parser.parse_args(argv)
    if args.buffer_m < 0 or not math.isfinite(args.buffer_m):
        raise ValueError('buffer-m must be finite and non-negative')
    if not _official_ea(args.wcs_base):
        raise ValueError('EA WCS base is not the pinned official host')
    matches = _load_matches(args.matched_manifest)
    session = requests.Session()
    session.headers.update({'User-Agent': 'TerraYield-AAYS/height_difference_3'})
    capabilities, caps_body, caps_url = _request_xml(session, args.wcs_base, [('service', 'WCS'), ('version', '2.0.1'), ('request', 'GetCapabilities')], args.timeout)
    coverage_id = _select_coverage(_coverage_ids(capabilities))
    description, desc_body, desc_url = _request_xml(session, args.wcs_base, [('service', 'WCS'), ('version', '2.0.1'), ('request', 'DescribeCoverage'), ('coverageId', coverage_id)], args.timeout)
    axis_x, axis_y = _axis_labels(description)
    records = []
    raster_paths = []
    for row in matches:
        geometry = wkt.loads(row['match']['geometry_wkt_epsg27700'])
        if geometry.is_empty or geometry.geom_type not in {'Polygon', 'MultiPolygon'}:
            raise ValueError(f"row {row.get('row_no')} has invalid matched geometry")
        minx, miny, maxx, maxy = geometry.bounds
        minx -= args.buffer_m
        miny -= args.buffer_m
        maxx += args.buffer_m
        maxy += args.buffer_m
        params = [('service', 'WCS'), ('version', '2.0.1'), ('request', 'GetCoverage'), ('coverageId', coverage_id), ('format', 'image/tiff'), ('subset', f'{axis_x}({minx:.3f},{maxx:.3f})'), ('subset', f'{axis_y}({miny:.3f},{maxy:.3f})')]
        output = args.output_dir / 'ea_dtm' / f"row_{int(row['row_no'])}_ea_dtm_1m.tif"
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f'.{output.stem}_', suffix='.tif.tmp', dir=output.parent)
        os.close(fd)
        temp_output = Path(temp_name)
        try:
            meta = _stream_get(session, args.wcs_base, params, temp_output, args.timeout)
            with rasterio.open(temp_output) as dataset:
                if dataset.crs is None:
                    raise ValueError(f"EA raster for row {row.get('row_no')} has no CRS")
                crs = CRS.from_user_input(dataset.crs)
                if crs != TARGET_CRS:
                    raise ValueError(f"EA raster for row {row.get('row_no')} is {crs}, expected EPSG:27700")
                if dataset.width <= 0 or dataset.height <= 0:
                    raise ValueError('EA raster has invalid dimensions')
                if not box(*dataset.bounds).intersects(geometry):
                    raise ValueError('EA raster does not intersect matched parcel geometry')
                resolution = [abs(float(dataset.res[0])), abs(float(dataset.res[1]))]
                if any((not math.isfinite(value) or value <= 0 for value in resolution)):
                    raise ValueError(f'EA raster has invalid resolution: {resolution}')
                if max(resolution) > 1.1:
                    raise ValueError(f'EA raster resolution is coarser than 1.1m: {resolution}')
                record = {'row_no': row.get('row_no'), 'parcel_id': row.get('parcel_id'), 'path': str(output), 'sha256': _sha256(temp_output), 'size_bytes': temp_output.stat().st_size, 'resolved_url': meta['resolved_url'], 'content_type': meta['content_type'], 'crs': crs.to_string(), 'width': dataset.width, 'height': dataset.height, 'resolution_m': resolution, 'bounds': list(map(float, dataset.bounds)), 'nodata': dataset.nodata, 'atomic_materialization': True}
            temp_output.replace(output)
        except Exception:
            temp_output.unlink(missing_ok=True)
            raise
        records.append(record)
        raster_paths.append(str(output))
    manifest = {'schema_version': 3, 'slot_id': 'height_difference_3', 'status': 'READY', 'wcs_base': args.wcs_base, 'official_host': EA_HOST, 'official_host_only': True, 'capabilities_url': caps_url, 'capabilities_sha256': hashlib.sha256(caps_body).hexdigest(), 'describe_coverage_url': desc_url, 'describe_coverage_sha256': hashlib.sha256(desc_body).hexdigest(), 'coverage_id': coverage_id, 'axis_labels': [axis_x, axis_y], 'axis_labels_inferred': False, 'candidate_count': len(records), 'records': records, 'raster_paths': raster_paths, 'atomic_raster_materialization': True, 'partial_canonical_rasters_forbidden': True, 'measurement_values_written': 0, 'manifest_atomic_materialization': True, 'final_ready': False, 'fake_data': False, 'db_write': False, 'migration': False, 'production_deploy': False}
    output_manifest = args.output_dir / 'ea_dtm_source_manifest.json'
    _write(output_manifest, manifest)
    print(json.dumps({'ok': True, 'manifest': str(output_manifest), 'rasters': len(records), 'atomic_raster_materialization': True}))
    return 0
if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': f'{type(exc).__name__}: {exc}'}), file=sys.stderr)
        raise
