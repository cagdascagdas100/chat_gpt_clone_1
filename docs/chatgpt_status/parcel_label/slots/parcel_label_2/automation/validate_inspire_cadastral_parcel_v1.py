from __future__ import annotations

import hashlib
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

_ALLOWED_GEOMETRY_TAGS = {"Polygon", "MultiPolygon", "MultiSurface", "Surface"}
_REFERENCE_TAG = "nationalCadastralReference"
_LOCAL_ID_TAG = "localId"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _finite_numbers(text: str | None) -> list[float]:
    values: list[float] = []
    for token in re.split(r"[\s,]+", (text or "").strip()):
        if not token:
            continue
        try:
            value = float(token)
        except ValueError:
            continue
        if math.isfinite(value):
            values.append(value)
    return values


def _dimension(node: ET.Element, fallback: ET.Element | None = None) -> int:
    raw = node.attrib.get("srsDimension") or (fallback.attrib.get("srsDimension") if fallback is not None else None) or "2"
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 2
    return value if 2 <= value <= 4 else 2


def _pairs_from_poslist(node: ET.Element, ring: ET.Element) -> list[tuple[float, float]]:
    values = _finite_numbers(node.text)
    dim = _dimension(node, ring)
    if len(values) < dim * 4 or len(values) % dim:
        return []
    return [(values[index], values[index + 1]) for index in range(0, len(values), dim)]


def _pairs_from_pos(nodes: Iterable[ET.Element], ring: ET.Element) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for node in nodes:
        values = _finite_numbers(node.text)
        dim = _dimension(node, ring)
        if len(values) < dim:
            return []
        pairs.append((values[0], values[1]))
    return pairs


def _pairs_from_coordinates(node: ET.Element) -> list[tuple[float, float]]:
    coordinate_separator = node.attrib.get("cs", ",")
    tuple_separator = node.attrib.get("ts", " ")
    text = (node.text or "").strip()
    if not text:
        return []
    raw_tuples = text.split(tuple_separator) if tuple_separator != " " else text.split()
    pairs: list[tuple[float, float]] = []
    for raw_tuple in raw_tuples:
        parts = [part.strip() for part in raw_tuple.split(coordinate_separator)]
        if len(parts) < 2:
            return []
        try:
            x, y = float(parts[0]), float(parts[1])
        except ValueError:
            return []
        if not math.isfinite(x) or not math.isfinite(y):
            return []
        pairs.append((x, y))
    return pairs


def _ring_pairs(ring: ET.Element) -> list[tuple[float, float]]:
    poslists = [node for node in ring.iter() if local(node.tag) == "posList"]
    if poslists:
        pairs: list[tuple[float, float]] = []
        for node in poslists:
            part = _pairs_from_poslist(node, ring)
            if not part:
                return []
            pairs.extend(part)
        return pairs
    positions = [node for node in ring.iter() if local(node.tag) == "pos"]
    if positions:
        return _pairs_from_pos(positions, ring)
    coordinate_nodes = [node for node in ring.iter() if local(node.tag) == "coordinates"]
    if coordinate_nodes:
        pairs = []
        for node in coordinate_nodes:
            part = _pairs_from_coordinates(node)
            if not part:
                return []
            pairs.extend(part)
        return pairs
    return []


def _ring_area(pairs: list[tuple[float, float]]) -> float:
    if len(pairs) < 4:
        return 0.0
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pairs, pairs[1:]))) / 2.0


def _ring_validation(ring: ET.Element) -> tuple[bool, list[tuple[float, float]], str]:
    pairs = _ring_pairs(ring)
    if len(pairs) < 4:
        return False, pairs, "LINEAR_RING_COORDINATE_COUNT_LT_4"
    if not (math.isclose(pairs[0][0], pairs[-1][0], rel_tol=0.0, abs_tol=1e-9) and math.isclose(pairs[0][1], pairs[-1][1], rel_tol=0.0, abs_tol=1e-9)):
        return False, pairs, "LINEAR_RING_NOT_CLOSED"
    if _ring_area(pairs) <= 0.0:
        return False, pairs, "LINEAR_RING_ZERO_AREA"
    return True, pairs, "PASS"


def _is_epsg_27700(value: str) -> bool:
    normalised = value.strip().casefold().rstrip("/")
    return bool(re.search(r"(?:epsg(?::|::|/0/)|/)(?:crs/)?27700$", normalised)) or normalised.endswith("/27700")


