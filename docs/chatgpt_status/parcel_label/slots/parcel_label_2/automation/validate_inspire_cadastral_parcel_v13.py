from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v12.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v12", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V12_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

BACKEND_PATH = Path(__file__).with_name("secure_lxml_backend_v1.py")
backend_spec = importlib.util.spec_from_file_location("parcel_label_2_secure_lxml_backend", BACKEND_PATH)
if backend_spec is None or backend_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_SECURE_LXML_BACKEND_IMPORT_FAILED")
backend = importlib.util.module_from_spec(backend_spec)
backend_spec.loader.exec_module(backend)

base = previous.base
_patched_modules = backend.patch_validator_chain(previous)
_underlying_parse = previous._underlying_parse


def parse(path: Path, target_ids: set[str]) -> tuple[dict[str, list[dict]], dict]:
    preflight = backend.validate_xml_structure(path)
    found, summary = _underlying_parse(path, target_ids)
    return found, summary | preflight | {
        "xml_backend_patched_validator_modules": list(_patched_modules),
        "xml_backend_expat_required": False,
    }


geometry = previous.geometry
validate_collection_cardinality = previous.validate_collection_cardinality
