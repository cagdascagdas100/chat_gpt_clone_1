from __future__ import annotations

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v7.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v7", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V7_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
base = previous.base

_WFS_NAMESPACES = {
    "http://www.opengis.net/wfs",
    "http://www.opengis.net/wfs/2.0",
}
_OGR_NAMESPACE = "http://ogr.maptools.org/"
_MEMBER_TAGS = {
    ("http://www.opengis.net/gml", "featureMember"),
    ("http://www.opengis.net/gml/3.2", "featureMember"),
    ("http://www.opengis.net/gml", "featureMembers"),
    ("http://www.opengis.net/gml/3.2", "featureMembers"),
    ("http://www.opengis.net/wfs", "member"),
    ("http://www.opengis.net/wfs/2.0", "member"),
    ("", "featureMember"),
    ("", "featureMembers"),
}
_COLLECTION_NAMESPACES = set(base._GML_NAMESPACES) | _WFS_NAMESPACES | {_OGR_NAMESPACE, ""}


def _feature_schema(tag: str) -> str | None:
    namespace, name = base.split_tag(tag)
    if name == "CadastralParcel" and base._is_cp_namespace(namespace):
        return "INSPIRE_CADASTRAL_PARCEL"
    if name == "PREDEFINED" and not namespace:
        return "HMLR_PREDEFINED_FLATTENED"
    return None


def _is_collection(tag: str, schema: str) -> bool:
    namespace, name = base.split_tag(tag)
    if name != "FeatureCollection" or namespace not in _COLLECTION_NAMESPACES:
        return False
    if schema == "INSPIRE_CADASTRAL_PARCEL":
        return namespace in set(base._GML_NAMESPACES) | _WFS_NAMESPACES
    return True


def _is_member(tag: str) -> bool:
    return base.split_tag(tag) in _MEMBER_TAGS


def validate_feature_membership(path: Path) -> dict:
    stack: list[str] = []
    root_tag: str | None = None
    supported = 0
    member_bound = 0
    schema_counts = {
        "INSPIRE_CADASTRAL_PARCEL": 0,
        "HMLR_PREDEFINED_FLATTENED": 0,
    }
    member_types: set[str] = set()
    collection_types: set[str] = set()

    for event, element in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            if root_tag is None:
                root_tag = element.tag
            schema = _feature_schema(element.tag)
            if schema is not None:
                supported += 1
                schema_counts[schema] += 1
                if not stack:
                    raise RuntimeError("CADASTRAL_FEATURE_AT_XML_ROOT")
                parent = stack[-1]
                if not _is_member(parent):
                    raise RuntimeError(f"CADASTRAL_FEATURE_NOT_DIRECT_MEMBER:{schema}")
                collection = next((tag for tag in reversed(stack[:-1]) if base.split_tag(tag)[1] == "FeatureCollection"), None)
                if collection is None or not _is_collection(collection, schema):
                    raise RuntimeError(f"CADASTRAL_FEATURE_COLLECTION_INVALID:{schema}")
                member_bound += 1
                member_types.add("|".join(base.split_tag(parent)))
                collection_types.add("|".join(base.split_tag(collection)))
            stack.append(element.tag)
            continue

        if not stack or stack[-1] != element.tag:
            raise RuntimeError("XML_ELEMENT_STACK_MISMATCH")
        stack.pop()
        element.clear()

    if root_tag is None:
        raise RuntimeError("GML_DOCUMENT_EMPTY")
    if supported == 0:
        raise RuntimeError("GML_CADASTRAL_FEATURE_SCHEMA_UNRECOGNISED")
    if member_bound != supported:
        raise RuntimeError(f"CADASTRAL_FEATURE_MEMBERSHIP_COUNT_MISMATCH:{member_bound}:{supported}")
    if all(count == 0 for count in schema_counts.values()):
        raise RuntimeError("GML_CADASTRAL_FEATURE_SCHEMA_UNRECOGNISED")

    return {
        "feature_membership_validation_passed": True,
        "supported_cadastral_feature_count": supported,
        "member_bound_cadastral_feature_count": member_bound,
        "membership_schema_counts": schema_counts,
        "accepted_member_types": sorted(member_types),
        "accepted_collection_types": sorted(collection_types),
        "feature_membership_policy": "supported cadastral feature must be a direct child of recognised GML/WFS member within a recognised FeatureCollection",
    }


def parse(path: Path, target_ids: set[str]) -> tuple[dict[str, list[dict]], dict]:
    membership = validate_feature_membership(path)
    found, summary = previous.parse(path, target_ids)
    return found, summary | membership


geometry = previous.geometry
