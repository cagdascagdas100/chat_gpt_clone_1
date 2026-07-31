from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v20.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v20", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V20_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

SNAPSHOT_PATH = Path(__file__).with_name("stable_xml_source_v3.py")
snapshot_spec = importlib.util.spec_from_file_location("parcel_label_2_immutable_xml_snapshot", SNAPSHOT_PATH)
if snapshot_spec is None or snapshot_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_IMMUTABLE_XML_SNAPSHOT_IMPORT_FAILED")
snapshot = importlib.util.module_from_spec(snapshot_spec)
snapshot_spec.loader.exec_module(snapshot)

base = previous.base
_underlying_parse = previous.previous.parse


def parse(path: Path, target_ids: set[str], *, expected_sha256: str):
    (found, summary), evidence = snapshot.guarded_immutable_snapshot_call(
        Path(path),
        expected_sha256=expected_sha256,
        operation=lambda stable_path: _underlying_parse(stable_path, target_ids),
    )
    return found, summary | evidence | {
        "xml_source_toctou_validation_passed": True,
        "xml_parse_bytes_bound_to_download_sha256": True,
        "xml_parser_source_bound_to_immutable_private_snapshot": True,
        "xml_transient_original_mutation_cannot_affect_parser": True,
    }


geometry = previous.geometry
validate_collection_cardinality = previous.validate_collection_cardinality
