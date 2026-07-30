from __future__ import annotations

import importlib.util
import io
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v2.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_v2", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V2_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
base = previous.base

base.TASK_VERSION = "6.2-official-gml-or-zip-strict-payload-batch"


def _looks_like_gml(payload: bytes) -> bool:
    probe = payload[:8192].lstrip(b"\xef\xbb\xbf\x00\t\r\n ").lower()
    if not probe.startswith(b"<"):
        return False
    return any(token in probe for token in (b"featurecollection", b"cadastralparcel", b"xmlns:gml", b"opengis.net/gml"))


def fetch(url: str, timeout: int, attempts: int = 2):
    error = None
    path = urllib.parse.urlsplit(url).path.rstrip("/")
    is_download_index = path == "/datasets/inspire/download"
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 TerraYield-AAYS/1.0",
                    "Accept": "text/html,application/gml+xml,application/xml,text/xml,application/zip,application/octet-stream,*/*",
                },
            )
            with previous.OPENER.open(request, timeout=timeout) as response:
                payload = response.read()
                final_url = response.geturl()
                media_type = (response.headers.get_content_type() or "").lower()

            if is_download_index:
                if "html" not in media_type and b"<html" not in payload[:4096].lower():
                    raise RuntimeError(f"DOWNLOAD_INDEX_UNEXPECTED_MEDIA_TYPE:{media_type}")
                return payload, final_url

            if zipfile.is_zipfile(io.BytesIO(payload)):
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    members = sorted(name for name in archive.namelist() if name.lower().endswith(".gml"))
                    if len(members) != 1:
                        raise RuntimeError(f"ZIP_GML_MEMBER_COUNT:{len(members)}")
                    extracted = archive.read(members[0])
                    if not _looks_like_gml(extracted):
                        raise RuntimeError("ZIP_MEMBER_NOT_RECOGNISED_GML")
                    return extracted, final_url + "#" + members[0]

            if "html" in media_type or b"<html" in payload[:4096].lower():
                raise RuntimeError("BINARY_ROUTE_RETURNED_HTML")
            if not _looks_like_gml(payload):
                raise RuntimeError(f"UNEXPECTED_HMLR_PAYLOAD:{media_type or 'unknown'}")
            return payload, final_url
        except Exception as exc:
            error = exc
            if attempt + 1 < attempts:
                previous.time.sleep(2)
    raise RuntimeError(f"FETCH_FAILED after {attempts} attempts: {error}")


base.fetch = fetch
base.discover = previous.discover

if __name__ == "__main__":
    raise SystemExit(base.main())
