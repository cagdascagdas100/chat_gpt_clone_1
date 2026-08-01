#!/usr/bin/env python3
"""Bounded DOM acceptance probe for AAYS ready_to_sell_3 Automation 167."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

SLOT_ID = "ready_to_sell_3"
TASK_ID = "aays1-ready-to-sell-3-automation-167-dom-proof-20260720"
INPUT_RELATIVE = Path("england_map_web/data/aays_21_slots/ready_to_sell_3/index.html")
OUTPUT_RELATIVE = Path(
    "england_map_web/data/aays_21_slots/ready_to_sell_3/automation_167_dom_proof_latest.json"
)
EXPECTED_TITLE = "ReadyToSell 3"
EXPECTED_H1_PREFIX = "ReadyToSell 3"
EXPECTED_IFRAME = "ready_to_sell_3_waves_1509_1512_live_progress.html"
DEFAULT_BASE_URL = "http://127.0.0.1:8012"


class DomSummaryParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._capture: str | None = None
        self._buffer: list[str] = []
        self.title = ""
        self.h1_values: list[str] = []
        self.iframe_sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in {"title", "h1"}:
            self._capture = lowered
            self._buffer = []
        if lowered == "iframe":
            attr_map = {key.lower(): value for key, value in attrs}
            src = attr_map.get("src")
            if src:
                self.iframe_sources.append(src)

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered != self._capture:
            return
        value = " ".join("".join(self._buffer).split())
        if lowered == "title":
            self.title = value
        elif lowered == "h1":
            self.h1_values.append(value)
        self._capture = None
        self._buffer = []


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_repo_root(explicit: str | None) -> Path:
    candidate = explicit or os.environ.get("AAYS_REPO_ROOT") or os.getcwd()
    root = Path(candidate).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Repository root does not exist: {root}")
    return root


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)


def probe(repo_root: Path, base_url: str, timeout_seconds: float) -> tuple[dict[str, Any], bool]:
    input_path = (repo_root / INPUT_RELATIVE).resolve()
    output_path = (repo_root / OUTPUT_RELATIVE).resolve()
    if repo_root not in input_path.parents or repo_root not in output_path.parents:
        raise ValueError("Resolved path escaped repository root")

    source_bytes = input_path.read_bytes()
    source_sha256 = sha256_bytes(source_bytes)
    runtime_url = f"{base_url.rstrip('/')}/{INPUT_RELATIVE.as_posix()}"

    payload: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "source_path": INPUT_RELATIVE.as_posix(),
        "source_sha256": source_sha256,
        "runtime_url": runtime_url,
        "expected": {
            "title": EXPECTED_TITLE,
            "h1_prefix": EXPECTED_H1_PREFIX,
            "iframe_src": EXPECTED_IFRAME,
        },
        "fake_data": False,
        "dom_proof_passed": False,
        "state": "BLOCKED",
    }

    try:
        request = urllib.request.Request(runtime_url, headers={"User-Agent": "AAYS-Automation-167/1.0"})
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            runtime_bytes = response.read()
            status_code = int(response.status)
            content_type = response.headers.get("Content-Type", "")

        parser = DomSummaryParser()
        parser.feed(runtime_bytes.decode("utf-8", errors="replace"))
        checks = {
            "http_200": status_code == 200,
            "title_exact": parser.title == EXPECTED_TITLE,
            "h1_prefix": any(value.startswith(EXPECTED_H1_PREFIX) for value in parser.h1_values),
            "iframe_exact": EXPECTED_IFRAME in parser.iframe_sources,
        }
        passed = all(checks.values())
        payload.update(
            {
                "runtime_status_code": status_code,
                "runtime_content_type": content_type,
                "runtime_content_sha256": sha256_bytes(runtime_bytes),
                "observed": {
                    "title": parser.title,
                    "h1_values": parser.h1_values,
                    "iframe_sources": parser.iframe_sources,
                },
                "checks": checks,
                "dom_proof_passed": passed,
                "state": "PUBLISHED" if passed else "BLOCKED",
            }
        )
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        passed = False
        payload.update(
            {
                "runtime_error_type": type(exc).__name__,
                "runtime_error": str(exc),
                "checks": {
                    "http_200": False,
                    "title_exact": False,
                    "h1_prefix": False,
                    "iframe_exact": False,
                },
            }
        )

    write_json_atomic(output_path, payload)
    return payload, passed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Repository root; defaults to AAYS_REPO_ROOT or cwd")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    args = parser.parse_args()

    if args.timeout_seconds <= 0 or args.timeout_seconds > 60:
        parser.error("--timeout-seconds must be greater than 0 and at most 60")

    repo_root = resolve_repo_root(args.repo_root)
    payload, passed = probe(repo_root, args.base_url, args.timeout_seconds)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
