#!/usr/bin/env python3
"""Fail-closed browser acceptance utility for the existing 300-row artifact.

This is not a generator, task runner, recovery refresh, or business writer. It only
accepts an already-present HTML body after verifying its Git blob identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

EXPECTED_BLOB_SHA = "eb5ddcf8cc60356e9ec8ebe65211ecb002f94876"
EXPECTED_ROWS = 300
EXPECTED_FIRST = "parcel_30762"
EXPECTED_LAST = "parcel_31061"


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--expected-blob-sha", default=EXPECTED_BLOB_SHA)
    args = parser.parse_args()

    html_path = Path(args.html_path)
    output_path = Path(args.output)
    result: dict[str, Any] = {
        "state": "FAIL_CLOSED",
        "html_path": str(html_path),
        "expected_blob_sha": args.expected_blob_sha,
        "expected_rows": EXPECTED_ROWS,
        "expected_first": EXPECTED_FIRST,
        "expected_last": EXPECTED_LAST,
        "business_rows_written": 0,
        "canonical_acceptance": False,
    }

    try:
        data = html_path.read_bytes()
        actual_blob_sha = git_blob_sha(data)
        result["bytes"] = len(data)
        result["actual_blob_sha"] = actual_blob_sha
        result["blob_identity_pass"] = actual_blob_sha == args.expected_blob_sha
        if not result["blob_identity_pass"]:
            raise RuntimeError("Git blob identity mismatch")

        html = data.decode("utf-8")
        console_messages: list[dict[str, str]] = []
        page_errors: list[str] = []
        request_failures: list[dict[str, str]] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=args.chromium,
                args=["--no-sandbox"],
            )
            page = browser.new_page()
            page.on("console", lambda m: console_messages.append({"type": m.type, "text": m.text}))
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.on("requestfailed", lambda r: request_failures.append({"url": r.url, "failure": str(r.failure)}))
            page.set_content(html, wait_until="load")

            parcel_cells = page.locator("tbody tr td:first-child")
            parcel_ids = [
                value.strip()
                for value in parcel_cells.all_text_contents()
                if value.strip().startswith("parcel_")
            ]
            result.update(
                {
                    "chromium_version": subprocess.check_output([args.chromium, "--version"], text=True).strip(),
                    "injection_method": "playwright_page_set_content_no_navigation",
                    "candidate_dom_rows": len(parcel_ids),
                    "first_parcel_id": parcel_ids[0] if parcel_ids else None,
                    "last_parcel_id": parcel_ids[-1] if parcel_ids else None,
                    "console_messages": console_messages,
                    "page_errors": page_errors,
                    "request_failures": request_failures,
                    "script_elements": page.locator("script").count(),
                    "external_src_elements": page.locator("[src]").count(),
                }
            )
            browser.close()

        gates = {
            "blob_identity": result["blob_identity_pass"],
            "candidate_dom_rows_300": result["candidate_dom_rows"] == EXPECTED_ROWS,
            "first_parcel": result["first_parcel_id"] == EXPECTED_FIRST,
            "last_parcel": result["last_parcel_id"] == EXPECTED_LAST,
            "no_console_errors": not any(m["type"] == "error" for m in console_messages),
            "no_page_errors": not page_errors,
            "no_request_failures": not request_failures,
            "no_script_elements": result["script_elements"] == 0,
            "no_external_src_elements": result["external_src_elements"] == 0,
        }
        result["gates"] = gates
        result["canonical_acceptance"] = all(gates.values())
        result["state"] = "PASS" if result["canonical_acceptance"] else "FAIL_CLOSED"
    except Exception as exc:  # fail closed and preserve evidence
        result["error"] = f"{type(exc).__name__}: {exc}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["canonical_acceptance"] else 2


if __name__ == "__main__":
    sys.exit(main())
