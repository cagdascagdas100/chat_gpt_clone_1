from __future__ import annotations

import importlib.util
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v2.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v2", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V2_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
base = getattr(previous, "base", previous)
_EPS = 1e-9


def _strict_dimension(node: ET.Element, fallback: ET.Element | None = None) -> tuple[int | None, str | None]:
    raw = node.attrib.get("srsDimension") or (fallback.attrib.get("srsDimension") if fallback is not None else None)
    if raw is None:
        return 2, None
    if not re.fullmatch(r"[0-9]+", raw.strip()):
        return None, "COORDINATE_DIMENSION_INVALID"
    value = int(raw)
    return (value, None) if 2 <= value <= 4 else (None, "COORDINATE_DIMENSION_OUT_OF_RANGE")


def _strict_numbers(text: str | None) -> tuple[list[float], str | None]:
    raw = (text or "").strip()
    if not raw:
        return [], "COORDINATE_TEXT_EMPTY"
    values: list[float] = []
    for token in raw.split():
        try:
            value = float(token)
        except ValueError:
            return [], "COORDINATE_TOKEN_INVALID"
        if not math.isfinite(value):
            return [], "COORDINATE_TOKEN_NON_FINITE"
        values.append(value)
    return values, None


def _strict_ring_pairs(ring: ET.Element) -> tuple[list[tuple[float, float]], str | None]:
    poslists = [node for node in ring.iter() if previous._is_gml(node, "posList")]
    positions = [node for node in ring.iter() if previous._is_gml(node, "pos")]
    coordinate_nodes = [node for node in ring.iter() if previous._is_gml(node, "coordinates")]
    families = sum(bool(nodes) for nodes in (poslists, positions, coordinate_nodes))
    if families == 0:
        return [], "LINEAR_RING_COORDINATE_ENCODING_MISSING"
    if families > 1:
        return [], "LINEAR_RING_COORDINATE_ENCODING_MIXED"
    if poslists:
        if len(poslists) != 1:
            return [], "LINEAR_RING_POSLIST_COUNT_NOT_ONE"
        values, error = _strict_numbers(poslists[0].text)
        if error:
            return [], error
        dimension, error = _strict_dimension(poslists[0], ring)
        if error or dimension is None:
            return [], error
        if len(values) % dimension:
            return [], "POSLIST_ORDINATE_COUNT_NOT_DIVISIBLE_BY_DIMENSION"
        if len(values) < dimension * 4:
            return [], "LINEAR_RING_COORDINATE_COUNT_LT_4"
        return [(values[i], values[i + 1]) for i in range(0, len(values), dimension)], None
    if positions:
        if len(positions) < 4:
            return [], "LINEAR_RING_COORDINATE_COUNT_LT_4"
        pairs: list[tuple[float, float]] = []
        expected: int | None = None
        for node in positions:
            values, error = _strict_numbers(node.text)
            if error:
                return [], error
            dimension, error = _strict_dimension(node, ring)
            if error or dimension is None:
                return [], error
            if expected is None:
                expected = dimension
            elif dimension != expected:
                return [], "POS_DIMENSION_INCONSISTENT"
            if len(values) != dimension:
                return [], "POS_ORDINATE_COUNT_MISMATCH"
            pairs.append((values[0], values[1]))
        return pairs, None
    if len(coordinate_nodes) != 1:
        return [], "LINEAR_RING_COORDINATES_COUNT_NOT_ONE"
    node = coordinate_nodes[0]
    cs, ts, decimal = node.attrib.get("cs", ","), node.attrib.get("ts", " "), node.attrib.get("decimal", ".")
    if not cs or not ts or cs == ts:
        return [], "COORDINATES_SEPARATOR_INVALID"
    if decimal != ".":
        return [], "COORDINATES_DECIMAL_SEPARATOR_UNSUPPORTED"
    text = (node.text or "").strip()
    tuples = [value for value in (text.split(ts) if ts != " " else text.split()) if value]
    if len(tuples) < 4:
        return [], "LINEAR_RING_COORDINATE_COUNT_LT_4"
    pairs: list[tuple[float, float]] = []
    width: int | None = None
    for raw_tuple in tuples:
        parts = [part.strip() for part in raw_tuple.split(cs)]
        if not 2 <= len(parts) <= 4:
            return [], "COORDINATES_TUPLE_WIDTH_INVALID"
        if width is None:
            width = len(parts)
        elif len(parts) != width:
            return [], "COORDINATES_TUPLE_WIDTH_INCONSISTENT"
        try:
            values = [float(part) for part in parts]
        except ValueError:
            return [], "COORDINATE_TOKEN_INVALID"
        if not all(math.isfinite(value) for value in values):
            return [], "COORDINATE_TOKEN_NON_FINITE"
        pairs.append((values[0], values[1]))
    return pairs, None


