from __future__ import annotations

import http.cookiejar
import importlib.util
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v14.py")
base_spec = importlib.util.spec_from_file_location("parcel_label_2_v14", BASE_PATH)
if base_spec is None or base_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V14_IMPORT_FAILED")
previous = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(previous)

TRANSPORT_PATH = Path(__file__).with_name("official_hmlr_transport_v1.py")
transport_spec = importlib.util.spec_from_file_location("parcel_label_2_trusted_transport", TRANSPORT_PATH)
if transport_spec is None or transport_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_TRUSTED_TRANSPORT_IMPORT_FAILED")
transport = importlib.util.module_from_spec(transport_spec)
transport_spec.loader.exec_module(transport)

base = previous.base
streaming = previous.streaming
base.TASK_VERSION = "7.4-trusted-hmlr-redirect-and-origin-pinning-batch"
EXACT_WEB = base.REPO / "england_map_web/data/aays_21_slots/parcel_label_2/progress_wave23_exact_result_latest.json"
_ALLOWED_WRITES = {base.RESULT.resolve(), base.RECON.resolve(), EXACT_WEB.resolve()}
_original_write = previous._original_write
_POOL = previous._POOL
_PRIMARY_HOST = previous._PRIMARY_HOST
_MAX_INDEX_BYTES = 8 * 1024 * 1024
_MAX_DOWNLOAD_BYTES = previous._MAX_DOWNLOAD_BYTES
_MAX_GML_BYTES = previous._MAX_GML_BYTES
_MAX_ZIP_MEMBERS = previous._MAX_ZIP_MEMBERS
_MAX_ZIP_RATIO = previous._MAX_ZIP_RATIO
_DNS_PREFLIGHT = previous._DNS_PREFLIGHT
_COOKIE_JAR = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(
    transport.TrustedHMLRRedirectHandler(_PRIMARY_HOST),
    urllib.request.HTTPCookieProcessor(_COOKIE_JAR),
)


def write(path: Path, payload: dict) -> None:
    target = Path(path).resolve()
    if target not in _ALLOWED_WRITES:
        raise RuntimeError(f"PARCEL_LABEL_2_WRITE_PATH_NOT_ALLOWED:{target}")
    _original_write(target, payload)


def _read_bounded(response, limit: int) -> bytes:
    payload = response.read(limit + 1)
    if len(payload) > limit:
        raise RuntimeError(f"RESPONSE_SIZE_LIMIT_EXCEEDED:{limit}")
    return payload


def fetch(url: str, timeout: int, attempts: int = 2):
    parsed = urllib.parse.urlsplit(url)
    is_index = parsed.path.rstrip("/") == "/datasets/inspire/download"
    transport.validate_official_hmlr_url(url, primary_host=_PRIMARY_HOST, require_primary=is_index)
    if _DNS_PREFLIGHT is not None:
        _DNS_PREFLIGHT()
    error = None
    for attempt in range(attempts):
        raw_path: Path | None = None
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 TerraYield-AAYS/1.0",
                    "Accept": "text/html,application/gml+xml,application/xml,text/xml,application/zip,application/octet-stream,*/*",
                },
            )
            with _OPENER.open(request, timeout=timeout) as response:
                final_url = transport.validate_official_hmlr_url(
                    response.geturl(), primary_host=_PRIMARY_HOST, require_primary=is_index
                )
                media_type = (response.headers.get_content_type() or "").lower()
                if is_index:
                    payload = _read_bounded(response, _MAX_INDEX_BYTES)
                else:
                    raw_path = streaming.stream_response_to_file(response, limit=_MAX_DOWNLOAD_BYTES)
            if is_index:
                if "html" not in media_type and b"<html" not in payload[:4096].lower():
                    raise RuntimeError(f"DOWNLOAD_INDEX_UNEXPECTED_MEDIA_TYPE:{media_type}")
                return payload, final_url
            assert raw_path is not None
            is_zip = zipfile.is_zipfile(raw_path)
            mapped, source_url = streaming.normalise_download_file(
                raw_path,
                final_url=final_url,
                media_type=media_type,
                pool=_POOL,
                max_gml_bytes=_MAX_GML_BYTES,
                max_zip_members=_MAX_ZIP_MEMBERS,
                max_zip_ratio=_MAX_ZIP_RATIO,
            )
            if is_zip:
                raw_path.unlink(missing_ok=True)
            return mapped, source_url
        except Exception as exc:
            error = exc
            if raw_path is not None:
                raw_path.unlink(missing_ok=True)
            if attempt + 1 < attempts:
                time.sleep(2)
    raise RuntimeError(f"FETCH_FAILED after {attempts} attempts: {error}")


base.WEB = EXACT_WEB
base.write = write
base.fetch = fetch
base.discover = previous.discover


def main() -> int:
    try:
        return base.main()
    finally:
        _POOL.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
