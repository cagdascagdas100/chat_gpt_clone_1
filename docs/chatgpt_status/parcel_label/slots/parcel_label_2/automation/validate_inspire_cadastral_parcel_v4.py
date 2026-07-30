from __future__ import annotations

import importlib.util
import math
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v3.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v3", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V3_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
base = getattr(previous, "base", previous)
_previous_geometry = previous.geometry

_EPS = 1e-9


def _point_location(point: tuple[float, float], ring: list[tuple[float, float]]) -> int:
    """Return 1 inside, 0 outside, -1 on boundary."""
    x, y = point
    inside = False
    for a, b in zip(ring, ring[1:]):
        if base._on_segment(a, point, b):
            return -1
        y_crosses = (a[1] > y) != (b[1] > y)
        if not y_crosses:
            continue
        x_at_y = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
        if math.isclose(x_at_y, x, rel_tol=0.0, abs_tol=_EPS):
            return -1
        if x_at_y > x:
            inside = not inside
    return 1 if inside else 0


def _rings_intersect(first: list[tuple[float, float]], second: list[tuple[float, float]]) -> bool:
    return any(
        base._segments_intersect(a, b, c, d)
        for a, b in zip(first, first[1:])
        for c, d in zip(second, second[1:])
    )


def _polygon_topology(
    exterior: list[tuple[float, float]],
    interiors: list[list[tuple[float, float]]],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    for index, interior in enumerate(interiors):
        if _rings_intersect(exterior, interior):
            reasons.append(f"INTERIOR_RING_{index}_INTERSECTS_EXTERIOR")
            continue
        locations = {_point_location(point, exterior) for point in interior[:-1]}
        if locations != {1}:
            reasons.append(f"INTERIOR_RING_{index}_NOT_STRICTLY_INSIDE_EXTERIOR")

    for first in range(len(interiors)):
        for second in range(first + 1, len(interiors)):
            ring_a, ring_b = interiors[first], interiors[second]
            if _rings_intersect(ring_a, ring_b):
                reasons.append(f"INTERIOR_RINGS_{first}_{second}_INTERSECT")
                continue
            # A hole nested inside another hole represents an island and requires
            # another polygon primitive rather than two interior rings in one Polygon.
            if _point_location(ring_a[0], ring_b) == 1 or _point_location(ring_b[0], ring_a) == 1:
                reasons.append(f"INTERIOR_RINGS_{first}_{second}_NESTED")
    return not reasons, reasons


def geometry(element: ET.Element) -> dict:
    output = _previous_geometry(element)
    topology_details: list[dict] = []
    topology_passed = bool(output.get("geometry_validation_passed"))

    if topology_passed:
        gml_nodes = [node for node in element.iter() if base.namespace(node.tag) in base._GML_NAMESPACES]
        polygon_nodes = [node for node in gml_nodes if base.local(node.tag) in {"Polygon", "PolygonPatch"}]
        for polygon_index, polygon in enumerate(polygon_nodes):
            exteriors = base._boundary_rings(polygon, "exterior")
            interiors = base._boundary_rings(polygon, "interior")
            exterior_results = [previous._ring_validation(ring) for ring in exteriors]
            interior_results = [previous._ring_validation(ring) for ring in interiors]
            if len(exterior_results) != 1 or not all(item[0] for item in exterior_results + interior_results):
                valid, reasons = False, ["POLYGON_RING_PREREQUISITE_FAILED"]
            else:
                valid, reasons = _polygon_topology(
                    exterior_results[0][1],
                    [item[1] for item in interior_results],
                )
            topology_details.append(
                {
                    "polygon_index": polygon_index,
                    "valid": valid,
                    "interior_ring_count": len(interiors),
                    "reasons": reasons,
                }
            )
        topology_passed = bool(topology_details) and all(item["valid"] for item in topology_details)

    output["polygon_boundary_topology_validation_passed"] = topology_passed
    output["invalid_polygon_boundary_topology"] = [item for item in topology_details if not item["valid"]]
    output["geometry_validation_passed"] = bool(output.get("geometry_validation_passed")) and topology_passed
    if not output["geometry_validation_passed"]:
        output["coordinate_pair_count"] = 0
        output.pop("native_bbox", None)
        output.pop("coordinate_preview", None)
    return output


# The inherited parser resolves geometry from the underlying validator module.
base.geometry = geometry
previous.geometry = geometry
parse = base.parse
