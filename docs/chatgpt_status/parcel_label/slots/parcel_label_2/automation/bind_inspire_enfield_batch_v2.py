from __future__ import annotations

import html
import http.cookiejar
import importlib.util
import io
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v1.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_v1", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V1_IMPORT_FAILED")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

base.TASK_VERSION = "6.1-official-inspire-zip-cookie-batch"
COOKIE_JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(COOKIE_JAR))


def fetch(url: str, timeout: int, attempts: int = 2):
    error = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 TerraYield-AAYS/1.0",
                    "Accept": "text/html,application/zip,application/octet-stream,*/*",
                },
            )
            with OPENER.open(request, timeout=timeout) as response:
                payload = response.read()
                final_url = response.geturl()
            if zipfile.is_zipfile(io.BytesIO(payload)):
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    members = sorted(name for name in archive.namelist() if name.lower().endswith(".gml"))
                    if len(members) != 1:
                        raise RuntimeError(f"ZIP_GML_MEMBER_COUNT:{len(members)}")
                    return archive.read(members[0]), final_url + "#" + members[0]
            return payload, final_url
        except Exception as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(2)
    raise RuntimeError(f"FETCH_FAILED after {attempts} attempts: {error}")


def discover(page: bytes, page_url: str):
    text = page.decode("utf-8", "replace")
    authority = re.search(re.escape(base.AUTHORITY), text, re.I)
    if authority is None:
        raise RuntimeError("LOCAL_AUTHORITY_NOT_LISTED")
    start = max(0, authority.start() - 3000)
    window = text[start : authority.end() + 6000]
    links = list(re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>.*?</a>', window, re.I | re.S))
    candidates = []
    for match in links:
        href = html.unescape(match.group(1))
        anchor = re.sub(r"<[^>]+>", " ", match.group(0))
        if href.lower().endswith((".zip", ".gml")) or "download" in anchor.lower():
            candidates.append(match)
    if not candidates:
        raise RuntimeError("AUTHORITY_ARCHIVE_LINK_NOT_FOUND")
    selected = min(candidates, key=lambda match: abs(start + match.start() - authority.start()))
    return urllib.parse.urljoin(page_url, html.unescape(selected.group(1)))


base.fetch = fetch
base.discover = discover

if __name__ == "__main__":
    raise SystemExit(base.main())
