from __future__ import annotations

import hashlib
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v5.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v5", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V5_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
base = previous.base

_PREDEFINED = "PREDEFINED"
_PREDEFINED_REFERENCE = "NATIONALCADASTRALREFERENCE"
_PREDEFINED_INSPIRE_ID = "INSPIREID"


def _detect_feature_schema(path: Path) -> tuple[str, dict]:
    cp_count = 0
    predefined_count = 0
    foreign_predefined_count = 0
    for _, element in ET.iterparse(path, events=("end",)):
        namespace, name = base.split_tag(element.tag)
        if name == "CadastralParcel" and base._is_cp_namespace(namespace):
            cp_count += 1
        elif name == _PREDEFINED:
            if namespace:
                foreign_predefined_count += 1
            else:
                predefined_count += 1
        element.clear()
    if cp_count and predefined_count:
        raise RuntimeError("MIXED_CADASTRAL_FEATURE_SCHEMAS")
    if cp_count:
        return "INSPIRE_CADASTRAL_PARCEL", {
            "recognised_cadastral_parcel_features": cp_count,
            "recognised_predefined_features": 0,
            "ignored_foreign_predefined_features": foreign_predefined_count,
        }
    if predefined_count:
        return "HMLR_PREDEFINED_FLATTENED", {
            "recognised_cadastral_parcel_features": 0,
            "recognised_predefined_features": predefined_count,
            "ignored_foreign_predefined_features": foreign_predefined_count,
        }
    raise RuntimeError("GML_CADASTRAL_FEATURE_SCHEMA_UNRECOGNISED")


def _parse_predefined(path: Path, target_ids: set[str]) -> tuple[dict[str, list[dict]], dict]:
    found = {target: [] for target in target_ids}
    scanned = 0
    ignored_non_reference_text_matches = 0
    ignored_foreign_predefined_features = 0
    for _, element in ET.iterparse(path, events=("end",)):
        element_namespace, element_name = base.split_tag(element.tag)
        if element_name != _PREDEFINED:
            continue
        if element_namespace:
            ignored_foreign_predefined_features += 1
            element.clear()
            continue

        references: set[str] = set()
        inspire_ids: set[str] = set()
        for node in element.iter():
            node_namespace, node_name = base.split_tag(node.tag)
            text = (node.text or "").strip()
            if node_namespace:
                continue
            if node_name == _PREDEFINED_REFERENCE and text:
                references.add(text)
            elif node_name == _PREDEFINED_INSPIRE_ID and text:
                inspire_ids.add(text)

        hits = references & target_ids
        all_text_hits = {(node.text or "").strip() for node in element.iter()} & target_ids
        ignored_non_reference_text_matches += len(all_text_hits - hits)
        if not hits:
            element.clear()
            continue
        if len(hits) != 1:
            raise RuntimeError(f"PREDEFINED_TARGET_REFERENCE_COUNT:{len(hits)}")
        if len(references) != 1:
            raise RuntimeError(f"PREDEFINED_NATIONAL_REFERENCE_COUNT:{len(references)}")
        target = next(iter(hits))
        if inspire_ids and inspire_ids != {target}:
            raise RuntimeError("PREDEFINED_INSPIRE_ID_REFERENCE_MISMATCH")

        scanned += 1
        record = {
            "feature_element": _PREDEFINED,
            "feature_namespace": "",
            "feature_schema": "HMLR_PREDEFINED_FLATTENED",
            "feature_sha256": hashlib.sha256(ET.tostring(element, encoding="utf-8")).hexdigest(),
            "national_cadastral_reference": target,
            "predefined_inspire_id": next(iter(inspire_ids), None),
            "predefined_inspire_id_exact_match": inspire_ids == {target},
        } | previous.geometry(element)
        found[target].append(record)
        element.clear()

    return found, {
        "matched_cadastral_parcels_scanned": scanned,
        "identifier_match_field": _PREDEFINED_REFERENCE,
        "identifier_namespace_policy": "unnamespaced HMLR PREDEFINED exact field only",
        "feature_schema": "HMLR_PREDEFINED_FLATTENED",
        "ignored_non_reference_text_matches": ignored_non_reference_text_matches,
        "ignored_foreign_predefined_features": ignored_foreign_predefined_features,
    }


def parse(path: Path, target_ids: set[str]) -> tuple[dict[str, list[dict]], dict]:
    schema, detection = _detect_feature_schema(path)
    if schema == "INSPIRE_CADASTRAL_PARCEL":
        found, summary = base.parse(path, target_ids)
        return found, summary | detection | {"feature_schema": schema}
    found, summary = _parse_predefined(path, target_ids)
    return found, summary | detection


geometry = previous.geometry
