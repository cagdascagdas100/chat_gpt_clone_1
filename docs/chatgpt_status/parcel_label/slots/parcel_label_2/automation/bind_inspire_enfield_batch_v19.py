from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v18.py")
base_spec = importlib.util.spec_from_file_location("parcel_label_2_v18", BASE_PATH)
if base_spec is None or base_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V18_IMPORT_FAILED")
previous = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(previous)

CANONICAL_PATH = Path(__file__).with_name("stream_canonical_inventory_v2.py")
canonical_spec = importlib.util.spec_from_file_location("parcel_label_2_full_canonical_inventory", CANONICAL_PATH)
if canonical_spec is None or canonical_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_CANONICAL_INVENTORY_V2_IMPORT_FAILED")
canonical_inventory = importlib.util.module_from_spec(canonical_spec)
canonical_spec.loader.exec_module(canonical_inventory)

base = previous.base
base.TASK_VERSION = "7.8-full-canonical-inventory-and-row-alignment-batch"
EXACT_WEB = base.REPO / "england_map_web/data/aays_21_slots/parcel_label_2/progress_wave27_exact_result_latest.json"
_ALLOWED_WRITES = {base.RESULT.resolve(), base.RECON.resolve(), EXACT_WEB.resolve()}
_original_write = previous._original_write
_POOL = previous._POOL


def write(path: Path, payload: dict) -> None:
    target = Path(path).resolve()
    if target not in _ALLOWED_WRITES:
        raise RuntimeError(f"PARCEL_LABEL_2_WRITE_PATH_NOT_ALLOWED:{target}")
    _original_write(target, payload)


def canonical():
    return canonical_inventory.canonical_targets(
        base.SOURCE,
        expected_blob_sha=base.BLOB,
        expected_feature_count=base.COUNT,
        target_ids=base.TARGET_IDS,
    )


base.WEB = EXACT_WEB
base.write = write
base.canonical = canonical
base.fetch = previous.fetch


def main() -> int:
    try:
        return base.main()
    finally:
        _POOL.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
