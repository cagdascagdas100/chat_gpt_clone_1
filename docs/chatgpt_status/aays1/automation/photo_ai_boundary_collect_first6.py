#!/usr/bin/env python3
"""
AAYS photo AI boundary collector, first batch scaffold.

Purpose:
- Read first6 manifest.
- Fetch listing pages.
- Extract candidate image URLs from og:image, twitter:image and img tags.
- Write a local JSON evidence manifest.

This script does not call a vision model by itself. It prepares inputs for a later
Vision API step: listing photos + existing polygon render.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[4]
MANIFEST = REPO_ROOT / "docs/chatgpt_status/aays1/photo_ai_boundary_review/first6_photo_ai_manifest.json"
OUT_DIR = REPO_ROOT / "england_map_web/data/geometry_review_3of4/photo_ai_evidence"
OUT_JSON = REPO_ROOT / "england_map_web/data/geometry_review_3of4/photo_ai_first6_collected.json"
UA = "Mozilla/5.0 AAYS-photo-ai-boundary-review/1.0"


class ImageHTMLParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        d = {str(k).lower(): str(v) for k, v in attrs if k and v}
        if tag.lower() == "meta":
            prop = (d.get("property") or d.get("name") or "").lower()
            if prop in {"og:image", "og:image:url", "twitter:image", "twitter:image:src"} and d.get("content"):
                self.images.append(urljoin(self.base_url, d["content"]))
        if tag.lower() == "img":
            for key in ("src", "data-src", "data-lazy-src"):
                if d.get(key):
                    self.images.append(urljoin(self.base_url, d[key]))
            if d.get("srcset"):
                for part in d["srcset"].split(","):
                    u = part.strip().split(" ")[0]
                    if u:
                        self.images.append(urljoin(self.base_url, u))


def fetch_text(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def candidate_images(html: str, base_url: str) -> list[str]:
    parser = ImageHTMLParser(base_url)
    parser.feed(html)
    imgs = []
    seen = set()
    for u in parser.images:
        if not u or u.startswith("data:"):
            continue
        if not re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", u, re.I):
            continue
        if u in seen:
            continue
        seen.add(u)
        imgs.append(u)
    return imgs[:12]


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for row in manifest["rows"]:
        row_id = row["row_id"]
        url = row["listing_url"]
        status = "ok"
        images: list[str] = []
        error = None
        try:
            html = fetch_text(url)
            images = candidate_images(html, url)
        except Exception as exc:  # noqa: BLE001
            status = "fetch_failed"
            error = str(exc)
        results.append({
            "row_id": row_id,
            "listing_url": url,
            "parcel_ref": row.get("parcel_ref"),
            "status": status,
            "candidate_image_urls": images,
            "image_count": len(images),
            "error": error,
            "next": "render polygon and run vision comparison" if images else "needs manual/source retry",
        })
        time.sleep(1)
    payload = {
        "version": "photo_ai_first6_collected_v1",
        "source_manifest": str(MANIFEST.relative_to(REPO_ROOT)),
        "rows": results,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