def _strict_ring_validation(ring: ET.Element) -> tuple[bool, list[tuple[float, float]], str]:
    if not previous._is_gml(ring, "LinearRing"):
        return False, [], "LINEAR_RING_NAMESPACE_INVALID"
    pairs, error = _strict_ring_pairs(ring)
    if error:
        return False, pairs, error
    if any(math.isclose(a[0], b[0], abs_tol=_EPS) and math.isclose(a[1], b[1], abs_tol=_EPS) for a, b in zip(pairs, pairs[1:])):
        return False, pairs, "LINEAR_RING_ZERO_LENGTH_SEGMENT"
    if not (math.isclose(pairs[0][0], pairs[-1][0], abs_tol=_EPS) and math.isclose(pairs[0][1], pairs[-1][1], abs_tol=_EPS)):
        return False, pairs, "LINEAR_RING_NOT_CLOSED"
    if previous._ring_area(pairs) <= 0.0:
        return False, pairs, "LINEAR_RING_ZERO_AREA"
    if previous._ring_self_intersects(pairs):
        return False, pairs, "LINEAR_RING_SELF_INTERSECTION"
    return True, pairs, "PASS"


def _point_location(point: tuple[float, float], ring: list[tuple[float, float]]) -> int:
    x, y = point
    inside = False
    for a, b in zip(ring, ring[1:]):
        if previous._on_segment(a, point, b):
            return -1
        if (a[1] > y) == (b[1] > y):
            continue
        crossing_x = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
        if math.isclose(crossing_x, x, abs_tol=_EPS):
            return -1
        if crossing_x > x:
            inside = not inside
    return 1 if inside else 0


def _rings_intersect(first: list[tuple[float, float]], second: list[tuple[float, float]]) -> bool:
    return any(previous._segments_intersect(a, b, c, d) for a, b in zip(first, first[1:]) for c, d in zip(second, second[1:]))


def _boundary_topology(exterior: list[tuple[float, float]], interiors: list[list[tuple[float, float]]]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for index, interior in enumerate(interiors):
        if _rings_intersect(exterior, interior):
            reasons.append(f"INTERIOR_RING_{index}_INTERSECTS_EXTERIOR")
        elif {_point_location(point, exterior) for point in interior[:-1]} != {1}:
            reasons.append(f"INTERIOR_RING_{index}_NOT_STRICTLY_INSIDE_EXTERIOR")
    for first in range(len(interiors)):
        for second in range(first + 1, len(interiors)):
            a, b = interiors[first], interiors[second]
            if _rings_intersect(a, b):
                reasons.append(f"INTERIOR_RINGS_{first}_{second}_INTERSECT")
            elif _point_location(a[0], b) == 1 or _point_location(b[0], a) == 1:
                reasons.append(f"INTERIOR_RINGS_{first}_{second}_NESTED")
    return not reasons, reasons


_previous_geometry = previous.geometry
previous._ring_validation = _strict_ring_validation


def geometry(element: ET.Element) -> dict:
    output = _previous_geometry(element)
    details: list[dict] = []
    topology_passed = bool(output.get("geometry_validation_passed"))
    if topology_passed:
        gml_nodes = [node for node in element.iter() if previous.namespace(node.tag) in previous._GML_NAMESPACES]
        polygons = [node for node in gml_nodes if previous.local(node.tag) in {"Polygon", "PolygonPatch"}]
        for index, polygon in enumerate(polygons):
            exteriors = previous._boundary_rings(polygon, "exterior")
            interiors = previous._boundary_rings(polygon, "interior")
            ext = [_strict_ring_validation(ring) for ring in exteriors]
            holes = [_strict_ring_validation(ring) for ring in interiors]
            if len(ext) != 1 or not all(item[0] for item in ext + holes):
                valid, reasons = False, ["POLYGON_RING_PREREQUISITE_FAILED"]
            else:
                valid, reasons = _boundary_topology(ext[0][1], [item[1] for item in holes])
            details.append({"polygon_index": index, "valid": valid, "interior_ring_count": len(interiors), "reasons": reasons})
        topology_passed = bool(details) and all(item["valid"] for item in details)
    output["coordinate_lexical_validation_passed"] = bool(output.get("geometry_validation_passed"))
    output["polygon_boundary_topology_validation_passed"] = topology_passed
    output["invalid_polygon_boundary_topology"] = [item for item in details if not item["valid"]]
    output["geometry_validation_passed"] = bool(output.get("geometry_validation_passed")) and topology_passed
    if not output["geometry_validation_passed"]:
        output["coordinate_pair_count"] = 0
        output.pop("native_bbox", None)
        output.pop("coordinate_preview", None)
    return output


previous.geometry = geometry
base.geometry = geometry
parse = base.parse
