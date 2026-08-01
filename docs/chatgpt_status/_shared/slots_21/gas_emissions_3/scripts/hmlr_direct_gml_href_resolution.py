#!/usr/bin/env python3
"""Bounded, fail-closed resolver for official HM Land Registry authority GML hrefs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


class BlockAnchorParser(HTMLParser):
    BLOCK_TAGS = {"tr", "li", "article", "section", "div"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[dict[str, Any]] = []
        self.blocks: list[dict[str, Any]] = []
        self.current_href: str | None = None
        self.current_anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.BLOCK_TAGS:
            self.stack.append({"tag": tag, "text": [], "anchors": []})
        if tag == "a":
            href = dict(attrs).get("href")
            self.current_href = href
            self.current_anchor_text = []

    def handle_data(self, data: str) -> None:
        if self.stack:
            self.stack[-1]["text"].append(data)
        if self.current_href is not None:
            self.current_anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self.current_href is not None:
            anchor = {
                "href": self.current_href,
                "text": " ".join("".join(self.current_anchor_text).split()),
            }
            if self.stack:
                self.stack[-1]["anchors"].append(anchor)
            self.current_href = None
            self.current_anchor_text = []
        if tag in self.BLOCK_TAGS and self.stack:
            block = self.stack.pop()
            block["text"] = " ".join("".join(block["text"]).split())
            if block["text"] or block["anchors"]:
                self.blocks.append(block)
            if self.stack:
                self.stack[-1]["text"].append(block["text"])
                self.stack[-1]["anchors"].extend(block["anchors"])


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--expected-slot", default="gas_emissions_3")
    p.add_argument("--expected-target-count", default=2, type=int)
    p.add_argument("--expected-input-sha256", required=True)
    p.add_argument("--expected-manifest-sha256", required=True)
    p.add_argument("--html-fixture", type=Path)
    return p.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def resolve_targets(html: str, base_url: str, targets: list[dict[str, str]]) -> list[dict[str, Any]]:
    parser = BlockAnchorParser()
    parser.feed(html)
    results: list[dict[str, Any]] = []
    for target in targets:
        authority = target["authority_name"]
        authority_key = normalise(authority)
        candidates: list[str] = []
        for block in parser.blocks:
            if authority_key not in normalise(block["text"]):
                continue
            for anchor in block["anchors"]:
                href = anchor.get("href") or ""
                anchor_text = normalise(anchor.get("text") or "")
                absolute = urllib.parse.urljoin(base_url, href)
                parsed = urllib.parse.urlparse(absolute)
                path = parsed.path.casefold()
                if (
                    parsed.scheme == "https"
                    and parsed.netloc
                    and (path.endswith(".gml") or "gml" in path)
                    and ("download" in anchor_text or ".gml" in anchor_text)
                ):
                    candidates.append(absolute)
        unique = sorted(set(candidates))
        results.append(
            {
                "target_id": target["target_id"],
                "authority_name": authority,
                "attempt_completed": True,
                "direct_download_href_resolved": len(unique) == 1,
                "resolved_href": unique[0] if len(unique) == 1 else None,
                "candidate_count": len(unique),
                "decision": "HREF_RESOLVED" if len(unique) == 1 else "NO_DATA_CONTINUE",
            }
        )
    return results


def fetch_html(url: str, timeout_seconds: int, user_agent: str) -> tuple[str | None, dict[str, Any]]:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "text/html"})
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds, context=context) as response:
            raw = response.read(8_000_000)
            content_type = response.headers.get("Content-Type", "")
            encoding = response.headers.get_content_charset() or "utf-8"
            html = raw.decode(encoding, errors="replace")
            return html, {
                "fetch_state": "FETCHED",
                "final_url": response.geturl(),
                "http_status": response.status,
                "content_type": content_type,
                "response_sha256": sha256_bytes(raw),
                "response_bytes": len(raw),
            }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        return None, {
            "fetch_state": "NO_DATA_CONTINUE",
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
        }


def main() -> int:
    args = parse_args()
    input_bytes = args.input.read_bytes()
    manifest_bytes = args.manifest.read_bytes()
    if sha256_bytes(input_bytes) != args.expected_input_sha256:
        raise ValueError("input SHA mismatch")
    if sha256_bytes(manifest_bytes) != args.expected_manifest_sha256:
        raise ValueError("manifest SHA mismatch")

    previous = json.loads(input_bytes)
    manifest = json.loads(manifest_bytes)
    if previous.get("slot_id") != args.expected_slot:
        raise ValueError("unexpected input slot")
    if previous.get("state") != "NO_DATA_CONTINUE":
        raise ValueError("previous task not fail-closed")
    if previous.get("next_unverified_step") != "RESOLVE_DIRECT_HMLR_GML_DOWNLOAD_HREFS":
        raise ValueError("unexpected prerequisite step")
    if manifest.get("schema_version") != 3 or manifest.get("slot_id") != args.expected_slot:
        raise ValueError("manifest schema/slot mismatch")
    if manifest.get("input_sha256") != args.expected_input_sha256:
        raise ValueError("manifest input SHA mismatch")

    targets = manifest.get("target_records")
    if not isinstance(targets, list) or len(targets) != args.expected_target_count:
        raise ValueError("target count mismatch")
    source_url = manifest["download_page"]["source_url"]

    if args.html_fixture:
        html = args.html_fixture.read_text(encoding="utf-8")
        fetch_meta = {
            "fetch_state": "FIXTURE",
            "final_url": source_url,
            "http_status": 200,
            "content_type": "text/html; charset=utf-8",
            "response_sha256": sha256_bytes(html.encode("utf-8")),
            "response_bytes": len(html.encode("utf-8")),
        }
    else:
        html, fetch_meta = fetch_html(
            source_url,
            int(manifest["network_policy"]["timeout_seconds"]),
            manifest["network_policy"]["user_agent"],
        )

    if html is None:
        results = [
            {
                "target_id": target["target_id"],
                "authority_name": target["authority_name"],
                "attempt_completed": True,
                "direct_download_href_resolved": False,
                "resolved_href": None,
                "candidate_count": 0,
                "decision": "NO_DATA_CONTINUE",
            }
            for target in targets
        ]
    else:
        results = resolve_targets(html, fetch_meta.get("final_url") or source_url, targets)

    completed = sum(bool(item["attempt_completed"]) for item in results)
    resolved = sum(bool(item["direct_download_href_resolved"]) for item in results)
    state = "HREFS_RESOLVED" if resolved == args.expected_target_count else "NO_DATA_CONTINUE"
    next_step = (
        "DOWNLOAD_AND_VALIDATE_HMLR_GML_FILES"
        if resolved == args.expected_target_count
        else "ACQUIRE_OFFICIAL_HMLR_DOWNLOAD_PAGE_HTML_OR_DIRECT_HREF_EVIDENCE"
    )

    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": args.expected_slot,
        "task_batch": 260,
        "state": state,
        "result": "DIRECT_HMLR_GML_HREF_RESOLUTION_ATTEMPTED_FAIL_CLOSED",
        "first_unverified_step_completed": "RESOLVE_DIRECT_HMLR_GML_DOWNLOAD_HREFS",
        "next_unverified_step": next_step,
        "input": {
            "path": args.input.as_posix(),
            "sha256": sha256_bytes(input_bytes),
            "manifest_path": args.manifest.as_posix(),
            "manifest_sha256": sha256_bytes(manifest_bytes),
        },
        "fetch": fetch_meta,
        "counts": {
            "completed_count": completed,
            "target_count": args.expected_target_count,
            "authority_resolution_attempts": completed,
            "direct_download_hrefs_resolved": resolved,
            "raw_gml_files_downloaded": 0,
            "raw_polygon_geometries": 0,
            "verified_inspire_ids": 0,
            "parcel_bindings": 0,
        },
        "decision": {
            "href_gate_passed": resolved == args.expected_target_count,
            "authority_entry_text_alone_is_not_download_url": True,
            "ambiguous_or_missing_href_is_rejected": True,
            "inferred_values": 0,
            "fake_data": False,
        },
        "targets": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    tmp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
