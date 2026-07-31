from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v16.py")
base_spec = importlib.util.spec_from_file_location("parcel_label_2_v16", BASE_PATH)
if base_spec is None or base_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V16_IMPORT_FAILED")
previous = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(previous)

TRANSPORT_PATH = Path(__file__).with_name("official_hmlr_transport_v3.py")
transport_spec = importlib.util.spec_from_file_location("parcel_label_2_public_dns_transport", TRANSPORT_PATH)
if transport_spec is None or transport_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_PUBLIC_DNS_TRANSPORT_IMPORT_FAILED")
transport = importlib.util.module_from_spec(transport_spec)
transport_spec.loader.exec_module(transport)

base = previous.base
base.TASK_VERSION = "7.6-public-dns-pinning-and-no-proxy-batch"
EXACT_WEB = base.REPO / "england_map_web/data/aays_21_slots/parcel_label_2/progress_wave25_exact_result_latest.json"
_ALLOWED_WRITES = {base.RESULT.resolve(), base.RECON.resolve(), EXACT_WEB.resolve()}
_original_write = previous._original_write
_POOL = previous._POOL

_INDEX_OPENER, _INDEX_COOKIE_JAR, _INDEX_PROXY_HANDLER, _INDEX_HTTPS_HANDLER = transport.build_public_dns_opener(
    previous._INDEX_REDIRECT_HANDLER,
    cookie_jar=previous._INDEX_COOKIE_JAR,
)
_BINARY_OPENER, _BINARY_COOKIE_JAR, _BINARY_PROXY_HANDLER, _BINARY_HTTPS_HANDLER = transport.build_public_dns_opener(
    previous._BINARY_REDIRECT_HANDLER,
    cookie_jar=previous._BINARY_COOKIE_JAR,
)
previous._INDEX_OPENER = _INDEX_OPENER
previous._BINARY_OPENER = _BINARY_OPENER


def write(path: Path, payload: dict) -> None:
    target = Path(path).resolve()
    if target not in _ALLOWED_WRITES:
        raise RuntimeError(f"PARCEL_LABEL_2_WRITE_PATH_NOT_ALLOWED:{target}")
    _original_write(target, payload)


base.WEB = EXACT_WEB
base.write = write
base.fetch = previous.fetch


def main() -> int:
    try:
        return base.main()
    finally:
        _POOL.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
