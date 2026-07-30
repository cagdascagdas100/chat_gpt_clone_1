from __future__ import annotations

import http.cookiejar
import importlib.util
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v13.py")
base_spec = importlib.util.spec_from_file_location("parcel_label_2_v13", BASE_PATH)
if base_spec is None or base_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V13_IMPORT_FAILED")
previous = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(previous)

STREAM_PATH = Path(__file__).with_name("stream_inspire_payload_v1.py")
stream_spec = importlib.util.spec_from_file_location("parcel_label_2_streaming_io", STREAM_PATH)
if stream_spec is None or stream_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_STREAMING_IO_IMPORT_FAILED")
streaming = importlib.util.module_from_spec(stream_spec)
stream_spec.loader.exec_module(streaming)

base = previous.base
base.TASK_VERSION = "7.3-streaming-canonical-and-download-batch"
EXACT_WEB = base.REPO / "england_map_web/data/aays_21_slots/parcel_label_2/progress_wave22_exact_result_latest.json"
_ALLOWED_WRITES = {base.RESULT.resolve(), base.RECON.resolve(), EXACT_WEB.resolve()}
_original_write = previous._original_write
_POOL = streaming.MappedPayloadPool()
_PRIMARY_HOST = urllib.parse.urlsplit(base.DOWNLOAD).hostname
if not _PRIMARY_HOST:
    raise RuntimeError("OFFICIAL_HMLR_PRIMARY_HOST_MISSING")
_MAX_DOWNLOAD_BYTES = 256 * 1024 * 1024
_MAX_GML_BYTES = 256 * 1024 * 1024
_MAX_ZIP_MEMBERS = 128
_MAX_ZIP_RATIO = 250.0
_COOKIE_JAR = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_COOKIE_JAR))


def _find_callable(module, name: str):
    seen: set[int] = set(); current = module
    for _ in range(20):
        if current is None or id(current) in seen: break
        seen.add(id(current)); value = getattr(current, name, None)
        if callable(value): return value
        current = getattr(current, "previous", None)
    return None


_DNS_PREFLIGHT = _find_callable(previous, "_bounded_dns_preflight")


def write(path: Path, payload: dict) -> None:
    target = Path(path).resolve()
    if target not in _ALLOWED_WRITES:
        raise RuntimeError(f"PARCEL_LABEL_2_WRITE_PATH_NOT_ALLOWED:{target}")
    _original_write(target, payload)


def canonical():
    return streaming.canonical_targets(base.SOURCE, expected_blob_sha=base.BLOB, expected_feature_count=base.COUNT, target_ids=base.TARGET_IDS)


def fetch(url: str, timeout: int, attempts: int = 2):
    parsed = urllib.parse.urlsplit(url); host = (parsed.hostname or "").casefold()
    if parsed.path.rstrip("/") == "/datasets/inspire/download":
        return previous.fetch(url, timeout, attempts)
    streaming.validate_https_url(url, primary_host=_PRIMARY_HOST, same_origin=True)
    if host == _PRIMARY_HOST.casefold() and _DNS_PREFLIGHT is not None: _DNS_PREFLIGHT()
    error = None
    for attempt in range(attempts):
        raw_path: Path | None = None
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TerraYield-AAYS/1.0", "Accept": "application/gml+xml,application/xml,text/xml,application/zip,application/octet-stream,*/*"})
            with _OPENER.open(request, timeout=timeout) as response:
                final_url = streaming.validate_https_url(response.geturl(), primary_host=_PRIMARY_HOST, same_origin=False)
                media_type = (response.headers.get_content_type() or "").lower()
                raw_path = streaming.stream_response_to_file(response, limit=_MAX_DOWNLOAD_BYTES)
            is_zip = zipfile.is_zipfile(raw_path)
            mapped, source_url = streaming.normalise_download_file(raw_path, final_url=final_url, media_type=media_type, pool=_POOL, max_gml_bytes=_MAX_GML_BYTES, max_zip_members=_MAX_ZIP_MEMBERS, max_zip_ratio=_MAX_ZIP_RATIO)
            if is_zip: raw_path.unlink(missing_ok=True)
            return mapped, source_url
        except Exception as exc:
            error = exc
            if raw_path is not None: raw_path.unlink(missing_ok=True)
            if attempt + 1 < attempts: time.sleep(2)
    raise RuntimeError(f"FETCH_FAILED after {attempts} attempts: {error}")


base.WEB = EXACT_WEB
base.write = write
base.canonical = canonical
base.fetch = fetch
base.sha256 = _POOL.sha256
base.discover = previous.discover


def main() -> int:
    try:
        return base.main()
    finally:
        _POOL.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
