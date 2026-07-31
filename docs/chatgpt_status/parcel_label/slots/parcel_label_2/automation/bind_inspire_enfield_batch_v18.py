from __future__ import annotations

import importlib.util
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v17.py")
base_spec = importlib.util.spec_from_file_location("parcel_label_2_v17", BASE_PATH)
if base_spec is None or base_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V17_IMPORT_FAILED")
previous = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(previous)

INTEGRITY_PATH = Path(__file__).with_name("official_hmlr_response_v1.py")
integrity_spec = importlib.util.spec_from_file_location("parcel_label_2_response_integrity", INTEGRITY_PATH)
if integrity_spec is None or integrity_spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_RESPONSE_INTEGRITY_IMPORT_FAILED")
integrity = importlib.util.module_from_spec(integrity_spec)
integrity_spec.loader.exec_module(integrity)


def _find_attr(module, name: str):
    seen: set[int] = set()
    current = module
    for _ in range(24):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        if hasattr(current, name):
            return getattr(current, name)
        current = getattr(current, "previous", None)
    raise RuntimeError(f"PARCEL_LABEL_2_INHERITED_ATTRIBUTE_MISSING:{name}")


def _find_transport_policy(module):
    seen: set[int] = set()
    current = module
    for _ in range(24):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        candidate = getattr(current, "transport", None)
        if callable(getattr(candidate, "validate_official_hmlr_url", None)):
            return candidate
        current = getattr(current, "previous", None)
    raise RuntimeError("PARCEL_LABEL_2_TRANSPORT_POLICY_MISSING")


base = previous.base
streaming = _find_attr(previous, "streaming")
transport_policy = _find_transport_policy(previous)
base.TASK_VERSION = "7.7-http-response-integrity-and-complete-body-batch"
EXACT_WEB = base.REPO / "england_map_web/data/aays_21_slots/parcel_label_2/progress_wave26_exact_result_latest.json"
_ALLOWED_WRITES = {base.RESULT.resolve(), base.RECON.resolve(), EXACT_WEB.resolve()}
_original_write = _find_attr(previous, "_original_write")
_POOL = _find_attr(previous, "_POOL")
_PRIMARY_HOST = _find_attr(previous, "_PRIMARY_HOST")
_MAX_INDEX_BYTES = _find_attr(previous, "_MAX_INDEX_BYTES")
_MAX_DOWNLOAD_BYTES = _find_attr(previous, "_MAX_DOWNLOAD_BYTES")
_MAX_GML_BYTES = _find_attr(previous, "_MAX_GML_BYTES")
_MAX_ZIP_MEMBERS = _find_attr(previous, "_MAX_ZIP_MEMBERS")
_MAX_ZIP_RATIO = _find_attr(previous, "_MAX_ZIP_RATIO")
_DNS_PREFLIGHT = _find_attr(previous, "_DNS_PREFLIGHT")
_INDEX_OPENER = _find_attr(previous, "_INDEX_OPENER")
_BINARY_OPENER = _find_attr(previous, "_BINARY_OPENER")


def write(path: Path, payload: dict) -> None:
    target = Path(path).resolve()
    if target not in _ALLOWED_WRITES:
        raise RuntimeError(f"PARCEL_LABEL_2_WRITE_PATH_NOT_ALLOWED:{target}")
    _original_write(target, payload)


def fetch(url: str, timeout: int, attempts: int = 2):
    parsed = urllib.parse.urlsplit(url)
    is_index = parsed.path.rstrip("/") == "/datasets/inspire/download"
    transport_policy.validate_official_hmlr_url(
        url,
        primary_host=_PRIMARY_HOST,
        require_primary=is_index,
    )
    if _DNS_PREFLIGHT is not None:
        _DNS_PREFLIGHT()
    opener = _INDEX_OPENER if is_index else _BINARY_OPENER
    error = None
    for attempt in range(attempts):
        raw_path: Path | None = None
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 TerraYield-AAYS/1.0",
                    "Accept": "text/html,application/gml+xml,application/xml,text/xml,application/zip,application/octet-stream,*/*",
                    "Accept-Encoding": "identity",
                },
            )
            with opener.open(request, timeout=timeout) as response:
                final_url = transport_policy.validate_official_hmlr_url(
                    response.geturl(),
                    primary_host=_PRIMARY_HOST,
                    require_primary=is_index,
                )
                media_type = (response.headers.get_content_type() or "").lower()
                limit = _MAX_INDEX_BYTES if is_index else _MAX_DOWNLOAD_BYTES
                metadata = integrity.validate_response_integrity(response, limit=limit)
                if is_index:
                    payload = integrity.read_bounded_complete(
                        response,
                        limit=limit,
                        metadata=metadata,
                    )
                else:
                    raw_path = streaming.stream_response_to_file(response, limit=limit)
                    integrity.verify_file_complete(raw_path, metadata)
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


def main() -> int:
    try:
        return base.main()
    finally:
        _POOL.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
