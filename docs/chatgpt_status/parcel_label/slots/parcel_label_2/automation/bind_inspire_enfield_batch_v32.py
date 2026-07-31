from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v31.py")
base_spec = importlib.util.spec_from_file_location("parcel_label_2_v31", BASE_PATH)
if base_spec is None or base_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V31_IMPORT_FAILED")
previous = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(previous)

VALIDATOR_PATH = Path(__file__).with_name("validate_inspire_cadastral_parcel_v19.py")
validator_spec = importlib.util.spec_from_file_location("parcel_label_2_stable_source_validator", VALIDATOR_PATH)
if validator_spec is None or validator_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_STABLE_SOURCE_VALIDATOR_IMPORT_FAILED")
validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(validator)

base = previous.base
base.TASK_VERSION = "9.1-download-sha256-to-parser-source-stability-batch"
EXACT_WEB = base.REPO / "england_map_web/data/aays_21_slots/parcel_label_2/progress_wave40_exact_result_latest.json"
_ALLOWED_WRITES = {base.RESULT.resolve(), base.RECON.resolve(), EXACT_WEB.resolve()}
_original_write = previous._original_write
_original_sha256 = base.sha256
_POOL = previous._POOL
_expected_gml_sha256: str | None = None


def write(path: Path, payload: dict) -> None:
    target = Path(path).resolve()
    if target not in _ALLOWED_WRITES:
        raise RuntimeError(f"PARCEL_LABEL_2_WRITE_PATH_NOT_ALLOWED:{target}")
    _original_write(target, payload)


def sha256(payload) -> str:
    global _expected_gml_sha256
    if _expected_gml_sha256 is not None:
        raise RuntimeError("XML_EXPECTED_SHA256_ALREADY_CAPTURED")
    digest = str(_original_sha256(payload)).strip().lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RuntimeError("XML_DOWNLOAD_SHA256_INVALID")
    _expected_gml_sha256 = digest
    return digest


def parse(path: Path, target_ids: set[str]):
    global _expected_gml_sha256
    expected = _expected_gml_sha256
    if expected is None:
        raise RuntimeError("XML_EXPECTED_SHA256_NOT_CAPTURED")
    try:
        return validator.parse(Path(path), target_ids, expected_sha256=expected)
    finally:
        _expected_gml_sha256 = None


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
