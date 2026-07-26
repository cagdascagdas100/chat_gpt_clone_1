#!/usr/bin/env python3
"""Resolve the current official Lambeth HMLR INSPIRE source and probe exact IDs.

This is a fail-closed diagnostic for the existing single runner. It does not
measure elevation, promote candidates, create a runner, or submit a queue task.

Resolution policy:
1. fetch the current official INSPIRE download page;
2. require the page to list London Borough of Lambeth;
3. prefer the unique exact page href when recoverable;
4. otherwise use the previously verified official Lambeth endpoint captured by
   the successful July-2026 canonical measurement manifest;
5. stream/hash the downloaded archive, safely extract GML/XML, and scan complete
   CadastralParcel feature elements for the four exact INSPIRE IDs;
6. require exactly one feature per target ID before reporting READY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import requests

OFFICIAL_HOST = "use-land-property-data.service.gov.uk"
DEFAULT_PAGE = f"https://{OFFICIAL_HOST}/datasets/inspire/download"
PINNED_LAMBETH_ENDPOINT = f"https://{OFFICIAL_HOST}/datasets/inspire/download/London_Borough_of_Lambeth.zip"
KNOWN_JULY_2026_GML_SHA256 = "a736605d1816b1c12bdc16362f6ebb9644d177d94da04ef2e22124168889b4b9"
TARGET_IDS = ("36760596", "36758146", "36781190", "36776765")
MAX_DOWNLOAD_BYTES = 1_500_000_000
MAX_EXTRACTED_BYTES = 2_000_000_000


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class LinkParser(HTMLParser):
    BLOCKS = {"tr", "li", "div"}

    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._href: str | None = None
        self._anchor: list[str] = []
        self._stack: list[tuple[str, list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower in self.BLOCKS:
            self._stack.append((lower, []))
        if lower == "a":
            self._href = dict(attrs).get("href")
            self._anchor = []

    def handle_data(self, data: str) -> None:
        for _, parts in self._stack:
            parts.append(data)
        if self._href is not None:
            self._anchor.append(data)

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "a" and self._href:
            context = " ".join(self._stack[-1][1]).strip() if self._stack else ""
            self.links.append({
                "href": self._href,
                "anchor": " ".join(self._anchor).strip(),
                "context": context,
            })
            self._href = None
            self._anchor = []
        if self._stack and self._stack[-1][0] == lower:
            self._stack.pop()


def _official(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname == OFFICIAL_HOST


def _stream_download(session: requests.Session, url: str, path: Path, timeout: int) -> dict[str, Any]:
    if not _official(url):
        raise ValueError("download URL is not the pinned HMLR official host")
    path.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with session.get(url, timeout=timeout, stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        resolved = r.url
        ctype = r.headers.get("content-type", "")
        with path.open("wb") as out:
            for chunk in r.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError("HMLR download exceeds safety limit")
                out.write(chunk)
    if total == 0:
        raise ValueError("HMLR download is empty")
    head = path.read_bytes()[:512].lstrip().lower()
    if head.startswith(b"<html") or b"<!doctype html" in head:
        raise ValueError("HMLR endpoint returned HTML instead of archive/GML")
    return {"resolved_url": resolved, "content_type": ctype, "size_bytes": total, "sha256": _sha256(path)}


def _safe_vectors(download: Path, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    if not zipfile.is_zipfile(download):
        target = out_dir / "source.gml"
        download.replace(target)
        return [target]
    vectors: list[Path] = []
    total = 0
    with zipfile.ZipFile(download) as zf:
        for info in zf.infolist():
            suffix = Path(info.filename).suffix.lower()
            if info.is_dir() or suffix not in {".gml", ".xml"}:
                continue
            total += info.file_size
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError("HMLR extracted content exceeds safety limit")
            target = out_dir / Path(info.filename).name
            with zf.open(info) as src, target.open("wb") as dst:
                while chunk := src.read(1024 * 1024):
                    dst.write(chunk)
            vectors.append(target)
    if not vectors:
        raise ValueError("HMLR archive contains no GML/XML")
    return vectors


def _feature_text(element: ET.Element) -> str:
    parts: list[str] = []
    for node in element.iter():
        if node.text:
            parts.append(node.text.strip())
        for value in node.attrib.values():
            parts.append(str(value).strip())
    return "\n".join(parts)


def _probe_gml(path: Path, target_ids: tuple[str, ...]) -> dict[str, Any]:
    counts = {target: 0 for target in target_ids}
    feature_examples: dict[str, dict[str, Any]] = {}
    feature_count = 0
    epsg27700_mentions = 0
    coordinate_nodes = 0
    for event, elem in ET.iterparse(path, events=("end",)):
        local = _local(elem.tag)
        if local in {"posList", "pos", "coordinates"}:
            coordinate_nodes += 1
        for key, value in elem.attrib.items():
            if _local(key).lower() == "srsname" and "27700" in str(value):
                epsg27700_mentions += 1
        if local == "CadastralParcel":
            feature_count += 1
            text = _feature_text(elem)
            for target in target_ids:
                if re.search(rf"(?<!\d){re.escape(target)}(?!\d)", text):
                    counts[target] += 1
                    if target not in feature_examples:
                        srs_values = sorted({
                            str(v) for n in elem.iter() for k, v in n.attrib.items()
                            if _local(k).lower() == "srsname"
                        })
                        pos_lists = [
                            (n.text or "").strip() for n in elem.iter()
                            if _local(n.tag) in {"posList", "coordinates"} and (n.text or "").strip()
                        ]
                        feature_examples[target] = {
                            "feature_tag": local,
                            "srs_names": srs_values,
                            "coordinate_sequence_count": len(pos_lists),
                            "first_coordinate_sequence_prefix": pos_lists[0][:500] if pos_lists else None,
                        }
            elem.clear()
        elif local in {"featureMember", "member"}:
            elem.clear()
    return {
        "feature_count_scanned": feature_count,
        "target_feature_match_counts": counts,
        "target_feature_examples": feature_examples,
        "epsg27700_attribute_mentions": epsg27700_mentions,
        "coordinate_nodes_seen": coordinate_nodes,
        "all_targets_exactly_one_feature": all(v == 1 for v in counts.values()),
    }


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--download-page", default=DEFAULT_PAGE)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--user-agent", default="TerraYield-AAYS/height_difference_3-batch115")
    args = ap.parse_args(argv)

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": args.user_agent})

    page = session.get(args.download_page, timeout=args.timeout, allow_redirects=True)
    page.raise_for_status()
    page_body = page.content
    page_text = page_body.decode("utf-8", errors="replace")
    if "London Borough of Lambeth" not in page_text:
        raise ValueError("fresh HMLR page does not list London Borough of Lambeth")

    parser = LinkParser()
    parser.feed(page_text)
    exact_links: dict[str, dict[str, str]] = {}
    for item in parser.links:
        context = f"{item['context']} {item['anchor']} {item['href']}"
        if "London Borough of Lambeth" in context or "London_Borough_of_Lambeth" in item["href"]:
            resolved = urljoin(page.url, item["href"])
            if _official(resolved):
                exact_links[resolved] = {**item, "resolved": resolved}

    if len(exact_links) == 1:
        selected_url = next(iter(exact_links))
        resolution_method = "FRESH_PAGE_UNIQUE_EXACT_LAMBETH_LINK"
    elif len(exact_links) == 0:
        selected_url = PINNED_LAMBETH_ENDPOINT
        resolution_method = "FRESH_PAGE_LISTING_PLUS_PREVIOUSLY_VERIFIED_OFFICIAL_ENDPOINT"
    else:
        raise ValueError(f"ambiguous Lambeth links: {sorted(exact_links)}")

    raw = out / "London_Borough_of_Lambeth.download"
    download_meta = _stream_download(session, selected_url, raw, args.timeout)
    vectors = _safe_vectors(raw, out / "extracted")
    vector_records = []
    all_counts = {target: 0 for target in TARGET_IDS}
    target_examples: dict[str, Any] = {}
    for vector in vectors:
        probe = _probe_gml(vector, TARGET_IDS)
        for target, count in probe["target_feature_match_counts"].items():
            all_counts[target] += int(count)
        target_examples.update(probe["target_feature_examples"])
        vector_records.append({
            "path": str(vector),
            "size_bytes": vector.stat().st_size,
            "sha256": _sha256(vector),
            "known_july_2026_hash_match": _sha256(vector) == KNOWN_JULY_2026_GML_SHA256,
            "probe": probe,
        })

    ready = all(value == 1 for value in all_counts.values())
    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "status": "READY_EXACT_IDS" if ready else "BLOCKED_EXACT_ID_PROBE",
        "official_download_page": args.download_page,
        "download_page_resolved_url": page.url,
        "download_page_sha256": hashlib.sha256(page_body).hexdigest(),
        "fresh_page_lists_lambeth": True,
        "selected_download_url": selected_url,
        "resolution_method": resolution_method,
        "known_previous_successful_official_endpoint": PINNED_LAMBETH_ENDPOINT,
        "known_july_2026_gml_sha256": KNOWN_JULY_2026_GML_SHA256,
        "download": download_meta,
        "vectors": vector_records,
        "target_ids": list(TARGET_IDS),
        "target_feature_match_counts_total": all_counts,
        "target_feature_examples": target_examples,
        "all_targets_exactly_one_feature": ready,
        "candidate_promotion_allowed": False,
        "numeric_publish_allowed": False,
        "nearest_or_fuzzy_match_used": False,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "final_ready": False,
        "fake_data": False,
    }
    manifest = out / "lambeth_hmlr_exact_id_probe.json"
    _write(manifest, payload)
    print(json.dumps({"ok": ready, "status": payload["status"], "manifest": str(manifest)}))
    return 0 if ready else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise
