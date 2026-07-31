from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v19.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v19", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V19_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

PIN_PATH = Path(__file__).with_name("stable_xml_source_v2.py")
pin_spec = importlib.util.spec_from_file_location("parcel_label_2_descriptor_pinning", PIN_PATH)
if pin_spec is None or pin_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_DESCRIPTOR_PINNING_IMPORT_FAILED")
pinning = importlib.util.module_from_spec(pin_spec)
pin_spec.loader.exec_module(pinning)

base = previous.base
_underlying_parse = previous.previous.parse


def parse(path: Path, target_ids: set[str], *, expected_sha256: str):
    (found, summary), evidence = pinning.guarded_descriptor_call(
        Path(path),
        expected_sha256=expected_sha256,
        operation=lambda stable_path: _underlying_parse(stable_path, target_ids),
    )
    return found, summary | evidence | {
        "xml_source_toctou_validation_passed": True,
        "xml_parse_bytes_bound_to_download_sha256": True,
        "xml_parser_uses_descriptor_pinned_source": True,
    }


geometry = previous.geometry
validate_collection_cardinality = previous.validate_collection_cardinality
