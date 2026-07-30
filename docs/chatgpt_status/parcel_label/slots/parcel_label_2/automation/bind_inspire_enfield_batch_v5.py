from __future__ import annotations

import importlib.util
import re
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

BASE_PATH = Path(__file__).with_name("bind_inspire_enfield_batch_v4.py")
spec = importlib.util.spec_from_file_location("parcel_label_2_v4", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("PARCEL_LABEL_2_V4_IMPORT_FAILED")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
base = previous.base

base.TASK_VERSION = "6.4-exact-authority-row-link-official-gml-batch"


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


class _AuthorityRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_row = False
        self._row_depth = 0
        self._text: list[str] = []
        self._links: list[str] = []
        self.rows: list[tuple[str, tuple[str, ...]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.casefold()
        if tag == "tr":
            if self._in_row:
                self._row_depth += 1
            else:
                self._in_row = True
                self._row_depth = 1
                self._text = []
                self._links = []
            return
        if self._in_row and tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() != "tr" or not self._in_row:
            return
        self._row_depth -= 1
        if self._row_depth == 0:
            self.rows.append((" ".join(self._text), tuple(self._links)))
            self._in_row = False

    def handle_data(self, data: str) -> None:
        if self._in_row:
            self._text.append(data)


def discover(page: bytes, page_url: str) -> str:
    parser = _AuthorityRowParser()
    parser.feed(page.decode("utf-8", "replace"))
    authority = _normalise(base.AUTHORITY)
    matching_rows = [row for row in parser.rows if authority in _normalise(row[0])]
    if len(matching_rows) != 1:
        raise RuntimeError(f"AUTHORITY_ROW_MATCH_COUNT:{len(matching_rows)}")

    links: list[str] = []
    for raw in matching_rows[0][1]:
        raw = raw.strip()
        if not raw or raw.startswith("#") or raw.casefold().startswith(("javascript:", "mailto:")):
            continue
        links.append(urllib.parse.urljoin(page_url, raw))
    unique_links = sorted(set(links))
    if len(unique_links) != 1:
        raise RuntimeError(f"AUTHORITY_ROW_DOWNLOAD_LINK_COUNT:{len(unique_links)}")
    return unique_links[0]


base.fetch = previous.fetch
base.discover = discover

if __name__ == "__main__":
    raise SystemExit(base.main())
