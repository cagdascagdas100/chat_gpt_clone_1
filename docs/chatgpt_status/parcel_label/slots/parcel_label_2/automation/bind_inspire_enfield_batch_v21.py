from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v20.py")
base_spec = importlib.util.spec_from_file_location("parcel_label_2_v20", BASE_PATH)
if base_spec is None or base_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V20_IMPORT_FAILED")
previous = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(previous)

VALIDATOR_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v9.py")
validator_spec = importlib.util.spec_from_file_location("parcel_label_2_collection_cardinality_validator", VALIDATOR_PATH)
if validator_spec is None or validator_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_COLLECTION_CARDINALITY_VALIDATOR_IMPORT_FAILED")
validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)

base = previous.base
base.TASK_VERSION = "8.0-feature-member-cardinality-and-collection-count-batch"
EXACT_WEB = base.REPO / "england_map_web/data/aays_21_slots/parcel_label_2/progress_wave29_exact_result_latest.json"
_ALLOWED_WRITES = {base.RESULT.resolve(), base.RECON.resolve(), EXACT_WEB.resolve()}
_original_write = previous._original_write
_POOL = previous._POOL


def write(path: Path, payload: dict) -> None:
    target = Path(path).resolve()
    if target not in _ALLOWED_WRITES:
        raise RuntimeError(f"PARCEL_LABEL_2_WRITE_PATH_NOT_ALLOWED:{target}")
    _original_write(target, payload)


base.WEB = EXACT_WEB
base.write = write
base.parse = validator.parse
base.geometry = validator.geometry


def main() -> int:
    try:
        return base.main()
    finally:
        _POOL.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
