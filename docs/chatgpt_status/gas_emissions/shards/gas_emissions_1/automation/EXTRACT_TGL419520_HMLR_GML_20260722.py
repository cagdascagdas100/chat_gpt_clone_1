#!/usr/bin/env python3
"""Read-only HMLR INSPIRE proximity extraction for gas_emissions_1.

HM Land Registry INSPIRE polygons cover registered freehold property and expose
INSPIRE polygon identifiers, not a guaranteed leasehold title-number field.
TGL419520 is described in official charge records as leasehold. Therefore this
script shortlists freehold INSPIRE polygons near the current permit point and
never claims that any candidate is TGL419520 or a parcel intersection.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_1"
TARGET_TITLE_CONTEXT = "TGL419520"
TARGET_TITLE_TENURE_CONTEXT = "LEASEHOLD_FROM_OFFICIAL_COMPANY_CHARGE_DESCRIPTION"
AUTHORITY = "London Borough of Barking and Dagenham"
INDEX_URL = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
USER_AGENT = "AAYS-gas_emissions_1-hmlr-inspire-proximity-audit/2.0"
TARGET_EASTING = 548335.0
TARGET_NORTHING = 182947.0
SEARCH_RADIUS_METRES = 300.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str, timeout: int = 180) -> tuple[bytes | None, str | None]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
        if not data:
            return None, "ZERO_BYTE_DOWNLOAD"
        return data, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def resolve_authority_gml(index_html: str) -> tuple[str | None, str | None]:
    escaped = re.escape(AUTHORITY)
    patterns = (
        rf"<tr[^>]*>.*?{escaped}.*?<a[^>]+href=[\"']([^\"']+)[\"']",
        rf"{escaped}.{{0,1800}}?<a[^>]+href=[\"']([^\"']+\.gml[^\"']*)[\"']",
    )
    for pattern in patterns:
        match = re.search(pattern, index_html, flags=re.I | re.S)
        if match:
            return urllib.parse.urljoin(INDEX_URL, match.group(1)), None
    return None, "BARKING_DAGENHAM_GML_LINK_NOT_RESOLVED"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def numbers(text: str) -> list[float]:
    result: list[float] = []
    for token in re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text):
        try:
            result.append(float(token))
        except ValueError:
            continue
    return result


def coordinate_pairs(element: ET.Element) -> list[list[float]]:
    pairs: list[list[float]] = []
    for node in element.iter():
        if local_name(node.tag) not in {"poslist", "pos", "coordinates"}:
            continue
        values = numbers(" ".join(node.itertext()))
        for index in range(0, len(values) - 1, 2):
            pairs.append([values[index], values[index + 1]])
    return pairs


def point_in_polygon(x: float, y: float, ring: list[list[float]]) -> bool:
    if len(ring) < 3:
        return False
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def geometry_distance(x: float, y: float, pairs: list[list[float]]) -> tuple[bool, float]:
    contained = point_in_polygon(x, y, pairs)
    if contained:
        return True, 0.0
    if len(pairs) == 1:
        return False, math.hypot(x - pairs[0][0], y - pairs[0][1])
    minimum = float("inf")
    for index in range(len(pairs) - 1):
        minimum = min(
            minimum,
            segment_distance(x, y, pairs[index][0], pairs[index][1], pairs[index + 1][0], pairs[index + 1][1]),
        )
    return False, minimum


def extract_identifiers(element: ET.Element) -> dict[str, list[str]]:
    accepted = {
        "identifier",
        "localid",
        "inspireid",
        "nationalcadastralreference",
        "label",
        "name",
        "beginslifespanversion",
        "endlifespanversion",
    }
    output: dict[str, list[str]] = {}
    for node in element.iter():
        key = local_name(node.tag)
        text = " ".join(part.strip() for part in node.itertext() if part and part.strip())
        if key in accepted and text and len(text) <= 500:
            output.setdefault(key, [])
            if text not in output[key]:
                output[key].append(text)
    return output


def parse_nearby_candidates(path: Path) -> tuple[int, int, list[dict[str, Any]], str | None]:
    feature_count = 0
    geometry_feature_count = 0
    candidates: list[dict[str, Any]] = []
    seen_geometry: set[str] = set()
    try:
        for _, element in ET.iterparse(path, events=("end",)):
            if local_name(element.tag) not in {"featuremember", "member"}:
                continue
            feature_count += 1
            pairs = coordinate_pairs(element)
            if pairs:
                geometry_feature_count += 1
                fingerprint = sha256_bytes(json.dumps(pairs, separators=(",", ":")).encode("utf-8"))
                if fingerprint not in seen_geometry:
                    seen_geometry.add(fingerprint)
                    contains_point, distance = geometry_distance(
                        TARGET_EASTING, TARGET_NORTHING, pairs
                    )
                    if distance <= SEARCH_RADIUS_METRES:
                        xs = [pair[0] for pair in pairs]
                        ys = [pair[1] for pair in pairs]
                        identifiers = extract_identifiers(element)
                        serialized = ET.tostring(element, encoding="unicode", method="xml")
                        srs_names = sorted(set(re.findall(r"srsName=[\"']([^\"']+)[\"']", serialized, flags=re.I)))
                        candidates.append(
                            {
                                "geometry_sha256": fingerprint,
                                "identifiers": identifiers,
                                "srs_names": srs_names,
                                "coordinate_pair_count": len(pairs),
                                "bbox": {
                                    "min_x": min(xs),
                                    "min_y": min(ys),
                                    "max_x": max(xs),
                                    "max_y": max(ys),
                                },
                                "contains_current_permit_point": contains_point,
                                "distance_to_current_permit_point_metres": round(distance, 3),
                                "coordinate_sample": pairs[:10],
                                "semantics": "HMLR_INSPIRE_FREEHOLD_PROXIMITY_CANDIDATE_REQUIRES_TITLE_LOOKUP",
                            }
                        )
            element.clear()
    except Exception as exc:
        return feature_count, geometry_feature_count, candidates, f"{type(exc).__name__}: {exc}"
    candidates.sort(key=lambda item: (item["distance_to_current_permit_point_metres"], item["geometry_sha256"]))
    return feature_count, geometry_feature_count, candidates[:100], None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID", SLOT_ID) != SLOT_ID:
        raise RuntimeError("WRONG_SLOT_CONTEXT")

    root = Path.cwd()
    report_path = root / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_hmlr_inspire_proximity_latest.json"
    status_path = root / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_hmlr_inspire_proximity_latest.json"
    web_path = root / "england_map_web/data/aays_21_slots/gas_emissions_1/hmlr_inspire_proximity_latest.json"

    index_data, index_error = fetch_bytes(INDEX_URL, timeout=90)
    gml_url = None
    resolve_error = index_error
    if index_data is not None:
        gml_url, resolve_error = resolve_authority_gml(index_data.decode("utf-8", errors="replace"))

    gml_data = None
    gml_error = resolve_error
    feature_count = 0
    geometry_feature_count = 0
    candidates: list[dict[str, Any]] = []
    parse_error = None
    diagnostic_title_occurrences = 0
    if gml_url:
        gml_data, gml_error = fetch_bytes(gml_url)
    if gml_data is not None:
        diagnostic_title_occurrences = gml_data.casefold().count(TARGET_TITLE_CONTEXT.casefold().encode("utf-8"))
        with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as handle:
            handle.write(gml_data)
            temporary_path = Path(handle.name)
        try:
            feature_count, geometry_feature_count, candidates, parse_error = parse_nearby_candidates(temporary_path)
        finally:
            temporary_path.unlink(missing_ok=True)

    passed = gml_data is not None and parse_error is None and len(candidates) > 0
    blocker = None if passed else (parse_error or gml_error or "NO_FREEHOLD_INSPIRE_POLYGON_WITHIN_RADIUS")
    payload: dict[str, Any] = {
        "schema_version": 2,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID", "gas_emissions_1_extract_hmlr_inspire_proximity_20260722"),
        "generated_at": utc_now(),
        "status": "PASS_HMLR_INSPIRE_FREEHOLD_PROXIMITY_CANDIDATES" if passed else "BLOCKED_HMLR_INSPIRE_PROXIMITY_NOT_EXTRACTED",
        "source": {
            "publisher": "HM Land Registry",
            "dataset": "INSPIRE Index Polygons",
            "dataset_scope": "REGISTERED_FREEHOLD_PROPERTY_ONLY",
            "snapshot_date": "2026-07-05",
            "authority": AUTHORITY,
            "index_url": INDEX_URL,
            "gml_url": gml_url,
            "index_sha256": sha256_bytes(index_data) if index_data else None,
            "gml_sha256": sha256_bytes(gml_data) if gml_data else None,
            "gml_size_bytes": len(gml_data) if gml_data else 0,
            "primary_crs": "EPSG:27700",
        },
        "target_context": {
            "title_number": TARGET_TITLE_CONTEXT,
            "tenure_context": TARGET_TITLE_TENURE_CONTEXT,
            "current_permit_point_bng": {"easting": TARGET_EASTING, "northing": TARGET_NORTHING},
            "search_radius_metres": SEARCH_RADIUS_METRES,
            "exact_title_occurrences_diagnostic_only": diagnostic_title_occurrences,
            "exact_title_occurrence_required": False,
        },
        "feature_member_count": feature_count,
        "geometry_feature_count": geometry_feature_count,
        "nearby_freehold_candidate_count": len(candidates),
        "candidates": candidates,
        "required_follow_up": [
            "Use HM Land Registry MapSearch, Search of the Index Map or a title-plan/register service to confirm leasehold TGL419520.",
            "Do not infer leasehold title identity from a nearby freehold INSPIRE polygon.",
            "Review CRS and geometry before any parcel intersection.",
        ],
        "blocker": blocker,
        "verified_title_geometry_candidates": 0,
        "verified_parcel_bindings": 0,
        "measured_parcel_emission_rows": 0,
        "quality_gate": "INSPIRE supplies indicative freehold polygons and INSPIRE IDs. TGL419520 is leasehold context; title identity and general boundary require separate HMLR title evidence before parcel attribution.",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    for path in (report_path, status_path, web_path):
        write_json(path, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
