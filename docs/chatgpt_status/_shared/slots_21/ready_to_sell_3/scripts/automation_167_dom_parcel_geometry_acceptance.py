#!/usr/bin/env python3
"""Fail-closed DOM/public-host/parcel-geometry acceptance probe for ready_to_sell_3."""
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

class ProbeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.h1 = ""
        self.iframes: list[str] = []
        self._tag = None
    def handle_starttag(self, tag, attrs):
        self._tag = tag
        if tag == "iframe":
            self.iframes.append(dict(attrs).get("src", ""))
    def handle_endtag(self, tag):
        if self._tag == tag:
            self._tag = None
    def handle_data(self, data):
        if self._tag == "title":
            self.title += data.strip()
        elif self._tag == "h1":
            self.h1 += data.strip()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", default=".")
    p.add_argument("--base-url", default="http://127.0.0.1:8012")
    p.add_argument("--output", required=True)
    p.add_argument("--expected-status-sha256", required=True)
    p.add_argument("--expected-index-sha256", required=True)
    args = p.parse_args()

    root = Path(args.repo_root).resolve()
    status_path = root / "docs/chatgpt_status/_shared/slots_21/ready_to_sell_3/status_latest.json"
    index_path = root / "england_map_web/data/aays_21_slots/ready_to_sell_3/index.html"
    live_path = root / "england_map_web/data/aays_21_slots/ready_to_sell_3/ready_to_sell_3_waves_1509_1512_live_progress.html"
    out = root / args.output
    allowed = root / "docs/chatgpt_status/aays1/shards/ready_to_sell_3/validation/automation_167_dom_parcel_geometry_acceptance_latest.json"
    if out.resolve() != allowed.resolve():
        raise SystemExit("output path outside exact_write_paths")
    for path in (status_path, index_path, live_path):
        if not path.is_file():
            raise SystemExit(f"missing input: {path.relative_to(root)}")

    status_raw = status_path.read_bytes()
    index_raw = index_path.read_bytes()
    live_raw = live_path.read_bytes()
    checks = {
        "status_sha256_match": sha256_bytes(status_raw) == args.expected_status_sha256,
        "index_sha256_match": sha256_bytes(index_raw) == args.expected_index_sha256,
    }
    status = json.loads(status_raw)
    local_parser = ProbeParser()
    local_parser.feed(index_raw.decode("utf-8"))
    checks.update({
        "local_title": local_parser.title == "ReadyToSell 3",
        "local_h1": "ReadyToSell 3" in local_parser.h1,
        "local_iframe": "ready_to_sell_3_waves_1509_1512_live_progress.html" in local_parser.iframes,
        "live_gate_marker": "Automation 167 port-8012 DOM kanıtı yok" in live_raw.decode("utf-8"),
    })

    url = args.base_url.rstrip("/") + "/england_map_web/data/aays_21_slots/ready_to_sell_3/index.html"
    public = {"url": url, "ok": False}
    try:
        req = Request(url, headers={"User-Agent": "AAYS-ready-to-sell-3-acceptance/1.0"})
        with urlopen(req, timeout=20) as response:
            body = response.read()
            parser = ProbeParser()
            parser.feed(body.decode("utf-8"))
            public = {
                "url": url,
                "ok": response.status == 200,
                "status": response.status,
                "content_sha256": sha256_bytes(body),
                "title": parser.title,
                "h1": parser.h1,
                "iframes": parser.iframes,
            }
            checks["public_http_200"] = response.status == 200
            checks["public_title"] = parser.title == "ReadyToSell 3"
            checks["public_iframe"] = "ready_to_sell_3_waves_1509_1512_live_progress.html" in parser.iframes
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError) as exc:
        public["error"] = str(exc)
        checks["public_http_200"] = False
        checks["public_title"] = False
        checks["public_iframe"] = False

    parcel_matches = int(status.get("parcel_matches", 0))
    geometry_matches = int(status.get("geometry_matches", 0))
    checks["parcel_match_positive"] = parcel_matches > 0
    checks["geometry_match_positive"] = geometry_matches > 0

    completed = sum(bool(v) for v in checks.values())
    target = len(checks)
    result = {
        "schema_version": 3,
        "slot_id": "ready_to_sell_3",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state": "PUBLISHED" if completed == target else "BLOCKED",
        "panel_status": "PUBLISHED" if completed == target else "BLOCKED",
        "completed_count": completed,
        "target_count": target,
        "progress_percent": completed / target * 100,
        "checks": checks,
        "public_host": public,
        "parcel_matches": parcel_matches,
        "geometry_matches": geometry_matches,
        "fake_data": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(out)
    return 0 if completed == target else 2

if __name__ == "__main__":
    sys.exit(main())
