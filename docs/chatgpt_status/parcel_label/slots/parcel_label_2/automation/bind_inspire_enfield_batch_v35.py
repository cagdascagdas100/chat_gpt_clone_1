from __future__ import annotations

import importlib.util
import os
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v34.py")
base_spec = importlib.util.spec_from_file_location("parcel_label_2_v34", BASE_PATH)
if base_spec is None or base_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V34_IMPORT_FAILED")
previous = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(previous)

VALIDATOR_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v22.py")
validator_spec = importlib.util.spec_from_file_location("parcel_label_2_bounded_snapshot_validator", VALIDATOR_PATH)
if validator_spec is None or validator_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_BOUNDED_SNAPSHOT_VALIDATOR_IMPORT_FAILED")
validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)


def _find_attr(module, name: str):
    seen: set[int] = set()
    current = module
    for _ in range(48):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        if hasattr(current, name):
            return getattr(current, name)
        current = getattr(current, "previous", None)
    raise RuntimeError(f"PARCEL_LABEL_2_INHERITED_ATTRIBUTE_MISSING:{name}")


base = previous.base
_sha_state = previous._sha_state
_previous_sha256 = base.sha256
_MAX_GML_BYTES = int(_find_attr(previous, "_MAX_GML_BYTES"))
base.TASK_VERSION = "9.4-exact-size-bounded-immutable-snapshot-batch"
EXACT_WEB = base.REPO / "england_map_web/data/aays_21_slots/parcel_label_2/progress_wave44_exact_result_latest.json"
_ALLOWED_WRITES = {base.RESULT.resolve(), base.RECON.resolve(), EXACT_WEB.resolve()}
_original_write = previous._original_write
_POOL = previous._POOL
_expected_gml_size_bytes: int | None = None


def _payload_size(payload) -> int:
    if isinstance(payload, (str, bytes, os.PathLike)) and not isinstance(payload, bytes):
        return int(Path(payload).stat().st_size)
    try:
        return int(len(payload))
    except (TypeError, AttributeError) as exc:
        raise RuntimeError("XML_DOWNLOAD_SIZE_UNAVAILABLE") from exc


def write(path: Path, payload: dict) -> None:
    target = Path(path).resolve()
    if target not in _ALLOWED_WRITES:
        raise RuntimeError(f"PARCEL_LABEL_2_WRITE_PATH_NOT_ALLOWED:{target}")
    _original_write(target, payload)


def sha256(payload) -> str:
    global _expected_gml_size_bytes
    if _expected_gml_size_bytes is not None:
        raise RuntimeError("XML_EXPECTED_SIZE_ALREADY_CAPTURED")
    size = _payload_size(payload)
    if size <= 0:
        raise RuntimeError("XML_DOWNLOAD_SIZE_INVALID")
    if size > _MAX_GML_BYTES:
        raise RuntimeError(f"XML_DOWNLOAD_SIZE_LIMIT_EXCEEDED:{size}:{_MAX_GML_BYTES}")
    try:
        digest = _previous_sha256(payload)
    except Exception:
        _expected_gml_size_bytes = None
        raise
    _expected_gml_size_bytes = size
    return digest


def parse(path: Path, target_ids: set[str]):
    global _expected_gml_size_bytes
    expected_sha256 = _sha_state._expected_gml_sha256
    expected_size = _expected_gml_size_bytes
    if expected_sha256 is None:
        raise RuntimeError("XML_EXPECTED_SHA256_NOT_CAPTURED")
    if expected_size is None:
        raise RuntimeError("XML_EXPECTED_SIZE_NOT_CAPTURED")
    try:
        return validator.parse(
            Path(path),
            target_ids,
            expected_sha256=expected_sha256,
            expected_size_bytes=expected_size,
            max_bytes=_MAX_GML_BYTES,
        )
    finally:
        _sha_state._expected_gml_sha256 = None
        _expected_gml_size_bytes = None


base.WEB = EXACT_WEB
base.write = write
base.sha256 = sha256
base.parse = parse
base.geometry = validator.geometry


def main() -> int:
    try:
        return base.main()
    finally:
        _POOL.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
