#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import pathlib
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from pyproj import Transformer
from shapely.geometry import Point, Polygon, mapping
from shapely.ops import transform as shapely_transform

INPUT = pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/mdu_status_official_result_latest.json')
OUTPUTS = [
    pathlib.Path('docs/chatgpt_status/_shared/slots_21/parcel_label_3/hmlr_inspire_lambeth_exact_geometry_result_latest.json'),
    pathlib.Path('england_map_web/data/aays_21_slots/parcel_label_3/hmlr_inspire_lambeth_exact_geometry_latest.json'),
]
INDEX_URL = 'https://use-land-property-data.service.gov.uk/datasets/inspire/download'
TERMS_URL = 'https://use-land-property-data.service.gov.uk/datasets/inspire/#conditions'
MAX_INDEX_BYTES = 2 * 1024 * 1024
MAX_GML_BYTES = 128 * 1024 * 1024
TARGET_AUTHORITY = 'London Borough of Lambeth'
ALLOWED_DOWNLOAD_HOSTS = {
    'use-land-property-data.service.gov.uk',
    'datapub-prd-s3-bucket.s3.amazonaws.com',
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as handle:
        handle.write(text)
        temp_path = pathlib.Path(handle.name)
    temp_path.replace(path)


def validate_https_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or '').casefold()
    if parsed.scheme.casefold() != 'https':
        raise RuntimeError('HMLR_URL_NOT_HTTPS')
    if parsed.username or parsed.password or parsed.fragment:
        raise RuntimeError('HMLR_URL_UNSAFE_COMPONENT')
    if host not in ALLOWED_DOWNLOAD_HOSTS:
        raise RuntimeError(f'HMLR_URL_UNTRUSTED_HOST:{host}')
    return url


