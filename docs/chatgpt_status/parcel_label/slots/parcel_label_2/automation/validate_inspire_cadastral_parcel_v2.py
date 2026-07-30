from __future__ import annotations

import hashlib
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

_ALLOWED_GEOMETRY_TAGS = {"Polygon", "MultiPolygon", "MultiSurface", "Surface", "PolygonPatch"}
_REFERENCE_TAG = "nationalCadastralReference"
_LOCAL_ID_TAG = "localId"
_GML_NAMESPACES = {
    "http://www.opengis.net/gml",
    "http://www.opengis.net/gml/3.2",
}
_CP_NAMESPACE_PREFIXES = (
    "http://inspire.ec.europa.eu/schemas/cp/",
    "urn:x-inspire:specification:gmlas:CadastralParcels:",
)
_BASE_NAMESPACE_PREFIXES = (
    "http://inspire.ec.europa.eu/schemas/base/",
    "urn:x-inspire:specification:gmlas:BaseTypes:",
)


def split_tag(tag: str) -> tuple[str, str]:
    if tag.startswith("{") and "}" in tag:
        namespace, local_name = tag[1:].split("}", 1)
        return namespace, local_name
    return "", tag


def local(tag: str) -> str:
    return split_tag(tag)[1]


def namespace(tag: str) -> str:
    return split_tag(tag)[0]


def _is_cp_namespace(value: str) -> bool:
    return any(value.startswith(prefix) for prefix in _CP_NAMESPACE_PREFIXES)


def _is_base_namespace(value: str) -> bool:
    return any(value.startswith(prefix) for prefix in _BASE_NAMESPACE_PREFIXES)


def _is_gml(node: ET.Element, *names: str) -> bool:
    node_namespace, node_name = split_tag(node.tag)
    return node_namespace in _GML_NAMESPACES and (not names or node_name in names)


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
    poslists = [node for node in ring.iter() if _is_gml(node, "posList")]
    if poslists:
        pairs: list[tuple[float, float]] = []
        for node in poslists:
            part = _pairs_from_poslist(node, ring)
            if not part:
                return []
            pairs.extend(part)
        return pairs
    positions = [node for node in ring.iter() if _is_gml(node, "pos")]
    if positions:
        return _pairs_from_pos(positions, ring)
    coordinate_nodes = [node for node in ring.iter() if _is_gml(node, "coordinates")]
    if coordinate_nodes:
        pairs: list[tuple[float, float]] = []
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


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    return (
        min(a[0], c[0]) - 1e-9 <= b[0] <= max(a[0], c[0]) + 1e-9
        and min(a[1], c[1]) - 1e-9 <= b[1] <= max(a[1], c[1]) + 1e-9
        and math.isclose(_orientation(a, b, c), 0.0, rel_tol=0.0, abs_tol=1e-9)
    )


def _segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if ((o1 > 1e-9 and o2 < -1e-9) or (o1 < -1e-9 and o2 > 1e-9)) and (
        (o3 > 1e-9 and o4 < -1e-9) or (o3 < -1e-9 and o4 > 1e-9)
    ):
        return True
    return (
        (math.isclose(o1, 0.0, abs_tol=1e-9) and _on_segment(a, c, b))
        or (math.isclose(o2, 0.0, abs_tol=1e-9) and _on_segment(a, d, b))
        or (math.isclose(o3, 0.0, abs_tol=1e-9) and _on_segment(c, a, d))
        or (math.isclose(o4, 0.0, abs_tol=1e-9) and _on_segment(c, b, d))
    )


def _ring_self_intersects(pairs: list[tuple[float, float]]) -> bool:
    segment_count = len(pairs) - 1
    for first in range(segment_count):
        a, b = pairs[first], pairs[first + 1]
        for second in range(first + 1, segment_count):
            if second == first + 1:
                continue
            if first == 0 and second == segment_count - 1:
                continue
            c, d = pairs[second], pairs[second + 1]
            if _segments_intersect(a, b, c, d):
                return True
    return False


def _ring_validation(ring: ET.Element) -> tuple[bool, list[tuple[float, float]], str]:
    if not _is_gml(ring, "LinearRing"):
        return False, [], "LINEAR_RING_NAMESPACE_INVALID"
    pairs = _ring_pairs(ring)
    if len(pairs) < 4:
        return False, pairs, "LINEAR_RING_COORDINATE_COUNT_LT_4"
    if any(
        math.isclose(a[0], b[0], rel_tol=0.0, abs_tol=1e-9)
        and math.isclose(a[1], b[1], rel_tol=0.0, abs_tol=1e-9)
        for a, b in zip(pairs, pairs[1:])
    ):
        return False, pairs, "LINEAR_RING_ZERO_LENGTH_SEGMENT"
    if not (
        math.isclose(pairs[0][0], pairs[-1][0], rel_tol=0.0, abs_tol=1e-9)
        and math.isclose(pairs[0][1], pairs[-1][1], rel_tol=0.0, abs_tol=1e-9)
    ):
        return False, pairs, "LINEAR_RING_NOT_CLOSED"
    if _ring_area(pairs) <= 0.0:
        return False, pairs, "LINEAR_RING_ZERO_AREA"
    if _ring_self_intersects(pairs):
        return False, pairs, "LINEAR_RING_SELF_INTERSECTION"
    return True, pairs, "PASS"


