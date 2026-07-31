from __future__ import annotations

import importlib.util
import re
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v8.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v8", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V8_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
base = previous.base

_SINGULAR_MEMBER_NAMES = {"featureMember", "member"}
_PLURAL_MEMBER_NAMES = {"featureMembers"}
_COUNT_NAMES = {"numberReturned", "numberMatched", "numberOfFeatures"}
_XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"


def _local(tag: str) -> str:
    return base.split_tag(tag)[1]


def _decimal_count(raw: str, name: str) -> int:
    value = raw.strip()
    if not re.fullmatch(r"[0-9]+", value):
        raise RuntimeError(f"FEATURE_COLLECTION_{name.upper()}_INVALID:{raw}")
    return int(value)


def _collection_metadata(element: ET.Element) -> dict[str, int]:
    values: dict[str, int] = {}
    for raw_name, raw_value in element.attrib.items():
        name = _local(raw_name)
        if name not in _COUNT_NAMES:
            continue
        if name == "numberMatched" and raw_value.strip().casefold() == "unknown":
            raise RuntimeError("FEATURE_COLLECTION_NUMBERMATCHED_UNKNOWN")
        parsed = _decimal_count(raw_value, name)
        if name in values and values[name] != parsed:
            raise RuntimeError(f"FEATURE_COLLECTION_{name.upper()}_CONFLICT")
        values[name] = parsed
    return values


def _has_external_member_reference(element: ET.Element) -> bool:
    for raw_name, raw_value in element.attrib.items():
        namespace, name = base.split_tag(raw_name)
        if (namespace == _XLINK_NAMESPACE and name == "href") or name.casefold() == "href":
            if raw_value.strip():
                return True
    return False


def validate_collection_cardinality(path: Path) -> dict:
    stack: list[ET.Element] = []
    collection_observed: dict[int, int] = {}
    collection_declared: list[dict] = []
    singular_supported: dict[int, int] = {}
    singular_direct_children: dict[int, int] = {}
    supported_count = 0

    for event, element in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            if stack:
                parent = stack[-1]
                parent_name = _local(parent.tag)
                if previous._is_member(parent.tag):
                    singular = parent_name in _SINGULAR_MEMBER_NAMES
                    plural = parent_name in _PLURAL_MEMBER_NAMES
                    if singular or plural:
                        if len(stack) < 2:
                            raise RuntimeError("FEATURE_MEMBER_COLLECTION_PARENT_MISSING")
                        collection = stack[-2]
                        schema = previous._feature_schema(element.tag)
                        if schema is not None:
                            supported_count += 1
                            if not previous._is_collection(collection.tag, schema):
                                raise RuntimeError(f"CADASTRAL_MEMBER_NOT_DIRECT_COLLECTION_CHILD:{schema}")
                            if singular:
                                singular_supported[id(parent)] = singular_supported.get(id(parent), 0) + 1
                        collection_observed[id(collection)] = collection_observed.get(id(collection), 0) + 1
                        if singular:
                            singular_direct_children[id(parent)] = singular_direct_children.get(id(parent), 0) + 1
            stack.append(element)
            continue

        if not stack or stack[-1] is not element:
            raise RuntimeError("XML_ELEMENT_STACK_MISMATCH")

        name = _local(element.tag)
        if name in _SINGULAR_MEMBER_NAMES and id(element) in singular_supported:
            if _has_external_member_reference(element):
                raise RuntimeError("CADASTRAL_FEATURE_MEMBER_XLINK_FORBIDDEN")
            supported = singular_supported[id(element)]
            direct_children = singular_direct_children.get(id(element), 0)
            if supported != 1:
                raise RuntimeError(f"CADASTRAL_FEATURE_MEMBER_SUPPORTED_COUNT:{supported}")
            if direct_children != 1:
                raise RuntimeError(f"CADASTRAL_FEATURE_MEMBER_CHILD_COUNT:{direct_children}")

        if name == "FeatureCollection" and id(element) in collection_observed:
            observed = collection_observed[id(element)]
            metadata = _collection_metadata(element)
            for key in ("numberReturned", "numberOfFeatures"):
                if key in metadata and metadata[key] != observed:
                    raise RuntimeError(f"FEATURE_COLLECTION_{key.upper()}_MISMATCH:{metadata[key]}:{observed}")
            if "numberMatched" in metadata and metadata["numberMatched"] != observed:
                raise RuntimeError(f"FEATURE_COLLECTION_NUMBERMATCHED_MISMATCH:{metadata['numberMatched']}:{observed}")
            collection_declared.append({"collection_type": "|".join(base.split_tag(element.tag)), "observed_direct_feature_count": observed, "declared_counts": metadata})

        stack.pop()
        element.clear()

    if stack:
        raise RuntimeError("XML_ELEMENT_STACK_NOT_EMPTY")
    if supported_count == 0:
        raise RuntimeError("GML_CADASTRAL_FEATURE_SCHEMA_UNRECOGNISED")
    if not collection_declared:
        raise RuntimeError("CADASTRAL_FEATURE_COLLECTION_CARDINALITY_NOT_OBSERVED")

    return {
        "feature_collection_cardinality_validation_passed": True,
        "supported_cadastral_feature_count_cardinality_scan": supported_count,
        "collection_cardinality_records": collection_declared,
        "collection_cardinality_policy": "member is direct collection child; singular member has exactly one inline feature; declared counts equal observed direct feature count",
    }


def parse(path: Path, target_ids: set[str]) -> tuple[dict[str, list[dict]], dict]:
    cardinality = validate_collection_cardinality(path)
    found, summary = previous.parse(path, target_ids)
    return found, summary | cardinality


geometry = previous.geometry
