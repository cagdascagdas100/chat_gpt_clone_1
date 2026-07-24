# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SLOT_ID = "internet_access_2"
API_BASE = "https://api-proxy.ofcom.org.uk/broadband/coverage"
API_PORTAL = "https://api.ofcom.org.uk/apis"
MAX_POSTCODES = 24
MIN_INTERVAL_SECONDS = 0.65
POSTCODE_RE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b", re.I)
KEY_ENV = "AAYS_OFCom_API_KEY"
INPUT_ENV = "AAYS_OFCom_POSTCODES_PATH"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalise_postcode(value: str) -> str:
    compact = re.sub(r"\s+", "", value.upper())
    if len(compact) < 5:
        raise ValueError(f"INVALID_POSTCODE:{value}")
    return compact[:-3] + " " + compact[-3:]


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            key_lower = str(key).casefold()
            if "postcode" in key_lower or "sample" in key_lower or "candidate" in key_lower:
                yield from iter_strings(item)


def load_postcodes(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    found: list[str] = []
    seen: set[str] = set()
    for text in iter_strings(payload):
        for match in POSTCODE_RE.finditer(text):
            postcode = normalise_postcode(match.group(1))
            if postcode not in seen:
                seen.add(postcode)
                found.append(postcode)
    if not found:
        raise RuntimeError("NO_POSTCODES_FOUND_IN_INPUT")
    if len(found) > MAX_POSTCODES:
        raise RuntimeError(f"TOO_MANY_POSTCODES:{len(found)}>{MAX_POSTCODES}")
    return found


def postcode_hash(postcode: str) -> str:
    return hashlib.sha256(postcode.encode("utf-8")).hexdigest()[:16]


def request_postcode(postcode: str, api_key: str, timeout: int) -> tuple[int, Any]:
    url = API_BASE + "/" + urllib.parse.quote(postcode, safe="")
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Ocp-Apim-Subscription-Key": api_key,
            "User-Agent": "AAYS-internet-access-2/1.0 (ephemeral Ofcom cross-check)",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(5_000_000)
            return int(response.status), json.loads(raw.decode("utf-8-sig"))
    except urllib.error.HTTPError as exc:
        raw = exc.read(1_000_000)
        try:
            body: Any = json.loads(raw.decode("utf-8-sig"))
        except Exception:
            body = {"message": raw.decode("utf-8", errors="replace")[:500]}
        return int(exc.code), body


def record_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("Count", "count"):
            if isinstance(payload.get(key), int):
                return int(payload[key])
        for key in ("Availability", "availability", "Results", "results", "Data", "data"):
            if isinstance(payload.get(key), list):
                return len(payload[key])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ephemeral Ofcom API cross-check for up to 24 postcodes")
    parser.add_argument("--input", help="JSON file containing the prepared postcode samples")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--summary-output", help="Optional operational summary JSON; never contains raw API data or postcodes")
    args = parser.parse_args()

    if os.environ.get("AAYS_SLOT_ID") not in (None, "", SLOT_ID):
        raise RuntimeError("WRONG_SLOT_EXECUTION_FORBIDDEN")

    input_value = args.input or os.environ.get(INPUT_ENV)
    summary: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "checked_at": now(),
        "api_portal": API_PORTAL,
        "api_endpoint_template": API_BASE + "/{PostCode}",
        "usage_mode": "EPHEMERAL_24_SAMPLE_CROSSCHECK_ONLY",
        "raw_api_payload_persisted": False,
        "coverage_values_persisted": False,
        "bulk_archive_replacement": False,
        "candidate_accuracy_written": 0,
        "final_ready": False,
    }

    if not input_value:
        summary.update({"state": "BLOCKED_SAMPLE_INPUT_REQUIRED", "sample_count": 0})
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 2

    postcodes = load_postcodes(Path(input_value).expanduser().resolve())
    summary["sample_count"] = len(postcodes)
    summary["sample_hashes"] = [postcode_hash(item) for item in postcodes]

    api_key = os.environ.get(KEY_ENV, "").strip()
    if not api_key:
        summary.update({"state": "BLOCKED_OFCom_SUBSCRIPTION_KEY_REQUIRED", "successful_queries": 0})
        if args.summary_output:
            Path(args.summary_output).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 2

    rows: list[dict[str, Any]] = []
    for index, postcode in enumerate(postcodes, start=1):
        if index > 1:
            time.sleep(MIN_INTERVAL_SECONDS)
        status, payload = request_postcode(postcode, api_key, args.timeout)
        rows.append(
            {
                "row": index,
                "postcode_hash": postcode_hash(postcode),
                "http_status": status,
                "record_count": record_count(payload) if status == 200 else 0,
                "state": "PASS" if status == 200 else "FAIL",
            }
        )

    successful = sum(1 for row in rows if row["state"] == "PASS")
    summary.update(
        {
            "state": "EPHEMERAL_CROSSCHECK_COMPLETE" if successful == len(rows) else "EPHEMERAL_CROSSCHECK_PARTIAL",
            "successful_queries": successful,
            "failed_queries": len(rows) - successful,
            "operation_rows": rows,
            "completed_at": now(),
        }
    )
    if args.summary_output:
        Path(args.summary_output).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if successful == len(rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
