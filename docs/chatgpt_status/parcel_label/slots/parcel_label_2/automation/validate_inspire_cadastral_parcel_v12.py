from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v11.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v11", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V11_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

STRUCTURE_PATH = Path(__file__).with_name("secure_xml_structure_v3.py")
structure_spec = importlib.util.spec_from_file_location("parcel_label_2_xml_structure_preflight_v3", STRUCTURE_PATH)
if structure_spec is None or structure_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_XML_STRUCTURE_V3_IMPORT_FAILED")
structure = importlib.util.module_from_spec(structure_spec)
structure_spec.loader.exec_module(structure)

base = previous.base
_underlying_parse = previous._underlying_parse


def parse(path: Path, target_ids: set[str]) -> tuple[dict[str, list[dict]], dict]:
    preflight = structure.validate_xml_structure(path)
    found, summary = _underlying_parse(path, target_ids)
    return found, summary | preflight


geometry = previous.geometry
validate_collection_cardinality = previous.validate_collection_cardinality
