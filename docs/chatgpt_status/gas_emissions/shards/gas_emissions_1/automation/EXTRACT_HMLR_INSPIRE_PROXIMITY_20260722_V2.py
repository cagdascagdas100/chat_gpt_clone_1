#!/usr/bin/env python3
"""Read-only HMLR INSPIRE freehold-proximity extraction for gas_emissions_1.

TGL419520 is leasehold context. HM Land Registry INSPIRE supplies indicative
freehold polygons and INSPIRE IDs, so this task only shortlists nearby freehold
polygons around the current permit point. It never assigns TGL419520 or a parcel.
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
TITLE_CONTEXT = "TGL419520"
AUTHORITY = "London Borough of Barking and Dagenham"
INDEX_URL = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
TARGET_X = 548335.0
TARGET_Y = 182947.0
RADIUS_M = 300.0
USER_AGENT = "AAYS-gas_emissions_1-hmlr-freehold-proximity/2.1"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str, timeout: int = 180) -> tuple[bytes | None, str | None]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
        if not data:
            return None, "ZERO_BYTE_DOWNLOAD"
        return data, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def resolve_gml(html: str) -> tuple[str | None, str | None]:
    escaped = re.escape(AUTHORITY)
    patterns = (
        rf"<tr[^>]*>.*?{escaped}.*?<a[^>]+href=[\"']([^\"']+)[\"']",
        rf"{escaped}.{{0,1800}}?<a[^>]+href=[\"']([^\"']+\.gml[^\"']*)[\"']",
    )
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.I | re.S)
        if match:
            return urllib.parse.urljoin(INDEX_URL, match.group(1)), None
    return None, "BARKING_DAGENHAM_GML_LINK_NOT_RESOLVED"


def lname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].casefold()


def coordinate_pairs(element: ET.Element) -> list[list[float]]:
    values: list[float] = []
    for node in element.iter():
        if lname(node.tag) not in {"poslist", "pos", "coordinates"}:
            continue
        text = " ".join(node.itertext())
        for token in re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text):
            try:
                values.append(float(token))
            except ValueError:
                continue
    return [[values[i], values[i + 1]] for i in range(0, len(values) - 1, 2)]


def inside_polygon(x: float, y: float, ring: list[list[float]]) -> bool:
    if len(ring) < 3:
        return False
    inside = False
    previous = len(ring) - 1
    for current in range(len(ring)):
        xi, yi = ring[current]
        xj, yj = ring[previous]
        if ((yi > y) != (yj > y)) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        previous = current
    return inside


def segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    ratio = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    ratio = max(0.0, min(1.0, ratio))
    return math.hypot(px - (ax + ratio * dx), py - (ay + ratio * dy))


def geometry_distance(pairs: list[list[float]]) -> tuple[bool, float]:
    contained = inside_polygon(TARGET_X, TARGET_Y, pairs)
    if contained:
        return True, 0.0
    if len(pairs) < 2:
        return False, math.hypot(TARGET_X - pairs[0][0], TARGET_Y - pairs[0][1]) if pairs else float("inf")
    distance = min(
        segment_distance(TARGET_X, TARGET_Y, pairs[i][0], pairs[i][1], pairs[i + 1][0], pairs[i + 1][1])
        for i in range(len(pairs) - 1)
    )
    return False, distance


def identifiers(element: ET.Element) -> dict[str, list[str]]:
    allowed = {"identifier", "localid", "inspireid", "nationalcadastralreference", "label", "name", "beginslifespanversion", "endlifespanversion"}
    output: dict[str, list[str]] = {}
    for node in element.iter():
        key = lname(node.tag)
        text = " ".join(value.strip() for value in node.itertext() if value and value.strip())
        if key in allowed and text and len(text) <= 500:
            output.setdefault(key, [])
            if text not in output[key]:
                output[key].append(text)
    return output


def parse(path: Path) -> tuple[int, int, list[dict[str, Any]], str | None]:
    members = 0
    geometry_members = 0
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    try:
        for _, element in ET.iterparse(path, events=("end",)):
            if lname(element.tag) not in {"featuremember", "member"}:
                continue
            members += 1
            pairs = coordinate_pairs(element)
            if pairs:
                geometry_members += 1
                fingerprint = sha256(json.dumps(pairs, separators=(",", ":")).encode("utf-8"))
                if fingerprint not in seen:
                    seen.add(fingerprint)
                    contained, distance = geometry_distance(pairs)
                    if distance <= RADIUS_M:
                        xs = [item[0] for item in pairs]
                        ys = [item[1] for item in pairs]
                        xml = ET.tostring(element, encoding="unicode")
                        candidates.append({
                            "geometry_sha256": fingerprint,
                            "identifiers": identifiers(element),
                            "srs_names": sorted(set(re.findall(r"srsName=[\"']([^\"']+)[\"']", xml, flags=re.I))),
                            "coordinate_pair_count": len(pairs),
                            "bbox": {"min_x": min(xs), "min_y": min(ys), "max_x": max(xs), "max_y": max(ys)},
                            "contains_current_permit_point": contained,
                            "distance_to_current_permit_point_metres": round(distance, 3),
                            "coordinate_sample": pairs[:10],
                            "semantics": "HMLR_INSPIRE_FREEHOLD_PROXIMITY_CANDIDATE_REQUIRES_LEASEHOLD_TITLE_LOOKUP"
                        })
            element.clear()
    except Exception as exc:
        return members, geometry_members, candidates, f"{type(exc).__name__}: {exc}"
    candidates.sort(key=lambda row: (row["distance_to_current_permit_point_metres"], row["geometry_sha256"]))
    return members, geometry_members, candidates[:100], None


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if os.environ.get("AAYS_SLOT_ID", SLOT_ID) != SLOT_ID:
        raise RuntimeError("WRONG_SLOT_CONTEXT")
    root = Path.cwd()
    outputs = [
        root / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_hmlr_inspire_proximity_latest.json",
        root / "docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_hmlr_inspire_proximity_latest.json",
        root / "england_map_web/data/aays_21_slots/gas_emissions_1/hmlr_inspire_proximity_latest.json",
    ]
    index_data, index_error = fetch(INDEX_URL, 90)
    gml_url, resolve_error = (None, index_error)
    if index_data is not None:
        gml_url, resolve_error = resolve_gml(index_data.decode("utf-8", errors="replace"))
    gml_data, gml_error = (None, resolve_error)
    if gml_url:
        gml_data, gml_error = fetch(gml_url)
    members = geometry_members = 0
    candidates: list[dict[str, Any]] = []
    parse_error = None
    diagnostic_title_occurrences = 0
    if gml_data is not None:
        diagnostic_title_occurrences = gml_data.lower().count(TITLE_CONTEXT.lower().encode("utf-8"))
        with tempfile.NamedTemporaryFile(suffix=".gml", delete=False) as handle:
            handle.write(gml_data)
            temp_path = Path(handle.name)
        try:
            members, geometry_members, candidates, parse_error = parse(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
    passed = gml_data is not None and parse_error is None and bool(candidates)
    payload = {
        "schema_version": 2,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": os.environ.get("AAYS_TASK_ID", "gas_emissions_1_extract_hmlr_inspire_proximity_20260722"),
        "generated_at": now_utc(),
        "status": "PASS_HMLR_INSPIRE_FREEHOLD_PROXIMITY_CANDIDATES" if passed else "BLOCKED_HMLR_INSPIRE_PROXIMITY_NOT_EXTRACTED",
        "source": {
            "publisher": "HM Land Registry",
            "dataset": "INSPIRE Index Polygons",
            "dataset_scope": "REGISTERED_FREEHOLD_PROPERTY_ONLY",
            "snapshot_date": "2026-07-05",
            "authority": AUTHORITY,
            "index_url": INDEX_URL,
            "gml_url": gml_url,
            "index_sha256": sha256(index_data) if index_data else None,
            "gml_sha256": sha256(gml_data) if gml_data else None,
            "gml_size_bytes": len(gml_data) if gml_data else 0,
            "primary_crs": "EPSG:27700"
        },
        "target_context": {
            "leasehold_title": TITLE_CONTEXT,
            "permit_point_bng": {"easting": TARGET_X, "northing": TARGET_Y},
            "search_radius_metres": RADIUS_M,
            "exact_title_occurrences_diagnostic_only": diagnostic_title_occurrences,
            "exact_title_occurrence_required": False
        },
        "feature_member_count": members,
        "geometry_feature_count": geometry_members,
        "nearby_freehold_candidate_count": len(candidates),
        "candidates": candidates,
        "required_follow_up": ["MapSearch or Search of the Index Map", "CCOD company-title verification", "title register and title plan review", "explicit parcel intersection review"],
        "blocker": None if passed else (parse_error or gml_error or "NO_FREEHOLD_INSPIRE_POLYGON_WITHIN_RADIUS"),
        "verified_title_geometry_candidates": 0,
        "verified_parcel_bindings": 0,
        "measured_parcel_emission_rows": 0,
        "quality_gate": "Nearby INSPIRE candidates are indicative freehold polygons. They are not leasehold title TGL419520 and are not parcel values.",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False
    }
    for output in outputs:
        write(output, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
