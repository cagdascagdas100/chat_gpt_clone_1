from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "security_public_safety_2"
EXPECTED_ROWS = 300
REQUIRED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch(url: str, timeout: int = 30) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-slot2-acceptance/2.0", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            return {"url": url, "http_status": response.status, "sha256": sha256_bytes(body), "body": body, "error": None}
    except Exception as exc:
        return {"url": url, "http_status": None, "sha256": None, "body": b"", "error": f"{type(exc).__name__}: {exc}"}


def browser_check(url: str) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        return {"available": False, "error": f"PLAYWRIGHT_IMPORT:{type(exc).__name__}:{exc}", "console_errors": [], "row_count": None}
    console_errors: list[str] = []
    page_errors: list[str] = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            page = browser.new_page()
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            response = page.goto(url, wait_until="networkidle", timeout=30000)
            row_count = page.locator("table tbody tr").count()
            body_slot = page.locator("body").get_attribute("data-slot-id")
            body_visible = page.locator("body").get_attribute("data-visible-row-count")
            browser.close()
        return {
            "available": True,
            "http_status": response.status if response else None,
            "row_count": row_count,
            "body_slot_id": body_slot,
            "body_visible_row_count": body_visible,
            "console_errors": console_errors,
            "page_errors": page_errors,
            "error": None,
        }
    except Exception as exc:
        return {"available": True, "error": f"BROWSER:{type(exc).__name__}:{exc}", "console_errors": console_errors, "page_errors": page_errors, "row_count": None}


def run(args: argparse.Namespace) -> dict[str, Any]:
    html_result = fetch(args.html_url)
    json_result = fetch(args.json_url)
    rows = None
    payload: dict[str, Any] = {}
    json_error = json_result["error"]
    if json_result["http_status"] == 200:
        try:
            payload = json.loads(json_result["body"].decode("utf-8-sig"))
            rows = len(payload.get("rows") or [])
        except Exception as exc:
            json_error = f"JSON_PARSE:{type(exc).__name__}:{exc}"
    guard = payload.get("canonical_guard") or {}
    exact_blob = guard.get("pass") is True and guard.get("observed_blob_sha") == REQUIRED_BLOB_SHA
    parity = bool((payload.get("artifacts") or {}).get("parity_pass"))
    all_rows_guarded = rows == EXPECTED_ROWS and all(int(row.get("accuracy_score_4") or 0) < 4 or exact_blob for row in (payload.get("rows") or []))

    html_text = html_result["body"].decode("utf-8", errors="replace")
    dom_tokens = {
        "slot_id": 'data-slot-id="security_public_safety_2"' in html_text,
        "row_count": 'data-visible-row-count="300"' in html_text,
        "final_false": 'data-final-ready="false"' in html_text,
        "table": "<table" in html_text and "<tbody" in html_text,
    }
    browser = browser_check(args.browser_url or args.html_url) if args.browser else {"available": False, "row_count": None, "console_errors": [], "page_errors": [], "error": "BROWSER_NOT_REQUESTED"}
    browser_console_zero = browser.get("available") is True and not browser.get("console_errors") and not browser.get("page_errors") and not browser.get("error")
    browser_rows_300 = browser.get("row_count") == EXPECTED_ROWS and browser.get("body_visible_row_count") == str(EXPECTED_ROWS)
    checks = {
        "html_http_200": html_result["http_status"] == 200,
        "json_http_200": json_result["http_status"] == 200,
        "json_rows_300": rows == EXPECTED_ROWS,
        "exact_canonical_blob_verified": exact_blob,
        "json_csv_geojson_parity": parity,
        "four_of_four_rows_blob_guarded": all_rows_guarded,
        "dom_slot_id": dom_tokens["slot_id"],
        "dom_row_count_300": dom_tokens["row_count"],
        "dom_final_false": dom_tokens["final_false"],
        "dom_table": dom_tokens["table"],
        "console_zero": browser_console_zero,
        "browser_visible_rows_300": browser_rows_300,
    }
    passed = sum(checks.values())
    output = {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "generated_at": utc_now(),
        "html": {key: value for key, value in html_result.items() if key != "body"},
        "json": {key: value for key, value in json_result.items() if key != "body"} | {"rows": rows, "parse_error": json_error},
        "canonical_guard": guard,
        "dom_tokens": dom_tokens,
        "browser": browser,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "browser_steps_pending": [] if browser_console_zero and browser_rows_300 else ["headless browser console capture", "rendered visible row count"],
        "final_ready": False,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html-url", required=True)
    parser.add_argument("--json-url", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--browser", action="store_true")
    parser.add_argument("--browser-url")
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({"passed": result["passed"], "total": result["total"], "final_ready": False}))
