from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v9.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v9", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V9_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

SECURITY_PATH = Path(__file__).with_name("secure_xml_preflight_v1.py")
security_spec = importlib.util.spec_from_file_location("parcel_label_2_xml_security_preflight", SECURITY_PATH)
if security_spec is None or security_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_XML_SECURITY_PREFLIGHT_IMPORT_FAILED")
security = importlib.util.module_from_spec(security_spec)
security_spec.loader.exec_module(security)

base = previous.base


def parse(path: Path, target_ids: set[str]) -> tuple[dict[str, list[dict]], dict]:
    preflight = security.validate_xml_security(path)
    found, summary = previous.parse(path, target_ids)
    return found, summary | preflight


geometry = previous.geometry
validate_collection_cardinality = previous.validate_collection_cardinality
