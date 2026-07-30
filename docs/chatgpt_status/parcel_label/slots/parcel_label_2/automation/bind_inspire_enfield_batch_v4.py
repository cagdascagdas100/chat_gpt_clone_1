from __future__ import annotations

import importlib.util
import socket
import threading
import time
import urllib.parse
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v3.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_v3", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V3_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
base = previous.base

base.TASK_VERSION = "6.3-bounded-dns-preflight-official-gml-batch"
_PRIMARY_HOST = urllib.parse.urlsplit(base.DOWNLOAD).hostname
if not _PRIMARY_HOST:
    raise RuntimeError("OFFICIAL_HMLR_PRIMARY_HOST_MISSING")

_PREFLIGHT_LOCK = threading.Lock()
_PREFLIGHT_OK = False
_PREFLIGHT_TTL_SECONDS = 300.0
_PREFLIGHT_AT = 0.0


def _resolve_primary() -> tuple[str, ...]:
    records = socket.getaddrinfo(_PRIMARY_HOST, 443, type=socket.SOCK_STREAM)
    addresses = sorted({record[4][0] for record in records if record and record[4]})
    if not addresses:
        raise RuntimeError("OFFICIAL_HMLR_DNS_NO_ADDRESSES")
    return tuple(addresses)


def _bounded_dns_preflight() -> tuple[str, ...]:
    global _PREFLIGHT_OK, _PREFLIGHT_AT
    now = time.monotonic()
    with _PREFLIGHT_LOCK:
        if _PREFLIGHT_OK and now - _PREFLIGHT_AT < _PREFLIGHT_TTL_SECONDS:
            return ()
        try:
            addresses = _resolve_primary()
        except Exception as exc:
            _PREFLIGHT_OK = False
            _PREFLIGHT_AT = now
            raise RuntimeError(
                f"OFFICIAL_HMLR_DNS_PREFLIGHT_FAILED:{_PRIMARY_HOST}:{type(exc).__name__}:{exc}"
            ) from exc
        _PREFLIGHT_OK = True
        _PREFLIGHT_AT = now
        return addresses


def fetch(url: str, timeout: int, attempts: int = 2):
    host = urllib.parse.urlsplit(url).hostname
    if host == _PRIMARY_HOST:
        _bounded_dns_preflight()
    return previous.fetch(url, timeout, attempts)


base.fetch = fetch
base.discover = previous.base.discover

if __name__ == "__main__":
    raise SystemExit(base.main())