def geometry(element: ET.Element) -> dict:
    tags = {local(node.tag) for node in element.iter() if local(node.tag) in _ALLOWED_GEOMETRY_TAGS | {"LinearRing"}}
    srs_names = sorted({node.attrib["srsName"] for node in element.iter() if node.attrib.get("srsName")})
    conflicting_srs = [value for value in srs_names if not _is_epsg_27700(value)]

    exterior_rings: list[ET.Element] = []
    interior_rings: list[ET.Element] = []
    for node in element.iter():
        name = local(node.tag)
        if name not in {"exterior", "interior"}:
            continue
        rings = [child for child in node.iter() if local(child.tag) == "LinearRing"]
        (exterior_rings if name == "exterior" else interior_rings).extend(rings)
    if not exterior_rings:
        exterior_rings = [node for node in element.iter() if local(node.tag) == "LinearRing"]

    exterior_results = [_ring_validation(ring) for ring in exterior_rings]
    interior_results = [_ring_validation(ring) for ring in interior_rings]
    valid_exteriors = [pairs for valid, pairs, _ in exterior_results if valid]
    valid_interiors = [pairs for valid, pairs, _ in interior_results if valid]

    geometry_type_valid = bool(tags & _ALLOWED_GEOMETRY_TAGS)
    exterior_valid = bool(exterior_results) and len(valid_exteriors) == len(exterior_results)
    crs_valid = not conflicting_srs
    passed = geometry_type_valid and exterior_valid and crs_valid
    accepted_pairs = [pair for ring in (valid_exteriors + valid_interiors) for pair in ring] if passed else []

    output = {
        "coordinate_pair_count": len(accepted_pairs),
        "geometry_tags": sorted(tags),
        "srs_names": srs_names,
        "british_national_grid_declared": any(_is_epsg_27700(value) for value in srs_names),
        "conflicting_srs_names": conflicting_srs,
        "linear_ring_count": len(exterior_results) + len(interior_results),
        "valid_exterior_ring_count": len(valid_exteriors),
        "invalid_exterior_ring_reasons": [reason for valid, _, reason in exterior_results if not valid],
        "valid_interior_ring_count": len(valid_interiors),
        "invalid_interior_ring_reasons": [reason for valid, _, reason in interior_results if not valid],
        "geometry_validation_passed": passed,
    }
    if accepted_pairs:
        xs = [x for x, _ in accepted_pairs]
        ys = [y for _, y in accepted_pairs]
        output.update(
            native_bbox=[min(xs), min(ys), max(xs), max(ys)],
            coordinate_preview=[list(pair) for pair in accepted_pairs[:4]],
        )
    return output


def parse(path: Path, target_ids: set[str]) -> tuple[dict[str, list[dict]], dict]:
    found = {target: [] for target in target_ids}
    scanned = 0
    ignored_non_reference_text_matches = 0
    for _, element in ET.iterparse(path, events=("end",)):
        if local(element.tag) != "CadastralParcel":
            continue
        national_references = {
            (node.text or "").strip()
            for node in element.iter()
            if local(node.tag) == _REFERENCE_TAG and (node.text or "").strip()
        }
        local_ids = {
            (node.text or "").strip()
            for node in element.iter()
            if local(node.tag) == _LOCAL_ID_TAG and (node.text or "").strip()
        }
        hits = national_references & target_ids
        all_text_hits = {(node.text or "").strip() for node in element.iter()} & target_ids
        ignored_non_reference_text_matches += len(all_text_hits - hits)
        if not hits:
            element.clear()
            continue
        if len(hits) != 1:
            raise RuntimeError(f"CADASTRAL_PARCEL_TARGET_REFERENCE_COUNT:{len(hits)}")
        target = next(iter(hits))
        scanned += 1
        record = {
            "feature_element": "CadastralParcel",
            "feature_sha256": hashlib.sha256(ET.tostring(element, encoding="utf-8")).hexdigest(),
            "national_cadastral_reference": target,
            "local_id_exact_match": target in local_ids,
        } | geometry(element)
        found[target].append(record)
        element.clear()
    return found, {
        "matched_cadastral_parcels_scanned": scanned,
        "identifier_match_field": _REFERENCE_TAG,
        "ignored_non_reference_text_matches": ignored_non_reference_text_matches,
    }
