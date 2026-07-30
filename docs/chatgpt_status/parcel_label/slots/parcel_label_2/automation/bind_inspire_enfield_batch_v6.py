from __future__ import annotations

import http.cookiejar
import importlib.util
import io
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v5.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_v5", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V5_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
base = previous.base

base.TASK_VERSION = "6.5-official-origin-and-xml-archive-safety-batch"

_PRIMARY_HOST = urllib.parse.urlsplit(base.DOWNLOAD).hostname
if not _PRIMARY_HOST:
    raise RuntimeError("OFFICIAL_HMLR_PRIMARY_HOST_MISSING")

_MAX_INDEX_BYTES = 8 * 1024 * 1024
_MAX_DOWNLOAD_BYTES = 256 * 1024 * 1024
_MAX_GML_BYTES = 256 * 1024 * 1024
_MAX_ZIP_RATIO = 250.0
_COOKIE_JAR = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_COOKIE_JAR))


def _read_bounded(response, limit: int) -> bytes:
    payload = response.read(limit + 1)
    if len(payload) > limit:
        raise RuntimeError(f"RESPONSE_SIZE_LIMIT_EXCEEDED:{limit}")
    return payload


def _validate_https_url(url: str, *, same_origin: bool) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.casefold() != "https":
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_NOT_HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_CONTAINS_USERINFO")
    if parsed.fragment:
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_CONTAINS_FRAGMENT")
    host = (parsed.hostname or "").casefold()
    if not host:
        raise RuntimeError("OFFICIAL_DOWNLOAD_URL_HOST_MISSING")
    if same_origin and host != _PRIMARY_HOST.casefold():
        raise RuntimeError(f"OFFICIAL_DOWNLOAD_URL_CROSS_ORIGIN:{host}")
    return url


def _reject_active_xml(payload: bytes) -> None:
    lowered = payload.lower()
    if b"<!doctype" in lowered:
        raise RuntimeError("GML_DOCTYPE_FORBIDDEN")
    if b"<!entity" in lowered:
        raise RuntimeError("GML_ENTITY_FORBIDDEN")


def _looks_like_gml(payload: bytes) -> bool:
    probe = payload[:8192].lstrip(b"\xef\xbb\xbf\x00\t\r\n ").lower()
    if not probe.startswith(b"<"):
        return False
    return any(token in probe for token in (b"featurecollection", b"cadastralparcel", b"xmlns:gml", b"opengis.net/gml"))


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts and bool(path.name)


def _normalise_download_payload(payload: bytes, final_url: str, media_type: str) -> tuple[bytes, str]:
    if len(payload) > _MAX_DOWNLOAD_BYTES:
        raise RuntimeError(f"DOWNLOAD_SIZE_LIMIT_EXCEEDED:{_MAX_DOWNLOAD_BYTES}")

    stream = io.BytesIO(payload)
    if zipfile.is_zipfile(stream):
        with zipfile.ZipFile(stream) as archive:
            infos = [info for info in archive.infolist() if not info.is_dir() and info.filename.lower().endswith(".gml")]
            if len(infos) != 1:
                raise RuntimeError(f"ZIP_GML_MEMBER_COUNT:{len(infos)}")
            info = infos[0]
            if not _safe_member_name(info.filename):
                raise RuntimeError("ZIP_GML_MEMBER_PATH_UNSAFE")
            if info.file_size > _MAX_GML_BYTES:
                raise RuntimeError(f"ZIP_GML_SIZE_LIMIT_EXCEEDED:{_MAX_GML_BYTES}")
            if info.file_size and info.compress_size == 0:
                raise RuntimeError("ZIP_GML_COMPRESSION_RATIO_INVALID")
            ratio = (info.file_size / info.compress_size) if info.compress_size else 0.0
            if ratio > _MAX_ZIP_RATIO:
                raise RuntimeError(f"ZIP_GML_COMPRESSION_RATIO_EXCEEDED:{ratio:.1f}")
            with archive.open(info, "r") as member:
                extracted = member.read(_MAX_GML_BYTES + 1)
            if len(extracted) > _MAX_GML_BYTES:
                raise RuntimeError(f"ZIP_GML_SIZE_LIMIT_EXCEEDED:{_MAX_GML_BYTES}")
            _reject_active_xml(extracted)
            if not _looks_like_gml(extracted):
                raise RuntimeError("ZIP_MEMBER_NOT_RECOGNISED_GML")
            return extracted, final_url + "#" + info.filename

    probe = payload[:4096].lower()
    if "html" in media_type or b"<html" in probe or b"<!doctype html" in probe:
        raise RuntimeError("BINARY_ROUTE_RETURNED_HTML")
    _reject_active_xml(payload)
    if not _looks_like_gml(payload):
        raise RuntimeError(f"UNEXPECTED_HMLR_PAYLOAD:{media_type or 'unknown'}")
    return payload, final_url


def discover(page: bytes, page_url: str) -> str:
    discovered = previous.discover(page, page_url)
    return _validate_https_url(discovered, same_origin=True)


def fetch(url: str, timeout: int, attempts: int = 2):
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").casefold()
    is_download_index = parsed.path.rstrip("/") == "/datasets/inspire/download"
    if host == _PRIMARY_HOST.casefold():
        previous.previous._bounded_dns_preflight()

    error = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 TerraYield-AAYS/1.0",
                    "Accept": "text/html,application/gml+xml,application/xml,text/xml,application/zip,application/octet-stream,*/*",
                },
            )
            with _OPENER.open(request, timeout=timeout) as response:
                final_url = _validate_https_url(response.geturl(), same_origin=False)
                media_type = (response.headers.get_content_type() or "").lower()
                payload = _read_bounded(response, _MAX_INDEX_BYTES if is_download_index else _MAX_DOWNLOAD_BYTES)

            if is_download_index:
                if "html" not in media_type and b"<html" not in payload[:4096].lower():
                    raise RuntimeError(f"DOWNLOAD_INDEX_UNEXPECTED_MEDIA_TYPE:{media_type}")
                return payload, final_url
            return _normalise_download_payload(payload, final_url, media_type)
        except Exception as exc:
            error = exc
            if attempt + 1 < attempts:
                previous.previous.time.sleep(2)
    raise RuntimeError(f"FETCH_FAILED after {attempts} attempts: {error}")


base.fetch = fetch
base.discover = discover

if __name__ == "__main__":
    raise SystemExit(base.main())