def _is_epsg_27700(value: str) -> bool:
    normalised = value.strip().casefold().rstrip("/")
    return bool(re.search(r"(?:epsg(?::|::|/0/)|/)(?:crs/)?27700$", normalised)) or normalised.endswith("/27700")


def _boundary_rings(polygon: ET.Element, boundary_name: str) -> list[ET.Element]:
    rings: list[ET.Element] = []
    for node in list(polygon):
        if not _is_gml(node, boundary_name):
            continue
        rings.extend(child for child in node.iter() if _is_gml(child, "LinearRing"))
    return rings


def geometry(element: ET.Element) -> dict:
    gml_nodes = [node for node in element.iter() if namespace(node.tag) in _GML_NAMESPACES]
    tags = {local(node.tag) for node in gml_nodes if local(node.tag) in _ALLOWED_GEOMETRY_TAGS | {"LinearRing"}}
    foreign_geometry_tags = sorted(
        {
            local(node.tag)
            for node in element.iter()
            if local(node.tag) in _ALLOWED_GEOMETRY_TAGS | {"LinearRing", "exterior", "interior"}
            and namespace(node.tag) not in _GML_NAMESPACES
        }
    )
    srs_names = sorted({node.attrib["srsName"] for node in gml_nodes if node.attrib.get("srsName")})
    conflicting_srs = [value for value in srs_names if not _is_epsg_27700(value)]

    polygon_nodes = [node for node in gml_nodes if local(node.tag) in {"Polygon", "PolygonPatch"}]
    polygon_results: list[dict] = []
    accepted_pairs: list[tuple[float, float]] = []
    for polygon in polygon_nodes:
        exteriors = _boundary_rings(polygon, "exterior")
        interiors = _boundary_rings(polygon, "interior")
        exterior_results = [_ring_validation(ring) for ring in exteriors]
        interior_results = [_ring_validation(ring) for ring in interiors]
        valid = (
            len(exteriors) == 1
            and all(result[0] for result in exterior_results)
            and all(result[0] for result in interior_results)
        )
        if valid:
            accepted_pairs.extend(pair for _, ring_pairs, _ in exterior_results + interior_results for pair in ring_pairs)
        polygon_results.append(
            {
                "valid": valid,
                "exterior_ring_count": len(exteriors),
                "interior_ring_count": len(interiors),
                "invalid_exterior_reasons": [reason for ok, _, reason in exterior_results if not ok],
                "invalid_interior_reasons": [reason for ok, _, reason in interior_results if not ok],
            }
        )

    geometry_type_valid = bool(tags & _ALLOWED_GEOMETRY_TAGS)
    polygon_structure_valid = bool(polygon_results) and all(result["valid"] for result in polygon_results)
    crs_valid = not conflicting_srs
    namespace_valid = not foreign_geometry_tags
    passed = geometry_type_valid and polygon_structure_valid and crs_valid and namespace_valid
    if not passed:
        accepted_pairs = []

    output = {
        "coordinate_pair_count": len(accepted_pairs),
        "geometry_tags": sorted(tags),
        "foreign_geometry_tags": foreign_geometry_tags,
        "srs_names": srs_names,
        "british_national_grid_declared": any(_is_epsg_27700(value) for value in srs_names),
        "conflicting_srs_names": conflicting_srs,
        "polygon_primitive_count": len(polygon_results),
        "invalid_polygon_primitive_count": sum(not result["valid"] for result in polygon_results),
        "invalid_polygon_details": [result for result in polygon_results if not result["valid"]],
        "geometry_namespace_validation_passed": namespace_valid,
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
    ignored_wrong_namespace_parcels = 0
    ignored_wrong_namespace_references = 0
    for _, element in ET.iterparse(path, events=("end",)):
        element_namespace, element_name = split_tag(element.tag)
        if element_name != "CadastralParcel":
            continue
        if not _is_cp_namespace(element_namespace):
            ignored_wrong_namespace_parcels += 1
            element.clear()
            continue
        national_references = set()
        local_ids = set()
        for node in element.iter():
            node_namespace, node_name = split_tag(node.tag)
            text = (node.text or "").strip()
            if node_name == _REFERENCE_TAG and text:
                if node_namespace == element_namespace:
                    national_references.add(text)
                else:
                    ignored_wrong_namespace_references += 1
            if node_name == _LOCAL_ID_TAG and text and _is_base_namespace(node_namespace):
                local_ids.add(text)
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
            "feature_namespace": element_namespace,
            "feature_sha256": hashlib.sha256(ET.tostring(element, encoding="utf-8")).hexdigest(),
            "national_cadastral_reference": target,
            "local_id_exact_match": target in local_ids,
        } | geometry(element)
        found[target].append(record)
        element.clear()
    return found, {
        "matched_cadastral_parcels_scanned": scanned,
        "identifier_match_field": _REFERENCE_TAG,
        "identifier_namespace_policy": "same recognised INSPIRE CP namespace as CadastralParcel",
        "ignored_non_reference_text_matches": ignored_non_reference_text_matches,
        "ignored_wrong_namespace_parcels": ignored_wrong_namespace_parcels,
        "ignored_wrong_namespace_references": ignored_wrong_namespace_references,
    }
