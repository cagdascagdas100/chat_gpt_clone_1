from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v18.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_validator_v18", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_VALIDATOR_V18_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

STABILITY_PATH = Path(__file__).with_name("stable_xml_source_v1.py")
stability_spec = importlib.util.spec_from_file_location("parcel_label_2_xml_source_stability", STABILITY_PATH)
if stability_spec is None or stability_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_XML_SOURCE_STABILITY_IMPORT_FAILED")
stability = importlib.util.module_from_spec(stability_spec)
stability_spec.loader.exec_module(stability)

base = previous.base


def parse(
    path: Path,
    target_ids: set[str],
    *,
    expected_sha256: str,
) -> tuple[dict[str, list[dict]], dict]:
    (found, summary), evidence = stability.guarded_call(
        Path(path),
        expected_sha256=expected_sha256,
        operation=lambda: previous.parse(Path(path), target_ids),
    )
    return found, summary | evidence | {
        "xml_parse_bytes_bound_to_download_sha256": True,
        "xml_source_toctou_validation_passed": True,
    }


geometry = previous.geometry
validate_collection_cardinality = previous.validate_collection_cardinality
