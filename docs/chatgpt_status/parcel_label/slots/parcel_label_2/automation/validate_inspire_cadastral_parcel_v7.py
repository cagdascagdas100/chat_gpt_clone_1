from __future__ import annotations

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v6.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v6", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V6_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
base = previous.base

_underlying_geometry = previous.previous.geometry
_ALLOWED_ROOTS = set(base._ALLOWED_GEOMETRY_TAGS)


def _is_geometry_root(node: ET.Element) -> bool:
    namespace, name = base.split_tag(node.tag)
    return namespace in base._GML_NAMESPACES and name in _ALLOWED_ROOTS


def _all_geometry_primitives(element: ET.Element) -> list[ET.Element]:
    return [node for node in element.iter() if _is_geometry_root(node)]


def _scope_failure(element: ET.Element, reasons: list[str], schema: str) -> dict:
    output = _underlying_geometry(element)
    output["geometry_feature_schema"] = schema
    output["geometry_scope_validation_passed"] = False
    output["geometry_scope_failure_reasons"] = reasons
    output["geometry_root_count"] = 0
    output["geometry_validation_passed"] = False
    output["coordinate_pair_count"] = 0
    output.pop("native_bbox", None)
    output.pop("coordinate_preview", None)
    return output


def _scope_output(element: ET.Element, scope: ET.Element, schema: str, root_count: int) -> dict:
    output = _underlying_geometry(scope)
    scope_nodes = set(scope.iter())
    outside = [node for node in _all_geometry_primitives(element) if node not in scope_nodes]
    reasons: list[str] = []
    if outside:
        reasons.append("GEOMETRY_PRIMITIVE_OUTSIDE_ACCEPTED_SCOPE")
    output["geometry_feature_schema"] = schema
    output["geometry_scope_validation_passed"] = not reasons
    output["geometry_scope_failure_reasons"] = reasons
    output["geometry_root_count"] = root_count
    output["geometry_primitives_outside_scope"] = len(outside)
    output["geometry_validation_passed"] = bool(output.get("geometry_validation_passed")) and not reasons
    if not output["geometry_validation_passed"]:
        output["coordinate_pair_count"] = 0
        output.pop("native_bbox", None)
        output.pop("coordinate_preview", None)
    return output


def _inspire_geometry_scope(element: ET.Element, feature_namespace: str) -> dict:
    properties = [
        child
        for child in list(element)
        if base.split_tag(child.tag) == (feature_namespace, "geometry")
    ]
    if len(properties) != 1:
        return _scope_failure(
            element,
            [f"INSPIRE_GEOMETRY_PROPERTY_COUNT:{len(properties)}"],
            "INSPIRE_CADASTRAL_PARCEL",
        )
    roots = [child for child in list(properties[0]) if _is_geometry_root(child)]
    if len(roots) != 1:
        return _scope_failure(
            element,
            [f"INSPIRE_GEOMETRY_ROOT_COUNT:{len(roots)}"],
            "INSPIRE_CADASTRAL_PARCEL",
        )
    return _scope_output(element, roots[0], "INSPIRE_CADASTRAL_PARCEL", len(roots))


def _predefined_geometry_scope(element: ET.Element) -> dict:
    wrappers = [
        child
        for child in list(element)
        if base.split_tag(child.tag) == ("", "GEOMETRY")
    ]
    direct_roots = [child for child in list(element) if _is_geometry_root(child)]
    if wrappers and direct_roots:
        return _scope_failure(
            element,
            ["PREDEFINED_GEOMETRY_SCOPE_MIXED"],
            "HMLR_PREDEFINED_FLATTENED",
        )
    if len(wrappers) > 1:
        return _scope_failure(
            element,
            [f"PREDEFINED_GEOMETRY_WRAPPER_COUNT:{len(wrappers)}"],
            "HMLR_PREDEFINED_FLATTENED",
        )
    if wrappers:
        roots = [child for child in list(wrappers[0]) if _is_geometry_root(child)]
        if len(roots) != 1:
            return _scope_failure(
                element,
                [f"PREDEFINED_GEOMETRY_ROOT_COUNT:{len(roots)}"],
                "HMLR_PREDEFINED_FLATTENED",
            )
        return _scope_output(element, roots[0], "HMLR_PREDEFINED_FLATTENED", len(roots))
    if len(direct_roots) != 1:
        return _scope_failure(
            element,
            [f"PREDEFINED_DIRECT_GEOMETRY_ROOT_COUNT:{len(direct_roots)}"],
            "HMLR_PREDEFINED_FLATTENED",
        )
    return _scope_output(element, direct_roots[0], "HMLR_PREDEFINED_FLATTENED", len(direct_roots))


def geometry(element: ET.Element) -> dict:
    feature_namespace, feature_name = base.split_tag(element.tag)
    if feature_name == "CadastralParcel" and base._is_cp_namespace(feature_namespace):
        return _inspire_geometry_scope(element, feature_namespace)
    if feature_name == "PREDEFINED" and not feature_namespace:
        return _predefined_geometry_scope(element)
    return _scope_failure(element, ["GEOMETRY_FEATURE_SCHEMA_UNSUPPORTED"], "UNSUPPORTED")


previous.base.geometry = geometry
previous.previous.geometry = geometry
base.geometry = geometry
parse = previous.parse
