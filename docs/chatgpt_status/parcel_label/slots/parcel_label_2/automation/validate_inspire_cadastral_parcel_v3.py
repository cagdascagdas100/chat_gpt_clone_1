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
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def _strict_dimension(node: ET.Element, fallback: ET.Element | None = None) -> tuple[int | None, str | None]:
    raw = node.attrib.get("srsDimension") or (fallback.attrib.get("srsDimension") if fallback is not None else None)
    if raw is None:
        return 2, None
    if not re.fullmatch(r"[0-9]+", raw.strip()):
        return None, "COORDINATE_DIMENSION_INVALID"
    value = int(raw)
    if not 2 <= value <= 4:
        return None, "COORDINATE_DIMENSION_OUT_OF_RANGE"
    return value, None


def _strict_float_tokens(text: str | None) -> tuple[list[float], str | None]:
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


def _pairs_from_poslist(node: ET.Element, ring: ET.Element) -> tuple[list[tuple[float, float]], str | None]:
    values, error = _strict_float_tokens(node.text)
    if error:
        return [], error
    dimension, error = _strict_dimension(node, ring)
    if error or dimension is None:
        return [], error
    if len(values) % dimension:
        return [], "POSLIST_ORDINATE_COUNT_NOT_DIVISIBLE_BY_DIMENSION"
    if len(values) < dimension * 4:
        return [], "LINEAR_RING_COORDINATE_COUNT_LT_4"
    return [(values[index], values[index + 1]) for index in range(0, len(values), dimension)], None


def _pairs_from_pos(nodes: list[ET.Element], ring: ET.Element) -> tuple[list[tuple[float, float]], str | None]:
    if len(nodes) < 4:
        return [], "LINEAR_RING_COORDINATE_COUNT_LT_4"
    pairs: list[tuple[float, float]] = []
    expected_dimension: int | None = None
    for node in nodes:
        values, error = _strict_float_tokens(node.text)
        if error:
            return [], error
        dimension, error = _strict_dimension(node, ring)
        if error or dimension is None:
            return [], error
        if expected_dimension is None:
            expected_dimension = dimension
        elif dimension != expected_dimension:
            return [], "POS_DIMENSION_INCONSISTENT"
        if len(values) != dimension:
            return [], "POS_ORDINATE_COUNT_MISMATCH"
        pairs.append((values[0], values[1]))
    return pairs, None


def _pairs_from_coordinates(node: ET.Element) -> tuple[list[tuple[float, float]], str | None]:
    coordinate_separator = node.attrib.get("cs", ",")
    tuple_separator = node.attrib.get("ts", " ")
    if not coordinate_separator or not tuple_separator or coordinate_separator == tuple_separator:
        return [], "COORDINATES_SEPARATOR_INVALID"
    if node.attrib.get("decimal", ".") != ".":
        return [], "COORDINATES_DECIMAL_SEPARATOR_UNSUPPORTED"
    text = (node.text or "").strip()
    if not text:
        return [], "COORDINATE_TEXT_EMPTY"
    raw_tuples = text.split(tuple_separator) if tuple_separator != " " else text.split()
    raw_tuples = [value for value in raw_tuples if value]
    if len(raw_tuples) < 4:
        return [], "LINEAR_RING_COORDINATE_COUNT_LT_4"
    pairs: list[tuple[float, float]] = []
    tuple_width: int | None = None
    for raw_tuple in raw_tuples:
        parts = [part.strip() for part in raw_tuple.split(coordinate_separator)]
        if not 2 <= len(parts) <= 4:
            return [], "COORDINATES_TUPLE_WIDTH_INVALID"
        if tuple_width is None:
            tuple_width = len(parts)
        elif len(parts) != tuple_width:
            return [], "COORDINATES_TUPLE_WIDTH_INCONSISTENT"
        values: list[float] = []
        for part in parts:
            try:
                value = float(part)
            except ValueError:
                return [], "COORDINATE_TOKEN_INVALID"
            if not math.isfinite(value):
                return [], "COORDINATE_TOKEN_NON_FINITE"
            values.append(value)
        pairs.append((values[0], values[1]))
    return pairs, None


def _ring_pairs(ring: ET.Element) -> tuple[list[tuple[float, float]], str | None]:
    poslists = [node for node in ring.iter() if base._is_gml(node, "posList")]
    positions = [node for node in ring.iter() if base._is_gml(node, "pos")]
    coordinate_nodes = [node for node in ring.iter() if base._is_gml(node, "coordinates")]
    family_count = sum(bool(nodes) for nodes in (poslists, positions, coordinate_nodes))
    if family_count == 0:
        return [], "LINEAR_RING_COORDINATE_ENCODING_MISSING"
    if family_count > 1:
        return [], "LINEAR_RING_COORDINATE_ENCODING_MIXED"
    if poslists:
        if len(poslists) != 1:
            return [], "LINEAR_RING_POSLIST_COUNT_NOT_ONE"
        return _pairs_from_poslist(poslists[0], ring)
    if positions:
        return _pairs_from_pos(positions, ring)
    if len(coordinate_nodes) != 1:
        return [], "LINEAR_RING_COORDINATES_COUNT_NOT_ONE"
    return _pairs_from_coordinates(coordinate_nodes[0])


def _ring_validation(ring: ET.Element) -> tuple[bool, list[tuple[float, float]], str]:
    if not base._is_gml(ring, "LinearRing"):
        return False, [], "LINEAR_RING_NAMESPACE_INVALID"
    pairs, error = _ring_pairs(ring)
    if error:
        return False, pairs, error
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
    if base._ring_area(pairs) <= 0.0:
        return False, pairs, "LINEAR_RING_ZERO_AREA"
    if base._ring_self_intersects(pairs):
        return False, pairs, "LINEAR_RING_SELF_INTERSECTION"
    return True, pairs, "PASS"


base._ring_pairs = _ring_pairs
base._ring_validation = _ring_validation
geometry = base.geometry
parse = base.parse
