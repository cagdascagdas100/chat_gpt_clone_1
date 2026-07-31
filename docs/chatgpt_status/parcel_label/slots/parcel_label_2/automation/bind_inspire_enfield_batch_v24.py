from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v23.py")
base_spec = importlib.util.spec_from_file_location("parcel_label_2_v23", BASE_PATH)
if base_spec is None or base_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V23_IMPORT_FAILED")
previous = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(previous)

ZIP_PATH = Path(__file__).with_name("secure_zip_payload_v2.py")
zip_spec = importlib.util.spec_from_file_location("parcel_label_2_secure_zip", ZIP_PATH)
if zip_spec is None or zip_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_SECURE_ZIP_IMPORT_FAILED")
secure_zip = importlib.util.module_from_spec(zip_spec)
zip_spec.loader.exec_module(secure_zip)


def _find_attr(module, name: str):
    seen: set[int] = set()
    current = module
    for _ in range(32):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        if hasattr(current, name):
            return getattr(current, name)
        current = getattr(current, "previous", None)
    raise RuntimeError(f"PARCEL_LABEL_2_INHERITED_ATTRIBUTE_MISSING:{name}")


base = previous.base
streaming = _find_attr(previous, "streaming")
_original_normalise_download_file = streaming.normalise_download_file
base.TASK_VERSION = "8.3-zip-member-metadata-crc-and-size-integrity-batch"
EXACT_WEB = base.REPO / "england_map_web/data/aays_21_slots/parcel_label_2/progress_wave32_exact_result_latest.json"
_ALLOWED_WRITES = {base.RESULT.resolve(), base.RECON.resolve(), EXACT_WEB.resolve()}
_original_write = previous._original_write
_POOL = previous._POOL


def write(path: Path, payload: dict) -> None:
    target = Path(path).resolve()
    if target not in _ALLOWED_WRITES:
        raise RuntimeError(f"PARCEL_LABEL_2_WRITE_PATH_NOT_ALLOWED:{target}")
    _original_write(target, payload)


def normalise_download_file(raw_path: Path, **kwargs):
    return secure_zip.normalise_download_file(
        raw_path,
        base=streaming,
        fallback=_original_normalise_download_file,
        **kwargs,
    )


streaming.normalise_download_file = normalise_download_file
base.TASK_VERSION = "8.3-zip-member-metadata-crc-and-size-integrity-batch"
base.WEB = EXACT_WEB
base.write = write
base.parse = previous.validator.parse
base.geometry = previous.validator.geometry


def main() -> int:
    try:
        return base.main()
    finally:
        _POOL.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