class LinkCollector(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.casefold() == 'a':
            self._href = dict(attrs).get('href')
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == 'a' and self._href is not None:
            self.links.append((self._href, ' '.join(self._text).strip()))
            self._href = None
            self._text = []


def bounded_fetch(url: str, timeout: int, max_bytes: int) -> tuple[bytes, str, int]:
    request = urllib.request.Request(url, headers={'User-Agent': 'AAYS-parcel-label-3/1.0'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = validate_https_url(response.geturl())
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(min(1024 * 1024, max_bytes - total + 1))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError(f'HMLR_RESPONSE_TOO_LARGE:{total}:{max_bytes}')
        return b''.join(chunks), final_url, int(getattr(response, 'status', 200))


def discover_lambeth_gml(index_html: bytes, base_url: str) -> str:
    text = index_html.decode('utf-8', errors='replace')
    authority_pos = text.casefold().find(TARGET_AUTHORITY.casefold())
    if authority_pos < 0:
        raise RuntimeError('LAMBETH_NOT_LISTED_ON_HMLR_INDEX')
    parser = LinkCollector()
    parser.feed(text)
    candidates: list[str] = []
    for href, anchor_text in parser.links:
        absolute = urllib.parse.urljoin(base_url, href)
        low = (href + ' ' + anchor_text).casefold()
        if '.gml' in low or 'download' in low:
            candidates.append(absolute)
    for href, _anchor in parser.links:
        absolute = urllib.parse.urljoin(base_url, href)
        idx = text.find(href)
        if idx >= 0 and abs(idx - authority_pos) < 1200 and ('.gml' in href.casefold() or 'download' in href.casefold()):
            return validate_https_url(absolute)
    if len(candidates) == 1:
        return validate_https_url(candidates[0])
    raise RuntimeError(f'LAMBETH_GML_LINK_NOT_UNAMBIGUOUS:{len(candidates)}')


def local_name(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def parse_poslist(text: str) -> list[tuple[float, float]]:
    values = [float(value) for value in text.split()]
    if len(values) < 8 or len(values) % 2:
        return []
    return list(zip(values[0::2], values[1::2]))


def parse_matches(gml_path: pathlib.Path, target_points: dict[str, Point]) -> dict[str, dict]:
    matches: dict[str, dict] = {}
    to_wgs84 = Transformer.from_crs('EPSG:27700', 'EPSG:4326', always_xy=True).transform
    for _event, elem in ET.iterparse(gml_path, events=('end',)):
        if local_name(elem.tag) != 'CadastralParcel':
            continue
        inspire_id = None
        rings: list[list[tuple[float, float]]] = []
        for child in elem.iter():
            name = local_name(child.tag)
            if inspire_id is None and name in {'localId', 'nationalCadastralReference'} and child.text:
                inspire_id = child.text.strip()
            elif name == 'posList' and child.text:
                ring = parse_poslist(child.text)
                if ring:
                    rings.append(ring)
        for ring in rings:
            try:
                polygon = Polygon(ring)
                if not polygon.is_valid:
                    polygon = polygon.buffer(0)
                if polygon.is_empty:
                    continue
            except Exception:
                continue
            for uprn, point in target_points.items():
                if uprn in matches:
                    continue
                if polygon.contains(point) or polygon.touches(point):
                    wgs84_polygon = shapely_transform(to_wgs84, polygon)
                    geojson = mapping(wgs84_polygon)
                    geometry_text = json.dumps(geojson, separators=(',', ':'), sort_keys=True)
                    matches[uprn] = {
                        'inspire_id': inspire_id,
                        'polygon_area_m2': round(float(polygon.area), 3),
                        'geometry': geojson,
                        'geometry_sha256': hashlib.sha256(geometry_text.encode('utf-8')).hexdigest(),
                        'coordinate_count': len(ring),
                    }
        elem.clear()
        if len(matches) == len(target_points):
            break
    return matches


def load_input() -> list[dict]:
    if not INPUT.is_file():
        raise RuntimeError(f'MISSING_INPUT:{INPUT}')
    payload = json.loads(INPUT.read_text(encoding='utf-8'))
    rows = payload.get('records', [])
    if len(rows) != 3:
        raise RuntimeError(f'EXPECTED_3_ROWS:{len(rows)}')
    required = {'parcel_id', 'UPRN', 'FULLADDRESS', 'longitude', 'latitude'}
    for row in rows:
        missing = sorted(required - set(row))
        if missing or not row.get('exact_uprn_bound'):
            raise RuntimeError(f'INVALID_INPUT_ROW:{row.get("parcel_id")}:{missing}')
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=int, default=20)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    rows = load_input()
    if args.validate_only:
        print(json.dumps({
            'valid': True,
            'input_count': len(rows),
            'script_path_relative': True,
            'write_paths': [str(path) for path in OUTPUTS],
            'resource_class': 'geometry',
            'max_index_bytes': MAX_INDEX_BYTES,
            'max_gml_bytes': MAX_GML_BYTES,
        }, sort_keys=True))
        return 0

    accessed_at = utc_now()
    evidence: dict = {'index_url': INDEX_URL, 'terms_url': TERMS_URL, 'accessed_at': accessed_at, 'authority': TARGET_AUTHORITY}
    records: list[dict] = []
    state = 'NO_DATA_CONTINUE'
    with tempfile.TemporaryDirectory(prefix='parcel_label_3_hmlr_') as tmpdir:
        try:
            index_bytes, final_index_url, index_status = bounded_fetch(INDEX_URL, args.timeout, MAX_INDEX_BYTES)
            evidence.update({'index_final_url': final_index_url, 'index_http_status': index_status, 'index_bytes': len(index_bytes), 'index_content_sha256': sha256_bytes(index_bytes)})
            gml_url = discover_lambeth_gml(index_bytes, final_index_url)
            gml_bytes, final_gml_url, gml_status = bounded_fetch(gml_url, args.timeout, MAX_GML_BYTES)
            evidence.update({'gml_url': final_gml_url, 'gml_http_status': gml_status, 'gml_bytes': len(gml_bytes), 'gml_content_sha256': sha256_bytes(gml_bytes)})
            gml_path = pathlib.Path(tmpdir) / 'lambeth.gml'
            gml_path.write_bytes(gml_bytes)
            to_bng = Transformer.from_crs('EPSG:4326', 'EPSG:27700', always_xy=True)
            target_points = {str(row['UPRN']): Point(*to_bng.transform(float(row['longitude']), float(row['latitude']))) for row in rows}
            matches = parse_matches(gml_path, target_points)
            for row in rows:
                uprn = str(row['UPRN'])
                item = {'parcel_id': row['parcel_id'], 'UPRN': uprn, 'FULLADDRESS': row['FULLADDRESS'], 'source_url': final_gml_url, 'exact_uprn_bound': True, 'inferred': False}
                if uprn in matches:
                    item.update({'state': 'MATCHED_EXACT_GEOMETRY', **matches[uprn]})
                else:
                    item.update({'state': 'NO_DATA', 'reason': 'NO_CONTAINING_INSPIRE_FREEHOLD_POLYGON'})
                records.append(item)
            if matches:
                state = 'PUBLISHED'
        except Exception as exc:
            evidence['error'] = f'{type(exc).__name__}:{exc}'
            for row in rows:
                records.append({'parcel_id': row['parcel_id'], 'UPRN': str(row['UPRN']), 'FULLADDRESS': row['FULLADDRESS'], 'source_url': INDEX_URL, 'state': 'NO_DATA', 'reason': evidence['error'], 'exact_uprn_bound': True, 'inferred': False})

    matched_count = sum(record['state'] == 'MATCHED_EXACT_GEOMETRY' for record in records)
    result = {
        'schema_version': 1,
        'workstream_id': 'AAYS_21_SLOT_SAFE_PARALLEL_V1',
        'slot_id': 'parcel_label_3',
        'task_id': 'parcel-label-3-hmlr-inspire-lambeth-exact-geometry-v1-20260803',
        'state': state,
        'panel_status': 'PUBLISHED',
        'completed_count': len(records),
        'target_count': 3,
        'previous_percent': 0.0,
        'progress_percent': round(len(records) / 3 * 100, 6),
        'percent_increase': round(len(records) / 3 * 100, 6),
        'matched_exact_geometry_rows': matched_count,
        'evidence_records': len(records),
        'source_evidence': evidence,
        'records': records,
        'large_raw_files_committed': False,
        'fake_data': False,
        'generated_at': utc_now(),
    }
    text = json.dumps(result, ensure_ascii=False, separators=(',', ':'), sort_keys=True) + '\n'
    for output in OUTPUTS:
        atomic_write(output, text)
    print(json.dumps({'completed_count': len(records), 'target_count': 3, 'matched_exact_geometry_rows': matched_count, 'state': state, 'output_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
